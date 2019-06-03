.. _example-napalm:

salt-sproxy with network devices
================================

This is the second example from the
`Quick Start <https://salt-sproxy.readthedocs.io/en/latest/#quick-start>`__
section of the documentation.

To be able to use this example, make sure you have NAPALM installed - see the 
complete installation notes from 
https://napalm.readthedocs.io/en/latest/installation/index.html.

.. raw:: html
  
  <a href="https://asciinema.org/a/247726" target="_blank"><img src="https://asciinema.org/a/247726.svg" /></a>

Using the Master configuration file under `examples/master 
<https://github.com/mirceaulinic/salt-sproxy/tree/master/examples/master>`__:


``/etc/salt/master``:

.. code-block:: yaml

  pillar_roots:
    base:
      - /srv/salt/pillar

The ``pillar_roots`` option points to ``/srv/salt/pillar``, so to be able to 
use this example, either create a symlink to the ``pillar`` directory in this 
example, or copy the files.
For example, if you just cloned this repository:

.. code-block:: bash

  $ mkdir -p /srv/salt/pillar
  $ git clone git@github.com:mirceaulinic/salt-sproxy.git
  $ cp salt-sproxy/examples/master /etc/salt/master
  $ cp salt-sproxy/examples/napalm/pillar/*.sls /srv/salt/pillar/

The contents of these two files:

``/srv/salt/pillar/top.sls``:

.. code-block:: yaml

  base:
    juniper-router:
      - junos

``/srv/salt/pillar/junos.sls``:

.. code-block:: yaml

  proxy:
    proxytype: napalm
    driver: junos
    host: juniper.salt-sproxy.digitalocean.cloud.tesuto.com
    username: test
    password: t35t1234

Having this setup ready, after you update the connection details, you can go ahead an execute:

.. code-block:: bash

  $ salt-sproxy juniper-router test.ping
  juniper-router:
      True

  # retrieve the ARP table from juniper-router
  $ salt-sproxy juniper-router net.arp
  juniper-router:
      ----------
      comment:
      out:
          |_
            ----------
            age:
                849.0
            interface:
                fxp0.0
            ip:
                10.96.0.1
            mac:
                92:99:00:0A:00:00
          |_
            ----------
            age:
                973.0
            interface:
                fxp0.0
            ip:
                10.96.0.13
            mac:
                92:99:00:0A:00:00
          |_
            ----------
            age:
                738.0
            interface:
                em1.0
            ip:
                128.0.0.16
            mac:
                02:42:AC:13:00:02
      result:
          True

  # apply a configuration change: dry run
  $ salt-sproxy juniper-router net.load_config text='set system ntp server 10.10.10.1' test=True
  juniper-router:
      ----------
      already_configured:
          False
      comment:
          Configuration discarded.
      diff:
          [edit system]
          +   ntp {
          +       server 10.10.10.1;
          +   }
      loaded_config:
      result:
          True

  # apply the configuration change and commit
  $ salt-sproxy juniper-router net.load_config text='set system ntp server 10.10.10.1'
  juniper-router:
      ----------
      already_configured:
          False
      comment:
      diff:
          [edit system]
          +   ntp {
          +       server 10.10.10.1;
          +   }
      loaded_config:
      result:
          True

If you run into issues when connecting to your device, you might want to go 
through this checklist: https://github.com/napalm-automation/napalm#faq.

.. note::

  For a better methodology on managing the configuration, you might want to 
  take a look at the `State system 
  <https://docs.saltstack.com/en/getstarted/fundamentals/states.html>`__, one 
  of the most widely used State modules for configuration management through 
  NAPALM being `Netconfig 
  <https://docs.saltstack.com/en/latest/ref/states/all/salt.states.netconfig.html>`__.
