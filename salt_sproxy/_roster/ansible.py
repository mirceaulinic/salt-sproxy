# -*- coding: utf-8 -*-
"""
Read in an Ansible inventory file or script

Flat inventory files should be in the regular ansible inventory format.

.. code-block:: ini

    [servers]
    salt.gtmanfred.com ansible_ssh_user=gtmanfred ansible_ssh_host=127.0.0.1 ansible_ssh_port=22 ansible_ssh_pass='password'

    [desktop]
    home ansible_ssh_user=gtmanfred ansible_ssh_host=12.34.56.78 ansible_ssh_port=23 ansible_ssh_pass='password'

    [computers:children]
    desktop
    servers

    [names:vars]
    http_port=80

then salt-ssh can be used to hit any of them

.. code-block:: bash

    [~]# salt-ssh -N all test.ping
    salt.gtmanfred.com:
        True
    home:
        True
    [~]# salt-ssh -N desktop test.ping
    home:
        True
    [~]# salt-ssh -N computers test.ping
    salt.gtmanfred.com:
        True
    home:
        True
    [~]# salt-ssh salt.gtmanfred.com test.ping
    salt.gtmanfred.com:
        True

There is also the option of specifying a dynamic inventory, and generating it on the fly

.. code-block:: bash

    #!/bin/bash
    echo '{
      "servers": [
        "salt.gtmanfred.com"
      ],
      "desktop": [
        "home"
      ],
      "computers": {
        "hosts": [],
        "children": [
          "desktop",
          "servers"
        ]
      },
      "_meta": {
        "hostvars": {
          "salt.gtmanfred.com": {
            "ansible_ssh_user": "gtmanfred",
            "ansible_ssh_host": "127.0.0.1",
            "ansible_sudo_pass": "password",
            "ansible_ssh_port": 22
          },
          "home": {
            "ansible_ssh_user": "gtmanfred",
            "ansible_ssh_host": "12.34.56.78",
            "ansible_sudo_pass": "password",
            "ansible_ssh_port": 23
          }
        }
      }
    }'

This is the format that an inventory script needs to output to work with ansible, and thus here.

.. code-block:: bash

    [~]# salt-ssh --roster-file /etc/salt/hosts salt.gtmanfred.com test.ping
    salt.gtmanfred.com:
            True

Any of the [groups] or direct hostnames will return.  The 'all' is special, and returns everything.
"""
# Import Python libs
from __future__ import absolute_import, print_function, unicode_literals
import copy
import json
import logging

# Import Salt libs
from salt.roster import get_roster_file

try:
    from salt.utils.path import which as utils_which
    from salt.utils.stringutils import to_str as utils_to_str
except ImportError:
    from salt.utils import which as utils_which
    from salt.utils import to_str as utils_to_str

# Import salt-sproxy modules
import salt_sproxy._roster

log = logging.getLogger(__name__)

CONVERSION = {
    "ansible_ssh_host": "host",
    "ansible_ssh_port": "port",
    "ansible_ssh_user": "user",
    "ansible_ssh_pass": "passwd",
    "ansible_sudo_pass": "sudo",
    "ansible_ssh_private_key_file": "priv",
}

__virtualname__ = "ansible"


def __virtual__():
    return (
        utils_which("ansible-inventory") and __virtualname__,
        "Install `ansible` to use inventory",
    )


def targets(tgt, tgt_type="glob", **kwargs):
    """
    Return the targets from the ansible inventory_file
    Default: /etc/salt/roster
    """
    inventory = __runner__["salt.cmd"](
        "cmd.run", "ansible-inventory -i {0} --list".format(get_roster_file(__opts__))
    )
    __context__["inventory"] = json.loads(utils_to_str(inventory))

    if tgt_type == "nodegroup":
        hosts = _get_hosts_from_group(tgt)
        return {host: _get_hostvars(host) for host in hosts}
    pool = {host: _get_hostvars(host) for host in _get_hosts_from_group("all")}
    pool = salt_sproxy._roster.load_cache(
        pool, __runner__, __opts__, tgt, tgt_type=tgt_type
    )
    log.debug("Ansible devices pool")
    log.debug(pool)
    engine = salt_sproxy._roster.TGT_FUN[tgt_type]
    return engine(pool, tgt, opts=__opts__)


def _get_hosts_from_group(group):
    inventory = __context__["inventory"]
    hosts = [host for host in inventory.get(group, {}).get("hosts", [])]
    for child in inventory.get(group, {}).get("children", []):
        hosts.extend(_get_hosts_from_group(child))
    return hosts


def _get_hostvars(host):
    hostvars = __context__["inventory"]["_meta"].get("hostvars", {}).get(host, {})
    ret = copy.deepcopy(__opts__.get("roster_defaults", {}))
    for key, value in CONVERSION.items():
        if key in hostvars:
            ret[value] = hostvars.pop(key)
    ret["minion_opts"] = hostvars
    if "host" not in ret:
        ret["host"] = host
    return ret
