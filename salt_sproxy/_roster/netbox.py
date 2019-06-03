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
'''
# Import Python libs
from __future__ import absolute_import, print_function, unicode_literals
import re
import fnmatch

try:
    import pynetbox  # pylint: disable=unused-import

    HAS_PYNETBOX = True
except ImportError:
    HAS_PYNETBOX = False

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
    netbox_devices = __runner__['salt.cmd'](
        'netbox.filter', 'dcim', 'devices', **netbox_filters
    )
    if tgt_type == 'glob':
        devices = [
            device['name']
            for device in netbox_devices
            if fnmatch.fnmatch(str(device['name']), tgt)
        ]
    elif tgt_type == 'list':
        devices = [device['name'] for device in netbox_devices if device['name'] in tgt]
    elif tgt_type == 'pcre':
        rgx = re.compile(tgt)
        devices = [
            device['name'] for device in netbox_devices if rgx.search(device['name'])
        ]
    elif tgt_type in ['grain', 'grain_pcre']:
        grains = __runner__['cache.grains'](tgt, tgt_type=tgt_type)
        devices = list(grains.keys())
    elif tgt_type in ['pillar', 'pillar_pcre']:
        pillars = __runner__['cache.pillar'](tgt, tgt_type=tgt_type)
        devices = list(pillars.keys())
    # elif tgt_type == 'compound':
    # TODO: Implement the compound matcher, might need quite a bit of work,
    # need to evaluate if it's worth pulling all this code from
    # https://github.com/saltstack/salt/blob/develop/salt/matchers/compound_match.py
    # or find a smarter way to achieve that.
    return {device: {} for device in devices}
