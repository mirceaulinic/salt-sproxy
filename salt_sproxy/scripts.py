# -*- coding: utf-8 -*-
from __future__ import absolute_import

import sys
import inspect
import logging
import traceback
import multiprocessing

import salt.netapi
import salt.scripts
from salt.ext import six
import salt.minion
import salt.cli.daemons
import salt.utils.parsers
from salt.scripts import _install_signal_handlers
from salt.exceptions import SaltInvocationError

from salt_sproxy.core import StandaloneProxy
from salt_sproxy._runners.proxy import execute as sproxy_execute

log = logging.getLogger(__name__)


def _prep_kwargs(kwargs, opts):
    '''
    Gather the sproxy execute argument from the Master opts when available.
    '''
    execute_args = set(inspect.getfullargspec(sproxy_execute)[0])
    sapi_args = execute_args - {'tgt', 'salt_function', 'tgt_type', 'static', 'timeout'}
    for arg in sapi_args:
        if arg not in kwargs and arg in opts:
            kwargs[arg] = opts[arg]
    return kwargs


def sapi_sproxy(
    self, tgt, fun, tgt_type='glob', timeout=None, full_return=False, **kwargs
):
    '''
    Shortcut to invoke an arbitrary Salt function via sproxy.
    '''
    kwargs.update(
        {'salt_function': fun, 'tgt': tgt, 'tgt_type': tgt_type, 'static': True}
    )
    kwargs = _prep_kwargs(kwargs, self.opts)
    log.debug('New kwargs:')
    log.debug(kwargs)
    return salt.netapi.NetapiClient.runner(
        self, 'proxy.execute', timeout=timeout, full_return=full_return, **kwargs
    )


def sapi_sproxy_async(
    self, tgt, fun, tgt_type='glob', timeout=None, full_return=False, **kwargs
):
    '''
    Shortcut to invoke an arbitrary Salt function via sproxy, asynchronously.
    '''
    kwargs.update(
        {'salt_function': fun, 'tgt': tgt, 'tgt_type': tgt_type, 'static': True}
    )
    kwargs = _prep_kwargs(kwargs, self.opts)
    log.debug('New kwargs:')
    log.debug(kwargs)
    return salt.netapi.NetapiClient.runner_async(
        self, 'proxy.execute', timeout=timeout, full_return=full_return, **kwargs
    )


salt.netapi.NetapiClient.sproxy = sapi_sproxy
salt.netapi.NetapiClient.sproxy_async = sapi_sproxy_async
salt.netapi.CLIENTS = [
    name
    for name, _ in inspect.getmembers(
        salt.netapi.NetapiClient, predicate=inspect.ismethod if six.PY2 else None
    )
    if not (name == 'run' or name.startswith('_'))
]
salt.utils.parsers.SaltAPIParser.description = (
    'salt-sapi is an enhanced Salt API system that provides additional '
    'sproxy and sproxy_async clients, to simplify the usage of salt-sproxy '
    'through the Salt REST API'
)
salt.utils.parsers.SaltAPIParser.epilog = (
    'You can find additional help about %prog issuing "man %prog" '
    'or on https://salt-sproxy.readthedocs.io/ and '
    'https://docs.saltstack.com/en/latest/ref/cli/salt-api.html.'
)


def _salt_call(function_name, function_args, executors, opts, data=None):
    '''
    '''
    if not data:
        data = {}
    opts['__cli'] = opts.get('__cli', 'salt-call')
    opts['__tgt'] = data.get('tgt', opts['id'])
    opts['__tgt_type'] = data.get('tgt_type', 'glob')
    opts['roster_opts'] = opts.get('roster_opts', {})
    returner = data.get('ret')
    opts['returner'] = returner
    opts['module_executors'] = executors
    unreachable_devices = multiprocessing.Queue()
    sa_proxy = StandaloneProxy(opts, unreachable_devices)
    if not sa_proxy.ready:
        log.debug(
            'The SProxy Minion for %s is not able to start up, aborting', opts['id']
        )
        return
    ret = None
    retcode = 0

    if function_name in sa_proxy.functions:
        func = sa_proxy.functions[function_name]
        args, kwargs = salt.minion.load_args_and_kwargs(func, function_args, data)
    else:
        func = function_name
        args, kwargs = function_args, data
    sa_proxy.functions.pack["__context__"]["retcode"] = 0

    try:
        if executors:
            for name in executors:
                ex_name = '{}.execute'.format(name)
                if ex_name not in sa_proxy.executors:
                    raise SaltInvocationError(
                        "Executor '{0}' is not available".format(name)
                    )
                ret = sa_proxy.executors[ex_name](opts, data, func, args, kwargs)
                if ret is not None:
                    break
        else:
            ret = sa_proxy.functions[function_name](*args, **kwargs)
        retcode = sa_proxy.functions.pack['__context__'].get('retcode', 0)
    except Exception as err:
        log.info('Exception while running %s on %s', function_name, opts['id'])
        ret = 'The minion function caused an exception: {err}'.format(
            err=traceback.format_exc()
        )
        if not retcode:
            retcode = 11
        if opts.get('failhard', False):
            raise
    finally:
        if sa_proxy.connected:
            shut_fun = '{}.shutdown'.format(sa_proxy.opts['proxy']['proxytype'])
            sa_proxy.proxy[shut_fun](opts)
    if returner:
        returner_fun = '{}.returner'.format(returner)
        if returner_fun in sa_proxy.returners:
            log.debug(
                'Sending the response from %s to the %s Returner', opts['id'], returner,
            )
            ret_data = {
                'id': opts['id'],
                'jid': data.get('jid'),
                'fun': function_name,
                'fun_args': function_args,
                'return': ret,
            }
            try:
                sa_proxy.returners[returner_fun](ret_data)
            except Exception as err:
                log.error(
                    'Exception while sending the response from %s to the %s returner',
                    opts['id'],
                    returner,
                )
                log.error(err, exc_info=True)
        else:
            log.warning(
                'Returner %s is not available. Check that the dependencies are properly installed'
            )
    sa_proxy.functions.pack["__context__"]["retcode"] = retcode
    return ret


def _post_master_init(self, master):
    '''
    '''
    log.debug('_post_master_init from sproxy')
    self.functions = {}


def _execute_job_function(self, function_name, function_args, executors, opts, data):
    '''
    '''
    log.debug('Calling _execute_job_function from sproxy')
    return _salt_call(function_name, function_args, executors, opts, data=data)


salt.minion.Minion._post_master_init = _post_master_init
salt.minion.Minion._execute_job_function = _execute_job_function
salt.minion.ProxyMinionManager = salt.minion.MinionManager
LightMinionDaemon = salt.cli.daemons.ProxyMinion


def salt_lproxy():
    '''
    Start up the Salt Light Proxy daemon.
    '''
    if '' in sys.path:
        sys.path.remove('')
    light_minion = LightMinionDaemon()
    light_minion.start()
    return


def salt_sapi():
    '''
    The main function for salt-sapi.
    '''
    salt.scripts.salt_api()


def salt_sproxy():
    '''
    Execute a salt convenience routine.
    '''
    import salt_sproxy.cli

    if '' in sys.path:
        sys.path.remove('')
    client = salt_sproxy.cli.SaltStandaloneProxy()
    _install_signal_handlers(client)
    client.run()


if __name__ == '__main__':
    salt_sproxy()
