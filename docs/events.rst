.. _events:

Event-Driven Automation and Orchestration
=========================================

.. _execution-events:

Execution Events
----------------

Even though ``salt-sproxy`` has been designed to be an on-demand executed
process  (as in opposite to an always running service), you still have the
possibility  to monitor what is being executed, and potentially export these
events or trigger a
`Reactor <https://docs.saltstack.com/en/latest/topics/reactor/>`__  execution
in response.

.. note::

    To be able to have events, you will need to have a Salt Master running, and
    preferrably using the same Master configuration file as salt-sproxy, to 
    ensure that they are both sharing the same socket object.

Using the ``--events`` option on the CLI (or by configuring ``events: true`` in 
the Master configuration file), ``salt-sproxy`` is going to inject events on the
Salt bus as you're running the usual Salt commands.

For example, running the following command (from the
`salt-sproxy with network devices <http://salt-sproxy.readthedocs.io/en/latest/examples/napalm.html>`__
example):

.. code-block:: bash

    $ salt-sproxy juniper-router net.arp --events

Watching the event bus on the Master, you should notice the following events:

.. code-block:: bash

    $ salt-run state.event pretty=True
    20190529143434052740	{
        "_stamp": "2019-05-29T14:34:34.053900", 
        "minions": [
            "juniper-router"
        ]
    }
    proxy/runner/20190529143434054424/new	{
        "_stamp": "2019-05-29T14:34:34.055386", 
        "arg": [], 
        "fun": "net.arp", 
        "jid": "20190529143434054424", 
        "minions": [
            "juniper-router"
        ], 
        "tgt": "juniper-router", 
        "tgt_type": "glob", 
        "user": "mircea"
    }
    proxy/runner/20190529143434054424/ret/juniper-router	{
        "_stamp": "2019-05-29T14:34:36.937409", 
        "fun": "net.arp", 
        "fun_args": [], 
        "id": "juniper-router", 
        "jid": "20190529143434054424", 
        "return": {
            "out": [
                {
                    "interface": "fxp0.0",
                    "mac": "92:99:00:0A:00:00",
                    "ip": "10.96.0.1",
                    "age": 926.0
                },
                {
                    "interface": "fxp0.0",
                    "mac": "92:99:00:0A:00:00",
                    "ip": "10.96.0.13",
                    "age": 810.0
                },
                {
                    "interface": "em1.0",
                    "mac": "02:42:AC:13:00:02",
                    "ip": "128.0.0.16",
                    "age": 952.0
                }
            ],
            "result": true,
            "comment": ""
        },
        "success": true
    }

As in the example, above, every execution pushes at least three events:

- Job creation. The tag is the JID of the execution.
- Job payload with the job details, i.e., function name, arguments, target
  expression and type, matched devices, etc.
- One separate return event from every device.

A more experienced Salt user may have already noticed that the structure of 
these events is *very* similar to the usual Salt native events when executing 
a regular command using the usual ``salt``. Let's take an example for clarity:

.. code-block:: bash

    $ salt 'test-minion' test.ping
    test-minion:
        True

The event bus:

.. code-block:: bash

    $ salt-run state.event pretty=True
    20190529144939496567	{
        "_stamp": "2019-05-29T14:49:39.496954", 
        "minions": [
            "test-minion"
        ]
    }
    salt/job/20190529144939496567/new	{
        "_stamp": "2019-05-29T14:49:39.498021", 
        "arg": [], 
        "fun": "test.ping", 
        "jid": "20190529144939496567", 
        "minions": [
            "test-minion"
        ], 
        "missing": [], 
        "tgt": "test-minion", 
        "tgt_type": "glob", 
        "user": "sudo_mulinic"
    }
    salt/job/20190529144939496567/ret/test-minion	{
        "_stamp": "2019-05-29T14:49:39.905727", 
        "cmd": "_return", 
        "fun": "test.ping", 
        "fun_args": [], 
        "id": "test-minion", 
        "jid": "20190529144939496567", 
        "retcode": 0, 
        "return": true, 
        "success": true
    }

That said, if you already have Reactors matching Salt events, in order to 
trigger them in response to salt-sproxy commands, you would only need to update 
the tag matching expression (i.e., besides ``salt/job/20190529144939496567/new``
should also match ``proxy/runner/20190529143434054424/new`` tags, etc.).

In the exact same way with other Engine types -- if you already have Engines 
exporting events, they should be able to export salt-sproxy events as well, 
which is a great easy win for PCI compliance, and generally to monitor who 
executes what.

.. _events-reactions:

Reactions to external events
----------------------------

Using the :ref:`runner`, you can configure a Reactor to execute a Salt function 
on a (network) device in response to an event.

For example, let's consider network events from
`napalm-logs <http://napalm-logs.com/en/latest/>`__. To import the napalm-logs 
events on the Salt bus, simply enable the `napalm_syslog 
<https://docs.saltstack.com/en/latest/ref/engines/all/salt.engines.napalm_syslog.html>`__ 
Salt Engine on the Master.

In response to an `INTERFACE_DOWN 
<http://napalm-logs.com/en/latest/messages/INTERFACE_DOWN.html>`__ 
notification, say we define the following reaction, in response to events with 
the ``napalm/syslog/*/INTERFACE_DOWN/*`` pattern (i.e., matching events such 
as ``napalm/syslog/iosxr/INTERFACE_DOWN/edge-router1``, 
``napalm/syslog/junos/INTERFACE_DOWN/edge-router2``, etc.):

``/etc/salt/master``

.. code-block:: yaml

    reactor:
      - 'napalm/syslog/*/INTERFACE_DOWN/*':
        - salt://reactor/if_down_shutdown.sls

The ``salt://reactor/if_down_shutdown.sls`` translates to 
``/etc/salt/reactor/if_down_shutdown.sls`` when ``/etc/salt`` is one of the 
configured ``file_roots``. To apply a configuration change on the device with 
the interface down, we can use the :func:`_runner.proxy.execute` Runner 
function:

.. code-block:: yaml

  shutdown_interface:
    runner.proxy.execute:
      - tgt: {{ data.host }}
      - kwarg:
          salt_function: net.load_template
          template_name: salt://templates/shut_interface.jinja
          interface_name: {{ data.yang_message.interfaces.interface.keys()[0] }}

This Reactor would apply a configuration change as rendered in the Jinja 
template ``salt://templates/shut_interface.jinja`` (physical path 
``/etc/salt/templates/shut_interface.jinja``). Or, to have an end-to-end 
overview of the system: when the device sends a notification that one interface 
is down, in response, Salt is automatically going to try and remediate the 
problem (in the ``shut_interface.jinja`` template you can define the business 
logic you need). Similarly, you can have other concurrent reactions to the 
same, e.g. to send a Slack notification, and email and so on.

For reactions to ``napalm-logs`` events specifically, you can continue reading 
more at https://mirceaulinic.net/2017-10-19-event-driven-network-automation/ 
for a more extensive introduction and the napalm-logs documentation available 
at https://napalm-logs.readthedocs.io/en/latest/, with the difference that 
instead of calling a Salt function directly, you go through the 
:func:`_runner.proxy.execute` or :func:`_runner.proxy.execute_devices` Runner 
functions.
