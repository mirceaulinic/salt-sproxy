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

import logging

try:
    import pynetbox  # pylint: disable=unused-import

    HAS_PYNETBOX = True
except ImportError:
    HAS_PYNETBOX = False

import salt.utils.args
from salt.exceptions import CommandExecutionError

import salt_sproxy._roster

__virtualname__ = 'netbox'

log = logging.getLogger(__name__)

AUTH_ENDPOINTS = ('secrets',)


def __virtual__():
    if not HAS_PYNETBOX:
        return (False, 'Please install pynetbox to be able to use the NetBox Roster')
    return __virtualname__


def _setval(key, val, dict_=None, delim=':'):
    '''
    Set a value under the dictionary hierarchy identified
    under the key. The target 'foo:bar:baz' returns the
    dictionary hierarchy {'foo': {'bar': {'baz': {}}}}.
    '''
    if not dict_:
        dict_ = {}
    prev_hier = dict_
    dict_hier = key.split(delim)
    for each in dict_hier[:-1]:
        if isinstance(each, str):
            if each not in prev_hier:
                prev_hier[each] = {}
            prev_hier = prev_hier[each]
        else:
            prev_hier[each] = [{}]
            prev_hier = prev_hier[each]
    prev_hier[dict_hier[-1]] = val
    return dict_


def _netbox_config():
    config = __opts__.get('netbox')
    if not config:
        raise CommandExecutionError(
            'NetBox configuration could not be found in the Master config'
        )
    return config


def _nb_obj(auth_required=False):
    pynb_kwargs = {}
    nb_config = _netbox_config()
    pynb_kwargs['token'] = nb_config.get('token')
    if auth_required:
        pynb_kwargs['private_key_file'] = nb_config.get('keyfile')
    return pynetbox.api(nb_config.get('url'), **pynb_kwargs)


def _strip_url_field(input_dict):
    if 'url' in input_dict.keys():
        del input_dict['url']
    for k, v in input_dict.items():
        if isinstance(v, dict):
            _strip_url_field(v)
    return input_dict


def _netbox_filter(app, endpoint, **kwargs):
    '''
    Get a list of items from NetBox.

    app
        String of netbox app, e.g., ``dcim``, ``circuits``, ``ipam``

    endpoint
        String of app endpoint, e.g., ``sites``, ``regions``, ``devices``

    kwargs
        Optional arguments that can be used to filter.
        All filter keywords are available in Netbox,
        which can be found by surfing to the corresponding API endpoint,
        and clicking Filters. e.g., ``role=router``

    Returns a list of dictionaries.
    '''
    ret = []
    nb = _nb_obj(auth_required=True if app in AUTH_ENDPOINTS else False)
    clean_kwargs = salt.utils.args.clean_kwargs(**kwargs)
    if not clean_kwargs:
        nb_query = getattr(getattr(nb, app), endpoint).all()
    else:
        nb_query = getattr(getattr(nb, app), endpoint).filter(**clean_kwargs)
    if nb_query:
        ret = [_strip_url_field(dict(i)) for i in nb_query]
    return ret


def targets(tgt, tgt_type='glob', **kwargs):
    '''
    Return the targets from NetBox.
    '''
    netbox_filters = __opts__.get('netbox', {}).get('filters', {})
    netbox_filters.update(**kwargs)
    filtered = False
    if tgt_type == 'list' or (
        tgt_type == 'glob' and not any([char in tgt for char in '*?[!'])
    ):
        netbox_filters['name'] = tgt
        filtered = True
    elif tgt_type == 'grain' and tgt.startswith('netbox:'):
        levels = tgt.split('netbox:')[1].split(':')
        if len(levels) > 2:
            netbox_filters[levels[0]] = _setval(':'.join(levels[1:-1]), levels[-1])
            filtered = True
        elif len(levels) == 2:
            netbox_filters[levels[0]] = levels[1]
            filtered = True
    log.debug('Querying NetBox with the following filters')
    log.debug(netbox_filters)
    netbox_devices = _netbox_filter('dcim', 'devices', **netbox_filters)
    pool = {
        device['name']: {'minion_opts': {'grains': {'netbox': device}}}
        for device in netbox_devices
    }
    if filtered:
        return pool
    pool = salt_sproxy._roster.load_cache(
        pool, __runner__, __opts__, tgt, tgt_type=tgt_type
    )
    engine = salt_sproxy._roster.TGT_FUN[tgt_type]
    return engine(pool, tgt, opts=__opts__)
