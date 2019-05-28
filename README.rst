Salt Super-Proxy  |Twitter|
================

.. |Twitter| image:: https://img.shields.io/twitter/url/http/shields.io.svg?style=social
   :target: https://twitter.com/intent/tweet?text=Get+started+with+salt-sproxy+and+automate+your+network+with+all+the+Salt+benefits%2C+without+having+to+manage+thousands+of+%28Proxy%29+MInion+processes&url=https://github.com/mirceaulinic/salt-sproxy&hashtags=networkAutomation,saltstack,salt-sproxy

|PyPI downloads| |Docker pulls| |PyPI status| |PyPI versions| |Code style| |License| |GitHub make-a-pull-requests|

.. |PyPI downloads| image:: https://pepy.tech/badge/salt-sproxy
   :target: https://pypi.python.org/pypi/salt-sproxy/

.. |Docker pulls| image:: https://img.shields.io/docker/pulls/mirceaulinic/salt-sproxy.svg
   :target: https://hub.docker.com/r/mirceaulinic/salt-sproxy

.. |PyPI status| image:: https://img.shields.io/pypi/status/salt-sproxy.svg
   :target: https://pypi.python.org/pypi/salt-sproxy/

.. |PyPI versions| image:: https://img.shields.io/pypi/pyversions/salt-sproxy.svg
   :target: https://pypi.python.org/pypi/salt-sproxy/

.. |Documentation Status| image:: https://readthedocs.org/projects/salt-sproxy/badge/?version=latest
   :target: http://salt-sproxy.readthedocs.io/?badge=latest

.. |Code style| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/python/black

.. |License| image:: https://img.shields.io/pypi/l/salt-sproxy.svg
   :target: https://pypi.python.org/pypi/salt-sproxy/

.. |GitHub make-a-pull-requests| image:: https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square
   :target: http://makeapullrequest.com

`Salt <https://github.com/saltstack/salt>`__ plugin to automate the management
and configuration of network devices at scale, without running (Proxy) Minions.

Using ``salt-sproxy``, you can continue to benefit from the scalability,
flexibility and extensibility of Salt, while you don't have to manage thousands
of (Proxy) Minion services. However, you are able to use both ``salt-sproxy`` 
and your (Proxy) Minions at the same time.

.. note::

    This is NOT a SaltStack product.

    This package may eventually be integrated in a future version of the 
    official Salt releases, in this form or slightly different.

Prerequisites
-------------

The package is distributed via PyPI, under the name ``salt-sproxy``. If you 
would like to install it on your computer, you might want to run it under a
`virtual environment <https://docs.python-guide.org/dev/virtualenvs/>`__.

Besides the CLI, the usage remains the same as when you're running a Salt 
environment with Proxy or regular Minions. See the following documents on how
to get started and fully unleash the power of Salt:

- `Salt in 10 minutes 
  <https://docs.saltstack.com/en/latest/topics/tutorials/walkthrough.html>`__.
- `Salt fundamentals 
  <https://docs.saltstack.com/en/getstarted/fundamentals/>`__.
- `Salt configuration management 
  <https://docs.saltstack.com/en/getstarted/config/>`__.
- `Network Automation features available in Salt 
  <https://docs.saltstack.com/en/develop/topics/network_automation/index.html>`__.
- `Network Automation at Scale: up and running in 60 minutes 
  <https://ripe74.ripe.net/presentations/18-RIPE-74-Network-automation-at-scale-up-and-running-in-60-minutes.pdf>`__.
- `Network Automation at Scale (free e-book) 
  <https://www.oreilly.com/library/view/network-automation-at/9781491992524/>`__.

Install
-------

Install this package where you would like to manage your devices from. In case
you need a specific Salt version, make sure you install it beforehand, 
otherwise this package will bring the latest Salt version available instead.

Execute:

.. code-block:: bash

    pip install salt-sproxy

To install a specific Salt version, execute, e.g.,

.. code-block:: bash

    pip install salt==2018.3.4
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

See also https://salt-sproxy.readthedocs.io/en/latest/examples/index.html for 
more usage examples.

What's included
---------------

When installing ``salt-sproxy``, besides the core files (i.e., ``cli.py``, 
``parsers.py``, ``scripts.py``, and ``version.py``), you will find the 
following directories and files, which provide additional features and 
backwards compatibility with older Salt versions:

.. code-block:: text

  |-- cli.py
  |-- __init__.py
  |-- parsers.py
  |-- _roster/
  |   |-- ansible.py
  |   `-- netbox.py
  |-- _runners/
  |   |-- __init__.py
  |   `-- proxy.py
  |-- scripts.py
  `-- version.py

The extension modules under the ``_roster`` and ``_runner`` directories are 
documented at https://salt-sproxy.readthedocs.io/en/latest/roster/index.html 
and https://salt-sproxy.readthedocs.io/en/latest/runners/index.html, 
respectively.

Docker
------

A Docker image is available at 
https://hub.docker.com/r/mirceaulinic/salt-sproxy, and you can pull it, e.g.,
``docker pull mirceaulinic/salt-sproxy``. See 
https://salt-sproxy.readthedocs.io/en/latest/#docker for further usage 
instructions and examples.

Community
---------

Get updates on the ``salt-sproxy`` development, and chat with the project 
maintainer(s) and community members:

- Follow `@mirceaulinic <https://twitter.com/mirceaulinic>`__
- `Google Groups <https://groups.google.com/forum/#!forum/salt-sproxy>`__
- Use the ``salt-sproxy`` tag on `Stack Overflow 
  <https://stackoverflow.com/>`__.
- The *#saltstack* channel under the `networktocode Slack 
  <https://networktocode.slack.com/messages/C0NL8RRMX/>`__.

License
-------

This project is licensed under the Apache 2.0 License - see the
`LICENSE <https://github.com/mirceaulinic/salt-sproxy/blob/master/LICENSE>`__
file for details.

Acknowledgments
---------------

Thanks to `Daniel Wallace <https://github.com/gtmanfred>`__ for the 
inspiration.
