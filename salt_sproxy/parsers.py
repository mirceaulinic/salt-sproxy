# -*- coding: utf-8 -*-

import sys
import logging
import optparse

import salt_sproxy.version

from salt.ext import six
import salt.version
import salt.utils.args
import salt.utils.parsers
import salt.config as config

try:
    from jnpr.junos import __version__ as jnpr_version

    # Ain't Juniper awkward?
except ImportError:
    jnpr_version = None


def salt_information():
    '''
    Return version of Salt and salt-sproxy.
    '''
    yield 'Salt', salt.version.__version__
    yield 'Salt SProxy', salt_sproxy.version.__version__


def dependency_information(include_salt_cloud=False):
    '''
    Report versions of library dependencies.

    This function has been ported from
    https://github.com/saltstack/salt/blob/develop/salt/version.py
    and extended here to collect the version information for several more
    libraries that may be necessary for various Proxy (or Execution) Modules.
    '''
    libs = [
        ('Python', None, sys.version.rsplit('\n')[0].strip()),
        ('NAPALM', 'napalm', '__version__'),
        ('Netmiko', 'netmiko', '__version__'),
        ('junos-eznc', None, jnpr_version),
        ('ncclient', 'ncclient', '__version__'),
        ('paramiko', 'paramiko', '__version__'),
        ('pyeapi', 'pyeapi', '__version__'),
        ('textfsm', 'textfsm', '__version__'),
        ('jxmlease', 'jxmlease', '__version__'),
        ('scp', 'scp', '__version__'),
        ('PyNSO', 'pynso', '__version__'),
        ('Ansible', 'ansible', '__version__'),
        ('PyNetBox', 'pynetbox', '__version__'),
        ('Jinja2', 'jinja2', '__version__'),
        ('M2Crypto', 'M2Crypto', 'version'),
        ('msgpack-python', 'msgpack', 'version'),
        ('msgpack-pure', 'msgpack_pure', 'version'),
        ('pycrypto', 'Crypto', '__version__'),
        ('pycryptodome', 'Cryptodome', 'version_info'),
        ('PyYAML', 'yaml', '__version__'),
        ('PyZMQ', 'zmq', '__version__'),
        ('ZMQ', 'zmq', 'zmq_version'),
        ('Mako', 'mako', '__version__'),
        ('Tornado', 'tornado', 'version'),
        ('timelib', 'timelib', 'version'),
        ('dateutil', 'dateutil', '__version__'),
        ('pygit2', 'pygit2', '__version__'),
        ('libgit2', 'pygit2', 'LIBGIT2_VERSION'),
        ('smmap', 'smmap', '__version__'),
        ('cffi', 'cffi', '__version__'),
        ('pycparser', 'pycparser', '__version__'),
        ('gitdb', 'gitdb', '__version__'),
        ('gitpython', 'git', '__version__'),
        ('python-gnupg', 'gnupg', '__version__'),
        ('docker-py', 'docker', '__version__'),
    ]

    if include_salt_cloud:
        libs.append(('Apache Libcloud', 'libcloud', '__version__'))

    for name, imp, attr in libs:
        if imp is None:
            yield name, attr
            continue
        try:
            imp = __import__(imp)
            version = getattr(imp, attr)
            if callable(version):
                version = version()
            if isinstance(version, (tuple, list)):
                version = '.'.join(map(str, version))
            yield name, version
        except Exception:
            yield name, None


salt.version.salt_information = salt_information
salt.version.dependency_information = dependency_information


