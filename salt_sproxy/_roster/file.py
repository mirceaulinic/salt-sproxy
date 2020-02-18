# -*- coding: utf-8 -*-
'''
Load the list of devices from an arbitrary SLS file.

To use this module, you only need to configure the --roster option to ``file``
(on the CLI or Master config), and if the Roster SLS file is in a different
location than ``/etc/salt/roster``, you'd also need to specify ``--roster-file``
(or ``roster_file`` in the Master config).
'''
# Import Python libs
from __future__ import absolute_import, print_function, unicode_literals
import logging

import salt.loader
from salt.roster import get_roster_file
from salt.template import compile_template

import salt_sproxy._roster

__virtualname__ = 'file'

log = logging.getLogger(__name__)


def targets(tgt, tgt_type='glob', **kwargs):
    '''
    Return the targets from the sls file, checks opts for location but
    defaults to /etc/salt/roster
    '''
    template = get_roster_file(__opts__)
    rend = salt.loader.render(__opts__, {})
    kwargs['__salt__'] = __runner__
    pool = compile_template(
        template,
        rend,
        __opts__['renderer'],
        __opts__['renderer_blacklist'],
        __opts__['renderer_whitelist'],
        mask_value='passw*',
        **kwargs
    )
    pool = {host: {'minion_opts': conf} for host, conf in pool.items()}
    pool = salt_sproxy._roster.load_cache(
        pool, __runner__, __opts__, tgt, tgt_type=tgt_type
    )
    engine = salt_sproxy._roster.TGT_FUN[tgt_type]
    return engine(pool, tgt, opts=__opts__)
