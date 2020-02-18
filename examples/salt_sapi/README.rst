.. _example-salt-sapi:

salt-sapi
=========

.. note::

    This functionality makes use of the ``sproxy`` and ``sproxy_async`` clients
    added in release 2020.2.0 through the ``salt-sapi`` entry point. See 
    https://salt-sproxy.readthedocs.io/en/latest/salt_api.html and 
    https://salt-sproxy.readthedocs.io/en/latest/salt_sapi.html for more 
    details.

.. important::

    In the configuration examples below, for simplicity, I've used the `auto 
    <https://docs.saltstack.com/en/latest/ref/auth/all/salt.auth.auto.html>`__ 
    external authentication, and disabled the SSL for the Salt API. This setup 
    is highly discouraged in production.

Using the Master configuration file under `examples/salt_sapi/master 
<https://github.com/mirceaulinic/salt-sproxy/tree/master/examples/salt_sapi/master>`__:

``/etc/salt/master``:

.. code-block:: yaml

  pillar_roots:
    base:
      - /srv/salt/pillar

  file_roots:
    base:
      - /srv/salt/extmods

  rest_cherrypy:
    port: 8080
    disable_ssl: true

  external_auth:
    auto:
      '*':
        - '@runner'

The ``pillar_roots`` option points to ``/srv/salt/pillar``, so to be able to 
use this example, either create a symlink to the ``pillar`` directory in this 
example, or copy the files.
For example, if you just cloned this repository:

.. code-block:: bash

  $ mkdir -p /srv/salt/pillar
  $ git clone git@github.com:mirceaulinic/salt-sproxy.git
  $ cp salt-sproxy/examples/salt_sapi/master /etc/salt/master
  $ cp salt-sproxy/examples/salt_sapi/pillar/*.sls /srv/salt/pillar/

The contents of Pillar files:

``/srv/salt/pillar/top.sls``:

.. code-block:: yaml

  base:
    mininon1:
      - dummy
    juniper-router:
      - junos

``/srv/salt/pillar/dummy.sls``:

.. code-block:: yaml

  proxy:
    proxytype: dummy

``/srv/salt/pillar/junos.sls``:

.. code-block:: yaml

  proxy:
    proxytype: napalm
    driver: junos
    host: juniper.salt-sproxy.digitalocean.cloud.tesuto.com
    username: test
    password: t35t1234

.. note::

    The ``top.sls``, ``dummy.sls``, and ``junos.sls`` are a combination of the 
    previous examples, `101 
    <https://salt-sproxy.readthedocs.io/en/latest/examples/101.html>`__ and 
    `napalm 
    <https://salt-sproxy.readthedocs.io/en/latest/examples/napalm.html>`__, 
    which is going to allow use to execute against both the dummy device and 
    a real network device.

In the example Master configuration file above, there's also a section for the
``file_roots``. As documented in `The Proxy Runner 
<https://salt-sproxy.readthedocs.io/en/latest/runner.html>`__ section of the 
documentation, you are going to reference the `proxy Runner 
<https://salt-sproxy.readthedocs.io/en/latest/runners/proxy.html>`__, e.g.

.. code-block:: bash

    $ mkdir -p /srv/salt/extmods/_runners
    $ cp salt-sproxy/salt_sproxy/_runners/proxy.py /srv/salt/extmods/_runners/

Or symlink:

.. code-block:: bash

    $ ln -s /path/to/git/clone/salt-sproxy/salt_sproxy /srv/salt/extmods

With the ``rest_cherrypy`` section, the Salt API will be listening to HTTP 
requests over port 8080, and SSL being disabled (not recommended in production):

.. code-block:: yaml

  rest_cherrypy:
    port: 8080
    disable_ssl: true


One another part of the configuration is the external authentication:

.. code-block:: yaml

  external_auth:
    auto:
      '*':
        - '@runner'

This grants access to anyone to execute any Runner (again, don't do this in 
production).

With this setup, we can start the Salt Master and the Salt API (running in 
background):

.. code-block:: bash

    $ salt-master -d
    $ salt-sapi -d

To verify that the REST API is ready, execute:

.. code-block:: bash

    $ curl -i localhost:8080
    HTTP/1.1 200 OK
    Content-Type: application/json
    Server: CherryPy/18.1.1
    Date: Wed, 01 Jan 2020 07:58:32 GMT
    Allow: GET, HEAD, POST
    Access-Control-Allow-Origin: *
    Access-Control-Expose-Headers: GET, POST
    Access-Control-Allow-Credentials: true
    Vary: Accept-Encoding
    Content-Length: 146

    {"return": "Welcome", "clients": ["local", "local_async", "local_batch", "local_subset", "runner", "runner_async", "sproxy", "sproxy_async", "ssh", "wheel", "wheel_async"]}

Now we can go ahead and execute the CLI command from `example 101 
<https://salt-sproxy.readthedocs.io/en/latest/examples/101.html>`__, by making 
an HTTP request:

.. code-block:: bash

  $ curl -sS localhost:8080/run -H 'Accept: application/x-yaml' \
    -d eauth='auto' \
    -d username='mircea' \
    -d password='pass' \
    -d client='sproxy' \
    -d tgt='minion1' \
    -d fun='test.ping'
  return:
  - minion1: true

Notice that ``eauth`` field in this case is ``auto`` as this is what we've 
configured in the ``external_auth`` on the Master.

Similarly, you can now execute the Salt functions from the `NAPALM example 
<https://salt-sproxy.readthedocs.io/en/latest/examples/napalm.html>`__, against
a network device, by making an HTTP request:

.. code-block:: bash

  $ curl -sS localhost:8080/run -H 'Accept: application/x-yaml' \
    -d eauth='auto' \
    -d username='mircea' \
    -d password='pass' \
    -d client='sproxy' \
    -d tgt='juniper-router' \
    -d fun='net.arp'
  return:
  - juniper-router:
      comment: ''
      out:
      - age: 891.0
        interface: fxp0.0
        ip: 10.96.0.1
        mac: 92:99:00:0A:00:00
      - age: 1001.0
        interface: fxp0.0
        ip: 10.96.0.13
        mac: 92:99:00:0A:00:00
      - age: 902.0
        interface: em1.0
        ip: 128.0.0.16
        mac: 02:42:AC:12:00:02
      result: true
