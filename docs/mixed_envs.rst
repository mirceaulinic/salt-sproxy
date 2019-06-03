.. _mixed-environments:

Mixed Environments
==================

When running in a mixed environment (you already have (Proxy) Minions running, 
and you would also like to use the salt-sproxy), it is highly recommended to 
ensure that salt-sproxy is using the same configuration file as your Master, 
and the Master is up and running.

Using the ``--use-existing-proxy`` option on the CLI, or configuring 
``use_existing_proxy: true`` in the Master configuration file, ``salt-sproxy`` 
is going to execute the command on the Minions that are connected to this 
Master (and matching your target), otherwise the command is going to be 
executed locally.

For example, suppose we have two devices, identified as ``minion1`` and 
``minion2``, extending the example :ref:`example-101`:

``/srv/salt/pillar/top.sls``:

.. code-block:: yaml

    base:
      'minion*':
        - dummy

``/srv/salt/pillar/dummy.sls``:

.. code-block:: yaml

    proxy:
      proxytype: dummy

The Master configuration remains the same:

``/etc/salt/master``:

.. code-block:: yaml

    pillar_roots:
      base:
        - /srv/salt/pillar

Starting up the Master, and the ``minion1`` Proxy:

.. code-block:: bash

    # start the Salt Master
    $ salt-master -d

    # start the Proxy Minion for ``minion1``
    $ salt-proxy --proxyid minion1 -d

    # accept the key of minion1
    $ salt-key -y -a minion1

    # check that minion1 is now up and running
    $ salt minion1 test.ping
    minion1:
        Test

In a different terminal window, you can start watching the Salt event bus (and 
leave it open, as I'm going to reference the events below):

.. code-block:: bash

    $ salt-run state.event pretty=True
    # here you will see the events flowing

Executing the following command, notice that the execution takes place locally 
(you can identify using the ``proxy/runner`` event tag):

.. code-block:: bash

    $ salt-sproxy -L minion1,minion2 test.ping --events
    minion1:
        True
    minion2:
        True

The event bus:

.. code-block:: text

    20190603145654312094	{
        "_stamp": "2019-06-03T13:56:54.312664",
        "minions": [
            "minion1",
            "minion2"
        ]
    }
    proxy/runner/20190603145654313680/new	{
        "_stamp": "2019-06-03T13:56:54.314249",
        "arg": [],
        "fun": "test.ping",
        "jid": "20190603145654313680",
        "minions": [
            "minion1",
            "minion2"
        ],
        "tgt": [
            "minion1",
            "minion2"
        ],
        "tgt_type": "list",
        "user": "sudo_mircea"
    }
    proxy/runner/20190603145654313680/ret/minion1	{
        "_stamp": "2019-06-03T13:56:54.406816",
        "fun": "test.ping",
        "fun_args": [],
        "id": "minion1",
        "jid": "20190603145654313680",
        "return": true,
        "success": true
    }
    proxy/runner/20190603145654313680/ret/minion2	{
        "_stamp": "2019-06-03T13:56:54.538850",
        "fun": "test.ping",
        "fun_args": [],
        "id": "minion2",
        "jid": "20190603145654313680",
        "return": true,
        "success": true
    }

As presented in :ref:`events`, there is one event for the job creating, then 
one for job start, and one event for each device separately (i.e.,
``proxy/runner/20190603145654313680/ret/minion1`` and
``proxy/runner/20190603145654313680/ret/minion2``, respectively).

.. _mixed-envs-example:

Now, if we want to execute the same, but use the already running Proxy Minion 
for ``minion1`` (started previously), simply pass the ``--use-existing-proxy`` 
option:

.. code-block:: bash

    $ salt-sproxy -L minion1,minion2 test.ping --events --use-existing-proxy
    minion2:
        True
    minion1:
        True

In this case, the event bus would look like below:

.. code-block:: text

    proxy/runner/20190603150335939481/new	{
        "_stamp": "2019-06-03T14:03:35.940128",
        "arg": [],
        "fun": "test.ping",
        "jid": "20190603150335939481",
        "minions": [
            "minion1",
            "minion2"
        ],
        "tgt": [
            "minion1",
            "minion2"
        ],
        "tgt_type": "list",
        "user": "sudo_mircea"
    }
    salt/job/20190603150335939481/new	{
        "_stamp": "2019-06-03T14:03:36.047971",
        "arg": [],
        "fun": "test.ping",
        "jid": "20190603150335939481",
        "minions": [
            "minion1"
        ],
        "missing": [],
        "tgt": "minion1",
        "tgt_type": "glob",
        "user": "sudo_mircea"
    }
    salt/job/20190603150335939481/ret/minion1	{
        "_stamp": "2019-06-03T14:03:36.147398",
        "cmd": "_return",
        "fun": "test.ping",
        "fun_args": [],
        "id": "minion1",
        "jid": "20190603150335939481",
        "retcode": 0,
        "return": true,
        "success": true
    }
    proxy/runner/20190603150335939481/ret/minion2	{
        "_stamp": "2019-06-03T14:03:36.245592",
        "fun": "test.ping",
        "fun_args": [],
        "id": "minion2",
        "jid": "20190603150335939481",
        "return": true,
        "success": true
    }
    proxy/runner/20190603150335939481/ret/minion1	{
        "_stamp": "2019-06-03T14:03:36.247206",
        "fun": "test.ping",
        "fun_args": [],
        "id": "minion1",
        "jid": "20190603150335939481",
        "return": true,
        "success": true
    }

In this sequence of events, you can notice that, in addition to the events from 
the previous example, there are two additional events: 
``salt/job/20190603150335939481/new`` - which is for the job start against the 
``minion1`` Proxy Minion, and ``salt/job/20190603150335939481/ret/minion1`` -
which is the return from the ``minion1`` Proxy Minion. The presence of the 
``salt/job`` event tags proves that the execution goes through the already 
existing Proxy Minion.

If you would like to always execute through the available Minions, whenever 
possible, you can add the following option to the Master configuration file:

.. code-block:: yaml

    use_existing_proxy: true
