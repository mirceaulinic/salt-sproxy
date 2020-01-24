# -*- coding: utf-8 -*-
# Copyright 2019 Mircea Ulinic. All rights reserved.
#
# The contents of this file are licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with the
# License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
'''
Salt Runner to invoke arbitrary commands on network devices that are not
managed via a Proxy or regular Minion. Therefore, this Runner doesn't
necessarily require the targets to be up and running, as it will connect to
collect the Grains, compile the Pillar, then execute the commands.
'''
from __future__ import absolute_import, print_function, unicode_literals

# Import Python std lib
import copy
import time
import hashlib
import logging
import threading
import multiprocessing

# Import Salt modules
import salt.cache
import salt.wheel
import salt.loader
import salt.output
import salt.version
import salt.utils.jid
import salt.utils.master
from salt.ext import six
from salt.minion import SMinion
from salt.ext.six.moves import range
import salt.utils.stringutils
import salt.defaults.exitcodes
from salt.exceptions import SaltSystemExit
from salt.defaults import DEFAULT_TARGET_DELIM

import salt.utils.napalm
import salt.utils.dictupdate

try:
    from salt.utils.platform import is_proxy
    from salt.utils.args import clean_kwargs
except ImportError:
    from salt.utils import is_proxy  # pylint: disable=unused-import
    from salt.utils import clean_kwargs

try:
    import progressbar

    HAS_PROGRESSBAR = True
except ImportError:
    HAS_PROGRESSBAR = False

# ------------------------------------------------------------------------------
# module properties
# ------------------------------------------------------------------------------

log = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# property functions
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# helper functions -- will not be exported
# ------------------------------------------------------------------------------


def _napalm_is_proxy(opts):
    return opts.get('proxy', {}).get('proxytype') == 'napalm'


# Point the native is_proxy function to the above, so it doesn't check whether
# we're actually running under a Proxy Minion
salt.utils.napalm.is_proxy = _napalm_is_proxy


def _is_proxy():
    return True


# Same rationale as above, for any other Proxy type.
is_proxy = _is_proxy


def _salt_call_and_return(
    minion_id,
    function,
    queue,
    unreachable_devices,
    failed_devices,
    arg=None,
    jid=None,
    events=True,
    **opts
):
    '''
    '''
    opts['jid'] = jid
    ret = salt_call(
        minion_id,
        function,
        unreachable_devices=unreachable_devices,
        failed_devices=failed_devices,
        **opts
    )
    if events:
        __salt__['event.send'](
            'proxy/runner/{jid}/ret/{minion_id}'.format(minion_id=minion_id, jid=jid),
            {
                'fun': function,
                'fun_args': arg,
                'id': minion_id,
                'jid': jid,
                'return': ret,
                'success': True,
            },
        )
    queue.put({minion_id: ret})


def _receive_replies_async(queue):
    '''
    '''
    while True:
        ret = queue.get()
        if ret == 'FIN.':
            break
        # When async, print out the replies as soon as they arrive
        # after passing them through the outputter of choice
        out_fmt = salt.output.out_format(
            ret, __opts__.get('output', 'nested'), opts=__opts__
        )

        salt.utils.stringutils.print_cli(out_fmt)


