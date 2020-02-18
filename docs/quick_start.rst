.. _quick-start:

Quick Start
===========

This is a configuration example to quickly get started with ``salt-sproxy``.

1. Install ``salt-sproxy``
--------------------------

Run ``pip install salt-sproxy`` either at root, or within a virtual 
environment.

If you don't know how to install ``pip``, see this document:
https://pip.pypa.io/en/stable/installing/. 

For setting up a virtual environment, check out
https://virtualenv.pypa.io/en/stable/installation/.

If you have more specific requirements for the ``salt-sproxy`` installation, 
see :ref:`install`.

2. Build the list of devices
----------------------------

Say you have a list of devices you want to manage. For ease, you can put them
into a file:

``/etc/salt/roster``

.. code-block:: yaml

  router1:
    driver: junos
  router2:
    driver: iosxr
  switch1:
    driver: eos
  fw1
    driver: panos
    host: fw1.firewall.as1234.net

.. note::

    The ``/etc/salt/roster`` file can use any of the available SLS formats 
    (combinations of the Salt `Renderer modules 
    <https://docs.saltstack.com/en/latest/ref/renderers/>`__) - Jinja + YAML, 
    YAML, JSON, pure Python, JSON5, HJSON, etc.

3. Configure
------------

Apply the following configuration:

``/etc/salt/master``

.. code-block:: yaml

    roster: file

This is all you need at minimum, however, you may have more specific 
requirements which you can customise using the configuration options documented
in https://docs.saltstack.com/en/latest/ref/configuration/master.html.

4. Prepare the connection credentials
-------------------------------------

In a file, say ``/srv/pillar/proxy.sls``, you'll need the following structure:

.. code-block:: sls

    proxy:
      proxytype: <proxy type>
      username: <username>
      password: <password>
      host: <host>

Where ``proxy type`` is the name of one of the available Proxy modules, either
Salt native (https://docs.saltstack.com/en/latest/ref/proxy/all/index.html), or
developed in your own environment.

.. note::

    Either of these fields (i.e., ``proxytype``, ``username``, ``password``,
    ``host``) can be specified in the list of devices in the Pillar above (step 
    2). Generally, in this file, you put the list of parameters that are 
    globally available to any devices. For example, if you're using the same 
    username to manage all devices, you don't need to put it in the Pillar 
    defined at *step 2*, but rather set it here.

Example:

.. code-block:: sls

    proxy:
      proxytype: napalm
      username: salt
      password: SaltSPr0xyRocks!
      host: {{ opts.id }}.as1234.net

The trick in the SLS above is the ``host`` field, which is rendered differently
for each device; for instance, the hostname for the device ``router1`` would be
``router1.as1234.net``, and so on. As an exception, at *step 2*, for ``fw2`` we 
defined a most specific ``host`` field, so ``salt-sproxy`` is going to use that 
one instead.

In the same way you can build custom dynamically rendered fields, as your 
business logic requires, making use of the flexibility of the SLS file format
(which is by default Jinja + YAML, see `this 
<https://docs.saltstack.com/en/latest/ref/renderers/>`__ for more information).

.. tip::

  If you want to use your own username / SSH key for authentication, you can 
  configure the following:

  .. code-block:: sls

      username: {{ salt.environ.get('USER') }}

  The configuration above, would dynamically use the username currently logged 
  in, which could be particularly useful for shared environments where multiple
  users (with potentially different access levels) can log in and run Salt
  commands.

  To authenticate using your SSH key, you need to set the ``password`` field
  blank / empty string (i.e., ``password: ''``).

  As for using a custom private SSH key, you should check the documentation of
  the Proxy module of choice. For example, if you're using `NAPALM 
  <https://docs.saltstack.com/en/latest/ref/proxy/all/salt.proxy.napalm.html>`__,
  the location of the SSH key would be configured under the ``optional_args`` 
  key, e.g.,

  .. code-block:: sls

      proxy:
        proxytype: napalm
        username: {{ salt.environ.get('USER') }}
        password: ''
        host: {{ opts.id }}.as1234.net
        optional_args:
          key_file: /path/to/priv/key

Granted you have the structure above in the ``/srv/pillar/proxy.sls`` file, as 
a last step, you only need to include it into the Pillar top file:

``/srv/pillar/top.sls``

.. code-block:: sls

    base:
      '*':
        - proxy

5. Happy automating!
--------------------

With these three files (``/srv/pillar/devices.sls``, ``/etc/salt/master``, and
``/srv/pillar/proxy.sls``) configured as described, you can now start 
automating your network, e.g.,

.. code-block:: bash

    $ salt-sproxy router1 net.arp
    # ... snip ...

    $ salt-sproxy -L router1,router2 net.load_config \
        text='set system ntp server 10.10.10.1'
    # ... snip ...

    $ salt-sproxy router2 napalm.junos_rpc 'get-validation-statistics'
    # ... snip ...

    $ salt-sproxy \* net.cli 'request system zeroize'
