# -*- coding: utf-8 -*-
'''
SSH Proxy
=========

Manage a remote host via SSH, using a Proxy Minion. This module doesn't have any
external dependencies, as it makes use of the native Salt internals used for
salt-ssh, therefore managing the remote machine by uploading a lightweight Salt
version on the target host, then invokes Salt functions over SSH (using the
``ssh`` binary installed on your computer or wherever this Proxy Minion runs).

.. note::

    To manage machines running Windows, you will need to install the
    ``saltwinshell`` library.

Pillar
------

The configuration is aligned to the general Proxy Minion standards: put the
connection details and credentials under the ``proxy`` key in the Proxy config
or Pillar.

.. important:

    Local (i.e., per Proxy) option override the global configuration or CLI
    options.

``host``
    The IP address or the hostname of the remove machine to manage.

``port``
    Integer, the port number to use when establishing he connection
    (defaults to 22).

``user``
    The username required for authentication.

``passwd``
    The password used for authentication.

``priv``
    Absolute path to the private SSH key used for authentication.

``priv_passwd``
    The SSH private key password.

``timeout``: 30
    The SSH timeout. Defaults to 30 seconds.

``sudo``: ``False``
    Execute commands as sudo.

``tty``: ``False``
    Connect over tty.

``sudo_user``
    The username that should execute the commands as sudo.

``remote_port_forwards``
    Enable remote port forwarding. Example: ``8888:my.company.server:443``.
    Multiple remote port forwardings are supported, using comma-separated
    values, e.g., ``8888:my.company.server:443,9999:my.company.server:80``.

``identities_only``: ``False``
    Execute SSH with ``-o IdentitiesOnly=yes``. This option is intended for
    situations where ssh-agent offers many different identities and allow ssh
    to ignore those identities and use the only one specified in options.

``ignore_host_keys``: ``False``
    By default ssh host keys are honored and connections will ask for approval.
    Use this option to disable ``StrictHostKeyChecking``.

``no_host_keys``: ``False``
    Fully ignores ssh host keys which by default are honored and connections
    would ask for approval. Useful if the host key of a remote server has
    changed and would still error with ``ignore_host_keys``.

``winrm``: ``False``
    Flag that tells Salt to connect to a Windows machine. This option requires
    the ``saltwinshell`` to be installed.

Example Pillar:

.. code-block:: yaml

  proxy:
    proxytype: ssh
    host: srv.example.com
    user: test
    passwd: test
    port: 2022
'''
from __future__ import absolute_import, print_function, unicode_literals

import json
import logging

import salt.client.ssh
import salt.fileclient
import salt.exceptions
import salt.utils.path
from salt.ext import six

__proxyenabled__ = ['ssh']

log = logging.getLogger(__name__)

CONN = None
INITIALIZED = False
GRAINS_CACHE = {}


def _prep_conn(opts, fun, *args, **kwargs):
    '''
    Prepare the connection.
    '''
    opts['_ssh_version'] = salt.client.ssh.ssh_version()
    fsclient = salt.fileclient.FSClient(opts)
    # TODO: Have here more options to simplify the usage, through features like
    # auto-expand the path to the priv key, auto-discovery, etc.
    argv = [fun]
    argv.extend([salt.utils.json.dumps(arg) for arg in args])
    argv.extend(
        [
            "{0}={1}".format(
                salt.utils.stringutils.to_str(key), salt.utils.json.dumps(val)
            )
            for key, val in six.iteritems(kwargs)
        ]
    )
    if not opts['proxy'].get('ssh_options'):
        opts['proxy']['ssh_options'] = []
    if opts['proxy'].get('ignore_host_keys', False):
        opts['proxy']['ssh_options'].append('StrictHostKeyChecking=no')
    if opts['proxy'].get('no_host_keys', False):
        opts['proxy']['ssh_options'].extend(
            ["StrictHostKeyChecking=no", "UserKnownHostsFile=/dev/null"]
        )
    for cli_opt in ('identities_only', 'priv', 'priv_passwd'):
        if opts.get(cli_opt) and not opts['proxy'].get(cli_opt):
            opts['proxy'][cli_opt] = opts[cli_opt]
    conn = salt.client.ssh.Single(
        opts, argv, opts['id'], fsclient=fsclient, **opts['proxy']
    )
    conn.args = args
    conn.kwargs = kwargs
    thin_dir = conn.opts['thin_dir']
    thin_dir = thin_dir.replace('proxy', '')
    conn.opts['thin_dir'] = thin_dir
    conn.thin_dir = thin_dir
    return conn


def init(opts):
    '''
    Init the SSH connection, and execute a simple call to ensure that the remote
    device is reachable, otherwise throw an error.
    '''
    global CONN, INITIALIZED
    if not salt.utils.path.which('ssh'):
        raise salt.exceptions.SaltSystemExit(
            code=-1,
            msg='No ssh binary found in path -- ssh must be installed for this Proxy module. Exiting.',
        )
    CONN = _prep_conn(opts, 'cmd.run', 'echo')
    INITIALIZED = True


def initialized():
    '''
    Proxy initialized properly?
    '''
    return INITIALIZED


def module_executors():
    '''
    Return the list of executors that should invoke the Salt functions.
    '''
    return ['ssh']


def call(fun, *args, **kwargs):
    '''
    Call an arbitrary Salt function and return the output.
    '''
    global CONN, INITIALIZED
    if not CONN or not INITIALIZED:
        return
    opts = CONN.opts
    opts['output'] = 'json'
    ssh_conn = _prep_conn(opts, fun, *args, **kwargs)
    ret = ssh_conn.run()
    if ret[2] != 0:
        log.error('[%s] %s', opts['id'], ret[1])
        return ret[0]
    thin_ret = json.loads(ret[0])
    if '_error' in thin_ret['local']:
        log.error(thin_ret['local']['_error'])
        if 'stdout' in thin_ret['local']:
            log.error(thin_ret['local']['stdout'])
    return thin_ret['local']['return']


def ping():
    '''
    Execute "echo" on the remote host to ensure it's still accessible.
    '''
    global CONN, INITIALIZED
    if not CONN or not INITIALIZED:
        log.debug('Not connected, or not initialized')
        return False
    ret = CONN.run()
    log.debug(ret)
    return ret[2] == 0


def grains():
    '''
    Invoke grains.items from the thin Salt on the remote machine, in order to
    return here the Grains.
    '''
    global GRAINS_CACHE
    if not GRAINS_CACHE:
        GRAINS_CACHE = call('grains.items')
    return GRAINS_CACHE


def shutdown(opts):
    '''
    Buh-bye...
    '''
    global CONN, INITIALIZED
    if CONN and INITIALIZED:
        del CONN
        INITIALIZED = False
