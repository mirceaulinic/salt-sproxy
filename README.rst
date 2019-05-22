================
Salt Super-Proxy
================

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

Quick Start
-----------

See this recording for a live quick start:

.. raw:: html

  <a href="https://asciinema.org/a/247697?autoplay=1" target="_blank"><img src="static/247697.svg" /></a>

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

  <a href="https://asciinema.org/a/247726?autoplay=1" target="_blank"><img src="static/247726.svg" /></a>

In the same Python virtual environment as previously, make sure  you have
``NAPALM`` installed, by executing ``pip install napalm`` (see
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
<https://docs.saltstack.com/en/latest/ref/states/top.html>`_ is correctly
defined and the ``proxy`` key is available into the Pillar. For more in-depth 
explanation and examples, check `this 
<https://docs.saltstack.com/en/latest/topics/proxyminion/index.html>`__ tutorial 
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


You can continue reading further details at 
https://salt-sproxy.readthedocs.io/en/latest/, for now, check out the following 
section to see how to get started with ``salt-sproxy`` straight away.