# The SProxyMinion class is back-ported from Salt 2019.2.0 (to be released soon)
# and extended to allow more flexible options for the (pre-)loading of the
# Pillars and the Grains.
class SProxyMinion(SMinion):
    '''
    Create an object that has loaded all of the minion module functions,
    grains, modules, returners etc.  The SProxyMinion allows developers to
    generate all of the salt minion functions and present them with these
    functions for general use.
    '''

    def _matches_target(self):
        match_func = self.matchers.get(
            '{0}_match.match'.format(self.opts['__tgt_type']), None
        )
        if match_func is None:
            return False
        if self.opts['__tgt_type'] in ('grain', 'grain_pcre', 'pillar'):
            delimiter = self.opts.get('delimiter', DEFAULT_TARGET_DELIM)
            if not match_func(self.opts['__tgt'], delimiter=delimiter):
                return False
        elif not match_func(self.opts['__tgt']):
            return False
        else:
            if not self.matchers['glob_match.match'](self.opts['__tgt']):
                return False
        return True

    def gen_modules(self, initial_load=False):
        '''
        Tell the minion to reload the execution modules.

        CLI Example:

        .. code-block:: bash

            salt '*' sys.reload_modules
        '''
        cached_grains = None
        if self.opts.get('proxy_use_cached_grains', True):
            cached_grains = self.opts.pop('proxy_cached_grains', None)

        if not cached_grains and self.opts.get('proxy_preload_grains', True):
            loaded_grains = salt.loader.grains(self.opts)
            self.opts['grains'].update(loaded_grains)
        elif cached_grains:
            self.opts['grains'].update(cached_grains)

        if (
            self.opts['roster_opts']
            and self.opts.get('proxy_merge_roster_grains', True)
            and 'grains' in self.opts['roster_opts']
            and isinstance(self.opts['roster_opts']['grains'], dict)
        ):
            # Merge the Grains from the Roster opts
            log.debug('Merging Grains with the Roster provided ones')
            self.opts['grains'] = salt.utils.dictupdate.merge(
                self.opts['roster_opts']['grains'], self.opts['grains']
            )

        cached_pillar = None
        if self.opts.get('proxy_use_cached_pillar', True):
            cached_pillar = self.opts.pop('proxy_cached_pillar', None)
        if not cached_pillar and self.opts.get('proxy_load_pillar', True):
            self.opts['pillar'] = salt.pillar.get_pillar(
                self.opts,
                self.opts['grains'],
                self.opts['id'],
                saltenv=self.opts['saltenv'],
                pillarenv=self.opts.get('pillarenv'),
            ).compile_pillar()
        elif cached_pillar:
            self.opts['pillar'] = salt.utils.dictupdate.merge(
                cached_pillar, self.opts['pillar']
            )

        if self.opts['roster_opts'] and self.opts.get('proxy_merge_roster_opts', True):
            if 'proxy' not in self.opts['pillar']:
                self.opts['pillar']['proxy'] = {}
            self.opts['pillar']['proxy'] = salt.utils.dictupdate.merge(
                self.opts['pillar']['proxy'], self.opts['roster_opts']
            )
            self.opts['pillar']['proxy'].pop('name', None)

        if self.opts.get('preload_targeting', False) or self.opts.get(
            'invasive_targeting', False
        ):
            log.debug('Loading the Matchers modules')
            self.matchers = salt.loader.matchers(self.opts)

        if self.opts.get('preload_targeting', False):
            log.debug(
                'Preload targeting requested, trying to see if %s matches the target %s (%s)',
                self.opts['id'],
                str(self.opts['__tgt']),
                self.opts['__tgt_type'],
            )
            matched = self._matches_target()
            if not matched:
                return

        if 'proxy' not in self.opts['pillar'] and 'proxy' not in self.opts:
            errmsg = (
                'No "proxy" configuration key found in pillar or opts '
                'dictionaries for id {id}. Check your pillar/options '
                'configuration and contents. Salt-proxy aborted.'
            ).format(id=self.opts['id'])
            log.error(errmsg)
            self._running = False
            raise SaltSystemExit(code=salt.defaults.exitcodes.EX_GENERIC, msg=errmsg)

        if 'proxy' not in self.opts:
            self.opts['proxy'] = self.opts['pillar']['proxy']

        # Then load the proxy module
        self.utils = salt.loader.utils(self.opts)
        self.proxy = salt.loader.proxy(self.opts, utils=self.utils)
        self.functions = salt.loader.minion_mods(
            self.opts, utils=self.utils, notify=False, proxy=self.proxy
        )
        self.functions.pack['__grains__'] = self.opts['grains']
        self.returners = None
        if self.opts['returner']:
            self.returners = salt.loader.returners(
                self.opts, self.functions, proxy=self.proxy
            )

        fq_proxyname = self.opts['proxy']['proxytype']
        self.functions.pack['__proxy__'] = self.proxy
        self.proxy.pack['__salt__'] = self.functions
        self.proxy.pack['__ret__'] = self.returners
        self.proxy.pack['__pillar__'] = self.opts['pillar']

        # No need to inject the proxy into utils, as we don't need scheduler for
        # this sort of short living Minion.
        # self.utils = salt.loader.utils(self.opts, proxy=self.proxy)
        self.proxy.pack['__utils__'] = self.utils

        # Reload all modules so all dunder variables are injected
        self.proxy.reload_modules()

        if self.opts.get('proxy_no_connect', False):
            log.info('Requested not to initialize the connection with the device')
        else:
            log.debug('Trying to initialize the connection with the device')
            # When requested --no-connect, don't init the connection, but simply
            # go ahead and execute the function requested.
            if (
                '{0}.init'.format(fq_proxyname) not in self.proxy
                or '{0}.shutdown'.format(fq_proxyname) not in self.proxy
            ):
                errmsg = (
                    '[{0}] Proxymodule {1} is missing an init() or a shutdown() or both. '.format(
                        self.opts['id'], fq_proxyname
                    )
                    + 'Check your proxymodule.  Salt-proxy aborted.'
                )
                log.error(errmsg)
                self._running = False
                if self.unreachable_devices is not None:
                    self.unreachable_devices.append(self.opts['id'])
                raise SaltSystemExit(
                    code=salt.defaults.exitcodes.EX_GENERIC, msg=errmsg
                )

            proxy_init_fn = self.proxy[fq_proxyname + '.init']
            try:
                proxy_init_fn(self.opts)
                self.connected = True
            except Exception as exc:
                log.error(
                    'Encountered error when starting up the connection with %s:',
                    self.opts['id'],
                )
                if self.unreachable_devices is not None:
                    self.unreachable_devices.append(self.opts['id'])
                raise
            if not cached_grains and self.opts.get('proxy_load_grains', True):
                # When the Grains are loaded from the cache, no need to re-load them
                # again.
                loaded_grains = salt.loader.grains(self.opts, proxy=self.proxy)
                self.opts['grains'] = salt.utils.dictupdate.merge(
                    self.opts['grains'], loaded_grains
                )
            self.functions.pack['__grains__'] = self.opts['grains']
        self.grains_cache = copy.deepcopy(self.opts['grains'])

        if self.opts.get('invasive_targeting', False):
            log.info(
                'Invasive targeting requested, trying to see if %s matches the target %s (%s)',
                self.opts['id'],
                str(self.opts['__tgt']),
                self.opts['__tgt_type'],
            )
            matched = self._matches_target()
            if not matched:
                # Didn't match, shutting down this Proxy Minion, and exiting.
                log.debug(
                    '%s does not match the target expression, aborting', self.opts['id']
                )
                proxy_shut_fn = self.proxy[fq_proxyname + '.shutdown']
                proxy_shut_fn(self.opts)
                return

        self.ready = True


