# -*- coding: utf-8 -*-
'''
Load devices from `NetBox <https://github.com/digitalocean/netbox>`__, and make
them available for salt-ssh or salt-sproxy (or any other program that doesn't
require (Proxy) Minions running).

Make sure that the following options are configured on the Master:

.. code-block:: yaml

    netbox:
      url: <NETBOX_URL>
      token: <NETBOX_USERNAME_API_TOKEN (OPTIONAL)>
      keyfile: </PATH/TO/NETBOX/KEY (OPTIONAL)>

If you want to pre-filter the devices, so it won't try to pull the whole
database available in NetBox, you can configure another key, ``filters``, under
``netbox``, e.g.,

.. code-block:: yaml

    netbox:
      url: <NETBOX_URL>
      filters:
        site: <SITE>
        status: <STATUS>

.. hint::

    You can use any NetBox field as a filter.

.. important::

    In NetBox v2.6 the default view permissions changed, so ``salt-sproxy`` may
    not able to get the device list from NetBox by default.

    Add ``EXEMPT_VIEW_PERMISSIONS = ['*']`` to the ``configuration.py`` NetBox
    file to change this behavior.
    See https://github.com/netbox-community/netbox/releases/tag/v2.6.0 for more
    information
'''
# Import Python libs
from __future__ import absolute_import, print_function, unicode_literals

try:
    import pynetbox  # pylint: disable=unused-import

    HAS_PYNETBOX = True
except ImportError:
    HAS_PYNETBOX = False

import salt_sproxy._roster

__virtualname__ = 'netbox'


def __virtual__():
    if not HAS_PYNETBOX:
        return (False, 'Please install pynetbox to be able to use the NetBox Roster')
    return __virtualname__


def targets(tgt, tgt_type='glob', **kwargs):
    '''
    Return the targets from NetBox.
    '''
    netbox_filters = __opts__.get('netbox', {}).get('filters', {})
    netbox_filters.update(**kwargs)
    if tgt_type == 'glob' and not any([char in tgt for char in '*?[!']):
        netbox_filters['name'] = tgt
    netbox_devices = __runner__['salt.cmd'](
        'netbox.filter', 'dcim', 'devices', **netbox_filters
    )
    pool = {
        device['name']: {'minion_opts': {'grains': {'netbox': device}}}
        for device in netbox_devices
    }
    engine = salt_sproxy._roster.TGT_FUN[tgt_type]
    return engine(pool, tgt, opts=__opts__)
