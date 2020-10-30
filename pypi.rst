Salt SProxy
===========

Salt plugin for interacting with network devices, without running Minions.

.. note::

    This is NOT a SaltStack product.

    This package may eventually be integrated in a future version of the 
    official Salt releases, in this form or slightly different.

Install
-------

Install this package where you would like to manage your devices from. In case
you need a specific Salt version, make sure you install it beforehand, 
otherwise this package will bring the latest Salt version available instead.

The package is distributed via PyPI, under the name ``salt-sproxy``.

Execute:

.. code-block:: bash

    pip install salt-sproxy

Documentation
-------------

The complete documentation is available at 
https://salt-sproxy.readthedocs.io/en/latest/.

Usage
-----

First off, make sure you have the Salt `Pillar Top file 
<https://docs.saltstack.com/en/latest/ref/states/top.html>`_ correctly defined
and the ``proxy`` key is available into the Pillar. For more in-depth 
explanation and examples, check `this 
<https://docs.saltstack.com/en/latest/topics/proxyminion/index.html>`_ tutorial 
from the official SaltStack docs.

Once you have that, you can start using ``salt-sproxy`` even without any Proxy
Minions or Salt Master running. To check, can start by executing:

.. code-block:: bash

    $ salt-sproxy -L a,b,c --preview-target
    - a
    - b
    - c

The syntax is very similar to the widely used CLI command ``salt``, however the
way it works is completely different under the hood:

``salt-sproxy <target> <function> [<arguments>]``

Usgae Example:

.. code-block:: bash

    $ salt-sproxy cr1.thn.lon test.ping
    cr1.thn.lon:
        True

One of the most important differences between ``salt`` and ``salt-sproxy`` is
that the former is aware of the devices available, thanks to the fact that the
Minions connect to the Master, therefore ``salt`` has the list of targets 
already available. ``salt-sproxy`` does not have this, as it doesn't require 
the Proxy Minions to be up and connected to the Master. For this reason, you 
will need to provide it a list of devices, or a `Roster file 
<https://docs.saltstack.com/en/latest/topics/ssh/roster.html>`_ that provides
the list of available devices.

The following targeting options are available:

- ``-E``, ``--pcre``: Instead of using shell globs to evaluate the target
  servers, use pcre regular expressions.
- ``-L``, ``--list``: Instead of using shell globs to evaluate the target
  servers, take a comma or space delimited list of servers.
- ``-G``, ``--grain``: Instead of using shell globs to evaluate the target
  use a grain value to identify targets, the syntax for the target is the grain
  key followed by a globexpression: ``"os:Arch*"``.
- ``-P``, ``--grain-pcre``: Instead of using shell globs to evaluate the target
  use a grain value to identify targets, the syntax for the target is the grain
  key followed by a pcre regular expression: "os:Arch.*".
- ``-N``, ``--nodegroup``: Instead of using shell globs to evaluate the target
  use one of the predefined nodegroups to identify a list of targets.
- ``-R``, ``--range``: Instead of using shell globs to evaluate the target
  use a range expression to identify targets. Range expressions look like
  %cluster.

.. warning::

    Some of the targeting options above may not be available for some Roster
    modules.

To use a specific Roster, configure the ``proxy_roster`` option into your
Master config file, e.g.,

.. code-block:: yaml

    proxy_roster: ansible

With the configuration above, ``salt-sproxy`` would try to use the `ansbile 
Roster module 
<https://docs.saltstack.com/en/latest/ref/roster/all/salt.roster.ansible.html#module-salt.roster.ansible>`_
to compile the Roster file (typically ``/etc/salt/roster``) which is structured 
as a regular Ansible Inventory file. This inventory should only provide the 
list of devices.

The Roster can also be specified on the fly, using the ``-R`` or ``--roster`` 
options, e.g., ``salt-sproxy cr1.thn.lon test.ping --roster=flat``. In this
example, we'd be using the `flat Roster module 
<https://docs.saltstack.com/en/latest/ref/roster/all/salt.roster.flat.html#module-salt.roster.flat>`_ 
to determine the list of devices matched by a specific target.

When you don't specify the Roster into the Master config, or from the CLI, you 
can use ``salt-sproxy`` to target on or more devices using the ``glob`` or 
``list`` target types, e.g., ``salt-sproxy cr1.thn.lon test.ping`` (glob) or 
``salt-sproxy -L cr1.thn.lon,cr2.thn.lon test.ping`` (to target a list of 
devices, cr1.thn.lon and cr2.thn.lon, respectively).

Note that in any case (with or without the Roster), you will need to provide 
a valid list of Minions.
