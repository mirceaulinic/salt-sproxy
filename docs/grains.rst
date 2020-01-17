.. _static-grains:

Managing Static Grains
======================

Grains are generally a delicate topic in Salt, particularly on Proxy Minions 
which need to be able to connect to the remote device to collect the Grains, 
while the connection credentials may depend on the Grains themselves - that 
becomes and chicken and egg type problem!

In *salt-sproxy*, you can configure static Grains, in different ways. One of 
the easiest is adding static data under the ``grains`` (or ``sproxy_grains`` or 
``default_grains``) key in the Master config file, for example:

``/etc/salt/master``

.. code-block:: yaml

    grains:
      salt:
        role: proxy

The static Grains configured in this way are going to be shared among all the 
devices / Minions managed via *salt-sproxy*.

.. important::

    The static Grains configured in these ways are available to be used in your
    target expressions. For example, the above can be used, e.g., ``salt-sproxy 
    -G salt:role:proxy --preview-target``.

To configure more specific Grains per device, or groups of devices, you have 
the following options:

Static Grains in File
---------------------

To configure static Grains for one specific device, you can put your data as 
described in 
https://docs.saltstack.com/en/latest/topics/grains/#grains-in-etc-salt-grains, 
more specifically under the ``/etc/salt/proxy.d/`` directory. For example, if 
you'd want to configure for the device ``router1``, you'd have the following 
file:

``/etc/salt/proxy.d/router1/grains``

.. code-block:: yaml

    role: router

Static Grains in Roster
-----------------------

Some :ref:`roster` modules allow you to put static Grains granularly. See, for 
example :ref:`pillar-roster-grains` (for the :ref:`pillar-roster`) or
:ref:`ansible-roster-grains` (for the :ref:`ansible-roster`).