class SaltStandaloneProxyOptionParser(
    six.with_metaclass(
        salt.utils.parsers.OptionParserMeta,
        salt.utils.parsers.OptionParser,
        salt.utils.parsers.ConfigDirMixIn,
        salt.utils.parsers.MergeConfigMixIn,
        salt.utils.parsers.TimeoutMixIn,
        salt.utils.parsers.LogLevelMixIn,
        salt.utils.parsers.HardCrashMixin,
        salt.utils.parsers.SaltfileMixIn,
        salt.utils.parsers.TargetOptionsMixIn,
        salt.utils.parsers.OutputOptionsMixIn,
        salt.utils.parsers.ArgsStdinMixIn,
        salt.utils.parsers.ProfilingPMixIn,
        salt.utils.parsers.EAuthMixIn,
        salt.utils.parsers.NoParseMixin,
    )
):

    default_timeout = 1

    description = (
        'salt-sproxy is a tool to invoke arbitrary Salt functions on a group\n'
        'of (network) devices connecting through a Salt Proxy Minion, without\n'
        'having the Proxy Minion services up and running (or the Master).'
    )

    VERSION = salt_sproxy.version.__version__

    usage = '%prog [options] <target> <function> [arguments]'

    epilog = (
        'You can find additional help about %prog at '
        'https://salt-sproxy.readthedocs.io/en/latest/'
    )

    # ConfigDirMixIn config filename attribute
    _config_filename_ = 'master'

    # LogLevelMixIn attributes
    _default_logging_level_ = config.DEFAULT_MASTER_OPTS['log_level']
    _default_logging_logfile_ = config.DEFAULT_MASTER_OPTS['log_file']

    def _mixin_setup(self):
        self.add_option(
            '-r', '--roster', default=False, help='The name of the Salt Roster to use.'
        )
        self.add_option(
            '--roster-file',
            dest='roster_file',
            help='Absolute path to the Roster file to use.',
        )
        self.add_option(
            '--sync',
            default=False,
            action='store_true',
            help=(
                'Return the replies from the devices immediately they are '
                'received, or everything at once.'
            ),
        )
        self.add_option(
            '--cache-grains',
            default=False,
            action='store_true',
            help=(
                'Cache the collected Grains. This is going to override the '
                'existing cached Grains.'
            ),
        )
        self.add_option(
            '--cache-pillar',
            default=False,
            action='store_true',
            help=(
                'Cache the compiled Pillar. This is going to override the '
                'existing cached Pillar.'
            ),
        )
        self.add_option(
            '--no-cached-grains',
            default=False,
            action='store_true',
            help='Do not use the available cached Grains (if any).',
        )
        self.add_option(
            '--no-cached-pillar',
            default=False,
            action='store_true',
            help='Do not use the available cached Pillar (if any)',
        )
        self.add_option(
            '--no-grains',
            default=False,
            action='store_true',
            help=(
                'Do not attempt to collect Grains at all. Use with care, it '
                'may lead to unexpected results.'
            ),
        )
        self.add_option(
            '--no-pillar',
            default=False,
            action='store_true',
            help=(
                'Do not compile Pillar at all. Use with care, it may lead to '
                'unexpected results.'
            ),
        )
        self.add_option(
            '-b',
            '--batch',
            '--batch-size',
            default=10,
            dest='batch_size',
            help='The number of devices to connect to in parallel.',
        )
        self.add_option(
            '--preview-target',
            dest='preview_target',
            action='store_true',
            help='Show the devices expected to match the target.',
        )
        self.add_option(
            '--sync-roster',
            dest='sync_roster',
            action='store_true',
            help=(
                'Synchronise the Roster modules (both salt-sproxy native '
                'and provided by the user in their own environment).'
            ),
        )
        self.add_option(
            '--events',
            dest='events',
            action='store_true',
            help=(
                'Whether should put the events on the Salt bus (mostly '
                'useful when having a Master running).'
            ),
        )
        self.add_option(
            '--use-proxy',
            '--use-existing-proxy',
            dest='use_existing_proxy',
            action='store_true',
            help=(
                'Use the existing Proxy Minions to execute the commands, '
                'whenever available.'
            ),
        )
        self.add_option(
            '--file-roots',
            '--display-file-roots',
            dest='display_file_roots',
            action='store_true',
            help=(
                'Display the file_roots option you would need to configure '
                'in order to use the salt-sproxy extension modules directly, '
                'and, implicitly, leverage the event-driven methodology and '
                'the Salt REST API.'
            ),
        )
        self.add_option(
            '--save-file-roots',
            dest='save_file_roots',
            action='store_true',
            help=(
                'Saves the file_roots configuration so you can start '
                'leveraging the event-driven automation and the Salt REST API.'
            ),
        )
        group = self.output_options_group = optparse.OptionGroup(
            self, 'Output Options', 'Configure your preferred output format.'
        )
        self.add_option_group(group)

        group.add_option(
            '-q',
            '--quiet',
            default=False,
            action='store_true',
            help='Do not display the results of the run.',
        )

    # Everything else that follows here is verbatim copy from
    # https://github.com/saltstack/salt/blob/develop/salt/utils/parsers.py
    def _mixin_after_parsed(self):
        if self.options.display_file_roots or self.options.save_file_roots:
            # Insert dummy arg when displaying the file_roots
            self.args.append('not_a_valid_target')
            self.args.append('not_a_valid_command')
        if self.options.list:
            try:
                if ',' in self.args[0]:
                    self.config['tgt'] = self.args[0].replace(' ', '').split(',')
                else:
                    self.config['tgt'] = self.args[0].split()
            except IndexError:
                self.exit(42, '\nCannot execute command without defining a target.\n\n')
        else:
            try:
                self.config['tgt'] = self.args[0]
            except IndexError:
                self.exit(42, '\nCannot execute command without defining a target.\n\n')

        if self.options.preview_target:
            # Insert dummy arg which won't be used
            self.args.append('not_a_valid_command')

        # Detect compound command and set up the data for it
        if self.args:
            try:
                if ',' in self.args[1]:
                    self.config['fun'] = self.args[1].split(',')
                    self.config['arg'] = [[]]
                    cmd_index = 0
                    if (
                        self.args[2:].count(self.options.args_separator)
                        == len(self.config['fun']) - 1
                    ):
                        # new style parsing: standalone argument separator
                        for arg in self.args[2:]:
                            if arg == self.options.args_separator:
                                cmd_index += 1
                                self.config['arg'].append([])
                            else:
                                self.config['arg'][cmd_index].append(arg)
                    else:
                        # old style parsing: argument separator can be inside args
                        for arg in self.args[2:]:
                            if self.options.args_separator in arg:
                                sub_args = arg.split(self.options.args_separator)
                                for sub_arg_index, sub_arg in enumerate(sub_args):
                                    if sub_arg:
                                        self.config['arg'][cmd_index].append(sub_arg)
                                    if sub_arg_index != len(sub_args) - 1:
                                        cmd_index += 1
                                        self.config['arg'].append([])
                            else:
                                self.config['arg'][cmd_index].append(arg)
                        if len(self.config['fun']) > len(self.config['arg']):
                            self.exit(
                                42,
                                'Cannot execute compound command without '
                                'defining all arguments.\n',
                            )
                        elif len(self.config['fun']) < len(self.config['arg']):
                            self.exit(
                                42,
                                'Cannot execute compound command with more '
                                'arguments than commands.\n',
                            )
                    # parse the args and kwargs before sending to the publish
                    # interface
                    for i in range(len(self.config['arg'])):
                        self.config['arg'][i] = salt.utils.args.parse_input(
                            self.config['arg'][i], no_parse=self.options.no_parse
                        )
                else:
                    self.config['fun'] = self.args[1]
                    self.config['arg'] = self.args[2:]
                    # parse the args and kwargs before sending to the publish
                    # interface
                    self.config['arg'] = salt.utils.args.parse_input(
                        self.config['arg'], no_parse=self.options.no_parse
                    )
            except IndexError:
                self.exit(42, '\nIncomplete options passed.\n\n')

    def setup_config(self):
        return config.client_config(self.get_config_file_path())