class StandaloneProxy(SProxyMinion):
    def __init__(
        self, opts, unreachable_devices=None
    ):  # pylint: disable=super-init-not-called
        self.opts = opts
        self.connected = False
        self.ready = False
        self.unreachable_devices = unreachable_devices
        self.gen_modules()


# ------------------------------------------------------------------------------
# callable functions
# ------------------------------------------------------------------------------


def salt_call(
    minion_id,
    function=None,
    unreachable_devices=None,
    failed_devices=None,
    with_grains=True,
    with_pillar=True,
    preload_grains=True,
    preload_pillar=True,
    default_grains=None,
    default_pillar=None,
    cache_grains=False,
    cache_pillar=False,
    use_cached_grains=True,
    use_cached_pillar=True,
    use_existing_proxy=False,
    no_connect=False,
    jid=None,
    roster_opts=None,
    test_ping=False,
    tgt=None,
    tgt_type=None,
    preload_targeting=False,
    invasive_targeting=False,
    failhard=False,
    timeout=60,
    returner='',
    returner_config='',
    returner_kwargs={},
    args=(),
    **kwargs
):
    '''
    Invoke a Salt Execution Function that requires or invokes an NAPALM
    functionality (directly or indirectly).

    minion_id:
        The ID of the Minion to compile Pillar data for.

    function
        The name of the Salt function to invoke.

    preload_grains: ``True``
        Whether to preload the Grains before establishing the connection with
        the remote network device.

    default_grains:
        Dictionary of the default Grains to make available within the functions
        loaded.

    with_grains: ``True``
        Whether to load the Grains modules and collect Grains data and make it
        available inside the Execution Functions.
        The Grains will be loaded after opening the connection with the remote
        network device.

    preload_pillar: ``True``
        Whether to preload Pillar data before opening the connection with the
        remote network device.

    default_pillar:
        Dictionary of the default Pillar data to make it available within the
        functions loaded.

    with_pillar: ``True``
        Whether to load the Pillar modules and compile Pillar data and make it
        available inside the Execution Functions.

    use_cached_pillar: ``True``
        Use cached Pillars whenever possible. If unable to gather cached data,
        it falls back to compiling the Pillar.

    use_cached_grains: ``True``
        Use cached Grains whenever possible. If unable to gather cached data,
        it falls back to collecting Grains.

    cache_pillar: ``False``
        Cache the compiled Pillar data before returning.

        .. warning::
            This option may be dangerous when targeting a device that already
            has a Proxy Minion associated, however recommended otherwise.

    cache_grains: ``False``
        Cache the collected Grains before returning.

        .. warning::
            This option may be dangerous when targeting a device that already
            has a Proxy Minion associated, however recommended otherwise.

    use_existing_proxy: ``False``
        Use the existing Proxy Minions when they are available (say on an
        already running Master).

    no_connect: ``False``
        Don't attempt to initiate the connection with the remote device.
        Default: ``False`` (it will initiate the connection).

    jid: ``None``
        The JID to pass on, when executing.

    test_ping: ``False``
        When using the existing Proxy Minion with the ``use_existing_proxy``
        option, can use this argument to verify also if the Minion is
        responsive.

    arg
        The list of arguments to send to the Salt function.

    kwargs
        Key-value arguments to send to the Salt function.

    CLI Example:

    .. code-block:: bash

        salt-run proxy.salt_call bgp.neighbors junos 1.2.3.4 test test123
        salt-run proxy.salt_call net.load_config junos 1.2.3.4 test test123 text='set system ntp peer 1.2.3.4'
    '''
    if use_existing_proxy:
        # When using the existing Proxies, simply send the command to the
        # Minion through the ``salt.execute`` Runner.
        # But first, check if the Minion ID is accepted, otherwise, continue
        # and execute the function withing this Runner.
        wheel = salt.wheel.WheelClient(__opts__)
        accepted_minions = wheel.cmd('key.list', ['accepted'], print_event=False).get(
            'minions', []
        )
        if minion_id in accepted_minions:
            log.debug(
                '%s seems to be a valid Minion, trying to spread out the command',
                minion_id,
            )
            log.info(
                'If %s is not responding, you might want to run without --use-existing-proxy, or with --test-ping',
                minion_id,
            )
            test_ping_succeeded = True
            if test_ping:
                log.debug('Checking if the Minion %s is responsive', minion_id)
                ret = __salt__['salt.execute'](minion_id, 'test.ping', jid=jid)
                test_ping_succeeded = ret.get(minion_id, False)
            if test_ping_succeeded:
                ret = __salt__['salt.execute'](
                    minion_id, function, arg=args, kwarg=kwargs, jid=jid
                )
                return ret.get(minion_id)
            else:
                log.info(
                    'Looks like the Minion %s is not responsive, executing locally',
                    minion_id,
                )
        else:
            log.debug(
                '%s doesn\'t seem to be a valid existing Minion, executing locally',
                minion_id,
            )
    opts = copy.deepcopy(__opts__)
    opts['id'] = minion_id
    opts['pillarenv'] = __opts__.get('pillarenv', 'base')
    opts['__cli'] = __opts__.get('__cli', 'salt-call')
    opts['__tgt'] = tgt
    opts['__tgt_type'] = tgt_type
    if 'saltenv' not in opts:
        opts['saltenv'] = 'base'
    if not default_grains:
        default_grains = {}
    if use_cached_grains or use_cached_pillar:
        minion_cache = __salt__['cache.fetch']('minions/{}'.format(minion_id), 'data')
    opts['grains'] = default_grains
    if not default_pillar:
        default_pillar = {}
    opts['pillar'] = default_pillar
    opts['proxy_load_pillar'] = with_pillar
    opts['proxy_load_grains'] = with_grains
    opts['proxy_preload_pillar'] = preload_pillar
    opts['proxy_preload_grains'] = preload_grains
    opts['proxy_cache_grains'] = cache_grains
    opts['proxy_cache_pillar'] = cache_pillar
    opts['preload_targeting'] = preload_targeting
    opts['invasive_targeting'] = invasive_targeting
    opts['proxy_use_cached_grains'] = use_cached_grains
    opts['proxy_no_connect'] = no_connect
    opts['proxy_test_ping'] = test_ping
    if use_cached_grains:
        opts['proxy_cached_grains'] = minion_cache.get('grains')
    opts['proxy_use_cached_pillar'] = use_cached_pillar
    if use_cached_pillar:
        opts['proxy_cached_pillar'] = minion_cache.get('pillar')
    opts['roster_opts'] = roster_opts
    opts['returner'] = returner
    minion_defaults = salt.config.DEFAULT_MINION_OPTS.copy()
    minion_defaults.update(salt.config.DEFAULT_PROXY_MINION_OPTS)
    for opt, val in six.iteritems(minion_defaults):
        if opt not in opts:
            opts[opt] = val
    sa_proxy = StandaloneProxy(opts, unreachable_devices)
    if not sa_proxy.ready:
        log.debug(
            'The SProxy Minion for %s is not able to start up, aborting', opts['id']
        )
        return
    kwargs = clean_kwargs(**kwargs)
    ret = None
    try:
        ret = sa_proxy.functions[function](*args, **kwargs)
    except Exception as err:
        log.error('Exception while running %s on %s', function, opts['id'])
        log.error(err, exc_info=True)
        if failed_devices is not None:
            failed_devices.append(opts['id'])
        if failhard:
            raise
    else:
        if returner:
            returner_fun = '{}.returner'.format(returner)
            if returner_fun in sa_proxy.returners:
                log.error('Sending the response from %s to the %s Returner', opts['id'], returner)
                ret_data = {
                    'id': opts['id'],
                    'jid': jid,
                    'fun': function,
                    'fun_args': args,
                    'return': ret,
                    'ret_config': returner_config,
                    'ret_kwargs': returner_kwargs,
                }
                try:
                    sa_proxy.returners[returner_fun](ret_data)
                except Exception as err:
                    log.error('Exception while sending the response from %s to the %s returner', opts['id'], returner)
                    log.error(err, exc_info=True)
            else:
                log.warning('Returner %s is not available. Check that the dependencies are properly installed')
    finally:
        if sa_proxy.connected:
            shut_fun = '{}.shutdown'.format(sa_proxy.opts['proxy']['proxytype'])
            sa_proxy.proxy[shut_fun](opts)
    if cache_grains:
        log.debug('Caching Grains for %s', minion_id)
        log.debug(sa_proxy.opts['grains'])
        cache_store = __salt__['cache.store'](
            'minions/{}/data'.format(minion_id), 'grains', sa_proxy.opts['grains']
        )
    if cache_pillar:
        log.debug('Caching Pillar for %s', minion_id)
        cached_store = __salt__['cache.store'](
            'minions/{}/data'.format(minion_id), 'pillar', sa_proxy.opts['pillar']
        )
    return ret


