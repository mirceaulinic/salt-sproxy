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
