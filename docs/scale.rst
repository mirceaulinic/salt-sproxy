.. _scale:

Large Scale Settings
====================

The reference document remains 
https://docs.saltstack.com/en/latest/topics/tutorials/intro_scale.html with 
some small differences. Note however that if you're running in 
:ref:`mixed-environments`, the notes from the *Using Salt at Scale* document 
must be followed in order to manage a large number of devices (i.e., thousands 
or tens of thousands).

When running salt-sproxy only - without relying on other existing Minions, it is
still highly encouraged to use the batch mode when executing:
https://docs.saltstack.com/en/latest/topics/tutorials/intro_scale.html#too-many-minions-returning-at-once
Usage example:

.. code-block:: bash

    $ salt-sproxy '*' state.highstate -b 20

This will only execute on 20 devices at once, while looping through all the 
targeted devices.

When running in an environment with a Salt Master running and pushing events on 
the bus as detailed in :ref:`execution-events`, targeting a large number of 
devices may lead to a higher density of events which requires to increase the 
size of the event bus and other specific options, e.g., the ZeroMQ high-water 
mark and backlog - see 
https://docs.saltstack.com/en/latest/ref/configuration/master.html#master-large-scale-tuning-settings 
for more details and options.
