# -*- coding: utf-8 -*-
'''
SSH Proxy
=========

Proxy Module that invokes Salt functions via SSH, by uploading a lightweight
Salt version on the target host.
'''
from __future__ import absolute_import, print_function, unicode_literals

import json
import logging

import salt.client.ssh
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
    argv = [fun]
    argv.extend(args)
    argv.extend(
        ['{key}={val}'.format(key=key, val=val) for key, val in six.iteritems(kwargs)]
    )
    # TODO: Have here more options to simplify the usage, through features like
    # auto-expand the path to the priv key, auto-discovery, etc.
    conn = salt.client.ssh.Single(opts, argv, opts['id'], **opts['proxy'])
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
    CONN = _prep_conn(opts, 'cmd.run', 'echo')
    ret = CONN.run()
    log.debug(ret)
    if ret[2] == 0:
        INITIALIZED = True
    else:
        log.error(ret[1])


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
