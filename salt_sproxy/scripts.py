# -*- coding: utf-8 -*-

import sys

from salt.scripts import _install_signal_handlers


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
