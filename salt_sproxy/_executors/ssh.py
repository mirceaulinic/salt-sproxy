# -*- coding: utf-8 -*-
'''
SSH Executor module
===================

Used in conjunction with the SSH Proxy, to invoke Salt functions through Salt
thin, on a remove mchine accessed via SSH.
'''
from __future__ import absolute_import, unicode_literals

import logging

__virtualname__ = 'ssh'
__proxyenabled__ = ['ssh']


log = logging.getLogger(__name__)


def __virtual__():
    if 'proxy' not in __opts__:
        return False, 'SSH Executor is only meant to be used with SSH Proxy Minions'
    if __opts__.get('proxy', {}).get('proxytype') != __virtualname__:
        return False, 'Proxytype does not match: {0}'.format(__virtualname__)
    return True


def execute(opts, data, func, args, kwargs):
    '''
    Directly calls the given function with arguments
    '''
    if data['fun'] == 'saltutil.find_job':
        return __executors__['direct_call.execute'](opts, data, func, args, kwargs)
    return __proxy__['ssh.call'](data['fun'], *args, **kwargs)


def allow_missing_func(function):  # pylint: disable=unused-argument
    '''
    Allow all calls to be passed through to docker container.

    The ssh call will use direct_call, which will return back if the module
    was unable to be run.
    '''
    return True
