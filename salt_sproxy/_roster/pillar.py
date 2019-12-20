# -*- coding: utf-8 -*-
'''
Load the list of devices from the Pillar.

Simply configure the ``roster`` option to point to this module, while making
sure that the data is available. As the Pillar is data associated with a
specific Minion ID, you may need to ensure that the Pillar is correctly
associated with the Minion configured (default ``*``), under the exact key
required (default ``devices``). To adjust these options, you can provide the
following under the ``roster_pillar`` option in the Master configuration:

minion_id: ``*``
    The ID of the Minion to compile the data for. Default: ``*`` (any Minion).

pillar_key: ``devices``
    The Pillar field to pull the list of devices from. Default: ``devices``.

saltenv: ``base``
    The Salt environment to use when compiling the Pillar data.

pillarenv
    The Pillar environment to use when compiling the Pillar data.

Configuration example:

.. code-block:: yaml

    roster: pillar
    roster_pillar:
      minion_id: sproxy
      pillar_key: minions

With the following configuration, when executing
``salt-run pillar.show_pillar sproxy`` you should have under ``minions`` the
list of devices / Minions you want to manage.

.. hint::

    The Pillar data can either be provided as files, or using one or more
    External Pillars. Check out
    https://docs.saltstack.com/en/latest/ref/pillar/all/index.html
    for the complete list of available Pillar modules you can use.
'''
# Import Python libs
from __future__ import absolute_import, print_function, unicode_literals
import logging

import salt_sproxy._roster

__virtualname__ = 'pillar'

log = logging.getLogger(__name__)


def targets(tgt, tgt_type='glob', **kwargs):
    '''
    Return the targets from External Pillar requested.
    '''
    roster_opts = __opts__.get('roster_pillar', {})
    minion_id = roster_opts.get('minion_id', kwargs.get('minion_id', '*'))
    pillar_key = roster_opts.get('pillar_key', kwargs.get('pillar_key', 'devices'))
    saltenv = roster_opts.get('saltenv', kwargs.get('saltenv', 'base'))
    pillarenv = roster_opts.get('pillarenv', kwargs.get('pillarenv'))
    pillar = __runner__['pillar.show_pillar'](
        minion=minion_id, saltenv=saltenv, pillarenv=pillarenv
    )
    pillar_devices = pillar[pillar_key]
    log.debug('Compiled the following list of devices from the Pillar')
    log.debug(pillar_devices)
    pool = {device['name']: {'minion_opts': device} for device in pillar_devices}
    pool = salt_sproxy._roster.load_cache(
        pool, __runner__, __opts__, tgt, tgt_type=tgt_type
    )
    engine = salt_sproxy._roster.TGT_FUN[tgt_type]
    return engine(pool, tgt, opts=__opts__)
