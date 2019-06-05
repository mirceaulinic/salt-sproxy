.. _salt-api:

Using the Salt REST API
=======================

To be able to use the Salt HTTP API, similarly to :ref:`events`, you will 
need to have the Salt Master running, and, of course, also the Salt API 
service.

As the core functionality if based on the :ref:`proxy-runner`, check out first 
the notes from :ref:`runner` to understand how to have the ``proxy`` Runner 
available on your Master.

The Salt API configuration is unchanged from the usual approaches: see 
https://docs.saltstack.com/en/latest/ref/netapi/all/salt.netapi.rest_cherrypy.html 
how to configure and https://docs.saltstack.com/en/latest/ref/cli/salt-api.html 
how to start up the salt-api process.

Suppose we have the following configuration:

``/etc/salt/master``

.. code-block:: yaml

  rest_cherrypy:
    port: 8080
    ssl_crt: /etc/pki/tls/certs/localhost.crt
    ssl_key: /etc/pki/tls/certs/localhost.key

After starting the salt-api process, we should get the following:

.. code-block:: bash

    $ curl -i localhost:8080
    HTTP/1.1 200 OK
    Content-Type: application/json
    Server: CherryPy/18.1.1
    Date: Wed, 05 Jun 2019 07:58:32 GMT
    Allow: GET, HEAD, POST
    Access-Control-Allow-Origin: *
    Access-Control-Expose-Headers: GET, POST
    Access-Control-Allow-Credentials: true
    Vary: Accept-Encoding
    Content-Length: 146

    {"return": "Welcome", "clients": ["local", "local_async", "local_batch", "local_subset", "runner", "runner_async", "ssh", "wheel", "wheel_async"]}

That means the Salt API is ready to receive requests.

To invoke a command on a (network) device managed through Salt, you can use the
``proxy`` Runner to invoke commands on, e.g.,

.. code-block:: bash

  $ curl -sS localhost:8080/run -H 'Accept: application/x-yaml' \
    -d eauth='pam' \
    -d username='mircea' \
    -d password='pass' \
    -d client='runner' \
    -d fun='proxy.execute' \
    -d tgt='minion1' \
    -d function='test.ping' \
    -d sync=True
  return:
  - minion1: true

Note that the execution is at the ``/run`` endpoint, with the following 
details:

- ``username``, ``password``, ``eauth`` as configured in the ``external_auth``. 
  See https://docs.saltstack.com/en/latest/topics/eauth/index.html for more 
  details and how to configure external authentication.
- ``client`` is *runner*, as we're going to use the ``proxy`` Runner.
- ``fun`` is the name of the Runner function, in this case 
  :func:`_runners.proxy.execute`.
- ``tgt`` is the Minion ID / device name to target.
- ``function`` is the Salt function to execute on the targeted device(s).
- ``sync`` is set as ``True`` as we're waiting for the output to be returned 
  back over the API. Otherwise, if we only need to invoke the function without
  expecting an output, we don't need to pass this argument.

This HTTP request is the equivalent of CLI from the example :ref:`example-101`:

.. code-block:: bash

    $ salt-sproxy minion1 test.ping

It works in the same way when execution function on actual devices, for 
instance when gathering the ARP table from a Juniper router (the equivalent 
of the ``salt-sproxy juniper-router net.arp`` CLI from the example 
:ref:`example-napalm`):

.. code-block:: bash

  $ curl -sS localhost:8080/run -H 'Accept: application/x-yaml' \
    -d eauth='auto' \
    -d username='mircea' \
    -d password='pass' \
    -d client='runner' \
    -d fun='proxy.execute' \
    -d tgt='juniper-router' \
    -d function='net.arp' \
    -d sync=True
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

Or when updating the configuration:

.. code-block:: bash

  $ curl -sS localhost:8080/run -H 'Accept: application/x-yaml' \
    -d eauth='auto' \
    -d username='mircea' \
    -d password='pass' \
    -d client='runner' \
    -d fun='proxy.execute' \
    -d tgt='juniper-router' \
    -d function='net.load_config' \
    -d text='set system ntp server 10.10.10.1' \
    -d test=True \
    -d sync=False
  return:
  - juniper-router:
      already_configured: false
      comment: Configuration discarded.
      diff: '[edit system]
        +   ntp {
        +       server 10.10.10.1;
        +   }'
      loaded_config: ''
      result: true

  $ curl -sS localhost:8080/run -H 'Accept: application/x-yaml' \
    -d eauth='auto' \
    -d username='mircea' \
    -d password='pass' \
    -d client='runner' \
    -d fun='proxy.execute' \
    -d tgt='juniper-router' \
    -d function='net.load_config' \
    -d text='set system ntp server 10.10.10.1' \
    -d sync=False
  return:
  - juniper-router:
      already_configured: false
      comment: ''
      diff: '[edit system]
        +   ntp {
        +       server 10.10.10.1;
        +   }'
      loaded_config: ''
      result: true


You can follow the same methodology with any other Salt function (including
States) that you might want to execute against a device, without having a
(Proxy) Minion running.
