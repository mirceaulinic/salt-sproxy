.. _best-practices:

Salt SProxy Best Practices
==========================

.. note::

    This document refers to best practices in regards to optimising the usage 
    of *salt-sproxy*.

    To refer to the Salt best practices concerning the structure of the 
    configuration files, see `this 
    <https://docs.saltstack.com/en/latest/topics/best_practices.html>`__ 
    document.

In order to simplify the default usage, *salt-sproxy* tries to load Grains, 
Roster, and Execution Modules; this adds an execution overhead everytime you 
invoke a Salt command through *salt-sproxy*, of approximatively 0.5s up to 
1 second. In some cases, this can be reduced or even removed entirely by
configuring one or more of the options below, depending on your use case.

TL;DR
-----

To speed up the execution, you can add the *salt-sproxy* installation path to 
your ``file_roots`` settings in the Master config (see :ref:`runner` for more 
notes on how to do this), and execute ``salt-run saltutil.sync_all``. At the 
same time, add the following in the Master config:

.. code-block:: yaml

    sync_grains: false
    sync_roster: false
    sync_modules: false

.. important::

    Once you have these settings enabled, while it will speed up the 
    *salt-sproxy* execution and make it more efficient, if you have custom
    Grains or Execution Modules in your own environment, you will need to take
    care that they are properly sync'ed on your Master. That is, execute
    ``salt-run saltutil.sync_all`` or equivalent whenever you update your
    modules. Examples include: manually execute ``salt-run saltutil.sync_all``
    (not recommended), a cron on the same, or if you have a Salt Master running
    you can have it automatically sync those for you by adding a `scheduled job 
    <https://docs.saltstack.com/en/latest/topics/jobs/>`__, e.g.,

    .. code-block:: yaml

        schedule:
          sync_all:
            function: saltutil.sync_all
            minutes: 5

    The example configuration snippet above would ensure that your custom 
    modules are sync'ed every 5 minutes.

If for some reason you can't do this for one or more of these modules, check out
the recommendations below for each of them.

Disable Grains
--------------

If you don't have any custom Grains modules in your environment, you can 
disable the load, by configuring ``sync_grains: false`` in your Master 
configuration file.

.. tip::

    If you do have custom Grains in your environment, you can disable the 
    *salt-sproxy* automatic sync by adding ``sync_grains: false`` to your 
    Master configuration, and sync the Grains manually or automatically 
    whenever you update (or create) your modules: ``salt-run 
    saltutil.sync_grains``.


Additionally, disabling the load of some specific Grains modules (whether your 
own, or natively available in Salt), may speed up your setup. Configure 
``disable_grains`` in your Master config, as a list of Grains modules to avoid
loading when executing through *salt-sproxy*.

Example:

.. code-block:: yaml

    disable_grains:
      - esxi

Disable Execution Modules
-------------------------

If you don't have any custom Execution modules in your own environment, and you 
don't make use of the modules shipped together with *salt-sproxy* (see 
:ref:`execution-modules`), you can disable the load by configuring 
``sync_modules: false`` in your Master configuration file.

.. tip::

    If you do have custom modules in your environment, you can disable the 
    *salt-sproxy* automatic sync by adding ``sync_modules: false`` to your 
    Master configuration, and sync the modules manually or automatically 
    whenever you update (or create) your modules: ``salt-run 
    saltutil.sync_modules``.

Additionally, disabling the load of some specific Execution modules (whether
your own, natively available in Salt, or provided through *salt-sproxy*), may
speed up your setup. Configure ``disable_modules`` in your Master config, as a
list of modules to avoid loading when executing through *salt-sproxy*.

Example:

.. code-block:: yaml

    disable_modules:
      - pip
      - statuspage

Disable Roster Sync
-------------------

If you use one of the Roster modules provided with this package, or from your 
own sources, *salt-sproxy* would attempt to sync only the Roster module you 
reference in ``roster:`` or using the ``--roster`` CLI argument. Even so, this 
may be time and resource consuming, so it'd may be optimal to disable the 
default behaviour by setting ``sync_roster: false`` in the Master 
configuration. Similarly to the previous sections, if you'd like to use 
a custom module in your own environment, you can sync them by running 
``salt-run saltutil.sync_roster``.

*salt-sproxy* core Runner
-----------------------

Another contributor to the *salt-sproxy* execution speed is the :ref:`runner` 
which is the very core of *salt-sproxy*. That said, if this Runner is already 
"well known" to the Salt filesystem, it'll make it more efficient.

In this case, you will need to follow the notes from :ref:`runner` to update 
your ``file_roots`` settings, and run ``salt-run saltutil.sync_runner``.

Remember that you'll need to re-run that in case you re-install *salt-sproxy*, 
Salt, or remove the Salt cache.

Of course, you can always have a scheduled job that does it for you, either 
a cron job, or a `scheduled job 
<https://docs.saltstack.com/en/latest/topics/jobs/>`__ if you have a Salt 
Master running, e.g., re-sync Runners every hour:

.. code-block:: yaml

    schedule:
      sync_runners:
        function: saltutil.sync_runner
        minutes: 60

File open limit
---------------

As *salt-sproxy* runs locally, it means it starts the processes and initializes 
the connection on the local computer. Every new process creates a process file, 
and every new connection creates at least one more file as well. That said, 
depending on your operating system and configuration, you may hit the hard 
limit for max open files. For example, on Unix operating systems, ``ulimit 
-Hn`` will tell you the max open files number. If you hit any issues, consider 
increasing this limit.
