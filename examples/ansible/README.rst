Using the Ansible Roster
========================

To be able to use the Ansible Roster, you will need to have ``ansible`` 
installed in the same environment as ``salt-sproxy``, e.g.,

.. code-block:: bash

  $ pip instal ansible

Using the Master configuration file under `examples/ansible/master 
<https://github.com/mirceaulinic/salt-sproxy/tree/master/examples/ansible/master>`__:


``/etc/salt/master``:

.. code-block:: yaml

  pillar_roots:
    base:
      - /srv/salt/pillar

  proxy_roster: ansible
  roster_file: /etc/salt/roster

Notice that compared to the previous examples, `101 
<https://github.com/mirceaulinic/salt-sproxy/tree/master/examples/101>`__ and 
`NAPALM 
<https://github.com/mirceaulinic/salt-sproxy/tree/master/examples/napalm>`__, 
there are two additional options: ``roster_file`` which specifies the path to 
the Roster file to use, and ``proxy_roster`` that tells how to interpret the 
Roster file - in this case, the Roster file ``/etc/salt/roster`` is going to be 
loaded as an Ansible inventory. Let's consider, for example, the following 
Roster / Ansible inventory which you can find at `examples/ansible/roster 
<https://github.com/mirceaulinic/salt-sproxy/tree/master/examples/ansible/roster>`__:

.. code-block:: yaml

  all:
    children:
      usa:
        children:
          northeast: ~
          northwest:
            children:
              seattle:
                hosts:
                  edge1.seattle
              vancouver:
                hosts:
                  edge1.vancouver
          southeast:
            children:
              atlanta:
                hosts:
                  edge1.atlanta:
                  edge2.atlanta:
              raleigh:
                hosts:
                  edge1.raleigh:
          southwest:
            children:
              san_francisco:
                hosts:
                  edge1.sfo
              los_angeles:
                hosts:
                  edge1.la

The ``pillar_roots`` option points to ``/srv/salt/pillar``, so to be able to 
use this example, either create a symlink to the ``pillar`` directory in this 
example, or copy the files.
For example, if you just cloned this repository:

.. code-block:: bash

  $ mkdir -p /srv/salt/pillar
  $ git clone git@github.com:mirceaulinic/salt-sproxy.git
  $ cp salt-sproxy/examples/ansible/master /etc/salt/master
  $ cp salt-sproxy/examples/ansible/roster /etc/salt/roster
  $ cp salt-sproxy/examples/ansible/pillar/*.sls /srv/salt/pillar/

The contents of these two files:

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
