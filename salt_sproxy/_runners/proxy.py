# -*- coding: utf-8 -*-
'''


Salt Runner to invoke arbitrary commands on network devices that are not
managed via a Proxy or regular Minion. Therefore, this Runner doesn't
necessarily require the targets to be up and running, as it will connect to
collect the Grains, compile the Pillar, then execute the commands.
'''
from __future__ import absolute_import, print_function, unicode_literals

# Import Python std lib
import copy
import logging
import threading
import multiprocessing

# Import Salt modules
import salt.loader
import salt.output
import salt.utils.jid
from salt.ext import six
from salt.minion import SMinion
from salt.ext.six.moves import range
import salt.defaults.exitcodes
from salt.exceptions import SaltSystemExit

import salt.utils.napalm

try:
    from salt.utils import is_proxy
    from salt.utils import clean_kwargs
except ImportError:
    from salt.utils.platform import is_proxy
    from salt.utils.args import clean_kwargs
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
    minion_id, function, queue, arg=None, jid=None, events=True, **opts
):
    '''
    '''
    ret = salt_call(minion_id, function, **opts)
    if events:
        __salt__['event.send'](
            'napalm/runner/{jid}/ret/{minion_id}'.format(minion_id=minion_id, jid=jid),
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
        print(out_fmt)


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

    def gen_modules(self, initial_load=False):
        '''
        Tell the minion to reload the execution modules
        CLI Example:
        .. code-block:: bash
            salt '*' sys.reload_modules
        '''
        cached_grains = None
        if self.opts.get('proxy_use_cached_grains', True):
            cached_grains = self.opts.pop('proxy_cached_grains', None)
        if not cached_grains and self.opts.get('proxy_preload_grains', True):
            self.opts['grains'].update(salt.loader.grains(self.opts))
        elif cached_grains:
            self.opts['grains'].update(cached_grains)

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
        self.returners = salt.loader.returners(
            self.opts, self.functions, proxy=self.proxy
        )
        self.functions['sys.reload_modules'] = self.gen_modules

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

        if (
            '{0}.init'.format(fq_proxyname) not in self.proxy
            or '{0}.shutdown'.format(fq_proxyname) not in self.proxy
        ):
            errmsg = (
                'Proxymodule {0} is missing an init() or a shutdown() or both. '.format(
                    fq_proxyname
                )
                + 'Check your proxymodule.  Salt-proxy aborted.'
            )
            log.error(errmsg)
            self._running = False
            raise SaltSystemExit(code=salt.defaults.exitcodes.EX_GENERIC, msg=errmsg)

        proxy_init_fn = self.proxy[fq_proxyname + '.init']
        proxy_init_fn(self.opts)
        if not cached_grains and self.opts.get('proxy_load_grains', True):
            # When the Grains are loaded from the cache, no need to re-load them
            # again.
            self.opts['grains'].update(
                salt.loader.grains(self.opts, proxy=self.proxy)
            )
        self.grains_cache = self.opts['grains']
        self.ready = True


class StandaloneProxy(SProxyMinion):
    def __init__(self, opts):  # pylint: disable=super-init-not-called
        self.opts = opts
        self.gen_modules()


# ------------------------------------------------------------------------------
# callable functions
# ------------------------------------------------------------------------------


def get_connection(
    driver,
    hostname,
    username,
    password,
    timeout=60,
    optional_args=None,
    provider=None,
    minion_id=None,
    with_pillar=False,
    with_grains=False,
    default_pillar=None,
    default_grains=None,
):
    '''
    Return the NAPALM connection object together with the associated Salt
    dunders packed, i.e., ``__salt__``, ``__utils__``, ``__opts__``, etc.

    This function establishes the connection to the remote device through
    NAPALM and returns the connection object.

    .. note::
        This function is not designed for CLI usage, but rather invoked from
        other Salt Runners.
        Similarly, it is up to the developer to ensure that the connection is
        closed properly.

    driver
        Specifies the network device operating system.
        For a complete list of the supported operating systems please refer to the
        `NAPALM Read the Docs page`_.

    hostname
        The IP Address or name server to use when connecting to the device.

    username
        The username to be used when connecting to the device.

    password
        The password needed to establish the connection.

        .. note::
            This field may not be mandatory when working with SSH-based drivers, and
            the username has a SSH key properly configured on the device targeted to
            be managed.

    optional_args
        Dictionary with the optional arguments.
        Check the complete list of supported `optional arguments`_.

    provider: ``napalm_base``
        The library that provides the ``get_network_device`` function.
        This option is useful when the user has more specific needs and requires
        to extend the NAPALM capabilities using a private library implementation.
        The only constraint is that the alternative library needs to have the
        ``get_network_device`` function available.

    default_grains:
        Dictionary of the default Grains to make available within the functions
        loaded.

    with_grains: ``False``
        Whether to load the Grains modules and collect Grains data and make it
        available inside the Execution Functions.

    default_pillar:
        Dictionary of the default Pillar data to make it available within the
        functions loaded.

    with_pillar: ``False``
        Whether to load the Pillar modules and compile Pillar data and make it
        available inside the Execution Functions.

    minion_id:
        The ID of the Minion to compile Pillar data for.

    .. _`NAPALM Read the Docs page`: https://napalm.readthedocs.io/en/latest/#supported-network-operating-systems
    .. _`optional arguments`: http://napalm.readthedocs.io/en/latest/support/index.html#list-of-supported-optional-arguments

    Usage Example:

    .. code-block:: python

        napalm_device = __salt__['napalm.get_connection']('eos', '1.2.3.4', 'test', 'test')
    '''
    if not optional_args:
        optional_args = {}
    opts = copy.deepcopy(__opts__)
    if 'proxy' not in opts:
        opts['proxy'] = {}
    opts['proxy'].update(
        {
            'proxytype': 'napalm',
            'driver': driver,
            'hostname': hostname,
            'username': username,
            'passwd': password,
            'timeout': timeout,
            'optional_args': optional_args,
            'provider': provider,
        }
    )
    if 'saltenv' not in opts:
        opts['saltenv'] = 'base'
    if minion_id:
        opts['id'] = minion_id
    opts['grains'] = {}
    if default_grains:
        opts['grains'] = default_grains
    if with_grains:
        opts['grains'].update(salt.loader.grains(opts))
    opts['pillar'] = {}
    if default_pillar:
        opts['pillar'] = default_pillar
    if with_pillar:
        opts['pillar'].update(
            salt.pillar.get_pillar(
                opts,
                opts['grains'],
                opts['id'],
                saltenv=opts['saltenv'],
                pillarenv=opts.get('pillarenv'),
            ).compile_pillar()
        )
    __utils__ = salt.loader.utils(opts)
    functions = salt.loader.minion_mods(opts, utils=__utils__, context=__context__)
    napalm_device = __utils__['napalm.get_device'](opts, salt_obj=functions)
    napalm_device.update(
        {'__utils__': __utils__, '__opts__': opts, '__salt__': functions}
    )
    return napalm_device


def call(
    method,
    driver,
    hostname,
    username,
    password,
    timeout=60,
    optional_args=None,
    provider=None,
    **kwargs
):
    '''
    Execute an arbitrary NAPALM method and return the result.

    method
        The name of the NAPALM method to invoke. Example: ``get_bgp_neighbors``.

    driver
        Specifies the network device operating system.
        For a complete list of the supported operating systems please refer to the
        `NAPALM Read the Docs page`_.

    hostname
        The IP Address or name server to use when connecting to the device.

    username
        The username to be used when connecting to the device.

    password
        The password needed to establish the connection.

        .. note::
            This field may not be mandatory when working with SSH-based drivers, and
            the username has a SSH key properly configured on the device targeted to
            be managed.

    optional_args
        Dictionary with the optional arguments.
        Check the complete list of supported `optional arguments`_.

    provider: ``napalm_base``
        The library that provides the ``get_network_device`` function.
        This option is useful when the user has more specific needs and requires
        to extend the NAPALM capabilities using a private library implementation.
        The only constraint is that the alternative library needs to have the
        ``get_network_device`` function available.

    .. _`NAPALM Read the Docs page`: https://napalm.readthedocs.io/en/latest/#supported-network-operating-systems
    .. _`optional arguments`: http://napalm.readthedocs.io/en/latest/support/index.html#list-of-supported-optional-arguments

    CLI Example:

    .. code-block:: bash

        salt-run napalm.call get_bgp_neighbors eos 1.2.3.4 test test123
    '''
    napalm_device = get_connection(
        driver,
        hostname,
        username,
        password,
        timeout=timeout,
        optional_args=optional_args,
        provider=provider,
    )
    __utils__ = napalm_device['__utils__']
    ret = __utils__['napalm.call'](napalm_device, method, **kwargs)
    try:
        __utils__['napalm.call'](napalm_device, 'close')
    except Exception as err:
        log.error(err)
    return ret


def salt_call(
    minion_id,
    function,
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

    arg
        The list of arguments to send to the Salt function.

    kwargs
        Key-value arguments to send to the Salt function.

    CLI Example:

    .. code-block:: bash

        salt-run napalm.salt_call bgp.neighbors junos 1.2.3.4 test test123
        salt-run napalm.salt_call net.load_config junos 1.2.3.4 test test123 text='set system ntp peer 1.2.3.4'
    '''
    opts = copy.deepcopy(__opts__)
    opts['id'] = minion_id
    opts['pillarenv'] = __opts__.get('pillarenv', 'base')
    opts['__cli'] = __opts__.get('__cli', 'salt-call')
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
    opts['proxy_use_cached_grains'] = use_cached_grains
    if use_cached_grains:
        opts['proxy_cached_grains'] = minion_cache.get('grains')
    opts['proxy_use_cached_pillar'] = use_cached_pillar
    if use_cached_pillar:
        opts['proxy_cached_pillar'] = minion_cache.get('pillar')
    sa_proxy = StandaloneProxy(opts)
    kwargs = clean_kwargs(**kwargs)
    ret = None
    try:
        ret = sa_proxy.functions[function](*args, **kwargs)
    except Exception as err:
        log.error(err, exc_info=True)
    finally:
        sa_proxy.proxy['napalm.shutdown'](opts)
    if cache_grains:
        __salt__['cache.store'](
            'minions/{}/data'.format(minion_id), 'grains', napalm_px.opts['grains']
        )
    if cache_pillar:
        __salt__['cache.store'](
            'minions/{}/data'.format(minion_id), 'pillar', napalm_px.opts['pillar']
        )
    return ret


def execute_devices(
    minions,
    fun,
    with_grains=True,
    with_pillar=True,
    preload_grains=True,
    preload_pillar=True,
    default_grains=None,
    default_pillar=None,
    args=(),
    batch_size=10,
    sync=False,
    tgt=None,
    tgt_type=None,
    jid=None,
    events=True,
    cache_grains=False,
    cache_pillar=False,
    use_cached_grains=True,
    use_cached_pillar=True,
    **kwargs
):
    '''
    Execute a Salt function on a group of network devices identified by their
    Minion ID, as listed under the ``minions`` argument.

    minions
        A list of Minion IDs to invoke ``fun`` on.

    fun
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

    sync: ``False``
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

    CLI Example:

    .. code-block:: bash

        salt-run napalm.execute "['172.17.17.1', '172.17.17.2']" test.ping driver=eos username=test password=test123
    '''
    __pub_user = kwargs.get('__pub_user')
    kwargs = clean_kwargs(**kwargs)
    if not jid:
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
        'args': args,
        'cache_grains': cache_grains,
        'cache_pillar': cache_pillar,
        'use_cached_grains': use_cached_grains,
        'use_cached_pillar': use_cached_pillar,
    }
    opts.update(kwargs)
    if events:
        __salt__['event.send'](
            'napalm/runner/{jid}/new'.format(jid=jid),
            {
                'fun': fun,
                'minions': minions,
                'arg': event_args,
                'jid': jid,
                'tgt': tgt,
                'tgt_type': tgt_type,
                'user': __pub_user,
            },
        )
    queue = multiprocessing.Queue()
    if not sync:
        thread = threading.Thread(target=_receive_replies_async, args=(queue,))
        thread.start()
    ret = {}
    batch_count = len(minions) / batch_size + 1
    for batch_index in range(batch_count):
        processes = []
        devices_batch = minions[
            batch_index * batch_size : (batch_index + 1) * batch_size
        ]
        for minion_id in devices_batch:
            device_proc = multiprocessing.Process(
                target=_salt_call_and_return,
                name=minion_id,
                args=(minion_id, fun, queue, event_args, jid, events),
                kwargs=opts,
            )
            device_proc.start()
            processes.append(device_proc)
        for proc in processes:
            proc.join()
    queue.put('FIN.')
    if sync:
        resp = {}
        while True:
            ret = queue.get()
            if ret == 'FIN.':
                break
            resp.update(ret)
        return resp
    else:
        return {}


def execute(
    tgt,
    fun,
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
    sync=False,
    events=True,
    cache_grains=False,
    cache_pillar=False,
    use_cached_grains=True,
    use_cached_pillar=True,
    **kwargs
):
    '''
    Invoke a Salt function on the list of devices matched by the Roster
    subsystem.

    tgt
        The target expression, e.g., ``*`` for all devices, or ``host1,host2``
        for a list, etc. The ``tgt_list`` argument must be used accordingly,
        depending on the type of this expression.

    fun
        The name of the Salt function to invoke.

    tgt_type: ``glob``
        The type of the ``tgt`` expression. Choose between: ``glob`` (default),
        ``list``, ``pcre``, ``rage``, or ``nodegroup``.

    roster: ``None``
        The name of the Roster to generate the targets. Alternatively, you can
        specify the name of the Roster by configuring the ``napalm_roster``
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

    sync: ``False``
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

    CLI Example:

    .. code-block:: bash

        salt-run napalm.execute_roster edge* test.ping
        salt-run napalm.execute_roster junos-edges test.ping tgt_type=nodegroup
    '''
    targets = []
    roster = roster or __opts__.get('napalm_roster', __opts__.get('roster'))
    if not roster:
        log.info(
            'No Roster specified. Please use the ``roster`` argument, or set the ``napalm_roster`` option in the '
            'Master configuration.'
        )
        targets = []
        if tgt_type == 'list':
            targets = tgt[:]
        elif tgt_type == 'glob' and tgt != '*':
            targets = [tgt]
    else:
        roster_modules = salt.loader.roster(__opts__, runner=__salt__)
        if '.targets' not in roster:
            roster = '{mod}.targets'.format(mod=roster)
        rtargets = roster_modules[roster](tgt, tgt_type=tgt_type)
        targets = list(rtargets.keys())
    if not targets:
        return 'No devices matched your target. Please review your tgt / tgt_type arguments, or the Roster data source'
    if preview_target:
        return targets
    jid = kwargs.get('__pub_jid')
    if not jid:
        jid = salt.utils.jid.gen_jid()
    if events:
        __salt__['event.send'](jid, {'minions': list(targets.keys())})
    return execute_devices(
        targets,
        fun,
        with_grains=with_grains,
        preload_grains=preload_grains,
        with_pillar=with_pillar,
        preload_pillar=preload_pillar,
        default_grains=default_grains,
        default_pillar=default_pillar,
        args=args,
        batch_size=batch_size,
        sync=sync,
        events=events,
        cache_grains=cache_grains,
        cache_pillar=cache_pillar,
        use_cached_grains=use_cached_grains,
        use_cached_pillar=use_cached_pillar,
        **kwargs
    )
