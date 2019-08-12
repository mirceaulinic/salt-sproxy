.. _example-netbox:

Using the NetBox Roster
=======================

To be able to use the NetBox Roster, you will need to have the ``pynetbox`` 
library installed in the same environment as ``salt-sproxy``, e.g.,

.. code-block:: bash

  $ pip install pynetbox

Using the Master configuration file under `examples/netbox/master 
<https://github.com/mirceaulinic/salt-sproxy/tree/master/examples/netbox/master>`__:


``/etc/salt/master``:

.. code-block:: yaml

  pillar_roots:
    base:
      - /srv/salt/pillar

  proxy_roster: netbox

  netbox:
    url: https://url-to-your-netbox-instance

With this configuration, the list of devices is going to be loaded from NetBox,
with the connection details provides under the ``netbox`` key.

.. note::

  To set up a NetBox instance, see the installation notes from 
  https://netbox.readthedocs.io/en/stable/installation/.

The ``pillar_roots`` option points to ``/srv/salt/pillar``, so to be able to 
use this example, either create a symlink to the ``pillar`` directory in this 
example, or copy the files.
For example, if you just cloned this repository:

.. code-block:: bash

  $ mkdir -p /srv/salt/pillar
  $ git clone git@github.com:mirceaulinic/salt-sproxy.git
  $ cp salt-sproxy/examples/netbox/master /etc/salt/master
  $ cp salt-sproxy/examples/netbox/pillar/*.sls /srv/salt/pillar/

The contents of these files highly depend on the device names you have in your 
NetBox instance. The following examples are crafted for device name starting 
with ``edge1`` and ``edge2``, e.g., ``edge1.atlanta``, ``edge1.seattle`` etc.
If you have different device names in your NetBox instance, you'll have to 
update these Pillars.

``/srv/salt/pillar/top.sls``:

.. code-block:: yaml

  base:
    'edge1*':
      - junos
    'edge2*':
      - eos

With this top file, Salt is going to load the Pillar data from 
``/srv/salt/pillar/junos.sls`` for ``edge1.seattle``, ``edge1.atlanta``, 
``edge1.raleigh``, ``edge1.sfo``, and ``edge1.la``, while loading the data from 
``/srv/salt/pillar/eos.sls`` for ``edge2.atlanta`` (and anything that would 
match the ``edge2*`` expression should you have others).

``/srv/salt/pillar/junos.sls``:

.. code-block:: yaml

  proxy:
    proxytype: napalm
    driver: junos
    host: {{ opts.id | replace('.', '-') }}.salt-sproxy.digitalocean.cloud.tesuto.com
    username: test
    password: t35t1234

``/srv/salt/pillar/eos.sls``:

.. code-block:: yaml

  proxy:
    proxytype: napalm
    driver: eos
    host: {{ opts.id | replace('.', '-') }}.salt-sproxy.digitalocean.cloud.tesuto.com
    username: test
    password: t35t1234

Note that in both case the ``hostname`` has been set as ``{{ opts.id 
| replace('.', '-') }}.salt-sproxy.digitalocean.cloud.tesuto.com``. ``opts.id`` 
points to the Minion ID, which means that the Pillar data is rendered depending 
on the name of the device; therefore, the hostname for ``edge1.atlanta`` will 
be ``edge1-atlanta.salt-sproxy.digitalocean.cloud.tesuto.com``, the hostname 
for ``edge2.atlanta`` is
``edge2-atlanta.salt-sproxy.digitalocean.cloud.tesuto.com``, and so on.

Having this setup ready, you can go ahead an execute:

.. code-block:: bash

  $ salt-sproxy '*' --preview-target
  - edge1.seattle
  - edge1.vancouver
  - edge1.atlanta
  - edge2.atlanta
  - edge1.raleigh
  - edge1.la
  - edge1.sfo
  ~~~ many others ~~~

  # get the LLDP neighbors from all the edge devices
  $ salt-sproxy 'edge*' net.lldp
  edge1.vancouver:
      ~~~ snip ~~~
  edge1.atlanta:
      ~~~ snip ~~~
  edge1.sfo:
      ~~~ snip ~~~
  edge1.seattle:
      ~~~ snip ~~~
  edge1.la:
      ~~~ snip ~~~
  edge1.raleigh:
      ~~~ snip ~~~
  edge2.atlanta:
      ~~~ snip ~~~

Alternative setup using Docker
------------------------------

1. Clone the salt-sproxy repository and change dir:

.. code-block:: bash

    $ git clone https://github.com/mirceaulinic/salt-sproxy.git
    $ cd salt-sproxy/

2. Update ``examples/netbox/master`` with your NetBox details (URL and token).

   Alternatively, for quick testing, you can also leave the existing values, to
   use the demo instance available at
   [https://netbox.live](https://netbox.live/).

3. Using the ``allinone-latest`` Docker image (see :ref:`docker`), you can run
   from this path (at the repository root):

.. code-block:: bash

    $ docker run --rm -v $PWD/examples/netbox/master:/etc/salt/master \
        -v $PWD/examples/netbox/pillar/:/srv/salt/pillar/ \
        --network host \
        -ti mirceaulinic/salt-sproxy:allinone-latest bash

    root@2c68721d93dc:/# salt-sproxy \* --preview-target
    - edge1.vlc1