def execute_devices(
    minions,
    function,
    with_grains=True,
    with_pillar=True,
    preload_grains=True,
    preload_pillar=True,
    default_grains=None,
    default_pillar=None,
    args=(),
    batch_size=10,
    batch_wait=0,
    static=False,
    tgt=None,
    tgt_type=None,
    jid=None,
    events=True,
    cache_grains=False,
    cache_pillar=False,
    use_cached_grains=True,
    use_cached_pillar=True,
    use_existing_proxy=False,
    no_connect=False,
    roster_targets=None,
    test_ping=False,
    preload_targeting=False,
    invasive_targeting=False,
    failhard=False,
    timeout=60,
    summary=False,
    verbose=False,
    progress=False,
    hide_timeout=False,
    returner='',
    returner_config='',
    returner_kwargs={},
    **kwargs
):
    '''
    Execute a Salt function on a group of network devices identified by their
    Minion ID, as listed under the ``minions`` argument.

    minions
        A list of Minion IDs to invoke ``function`` on.

    function
        The name of the Salt function to invoke.

    preload_grains: ``True``
        Whether to preload the Grains before establishing the connection with
        the remote network device.

    default_grains:
        Dictionary of the default Grains to make available within the functions
        loaded.

    with_grains: ``False``
        Whether to load the Grains modules and collect Grains data and make it
        available inside the Execution Functions.
        The Grains will be loaded after opening the connection with the remote
        network device.

    preload_pillar: ``True``
        Whether to preload Pillar data before opening the connection with the
        remote network device.

    default_pillar:
        Dictionary of the default Pillar data to make it available within the
        functions loaded.

    with_pillar: ``True``
        Whether to load the Pillar modules and compile Pillar data and make it
        available inside the Execution Functions.

    args
        The list of arguments to send to the Salt function.

    kwargs
        Key-value arguments to send to the Salt function.

    batch_size: ``10``
        The size of each batch to execute.

    static: ``False``
        Whether to return the results synchronously (or return them as soon
        as the device replies).

    events: ``True``
        Whether should push events on the Salt bus, similar to when executing
        equivalent through the ``salt`` command.

    use_cached_pillar: ``True``
        Use cached Pillars whenever possible. If unable to gather cached data,
        it falls back to compiling the Pillar.

    use_cached_grains: ``True``
        Use cached Grains whenever possible. If unable to gather cached data,
        it falls back to collecting Grains.

    cache_pillar: ``False``
        Cache the compiled Pillar data before returning.

        .. warning::
            This option may be dangerous when targeting a device that already
            has a Proxy Minion associated, however recommended otherwise.

    cache_grains: ``False``
        Cache the collected Grains before returning.

        .. warning::
            This option may be dangerous when targeting a device that already
            has a Proxy Minion associated, however recommended otherwise.

    use_existing_proxy: ``False``
        Use the existing Proxy Minions when they are available (say on an
        already running Master).

    no_connect: ``False``
        Don't attempt to initiate the connection with the remote device.
        Default: ``False`` (it will initiate the connection).

    test_ping: ``False``
        When using the existing Proxy Minion with the ``use_existing_proxy``
        option, can use this argument to verify also if the Minion is
        responsive.

    CLI Example:

    .. code-block:: bash

        salt-run proxy.execute "['172.17.17.1', '172.17.17.2']" test.ping driver=eos username=test password=test123
    '''
    resp = ''
    __pub_user = kwargs.get('__pub_user')
    if not __pub_user:
        __pub_user = __utils__['user.get_specific_user']()
    kwargs = clean_kwargs(**kwargs)
    if not jid:
        if salt.version.__version_info__ >= (2018, 3, 0):
            jid = salt.utils.jid.gen_jid(__opts__)
        else:
            jid = salt.utils.jid.gen_jid()
    event_args = list(args[:])
    if kwargs:
        event_kwargs = {'__kwarg__': True}
        event_kwargs.update(kwargs)
        event_args.append(event_kwargs)
    opts = {
        'with_grains': with_grains,
        'with_pillar': with_pillar,
        'preload_grains': preload_grains,
        'preload_pillar': preload_pillar,
        'default_grains': default_grains,
        'default_pillar': default_pillar,
        'preload_targeting': preload_targeting,
        'invasive_targeting': invasive_targeting,
        'args': args,
        'cache_grains': cache_grains,
        'cache_pillar': cache_pillar,
        'use_cached_grains': use_cached_grains,
        'use_cached_pillar': use_cached_pillar,
        'use_existing_proxy': use_existing_proxy,
        'no_connect': no_connect,
        'test_ping': test_ping,
        'tgt': tgt,
        'tgt_type': tgt_type,
        'failhard': failhard,
        'timeout': timeout,
        'returner': returner,
        'returner_config': returner_config,
        'returner_kwargs': returner_kwargs,
    }
    opts.update(kwargs)
    if events:
        __salt__['event.send'](
            'proxy/runner/{jid}/new'.format(jid=jid),
            {
                'fun': function,
                'minions': minions,
                'arg': event_args,
                'jid': jid,
                'tgt': tgt,
                'tgt_type': tgt_type,
                'user': __pub_user,
            },
        )
    queue = multiprocessing.Queue()
    if not static:
        thread = threading.Thread(target=_receive_replies_async, args=(queue,))
        thread.start()
    ret = {}
    batch_size = int(batch_size)
    batch_count = int(len(minions) / batch_size) + (
        1 if len(minions) % batch_size else 0
    )
    log.info(
        '%d devices matched the target, executing in %d batches',
        len(minions),
        batch_count,
    )
    stop_iteration = False
    progress_bar = None
    if progress and HAS_PROGRESSBAR:
        progress_bar = progressbar.ProgressBar(
            max_value=len(minions), enable_colors=True, redirect_stdout=True
        )
    with multiprocessing.Manager() as manager:
        timeout_devices = manager.list()
        failed_devices = manager.list()
        unreachable_devices = manager.list()
        for batch_index in range(batch_count):
            log.info('Batch #%d', batch_index)
            processes = []
            devices_batch = minions[
                batch_index * batch_size : (batch_index + 1) * batch_size
            ]
            log.info('Devices in batch #%d:', batch_index)
            log.info(devices_batch)
            if verbose:
                salt.utils.stringutils.print_cli(
                    'Executing run on {0}'.format(devices_batch)
                )
            for minion_index, minion_id in enumerate(devices_batch):
                device_count = batch_index * batch_size + minion_index + 1
                log.info('Executing on %s', minion_id)
                device_opts = copy.deepcopy(opts)
                if roster_targets and isinstance(roster_targets, dict):
                    device_opts['roster_opts'] = roster_targets.get(minion_id, {}).get(
                        'minion_opts'
                    )
                device_proc = multiprocessing.Process(
                    target=_salt_call_and_return,
                    name=minion_id,
                    args=(
                        minion_id,
                        function,
                        queue,
                        unreachable_devices,
                        failed_devices,
                        event_args,
                        jid,
                        events,
                    ),
                    kwargs=device_opts,
                )
                device_proc.start()
                processes.append(device_proc)
            for proc in processes:
                if stop_iteration:
                    proc.terminate()
                    if progress_bar:
                        progress_bar.update(device_count)
                    continue
                if failhard and proc.exitcode:
                    stop_iteration = True
                proc.join(timeout=timeout)
                if proc.is_alive():
                    log.info(
                        'Terminating the process for %s, as it didn\'t reply within %d seconds',
                        proc._name,
                        timeout,
                    )
                    if not hide_timeout:
                        queue.put({proc._name: 'Minion did not return. [No response]'})
                    timeout_devices.append(proc._name)
                proc.terminate()
                if progress_bar:
                    progress_bar.update(device_count)
                continue
            if failhard and proc.exitcode:
                stop_iteration = True
            if stop_iteration:
                log.error('Exiting as an error has occurred')
                queue.put('FIN.')
                if progress_bar:
                    progress_bar.finish()
                raise StopIteration
            if batch_wait:
                log.debug(
                    'Waiting %f seconds before executing the next batch', batch_wait
                )
                time.sleep(batch_wait)
        queue.put('FIN.')
        if progress_bar:
            progress_bar.finish()
        if static:
            resp = {}
            while True:
                ret = queue.get()
                if ret == 'FIN.':
                    break
                resp.update(ret)
        if summary:
            salt.utils.stringutils.print_cli('\n')
            salt.utils.stringutils.print_cli(
                '-------------------------------------------'
            )
            salt.utils.stringutils.print_cli('Summary')
            salt.utils.stringutils.print_cli(
                '-------------------------------------------'
            )
            salt.utils.stringutils.print_cli(
                '# of devices targeted: {0}'.format(len(minions))
            )
            salt.utils.stringutils.print_cli(
                '# of devices returned: {0}'.format(
                    len(minions) - len(timeout_devices) - len(unreachable_devices)
                )
            )
            salt.utils.stringutils.print_cli(
                '# of devices that did not return: {0}'.format(len(timeout_devices))
            )
            salt.utils.stringutils.print_cli(
                '# of devices with errors: {0}'.format(len(failed_devices))
            )
            salt.utils.stringutils.print_cli(
                '# of devices unreachable: {0}'.format(len(unreachable_devices))
            )
            if verbose:
                if timeout_devices:
                    salt.utils.stringutils.print_cli(
                        (
                            '\nThe following devices didn\'t return (timeout):'
                            '\n - {0}'.format('\n - '.join(timeout_devices))
                        )
                    )
                if failed_devices:
                    salt.utils.stringutils.print_cli(
                        (
                            '\nThe following devices returned "bad" output:'
                            '\n - {0}'.format('\n - '.join(failed_devices))
                        )
                    )
                if unreachable_devices:
                    salt.utils.stringutils.print_cli(
                        (
                            '\nThe following devices are unreachable:'
                            '\n - {0}'.format('\n - '.join(unreachable_devices))
                        )
                    )
            salt.utils.stringutils.print_cli(
                '-------------------------------------------'
            )
    return resp


