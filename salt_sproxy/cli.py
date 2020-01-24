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
The CLI entry point module.
'''
from __future__ import absolute_import, print_function, unicode_literals

from salt_sproxy.parsers import SaltStandaloneProxyOptionParser

import os
import ast
import sys
import logging

import salt.runner
import salt.utils.parsers
from salt.utils.verify import check_user, verify_log
from salt.exceptions import SaltClientError
from salt.ext import six
import salt.defaults.exitcodes  # pylint: disable=W0611
import salt.utils.stringutils

try:
    from salt.utils.file import fopen
    from salt.utils.yamldumper import safe_dump
    from salt.utils.yamlloader import safe_load
    from salt.utils.profile import output_profile
    from salt.utils.profile import activate_profile
except ImportError:
    from salt.utils import fopen
    from salt.utils.yamldumper import safe_dump
    from salt.utils.yamlloader import load as safe_load
    from salt.utils import output_profile
    from salt.utils import activate_profile

log = logging.getLogger(__name__)


class SaltStandaloneProxy(SaltStandaloneProxyOptionParser):
    '''
    Used to execute Salt functions on a number of devices.
    '''

    def run(self):
        '''
        Execute salt-run
        '''
        self.parse_args()

        if self.config.get('config_dump'):
            sys.stdout.write(safe_dump(self.config, default_flow_style=False))
            return self.config

        # Setup file logging!
        self.setup_logfile_logger()
        verify_log(self.config)
        profiling_enabled = self.options.profiling_enabled
        curpath = os.path.dirname(os.path.realpath(__file__))
        saltenv = self.config.get('saltenv')
        if not saltenv:
            saltenv = 'base'
        if self.config.get('pillar_root'):
            log.info(
                'Setting and using %s as the Pillar root', self.config['pillar_root']
            )
            self.config['pillar_roots'] = {saltenv: self.config['pillar_root']}
        if self.config.get('file_root'):
            log.info(
                'Setting and using %s as the Salt file root', self.config['file_root']
            )
            self.config['file_root'] = {saltenv: self.config['file_root']}
        if self.config.get('display_file_roots'):
            salt.utils.stringutils.print_cli(
                'salt-sproxy is installed at: {}'.format(curpath)
            )
            salt.utils.stringutils.print_cli(
                '\nYou can configure the file_roots on the Master, e.g.,\n'
            )
            salt.utils.stringutils.print_cli(
                'file_roots:\n  {0}:\n    - {1}'.format(saltenv, curpath)
            )
            salt.utils.stringutils.print_cli('\n\nOr only for the Runners:\n')
            salt.utils.stringutils.print_cli(
                'runner_dirs:\n  - {}/_runners'.format(curpath)
            )
            return
        if self.config.get('save_file_roots'):
            updated = False
            with fopen(self.config['conf_file'], 'r+') as master_fp:
                master_cfg = safe_load(master_fp)
                if not master_cfg:
                    master_cfg = {}
                file_roots = master_cfg.get('file_roots', {saltenv: []}).get(
                    saltenv, []
                )
                runner_dirs = master_cfg.get('runner_dirs', [])
                sproxy_runners = os.path.join(curpath, '_runners')
                if curpath not in file_roots:
                    file_roots.append(curpath)
                    master_cfg['file_roots'] = {saltenv: file_roots}
                    updated = True
                    salt.utils.stringutils.print_cli(
                        '{} added to the file_roots:\n'.format(curpath)
                    )
                    salt.utils.stringutils.print_cli(
                        'file_roots:\n  {0}\n    - {1}\n'.format(
                            saltenv, '\n    -'.join(file_roots)
                        )
                    )
                if sproxy_runners not in runner_dirs:
                    runner_dirs.append(sproxy_runners)
                    master_cfg['runner_dirs'] = runner_dirs
                    updated = True
                    salt.utils.stringutils.print_cli(
                        '{} added to runner_dirs:\n'.format(sproxy_runners)
                    )
                    salt.utils.stringutils.print_cli(
                        'runner_dirs:\n  - {0}'.format('\n  - '.join(runner_dirs))
                    )
                if updated:
                    master_fp.seek(0)
                    safe_dump(master_cfg, master_fp, default_flow_style=False)
                    log.debug('Syncing Runners on the Master')
                    runner_client = salt.runner.RunnerClient(self.config)
                    sync_runners = runner_client.cmd(
                        'saltutil.sync_all',
                        kwarg={'saltenv': saltenv},
                        print_event=False,
                    )
                    log.debug('saltutil.sync_all output:')
                    log.debug(sync_runners)
                else:
                    salt.utils.stringutils.print_cli(
                        'The {} path is already included into the file_roots and runner_dirs'.format(
                            curpath
                        )
                    )
                salt.utils.stringutils.print_cli(
                    '\nNow you can start using salt-sproxy for '
                    'event-driven automation, and the Salt REST API.\n'
                    'See https://salt-sproxy.readthedocs.io/en/latest/salt_api.html'
                    '\nand https://salt-sproxy.readthedocs.io/en/latest/events.html '
                    'for more details.'
                )
            return
        # The code below executes the Runner sequence, but it swaps the function
        # to be invoked, and instead call ``napalm.execute``, passing the
        # function requested by the user from the CLI, as an argument.
        # The same goes with the CLI options that are sent as kwargs to the
        # proxy Runner.
        tgt = self.config['tgt']
        fun = self.config['fun']
        args = self.config['arg']
        kwargs = {}
        if 'output' not in self.config and fun in (
            'state.sls',
            'state.apply',
            'state.highstate',
        ):
            self.config['output'] = 'highstate'
        kwargs['progress'] = self.config.pop('progress', False)
        # To be able to reuse the proxy Runner (which is not yet available
        # natively in Salt), we can override the ``runner_dirs`` configuration
        # option to tell Salt to load that Runner too. This way, we can also
        # load other types of modules that may be required or we provide fixes
        # or backports - for example the Ansible Roster which doesn't work fine
        # pre Salt 2018.3 (in case anyone would like to use it).
        file_roots = self.config.get('file_roots', {saltenv: []})
        if saltenv not in file_roots:
            file_roots[saltenv] = []
        file_roots[saltenv].append(curpath)
        self.config['file_roots'] = file_roots
        runner_dirs = self.config.get('runner_dirs', [])
        runner_path = os.path.join(curpath, '_runners')
        runner_dirs.append(runner_path)
        self.config['runner_dirs'] = runner_dirs
        runner_client = None
        sync_all = self.config.get('sync_all', False)
        sync_grains = self.config.get('sync_grains', True)
        sync_modules = self.config.get('sync_modules', False)
        sync_roster = self.config.get('sync_roster', True)
        if any([sync_all, sync_grains, sync_modules, sync_roster]):
            runner_client = salt.runner.RunnerClient(self.config)
        if sync_all:
            log.debug('Sync all')
            sync_all_ret = runner_client.cmd(
                'saltutil.sync_all', kwarg={'saltenv': saltenv}, print_event=False
            )
            log.debug(sync_all_ret)
        if sync_grains and not sync_all:
            log.debug('Syncing grains')
            sync_grains_ret = runner_client.cmd(
                'saltutil.sync_grains', kwarg={'saltenv': saltenv}, print_event=False
            )
            log.debug(sync_grains_ret)
        if self.config.get('module_dirs_cli'):
            log.debug(
                'Loading execution modules from the dirs provided via --module-dirs'
            )
            module_dirs = self.config.get('module_dirs', [])
            module_dirs.extend(self.config['module_dirs_cli'])
            self.config['module_dirs'] = module_dirs
        if sync_modules and not sync_all:
            # Don't sync modules by default
            log.debug('Syncing modules')
            module_dirs = self.config.get('module_dirs', [])
            module_path = os.path.join(curpath, '_modules')
            module_dirs.append(module_path)
            self.config['module_dirs'] = module_dirs
            # No need to explicitly load the modules here, as during runtime,
            # Salt is anyway going to load the modules on the fly.
            sync_modules_ret = runner_client.cmd(
                'saltutil.sync_modules', kwarg={'saltenv': saltenv}, print_event=False
            )
            log.debug(sync_modules_ret)
        # Resync Roster module to load the ones we have here in the library, and
        # potentially others provided by the user in their environment
        if sync_roster and not sync_all:
            # Sync Rosters by default
            log.debug('Syncing roster')
            roster_dirs = self.config.get('roster_dirs', [])
            roster_path = os.path.join(curpath, '_roster')
            roster_dirs.append(roster_path)
            self.config['roster_dirs'] = roster_dirs
            sync_roster_ret = runner_client.cmd(
                'saltutil.sync_roster', kwarg={'saltenv': saltenv}, print_event=False
            )
            log.debug(sync_roster_ret)
        if self.config.get('states_dir'):
            states_dirs = self.config.get('states_dirs', [])
            states_dirs.append(self.config['states_dir'])
            self.config['states_dirs'] = states_dirs
        self.config['fun'] = 'proxy.execute'
        tmp_args = args[:]
        for index, arg in enumerate(tmp_args):
            if isinstance(arg, dict) and '__kwarg__' in arg:
                args.pop(index)
                kwargs = arg
        kwargs['__kwarg__'] = True
        tgt_types = (
            'compound',
            'list',
            'grain',
            'pcre',
            'grain_pcre',
            'pillar_pcre',
            'nodegroup',
        )
        kwargs['tgt_type'] = 'glob'
        for tgt_type in tgt_types:
            if hasattr(self.options, tgt_type) and getattr(self.options, tgt_type):
                kwargs['tgt_type'] = tgt_type
        kwargs_opts = (
            'preview_target',
            'batch_size',
            'batch_wait',
            'cache_grains',
            'cache_pillar',
            'roster',
            'timeout',
            'static',
            'no_connect',
            'failhard',
            'summary',
            'verbose',
            'show_jid',
            'hide_timeout',
            'progress',
            'returner',
            'returner_config',
            'returner_kwargs',
        )
        for kwargs_opt in kwargs_opts:
            if getattr(self.options, kwargs_opt) is not None:
                kwargs[kwargs_opt] = getattr(self.options, kwargs_opt)
        reverse_opts = {
            # option_name: runner_kwarg
            'no_cached_grains': 'use_cached_grains',
            'no_cached_pillar': 'use_cached_pillar',
            'no_grains': 'with_grains',
            'no_pillar': 'with_pillar',
            'no_target_cache': 'target_cache',
        }
        for opt, kwarg in six.iteritems(reverse_opts):
            if getattr(self.options, opt):
                kwargs[kwarg] = False
        kwargs['events'] = self.config.get('events', False)
        kwargs['use_existing_proxy'] = self.config.get('use_existing_proxy', False)
        kwargs['test_ping'] = self.config.get('test_ping', False)
        kwargs['target_cache_timeout'] = self.config.get(
            'target_cache_timeout', 60
        )  # seconds
        kwargs['args'] = args
        kwargs['default_grains'] = self.config.get(
            'sproxy_grains',
            self.config.get('default_grains', self.config.get('grains')),
        )
        kwargs['default_pillar'] = self.config.get(
            'sproxy_pillar',
            self.config.get('default_pillar', self.config.get('pillar')),
        )
        kwargs['preload_targeting'] = self.config.get('preload_targeting', False)
        kwargs['invasive_targeting'] = self.config.get('invasive_targeting', False)
        kwargs['failhard'] = self.config.get('failhard', False)
        self.config['arg'] = [tgt, fun, kwargs]
        runner = salt.runner.Runner(self.config)

        # Run this here so SystemExit isn't raised anywhere else when
        # someone tries to use the runners via the python API
        try:
            if check_user(self.config['user']):
                pr = activate_profile(profiling_enabled)
                try:
                    ret = runner.run()
                    # In older versions ret['data']['retcode'] was used
                    # for signaling the return code. This has been
                    # changed for the orchestrate runner, but external
                    # runners might still use it. For this reason, we
                    # also check ret['data']['retcode'] if
                    # ret['retcode'] is not available.
                    if isinstance(ret, dict) and 'retcode' in ret:
                        self.exit(ret['retcode'])
                    elif isinstance(ret, dict) and 'retcode' in ret.get('data', {}):
                        self.exit(ret['data']['retcode'])
                finally:
                    output_profile(
                        pr, stats_path=self.options.profiling_path, stop=True
                    )

        except SaltClientError as exc:
            raise SystemExit(six.text_type(exc))
