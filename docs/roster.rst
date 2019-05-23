.. _using-roster:

Using the Roster Interface
==========================

While from the CLI perspective ``salt-sproxy`` looks like it works similar to
the usual ``salt`` command, in fact, they work fundamentally different. One of
the most important differences being that ``salt`` is aware what Minions are 
connected to the Master, therefore it is easy to know what Minions would be 
matched by a certain target expression (see 
https://docs.saltstack.com/en/latest/topics/targeting/ for further details). In
contrast, by definition, ``salt-sproxy`` doesn't suppose there are any (Proxy) 
Minions running, so it cannot possible know what Minions would be matched by an 
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

Roster usage example: Ansible
-----------------------------

If you already have an Ansible inventory, simply drop it into a file, e.g.,
``/etc/salt/roster``.

.. note::

    The Ansible inventory file doesn't need to provide any connection details, 
    as they must be configured into the Pillar. If you do provide them however, 
    they will be ignored. The Roster file (Ansible inventory in this case) 
    needs to provide really just the name of the devices you want to manage -- 
    everything else must go into the Pillar.

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
