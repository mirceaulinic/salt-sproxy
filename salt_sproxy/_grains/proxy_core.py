# -*- coding: utf-8 -*-
'''
Override core Grains.
'''
import tempfile

import salt.grains.core
import salt.utils.platform
import salt.modules.cmdmod

__proxyenabled__ = ["netmiko"]


def _decorate(func, proxy=None):
    if not proxy:
        return
    if not (__opts__['proxy']['proxytype'] == 'netmiko' and __opts__['proxy']['device_type'] == 'linux'):
        return
    conn = proxy['netmiko.conn']()
    send_cmd = getattr(conn, 'send_command')
    salt.modules.cmdmod.run = send_cmd
    proxy.pack['__salt__']['cmd.run'] = send_cmd
    def run_all(*args, **kwargs):
        # TODO: find a way to set environment variables, etc. on the remote.
        # TODO: pass in Netmiko args.
        cmd = ' '.join(args[0])
        ret = send_cmd(cmd)
        return {
            'stdout': ret,
            'retcode': 0 if 'Failed' not in ret else 1,
            'stderr': ret if 'Failed' in ret else '',
        }
    salt.modules.cmdmod.run_all = run_all
    proxy.pack['__salt__']['cmd.run_all'] = run_all

    def fopen(*args, **kwargs):
        read = send_cmd('cat {}'.format(args[0]))
        tmp = tempfile.mkstemp()
        with open(tmp[1], 'w') as fh:
            fh.write(read)
        f_handle = open(tmp[1], **kwargs)
        return f_handle

    def fread(path, binary=False):
        with fopen(path) as f_handle:
            return f_handle.read()

    proxy.pack['__salt__']['file.read'] = fread

    salt.utils.files.fopen = fopen
    salt.utils.platform.is_proxy = lambda: False
    salt.utils.platform.is_linux = lambda: True
    func.__globals__['__opts__'] = __opts__
    ret = func()
    salt.utils.platform.is_proxy = lambda: True
    salt.utils.platform.is_linux = lambda: False
    return ret


def os_data(proxy=None):
    return _decorate(salt.grains.core.os_data, proxy=proxy)


def locale_info(proxy=None):
    return _decorate(salt.grains.core.locale_info, proxy=proxy)


def _hostname():
    return {'host': salt.modules.cmdmod.run('hostname')}


def hostname(proxy=None):
    return _decorate(_hostname, proxy=proxy)
