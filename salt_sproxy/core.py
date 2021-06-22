# -*- coding: utf-8 -*-
# Copyright 2019-2021 Mircea Ulinic. All rights reserved.
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
from __future__ import absolute_import, print_function, unicode_literals

# Import Python std lib
import copy
import logging

# Import Salt modules
import salt.cache
import salt.loader
import salt.client
import salt.output
import salt.version
import salt.utils.jid
import salt.utils.master
from salt.minion import SMinion
import salt.defaults.exitcodes
from salt.exceptions import SaltSystemExit
from salt.defaults import DEFAULT_TARGET_DELIM

import salt.utils.dictupdate


log = logging.getLogger(__name__)


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

    def gen_modules(self, initial_load=False):  # pylint: disable=arguments-differ
        '''
        Tell the minion to reload the execution modules.

        CLI Example:

        .. code-block:: bash

            salt '*' sys.reload_modules
        '''
        if self.opts.get('proxy_preload_grains', True):
            loaded_grains = salt.loader.grains(self.opts)
            self.opts['grains'].update(loaded_grains)

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

        cached_grains = None
        if self.opts.get('proxy_use_cached_grains', True):
            cached_grains = self.opts.pop('proxy_cached_grains', None)

        initial_grains = copy.deepcopy(self.opts['grains'])
        if cached_grains:
            # Merging the collected Grains into the cached Grains, but only for
            # the initial Pillar compilation, to ensure we only do so to avoid
            # any processing errors.
            initial_grains = salt.utils.dictupdate.merge(cached_grains, initial_grains)

        if self.opts.get('proxy_load_pillar', True):
            self.opts['pillar'] = salt.pillar.get_pillar(
                self.opts,
                initial_grains,
                self.opts['id'],
                saltenv=self.opts['saltenv'],
                pillarenv=self.opts.get('pillarenv'),
            ).compile_pillar()

        if self.opts['roster_opts'] and self.opts.get('proxy_merge_roster_opts', True):
            if 'proxy' not in self.opts['pillar']:
                self.opts['pillar']['proxy'] = {}
            self.opts['pillar']['proxy'] = salt.utils.dictupdate.merge(
                self.opts['pillar']['proxy'], self.opts['roster_opts']
            )
            self.opts['pillar']['proxy'].pop('grains', None)
            self.opts['pillar']['proxy'].pop('pillar', None)

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
            self.opts['proxy'] = {}
        if 'proxy' not in self.opts['pillar']:
            self.opts['pillar']['proxy'] = {}
        self.opts['proxy'] = salt.utils.dictupdate.merge(
            self.opts['proxy'], self.opts['pillar']['proxy']
        )

        # Then load the proxy module
        fq_proxyname = self.opts['proxy']['proxytype']
        self.utils = salt.loader.utils(self.opts)
        self.proxy = salt.loader.proxy(
            self.opts, utils=self.utils, whitelist=[fq_proxyname]
        )
        self.functions = salt.loader.minion_mods(
            self.opts, utils=self.utils, notify=False, proxy=self.proxy
        )
        self.functions.pack['__grains__'] = copy.deepcopy(self.opts['grains'])

        self.functions.pack['__proxy__'] = self.proxy
        self.proxy.pack['__salt__'] = self.functions
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
                    exc_info=True,
                )
                if self.unreachable_devices is not None:
                    self.unreachable_devices.append(self.opts['id'])
                raise
            if self.opts.get('proxy_load_grains', True):
                # When the Grains are loaded from the cache, no need to re-load them
                # again.

                grains = copy.deepcopy(self.opts['grains'])
                # Copy the existing Grains loaded so far, otherwise
                # salt.loader.grains is going to wipe what's under the grains
                # key in the opts.
                # After loading, merge with the previous loaded grains, which
                # may contain other grains from different sources, e.g., roster.
                loaded_grains = salt.loader.grains(self.opts, proxy=self.proxy)
                self.opts['grains'] = salt.utils.dictupdate.merge(grains, loaded_grains)
            if self.opts.get('proxy_load_pillar', True):
                self.opts['pillar'] = salt.pillar.get_pillar(
                    self.opts,
                    self.opts['grains'],
                    self.opts['id'],
                    saltenv=self.opts['saltenv'],
                    pillarenv=self.opts.get('pillarenv'),
                ).compile_pillar()
            self.functions.pack['__opts__'] = self.opts
            self.functions.pack['__grains__'] = copy.deepcopy(self.opts['grains'])
            self.functions.pack['__pillar__'] = copy.deepcopy(self.opts['pillar'])
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

        self.module_executors = self.proxy.get(
            '{0}.module_executors'.format(fq_proxyname), lambda: []
        )() or self.opts.get('module_executors', [])
        if self.module_executors:
            self.executors = salt.loader.executors(
                self.opts, self.functions, proxy=self.proxy
            )

        # Late load the Returners, as they might need Grains, which may not be
        # properly or completely loaded before this.
        self.returners = None
        if self.opts['returner']:
            self.returners = salt.loader.returners(
                self.opts, self.functions, proxy=self.proxy
            )
        self.proxy.pack['__ret__'] = self.returners

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
