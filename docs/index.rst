================
Salt Super-Proxy
================

Salt plugin to automate the management and configuration of network devices at
scale, without running (Proxy) Minions.

Using ``salt-sproxy``, you can continue to benefit from the scalability,
flexibility and extensibility of Salt, while you don't have to manage thousands
of (Proxy) Minion services. However, you are able to use both ``salt-sproxy``
and your (Proxy) Minions at the same time.

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

See :ref:`install` for more detailed installation notes.

Quick Start
-----------

See this recording for a live quick start:

.. raw:: html

  <script id="asciicast-247697" src="https://asciinema.org/a/247697.js" async></script>

In the above, ``minion1`` is 
a `dummy  <https://docs.saltstack.com/en/latest/ref/proxy/all/salt.proxy.dummy.html>`__
Proxy Minion, that can be used for getting started and make the first steps 
without connecting to an actual device, but get used to the ``salt-sproxy``
methodology.

The Master configuration file is ``/home/mircea/master``, which is why the
command is executed using the ``-c`` option specifying the path to the directory
with the configuration file. In this Master configuration file, the
``pillar_roots`` option points to ``/srv/salt/pillar`` which is where 
``salt-sproxy`` is going to load the Pillar data from. Accordingly, the Pillar 
Top file is under that path, ``/srv/salt/pillar/top.sls``:

.. code-block:: yaml

  base:
    minion1:
      - dummy

This Pillar Top file says that the Minion ``minion1`` will have the Pillar data 
from the ``dummy.sls`` from the same directory, thus 
``/srv/salt/pillar/dummy.sls``:

.. code-block:: yaml

  proxy:
    proxytype: dummy

In this case, it was sufficient to only set the ``proxytype`` field to 
``dummy``.

``salt-sproxy`` can be used in conjunction with any of the available `Salt 
Proxy modules <https://docs.saltstack.com/en/latest/ref/proxy/all/index.html>`__,
or others that you might have in your own environment. See 
https://docs.saltstack.com/en/latest/topics/proxyminion/index.html to 
understand how to write a new Proxy module if you require.

For example, let's take a look at how we can manage a network device through 
the `NAPALM Proxy <https://docs.saltstack.com/en/latest/ref/proxy/all/salt.proxy.napalm.html>`__:

.. raw:: html

  <script id="asciicast-247726" src="https://asciinema.org/a/247726.js" async></script>

In the above, in the same Python virtual environment as previously make sure 
you have ``NAPALM`` installed, by executing ``pip install napalm`` (see
https://napalm.readthedocs.io/en/latest/installation/index.html for further 
installation requirements, depending on the platform you're running on). The 
connection credentials for the ``juniper-router`` are stored in the 
``/srv/salt/pillar/junos.sls`` Pillar, and we can go ahead and start executing
arbitrary Salt commands, e.g., `net.arp 
<https://docs.saltstack.com/en/latest/ref/modules/all/salt.modules.napalm_network.html#salt.modules.napalm_network.arp>`__ 
to retrieve the ARP table, or `net.load_config 
<https://docs.saltstack.com/en/latest/ref/modules/all/salt.modules.napalm_network.html#salt.modules.napalm_network.load_config>`__ 
to apply a configuration change on the router.

The Pillar Top file in this example was (under the same path as previously, as 
the Master config was the same):

.. code-block:: yaml

  base:
    juniper-router:
      - junos

Thanks to `Tesuto <https://www.tesuto.com/>`__ for providing the virtual 
machine for the demos!

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

Usage Example:

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

    Some of the targeting options above may not be avaialble for some Roster
    modules.

To use a specific Roster, configure the ``proxy_roster`` (or simply ``roster``)
option into your Master config file, e.g.,

.. code-block:: yaml

    proxy_roster: ansible

.. note::

    It is recommended to prefer the ``proxy_roster`` option in the favour of 
    ``roster`` as the latter is used by Salt SSH. In case you want to use both
    salt-sproxy and Salt SSH, you may want to use different Roster files, which 
    is why there are two different options.

    salt-sproxy will evauluate both ``proxy_roster`` and ``roster``, in this 
    order.

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
devices, ``cr1.thn.lon`` and ``cr2.thn.lon``, respectively).

Note that in any case (with or without the Roster), you will need to provide 
a valid list of Minions.

.. _docker:

Docker
------

There are Docker images available should you need or prefer: 
https://hub.docker.com/r/mirceaulinic/salt-sproxy.

You can see here the available tags: 
https://hub.docker.com/r/mirceaulinic/salt-sproxy/tags. ``latest`` provides the
code merged into the ``master`` branch, and ``allinone-latest`` is the code
merged into the ``master`` branch with several libraries such as
`NAPALM <https://github.com/napalm-automation/napalm>`__,
`Netmiko <https://github.com/ktbyers/netmiko>`__, 
`ciscoconfparse <http://www.pennington.net/py/ciscoconfparse/>`__, or Ansible
which you may need for your modules or Roster (if you'd want to use the 
`Ansible Roster <https://salt-sproxy.readthedocs.io/en/latest/roster/ansible.html>`__,
for  example).

These can be used in various scenarios. For example, if you would like to use
``salt-proxy`` but without installing it, and prefer to use Docker instead, you
can define the following convoluted alias:

.. code-block:: bash

  alias salt-sproxy='f(){ docker run --rm --network host -v $SALT_PROXY_PILLAR_DIR:/etc/salt/pillar/ -ti mirceaulinic/salt-sproxy salt-sproxy $@; }; f'

And in the ``SALT_PROXY_PILLAR_DIR`` environment variable, you set the path to
the directory where you have the Pillars, e.g.,

.. code-block:: bash

  export SALT_PROXY_PILLAR_DIR=/path/to/pillars/dir

With this setup, you would be able to go ahead and execute "as normally" (with 
the difference that the code is executed inside the container, however from the 
CLI it won't look different):

.. code-block:: bash

  salt-sproxy minion1 test.ping

More usage examples
-------------------

See the following examples to help getting started with salt-sproxy:

.. toctree::
   :maxdepth: 1

   examples/index

Extension Modules
-----------------

``salt-sproxy`` is delivered together with a few extension modules that are
dynamically loaded and immediately available. Please see below the 
documentation for these modules:

.. toctree::
   :maxdepth: 1

   roster/index
   runners/index

See Also
--------


.. toctree::
   :maxdepth: 1

   quick_start
   opts
   install
   roster
   runner
   events
   salt_api
   mixed_envs
   scale
