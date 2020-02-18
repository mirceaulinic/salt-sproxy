.. _example-file-roster:

Using the File Roster
=====================

The `File Roster <https://salt-sproxy.readthedocs.io/en/latest/roster/pillar.html>`__
allows you to easily manage the list of devices through an SLS file - that 
being any combination of the `available Roster modules 
<https://docs.saltstack.com/en/latest/ref/renderers/>`__: Jinja+YAML, YAML, 
JSON, pure Python, JSON5, HJSON, etc.

By default, the Roster file is ``/etc/salt/roster``, but you can have 
a different path by configuring ``roster_file`` (or ``--roster-file`` on the 
command line) to point to an alternative absolute path, e.g.,

``/etc/salt/master``

.. code-block:: yaml

  roster: file
  roster_file: /path/to/roster/file

For starters, let's consider the following simple Roster SLS file:

``/etc/salt/roster``

.. code-block:: yaml

  device1: {}
  device2: {}

To check that everything is properly configured, you can execute:

.. code-block:: bash

  $ salt-sproxy \* --preview-target
  - device1
  - device2

As always, you'll need to provide the connection credentials, in the Pillar. 
That is, you can have a structure as the following Pillar top file:

``/srv/pillar/top.sls``

.. code-block:: yaml

  base:
    '*':
      - proxy

And the connection credentials - example using NAPALM:

``/srv/pillar/proxy.sls``

.. code-block:: yaml

  proxy:
    proxytype: napalm
    driver: junos
    hostname: {{ opts.id }}.example.com
    password: superS3kure

With this configuration, ``device1`` will try to connect to 
``device1.example.com``, and ``device2`` to ``device2.example.com``, 
respectively, using the NAPALM Junos driver.

If you want more specific connection options per device, you can manage that in 
the Roster SLS file (under each device you can specify any connection argument 
to override the details from the ``proxy`` Pillar), e.g.,

``/etc/salt/roster``

.. code-block:: yaml

  device1:
    driver: eos
    hostname: different-hostname-for-device1.example.com
  device2:
    password: m0reS3kure

Using the previous example, ``device1`` will connect to 
``different-hostname-for-device1.example.com`` using the NAPALM EOS driver for 
Arista, while ``device2`` uses a different password.

In a similar way, you can provide static Grains per device, under the 
``grains`` key, e.g.,

``/etc/salt/roster``:

.. code-block:: yaml

  device1:
    grains:
      site: site1
  device2:
    grains:
      site: site2

If you prefer to manage a JSON structure instead:

``/etc/salt/roster``:

.. code-block:: json

  {
    "device1": {
      "grains": {
        "site": "site1"
      }
    },
    "device2": {
      "grains": {
        "site": "site2"
      }
    }
  }

With that clarified, let's make the Roster SLS file more dynamic, and instead 
of managing the list of devices manually, have it auto-generated:

``/etc/salt/roster``:

.. code-block:: yaml

  {%- for i in range(50) %}
  device{{ i }}:
    grains:
      site: site{{ i }}
  {%- endfor %}

The example above provides a list of 50 devices. Although probably too 
simplistic for real-world usage, it may be sufficient to exemplify the 
use-case.

Remember that being interpreted as an SLS, you can also invoke Salt 
functions, using the ``__salt__`` global variable. For example, to retrieve 
and build the list of devices dynamically using an HTTP query, you can do, 
e.g.,

.. code-block:: sls

  {%- set ret = __salt__.http.query('https://netbox.live/api/dcim/devices/', decode=true) %}
  {%- for device in ret.dict.results %}
  {{ device.name }}:
    grains:
      site: {{ device.site.slug }}
  {%- endfor %}

Ultimately, for higher complexity, consider using the `pure Python Renderer 
<https://docs.saltstack.com/en/latest/ref/renderers/all/salt.renderers.py.html#module-salt.renderers.py>`__
whenever you need to put more business logic in selecting the devices you need 
to manage.