def execute(
    tgt,
    function=None,
    tgt_type='glob',
    roster=None,
    preview_target=False,
    target_details=False,
    timeout=60,
    with_grains=True,
    with_pillar=True,
    preload_grains=True,
    preload_pillar=True,
    default_grains=None,
    default_pillar=None,
    args=(),
    batch_size=10,
    batch_wait=0,
    static=False,
    events=True,
    cache_grains=False,
    cache_pillar=False,
    use_cached_grains=True,
    use_cached_pillar=True,
    use_existing_proxy=False,
    no_connect=False,
    test_ping=False,
    target_cache=True,
    target_cache_timeout=60,
    preload_targeting=False,
    invasive_targeting=False,
    failhard=False,
    summary=True,
    verbose=False,
    show_jid=False,
    progress=False,
    hide_timeout=False,
    saltenv='base',
    sync_roster=False,
    sync_modules=False,
    sync_grains=False,
    sync_all=False,
    returner='',
    returner_config='',
    returner_kwargs={},
    **kwargs
):
    '''
    Invoke a Salt function on the list of devices matched by the Roster
    subsystem.

    tgt
        The target expression, e.g., ``*`` for all devices, or ``host1,host2``
        for a list, etc. The ``tgt_list`` argument must be used accordingly,
        depending on the type of this expression.

    function
        The name of the Salt function to invoke.

    tgt_type: ``glob``
        The type of the ``tgt`` expression. Choose between: ``glob`` (default),
        ``list``, ``pcre``, ``rage``, or ``nodegroup``.

    roster: ``None``
        The name of the Roster to generate the targets. Alternatively, you can
        specify the name of the Roster by configuring the ``proxy_roster``
        option into the Master config.

    preview_target: ``False``
        Return the list of Roster targets matched by the ``tgt`` and
        ``tgt_type`` arguments.

    preload_grains: ``True``
        Whether to preload the Grains before establishing the connection with
        the remote network device.

    default_grains:
        Dictionary of the default Grains to make available within the functions
        loaded.

    with_grains: ``True``
        Whether to load the Grains modules and collect Grains data and make it
        available inside the Execution Functions.
        The Grains will be loaded after opening the connection with the remote
        network device.

    default_pillar:
        Dictionary of the default Pillar data to make it available within the
        functions loaded.

    with_pillar: ``True``
        Whether to load the Pillar modules and compile Pillar data and make it
        available inside the Execution Functions.

    arg
        The list of arguments to send to the Salt function.

    kwargs
        Key-value arguments to send to the Salt function.

    batch_size: ``10``
        The size of each batch to execute.

    static: ``False``
        Whether to return the results synchronously (or return them as soon
        as the device replies).

    events: ``True``
        Whether should push events on the Salt bus, similar to when executing
        equivalent through the ``salt`` command.

    use_cached_pillar: ``True``
        Use cached Pillars whenever possible. If unable to gather cached data,
        it falls back to compiling the Pillar.

    use_cached_grains: ``True``
        Use cached Grains whenever possible. If unable to gather cached data,
        it falls back to collecting Grains.

    cache_pillar: ``False``
        Cache the compiled Pillar data before returning.

        .. warning::
            This option may be dangerous when targeting a device that already
            has a Proxy Minion associated, however recommended otherwise.

    cache_grains: ``False``
        Cache the collected Grains before returning.

        .. warning::
            This option may be dangerous when targeting a device that already
            has a Proxy Minion associated, however recommended otherwise.

    use_existing_proxy: ``False``
        Use the existing Proxy Minions when they are available (say on an
        already running Master).

    no_connect: ``False``
        Don't attempt to initiate the connection with the remote device.
        Default: ``False`` (it will initiate the connection).

    test_ping: ``False``
        When using the existing Proxy Minion with the ``use_existing_proxy``
        option, can use this argument to verify also if the Minion is
        responsive.

    target_cache: ``True``
        Whether to use the cached target matching results.

    target_cache_timeout: 60
        The duration to cache the target results for (in seconds).

    CLI Example:

    .. code-block:: bash

        salt-run proxy.execute_roster edge* test.ping
        salt-run proxy.execute_roster junos-edges test.ping tgt_type=nodegroup
    '''
    targets = []
    rtargets = None
    roster = roster or __opts__.get('proxy_roster', __opts__.get('roster'))

    if sync_roster:
        __salt__['saltutil.sync_roster'](saltenv=saltenv)
    if sync_modules:
        __salt__['saltutil.sync_modules'](saltenv=saltenv)
    if sync_all:
        __salt__['saltutil.sync_all'](saltenv=saltenv)

    if not timeout:
        log.warning('Timeout set as 0, will wait for the devices to reply indefinitely')
        # Setting the timeout as None, because that's the value we need to pass
        # to multiprocessing's join() method to wait for the devices to reply
        # indefinitely.
        timeout = None

    if preload_targeting or invasive_targeting:
        _tgt = '*'
        _tgt_type = 'glob'
    else:
        _tgt = tgt
        _tgt_type = tgt_type

    if not roster or roster == 'None':
        log.info(
            'No Roster specified. Please use the ``roster`` argument, or set the ``proxy_roster`` option in the '
            'Master configuration.'
        )
        targets = []
        if use_existing_proxy:
            # When targeting exiting Proxies, we're going to look and match the
            # accepted keys
            log.debug('Requested to match the target based on the existing Minions')
            target_util = salt.utils.master.MasterPillarUtil(
                tgt,
                tgt_type,
                use_cached_grains=True,
                grains_fallback=False,
                opts=__opts__,
            )
            targets = target_util._tgt_to_list()
        else:
            # Try a fuzzy match based on the exact target the user requested
            # only when not attempting to match an existing Proxy. If you do
            # want however, it won't be of much use, as the command is going to
            # be spread out to non-existing minions, so better turn off that
            # feature.
            log.debug('Trying a fuzzy match on the target')
            if tgt_type == 'list':
                targets = tgt[:]
            elif tgt_type == 'glob' and tgt != '*':
                targets = [tgt]
    else:
        targets = None
        if target_cache and not (invasive_targeting or preload_targeting):
            cache_bank = salt.cache.factory(__opts__)
            cache_key = hashlib.sha1(
                '{tgt}_{tgt_type}'.format(tgt=tgt, tgt_type=tgt_type).encode()
            ).hexdigest()
            cache_time_key = '{}_time'.format(cache_key)
            cache_time = cache_bank.fetch('_salt_sproxy_target', cache_time_key)
            if cache_time and time.time() - cache_time <= target_cache_timeout:
                log.debug('Loading the targets from the cache')
                targets = cache_bank.fetch('_salt_sproxy_target', cache_key)
        if not targets:
            log.debug('Computing the target using the %s Roster', roster)
            __opts__['use_cached_grains'] = use_cached_grains
            __opts__['use_cached_pillar'] = use_cached_pillar
            roster_modules = salt.loader.roster(__opts__, runner=__salt__)
            if '.targets' not in roster:
                roster = '{mod}.targets'.format(mod=roster)
            rtargets = roster_modules[roster](_tgt, tgt_type=_tgt_type)
            targets = list(rtargets.keys())
            if target_cache and not (invasive_targeting or preload_targeting):
                cache_bank.store('_salt_sproxy_target', cache_key, targets)
                cache_bank.store('_salt_sproxy_target', cache_time_key, time.time())
    if preload_targeting or invasive_targeting:
        log.debug(
            'Loaded everything from the Roster, to start collecting Grains and Pillars:'
        )
    else:
        log.debug(
            'The target expression "%s" (%s) matched the following:', str(tgt), tgt_type
        )
    log.debug(targets)
    if not targets:
        return 'No devices matched your target. Please review your tgt / tgt_type arguments, or the Roster data source'
    if preview_target:
        return targets
    elif not function:
        return 'Please specify a Salt function to execute.'
    jid = kwargs.get('__pub_jid')
    if not jid:
        if salt.version.__version_info__ >= (2018, 3, 0):
            jid = salt.utils.jid.gen_jid(__opts__)
        else:
            jid = salt.utils.jid.gen_jid()
    if verbose or show_jid:
        salt.utils.stringutils.print_cli('Executing job with jid {0}'.format(jid))
        salt.utils.stringutils.print_cli(
            '-------------------------------------------\n'
        )
    if events:
        __salt__['event.send'](jid, {'minions': targets})
    return execute_devices(
        targets,
        function,
        tgt=tgt,
        tgt_type=tgt_type,
        with_grains=with_grains,
        preload_grains=preload_grains,
        with_pillar=with_pillar,
        preload_pillar=preload_pillar,
        default_grains=default_grains,
        default_pillar=default_pillar,
        args=args,
        batch_size=batch_size,
        batch_wait=batch_wait,
        static=static,
        events=events,
        cache_grains=cache_grains,
        cache_pillar=cache_pillar,
        use_cached_grains=use_cached_grains,
        use_cached_pillar=use_cached_pillar,
        use_existing_proxy=use_existing_proxy,
        no_connect=no_connect,
        roster_targets=rtargets,
        test_ping=test_ping,
        preload_targeting=preload_targeting,
        invasive_targeting=invasive_targeting,
        failhard=failhard,
        timeout=timeout,
        summary=summary,
        verbose=verbose,
        progress=progress,
        hide_timeout=hide_timeout,
        returner=returner,
        returner_config=returner_config,
        returner_kwargs=returner_kwargs,
        **kwargs
    )
    return ret
