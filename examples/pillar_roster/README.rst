.. _example-pillar-roster:

Using the Pillar Roster
=======================

You can thing of the
`Pillar Roster <https://salt-sproxy.readthedocs.io/en/latest/roster/pillar.html>`__
as a Roster that loads the list of devices / inventory dynamically using the 
Pillar subsystem. Or, in simpler words, you can use any of these features from 
here: https://docs.saltstack.com/en/latest/ref/pillar/all/index.html to load 
the list of your devices, including: JSON / YAML HTTP API, load from MySQL 
/ Postgres database, LDAP, Redis, MongoDB, etcd, Consul, and many others; 
needless to say that this is another pluggable interface and, in case you have 
a more specific requirement, you can easily extend Salt in your environment by 
providing another Pillar module under the ``salt://_pillar`` directory. For 
example, see this old yet still accurate article: 
https://medium.com/@Drew_Stokes/saltstack-extending-the-pillar-494d41ee156d.


The core idea is that you are able to use the data pulled via the Pillar 
modules once you are able to execute the following command and see the list of 
devices you're aiming to manage:

.. code-block:: bash

    $ salt-run pillar.show_pillar
    devices:
      - name: device1
      ...

It really doesn't matter where is Salt pulling this data from.

By default, the Pillar Roster is going to check the Pillar data for ``*`` (any
Minion), and load it from the ``devices`` key. In other words, when executing
``salt-sproxy pillar.show_pillar`` the output should have at least the 
``devices`` key. To use different settings, have a look at the documentation: 
:ref:`pillar-roster`.

Say we want to pull the list of devices from an HTTP API module providing the 
data in JSON format. In this case, we can use the `http_json 
<https://docs.saltstack.com/en/latest/ref/pillar/all/salt.pillar.http_json.html#module-salt.pillar.http_json>`__ 
module.

If the data is available at http://example.com/devices, and you can verify, 
e.g., using ``curl``:

.. code-block:: bash

    $ curl http://example.com/devices
    {"devices": [{"name": "router1"}, {"name": "router2"}, {"name": "switch1"}]}

That being available, we can configure the ``http_json`` External Pillar:

``/etc/salt/master``:

.. code-block:: yaml

  roster: pillar

  ext_pillar:
    - http_json:
        url: http://example.com/devices

Now, let's verify that the data is pulled properly into the Pillar:

.. code-block:: bash

  $ salt-run pillar.show_pillar
  devices:
    - name: router1
    - name: router2
    - name: switch1

That being validated, salt-sproxy is now aware of all the devices to be 
managed:

.. code-block:: bash

  $ salt-sproxy \* --preview-target
  - router1
  - router2
  - switch1

As well as other target types such as ``list`` or ``PCRE``:

.. code-block:: bash

  # target a fixed list of devices:

  $ salt-sproxy -L router1,router2 --preview-target
  - router1
  - router2

  # target all devices with the name starting with "router",
  # followed by one or more numbers:
  
  $ salt-sproxy -E 'router\d+' --preview-target
  - router1
  - router2

The same methodology applies to any of the other External Pillar modules.
