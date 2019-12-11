.. _using-roster:

Using the Roster Interface
==========================

While from the CLI perspective ``salt-sproxy`` looks like it works similar to
the usual ``salt`` command, in fact, they work fundamentally different. One of
the most important differences is that ``salt`` is aware of what Minions are 
connected to the Master, therefore it is easy to know what Minions would be 
matched by a certain target expression (see 
https://docs.saltstack.com/en/latest/topics/targeting/ for further details). In
contrast, by definition, ``salt-sproxy`` doesn't suppose there are any (Proxy) 
Minions running, so it cannot possibly know what Minions would be matched by an 
arbitrary expression. For this reasoning, we need to "help" it by providing 
the list of all the devices it should be aware of. This is done through the 
`Roster <https://docs.saltstack.com/en/latest/topics/ssh/roster.html>`__
interface; even though this Salt subsystem has initially been developed for 
`salt-ssh <https://docs.saltstack.com/en/latest/topics/ssh/>`__.

There are several `Roster modules 
<https://docs.saltstack.com/en/latest/ref/roster/all/index.html#all-salt-roster>`__ 
natively available in Salt, or you may write a custom one in your own
environment, under the ``salt://_roster`` directory.

To make it work, you would need to provide two configuration options (either 
via the CLI, or through the Master configuration file. See :ref:`opts`, in 
particular ``-r`` (or ``-roster``), and ``--roster-file`` (when the Roster 
module loads the list of devices from a file).

For example, let's see how we can use the :ref:`ansible-roster`.

.. _roster-example-ansible:

Roster usage example: Ansible
-----------------------------

If you already have an Ansible inventory, simply drop it into a file, e.g.,
``/etc/salt/roster``.

.. note::

    The Ansible inventory file doesn't need to provide any connection details, 
    as they must be configured into the Pillar. If you do provide them however, 
    they could be used to override the data compiled from the Pillar.
    See :ref:`ansible-roster-opts` for an example.

With that in mind, let's consider a very simply inventory, e.g.,

``/etc/salt/roster``:

.. code-block:: text

  [routers]
  router1
  router2
  router3

  [switches]
  switch1
  switch2

Reference this file, and tell ``salt-sproxy`` to interpret this file as an
Ansible inventory:

``/etc/salt/master``:

.. code-block:: yaml

  roster: ansible
  roster_file: /etc/salt/roster

To verify that the inventory is interpreted correctly, run the following 
command which should display all the possible devices salt-sproxy should be 
aware of:

.. code-block:: bash

  $ salt-sproxy \* --preview-target
  - router1
  - router2
  - router3
  - switch1
  - switch2

Then you can check that your desired target matches - say run against all the 
routers:

.. code-block:: bash

  $ salt-sproxy 'router*' --preview-target
  - router1
  - router2
  - router3

.. hint::

    If you don't provide the Roster name and the path to the Roster file, into
    the Master config file, you can specify them on the command line, e.g.,

    .. code-block:: bash

      $ salt-sproxy 'router*' --preview-target -r ansible --roster-file /etc/salt/roster

The default target matching is ``glob`` (shell-like globbing) - see
:ref:`target-selection` for more details, and other target selection options.

.. important::

    Keep in mind that some Roster modules may not implement all the possible
    target selection options.

Using the inventory above, we can also use the `PCRE 
<https://docs.saltstack.com/en/latest/topics/targeting/globbing.html#regular-expressions>`__ 
(Perl Compatible Regular Expression) matching and target devices using 
a regular expression, e.g.,

.. code-block:: bash

  $ salt-sproxy -E 'router(1|2).?' --preview-target
  - router1
  - router2
  $ salt-sproxy -E '(switch|router)1' --preview-target
  - router1
  - switch1

The inventory file doesn't necessarily need to be flat, can be as complex as 
you want, e.g.,

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

Using this inventory, you can then run, for example, against all the devices in 
Atlanta, to gather the LLDP neighbors for every device:

.. code-block:: bash

  $ salt-sproxy '*.atlanta' net.lldp
  edge1.atlanta:
     ~~~ snip ~~~
  edge2.atlanta:
     ~~~ snip ~~~

.. _ansible-roster-groups:

Targeting using groups
~~~~~~~~~~~~~~~~~~~~~~

Another very important detail here is that, depending on the structure of the 
inventory, and how the devices are grouped, you can use these groups to target 
using the ``-N`` target type (nodegroup). For example, based on the 
hierarchical inventory file above, we can use these targets:

.. code-block:: bash

  # All devices in the USA:
  $ salt-sproxy -N usa --preview-target
  - edge1.seattle
  - edge1.vancouver
  - edge1.atlanta
  - edge2.atlanta
  - edge1.raleigh
  - edge1.la
  - edge1.sfo

  # All devices in the North-West region:
  $ salt-sproxy -N northwest --preview-target
  - edge1.seattle
  - edge1.vancouver

  # All devices in the Atlanta area:
  $ salt-sproxy -N atlanta --preview-target
  - edge1.atlanta
  - edge2.atlanta

The nodegroups you can use for targeting depend on the names you've assigned 
in your inventory, and sometimes may be more useful to use them vs. the device 
name (which may not contain the area / region / country name).

.. _ansible-roster-opts:

Overriding Pillar data
~~~~~~~~~~~~~~~~~~~~~~

In the Roster file (Ansible inventory) you may prefer to have more specific 
connection credentials for some particular devices. In this case, you only need 
to specify them directly under the device, or using ``host_vars`` as normally; 
for example, let's consider the inventory from the above, with the difference 
that now ``edge1.raleigh`` has more specific details:

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
                    username: different
                    password: not-the-same
          southwest:
            children:
              san_francisco:
                hosts:
                  edge1.sfo
              los_angeles:
                hosts:
                  edge1.la

With this Roster, ``salt-sproxy`` will try to authenticate using the username 
and password specified. The same goes to the rest of the other credentials and 
fields required by the Proxy module you're using, i.e., ``port``, 
``optional_args``, etc. - check the Salt documentation to understand what 
fields you have available.

.. _ansible-roster-grains:

Configuring static Grains
~~~~~~~~~~~~~~~~~~~~~~~~~

In a similar way to overriding Pillar data for authentication (see the 
paragraph above), you can equally configure static Grains per device, by simply 
providing them under the ``grains`` key, e.g.,


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
                    grains:
                      role: transit
                      site: atl01
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

With the Roster above, derived from the previous examples, the 
``edge2.atlanta`` device is going to have two static Grains associated, i.e., 
``site`` and ``role`` with the values as configured in the Roster.

.. _roster-example-pillar:

Loading the list of devices from the Pillar
-------------------------------------------

The Pillar subsystem is powerful and flexible enough to be used as an input 
providing the list of devices and their properties.

To use the :ref:`pillar-roster` you only need to ensure that you can access the
list of devices you want to manage into a Pillar. The Pillar system is designed 
to provide data (from whatever source, i.e., HTTP API, database, or any file 
format you may prefer) to one specific Minion (or some / all). That doesn't 
mean that the Minion must be up and running, but simply just that one or more
Minions have access to this data.

In the Master configuration file, configure the ``roster`` or ``proxy_roster``, 
e.g.,

.. code-block:: yaml

    roster: pillar

By default, the Pillar Roster is going to check the Pillar data for ``*`` (any
Minion), and load it from the ``devices`` key. In other words, when executing
``salt-sproxy pillar.show_pillar`` the output should have at least the 
``devices`` key. To use different settings, have a look at the documentation: 
:ref:`pillar-roster`.

Consider the following example setup:

``/etc/salt/master``

.. code-block:: yaml

    pillar_roots:
      base:
        - /srv/salt/pillar

    roster: pillar

``/srv/salt/pillar/top.sls``

.. code-block:: yaml

    base:
      '*':
        - devices_pillar
      'minion*':
        - dummy_pillar

``/srv/salt/pillar/devices_pillar.sls``

.. code-block:: yaml

    devices:
      - name: minion1
      - name: minion2

``/srv/salt/pillar/dummy_pillar.sls``

.. code-block:: yaml

    proxy:
      proxytype: dummy

With this configuration, you can verify that the list of expected devices is 
properly defined:

.. code-block:: bash

    $ salt-run pillar.show_pillar
    devices:
        |_
          ----------
          name:
              minion1
        |_
          ----------
          name:
              minion2

Having this available, we can now start using salt-sproxy:

.. code-block:: bash

    $ salt-sproxy \* --preview-target
    - minion1
    - minion2

When working with Pillar SLS files, you can provide them in any format, either
Jinja + YAML, or pure Python, e.g. generate a longer list of devices,
dynamically:

``/srv/salt/pillar/devices_pillar.sls``

.. code-block:: jinja

    devices:
      {% for id in range(100) %}
      - name: minion{{ id }}
      {%- endfor %}

Or:

``/srv/salt/pillar/devices_pillar.sls``

.. code-block:: python

    #!py

    def run():
        return {
            'devices': [
                'minion{}'.format(id_)
                for id_ in range(100)
            ]
        }

.. note::

    The latter Python example would be particularly useful when the data 
    compilation requires more computation, while keeping the code readable, 
    e.g., execute HTTP requests, or anything you can usually do in Python 
    scripts in general.

With either of the examples above, the targeting would match:

.. code-block:: bash

    $ salt-sproxy \* --preview-target
    - minion0
    - minion1

    ~~~ snip ~~~

    - minion98
    - minion99

As the Pillar SLS files are flexible enough to allow you to compile the list of 
devices you want to manage using whatever way you need and possibly coded in 
Python. Say we would want to gather the list of devices from an HTTP API:

``/srv/salt/pillar/devices_pillar.sls``

.. code-block:: python

    #!py

    import requests

    def run():
        ret = requests.post('http://example.com/devices')
        return {'devices': ret.json()}

Or another example, slightly more advanced - retrieve the devices from a
MySQL database:

``/srv/salt/pillar/devices_pillar.sls``

.. code-block:: python

    #!py

    import mysql.connector

    def run():
       devices = []
       mysql_conn = mysql.connector.connect(host='localhost',
                                            database='database',
                                            user='user',
                                            password='password')
       get_devices_query = 'select * from devices'
       cursor = mysql_conn.cursor()
       cursor.execute(get_devices_query)
       records = cursor.fetchall()
       for row in records:
           devices.append({'name': row[1]})
       cursor.close()
       return {'devices': devices}

.. important::

  Everything with the Pillar system remains the same as always, so you can very
  well use also the External Pillar to provide the list of devices - see 
  https://docs.saltstack.com/en/latest/ref/pillar/all/index.html for the 
  list of the available External Pillars modules that allow you to load data
  from various sources.

  Check also the :ref:`example-pillar-roster` example on how to load the list of
  devices from an External Pillar, as the functionaly you may need might 
  already be implemented and available.

.. _pillar-roster-grains:

Configuring static Grains
~~~~~~~~~~~~~~~~~~~~~~~~~

Using the ``devices_pillar.sls`` file from the previous examples, you can 
provide static Grains per device, under the ``grains`` key, e.g.,

``/srv/salt/pillar/devices_pillar.sls``

.. code-block:: jinja

    devices:
      {% for id in range(100) %}
      - name: minion{{ id }}
        grains:
          site: site{{ id }}
      {%- endfor %}

In this case, the Grains data is dynamically generated through the Jinja loop, 
however it could be provided in any way you'd prefer. Executing the following
command, you can check that the Grains data is properly distributed:

.. code-block:: bash

    $ salt-sproxy minion17 grains.get site
    minion17:
        site17

.. _roster-example-netbox:

Roster usage example: NetBox
----------------------------

The :ref:`netbox-roster` is a good example of a Roster modules that doesn't 
work with files, rather gathers the data from
`NetBox <https://github.com/digitalocean/netbox>`__ via the `API 
<https://netbox.readthedocs.io/en/stable/api/overview/>`__.

.. note::

    The NetBox Roster module is currently not available in the official Salt 
    releases, and it is distributed as part of the ``salt-sproxy`` package and 
    dynamically loaded on runtime, so you don't need to worry about that, 
    simply reference it, configure the details as documented and start using 
    it straight away.

To use the NetBox Roster, simply put the following details in the Master 
configuration you want to use (default ``/etc/salt/master``):

.. code-block:: yaml

  roster: netbox

  netbox:
   url: <NETBOX_URL>

You can also specify the ``token``, and the ``keyfile`` but for this Roster 
specifically, the ``url`` is sufficient.

To verify that you are indeed able to retrieve the list of devices from your 
NetBox instance, you can, for example, execute:

.. code-block:: bash

  $ salt-run salt.cmd netbox.filter dcim devices
  # ~~~ should normally return all the devices ~~~

  # Or with some specific filters, e.g.:
  $ salt-run salt.cmd netbox.filter dcim devices site=<SITE> status=<STATUS>

Once confirmed this works well, you can verify that the Roster is able to pull 
the data:

.. code-block:: bash

  $ salt-sproxy '*' --preview-target

In the same way, you can then start executing Salt commands targeting using 
expressions that match the name of the devices you have in NetBox:

.. code-block:: bash

  $ salt-sproxy '*atlanta' net.lldp
  edge1.atlanta:
      ~~~ snip ~~~
  edge2.atlanta:
      ~~~ snip ~~~

.. _netbox-roster-grain:

Enhanced Grain targeting
^^^^^^^^^^^^^^^^^^^^^^^^

When NetBox Roster pulls the data from NetBox via the API, from the ``dcim`` 
app, ``devices`` endpoint, it retrieves additional information about the 
device, e.g.,

.. code-block:: json

    {
        "count": 1,
        "next": null,
        "previous": null,
        "results": [
            {
                "id": 1,
                "name": "edge1.vlc1",
                "display_name": "edge1.vlc1",
                "device_type": {
                    "id": 1,
                    "url": "https://netbox.live/api/dcim/device-types/1/",
                    "manufacturer": {
                        "id": 5,
                        "url": "https://netbox.live/api/dcim/manufacturers/5/",
                        "name": "Juniper",
                        "slug": "juniper"
                    },
                    "model": "MX960",
                    "slug": "mx960",
                    "display_name": "Juniper MX960"
                },
                "device_role": {
                    "id": 7,
                    "url": "https://netbox.live/api/dcim/device-roles/7/",
                    "name": "Router",
                    "slug": "router"
                },
                "tenant": null,
                "platform": {
                    "id": 3,
                    "url": "https://netbox.live/api/dcim/platforms/3/",
                    "name": "Juniper Junos",
                    "slug": "juniper-junos"
                },
                "serial": "",
                "asset_tag": null,
                "site": {
                    "id": 1,
                    "url": "https://netbox.live/api/dcim/sites/1/",
                    "name": "VLC1",
                    "slug": "vlc1"
                },
                "rack": {
                    "id": 1,
                    "url": "https://netbox.live/api/dcim/racks/1/",
                    "name": "R1",
                    "display_name": "R1"
                },
                "position": 1,
                "face": {
                    "value": 0,
                    "label": "Front"
                },
                "parent_device": null,
                "status": {
                    "value": 1,
                    "label": "Active"
                },
                "primary_ip": null,
                "primary_ip4": null,
                "primary_ip6": null,
                "cluster": null,
                "virtual_chassis": null,
                "vc_position": null,
                "vc_priority": null,
                "comments": "",
                "local_context_data": null,
                "tags": [],
                "custom_fields": {},
                "created": "2019-08-12",
                "last_updated": "2019-08-12T11:08:21.706641Z"
            }
        ]
    }

All this data is by default available in the Grains when targeting, so you can 
use the :ref:`targeting-grain` to match the devices you want to run against.

Examples:

- Select devices under the ``router`` role:

.. code-block:: bash

    salt-sproxy -G netbox:device_role:role test.ping

- Select devices from the ``vlc1`` site:

.. code-block:: bsah

    salt-sproxy -G netbox:site:slug:vlc1 test.ping

.. _other-roster:

Other Roster modules
--------------------

If you may need to load your data from various other data sources, that might 
not be covered in the existing Roster modules. Roster modules are easy to 
write, and you only need to drop them into your ``salt://_roster`` directory,
then it would be great if you could open source them for the benefit of the 
community (either submit them to this repository, at 
https://github.com/mirceaulinic/salt-sproxy, or to the official
`Salt repository <https://github.com/saltstack/salt>`__ on GitHub)
