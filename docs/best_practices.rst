.. _best-practices:

Salt SProxy Best Practices
==========================

.. note::

    This document refers to best practices in regards to optimising the usage 
    of salt-sproxy.

    To refer to the Salt best practices concerning the structure of the 
    configuration files, see `this 
    <https://docs.saltstack.com/en/latest/topics/best_practices.html>`__ 
    document.

In order to simplify the default usage, salt-sproxy tries to load Grains, 
Roster, and Execution Modules; this adds an execution overhead everytime you 
invoke a Salt command through salt-sproxy, of approximatively 0.5s up to 
1 second. In some cases, this can be reduced or even removed entirely by
configuring one or more of the options below, depending on your use case.

Disable Grains
--------------

If you don't have any custom Grains modules in your environment, you can 
disable the load, by configuring ``sync_grains: false`` in your Master 
configuration file.

Additionally, disabling the load of some specific Grains modules (whether your 
own, or natively available in Salt), may speed up your setup. Configure 
``disable_grains`` in your Master config, as a list of Grains modules to avoid
loading when executing through salt-sproxy.

Example:

.. code-block:: yaml

    disable_grains:
      - esxi

Disable Execution Modules
-------------------------

If you don't have any custom Execution modules in your own environment, and you 
don't make use of the modules shipped together with salt-sproxy (see 
:ref:`execution-modules`), you can disable the load by configuring 
``sync_modules: false`` in your Master configuration file.

Additionally, disabling the load of some specific Execution modules (whether
your own, natively available in Salt, or provided through salt-sproxy), may
speed up your setup. Configure ``disable_modules`` in your Master config, as a
list of modules to avoid loading when executing through salt-sproxy.

Example:

.. code-block:: yaml

    disable_modules:
      - pip
      - statuspage
