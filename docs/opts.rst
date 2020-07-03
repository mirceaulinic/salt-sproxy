.. _opts:

Command Line and Configuration Options
======================================

There are a few options specific for ``salt-sproxy``, however you might be 
already familiar with a vast majority of them from the `salt 
<https://docs.saltstack.com/en/latest/ref/cli/salt.html>`__ or `salt-run 
<https://docs.saltstack.com/en/latest/ref/cli/salt-run.html>`__ Salt commands.

.. hint::

    Many of the CLI options are available to be configured through the file 
    you can specifiy through the ``-c`` (``-config-dir``) option, with the 
    difference that in the file you need to use the longer name and underscore 
    instead of hyphen. For example, the ``--roster-file`` option would be 
    configured as ``roster_file: /path/to/roster/file`` in the config file.

.. option:: --version

    Print the version of Salt and Salt SProxy that is running.

.. option:: --versions-report

    Show program's dependencies and version number, and then exit.

.. option:: -h, --help

    Show the help message and exit.

.. option:: -c CONFIG_DIR, --config-dir=CONFIG_dir

    The location of the Salt configuration directory. This directory contains
    the configuration files for Salt master and minions. The default location
    on most systems is ``/etc/salt``.

.. option:: --config-dump

    .. versionadded:: 2020.2.0

    Print the complete salt-sproxy configuration values (with the defaults), as 
    YAML.

.. option:: -t, --timeout

    The time in seconds to await for a device to reply. Default: 60 (seconds).

    When a device is not replying within this time, it is a good idea to 
    increase the timeout value. The return when the device is slowly responding 
    is ``Minion did not return. [No response]``. When used in conjunction with 
    ``--summary``, the device will be counted under ``# of devices that did not 
    return``, but not ``# of devices returned``. Moreover, salt-sproxy will 
    exit with non-zero code, and the ``ERROR: Minions returned with non-zero 
    exit code`` message will be displayed at the end.

.. option:: -r, --roster

    The Roster module to use to compile the list of targeted devices.

.. option:: --roster-file

    Absolute path to the Roster file to load (when the Roster module requires 
    a file). Default: ``/etc/salt/roster``.

.. option:: --invasive-targeting

    .. versionadded:: 2020.2.0

    The native *salt-sproxy* targeting highly depends on the data your provide 
    mainly through the Roster system (see also :ref:`using-roster`). Through 
    the Roster interface and other mechanisms, you are able to provide static
    Grains (see also :ref:`static-grains`), which you can use in your targeting 
    expressions. There are situations when you may want to target using more 
    dynamic Grains that you probably don't want to manage statically.

    In such case, the ``--invasive-targeting`` targeting can be helpful as it
    connects to the device, retrieves the Grains, then executes the requested
    command, *only* on the devices matched by your target.

    .. important::

        The maximum set of devices you can query is the devices you have 
        defined in your Roster -- targeting in this case helps you select 
        a subset of the devices *salt-sproxy* is aware of, based on their 
        properties.

    .. caution::

        While this option can be very helpful, bear in mind that in order to 
        retrieve all this data, *salt-sproxy* initiates the connection with ALL 
        the devices provided through the Roster interface. That means, not only 
        that resources consumption is expected to increase, but also the
        execution time would similarlly be higher. Depending on your setup and
        use case, you may want to consider using ``--cache-grains`` and / or 
        ``--cache-pillar``. The idea is to firstly run ``--invasive-targeting``
        together with ``--cache-grains`` and / or ``--cache-pillar``, in order
        to cache your data, and the subsequent executions through *salt-sproxy* 
        are going to use that data, device target matching included.

.. option:: --preload-targeting

    .. versionadded:: 2020.2.0

    This is a lighter derivative of the ``--invasive-targeting`` option (see 
    above), with the difference that *salt-sproxy* is not going to establish 
    the connection with the remote device to gather the data, but will just 
    load all the possible data without the connection. In other words, you can 
    look at it like a combination of both ``--invasive-targeting`` and 
    ``-no-connect`` used together.

    This option is useful when the Grains and Pillars you want to use in your
    targeting expression don't depend on the connection with the device itself,
    but they are dynamically pulled from various systems, e.g., from an HTTP
    API, database, etc.

.. option:: --sync

    .. deprecated:: 2020.2.0

        This option has been replaced by ``--static`` (see below).

    Whether should return the entire output at once, or for every device 
    separately as they return.

.. option:: -s, --static

    .. versionadded:: 2020.2.0

        Starting with this release, ``--static``, replaces the previous CLI
        option ``--sync``, with the same functionality.

    Whether should return the entire output at once, or for every device 
    separately as they return.

.. option:: --cache-grains

    Cache the collected Grains. Beware that this option overwrites the existing
    Grains. This may be helpful when using the ``salt-sproxy`` only, but may 
    lead to unexpected results when running in :ref:`mixed-environments`. That 
    said, when running together with ``--use-existing-proxy``, there shouldn't
    be any issues, as *salt-sproxy* will attemtp to use the existing (Proxy) 
    Minion if any, otherwise it will write the collected Grains to the cache, 
    which is a safe operation in this case (i.e., it won't overwrite the Grains 
    of an existing Minion).

.. option:: --cache-pillar

    Cache the collected Pillar. Beware that this option overwrites the existing
    Pillar. This may be helpful when using the ``salt-sproxy`` only, but may 
    lead to unexpected results when running in :ref:`mixed-environments`. That 
    said, when running together with ``--use-existing-proxy``, there shouldn't
    be any issues, as *salt-sproxy* will attemtp to use the existing (Proxy) 
    Minion if any, otherwise it will write the compiled Pillar to the cache, 
    which is a safe operation in this case (i.e., it won't overwrite the cached
    Pillar of an existing Minion).

.. option:: --no-cached-grains

    Do not use the cached Grains (i.e., always collect Grains).

.. option:: --no-cached-pillar

    Do not use the cached Pillar (i.e., always re-compile the Pillar).

.. option:: --no-grains

    Do not attempt to collect Grains at all. While it does reduce the runtime, 
    this may lead to unexpected results when the Grains are referenced in other
    subsystems.

.. option:: --no-pillar

    Do not attempt to compile Pillar at all. While it does reduce the runtime, 
    this may lead to unexpected results when the Pillar data is referenced in
    other subsystems.

.. option:: -b, --batch, --batch-size

    The number of devices to connect to in parallel.

.. option:: --batch-wait

    .. versionadded:: 2020.2.0

    Wait a specific number of seconds after each batch is done before executing 
    the next one.

.. option:: -p, --progress

    .. versionadded:: 2020.2.0

    Display a progress graph to visually show the execution of the command 
    across the list of devices.

    .. note::

        As of release 2020.2.0, the best experience of using the progress graph 
        is in conjunction with the ``-s`` / ``--static`` option, otherwise 
        there's a small display issue.

.. option:: --hide-timeout

    .. versionadded:: 2020.2.0

    Hide devices that timeout.

.. option:: --failhard

    .. versionadded:: 2020.2.0

    Stop the execution at the first error.

.. option:: --summary

    .. versionadded:: 2020.2.0

    Display a summary of the command execution:

    - Total number of devices targeted.
    - Number of devices that returned without issues.
    - Number of devices that timed out executing the command. See also ``-t`` 
      or ``--timeout`` argument to adjust the timeout value.
    - Number of devices with errors (i.e., there was an error while executing 
      the command).
    - Number of unreachable devices (i.e., couldn't establish the connection 
      with the remote device).

    In ``-v`` / ``--verbose`` mode, this output is enahnced by displaying the 
    list of devices that did not return / with errors / unreachable.

    Example:

    .. code-block:: text

        -------------------------------------------
        Summary
        -------------------------------------------
        # of devices targeted: 10
        # of devices returned: 3
        # of devices that did not return: 5
        # of devices with errors: 0
        # of devices unreachable: 2
        -------------------------------------------

.. option:: --show-jid

    .. versionadded:: 2020.2.0

    Display jid without the additional output of --verbose.

.. option:: -v, --verbose

    .. versionadded:: 2020.2.0

    Turn on command verbosity, display jid, devices per batch, and detailed
    summary.

.. option:: --preview-target

    Show the devices expected to match the target, without executing any 
    function (i.e., just print the list of devices matching, then exit).

.. option:: --sync-roster

    Synchronise the Roster modules (both salt-sproxy native and provided by the
    user in their own environment). Default: ``True``.

.. option:: --sync-modules

    .. versionadded:: 2019.10.0

    Load the Execution modules provided together with salt-sproxy. Beware that
    it may override the Salt native modules, or your own extension modules.
    Default: ``False``.

    You can also add ``sync_modules: true`` into the Master config file, if you
    want to always ensure that salt-sproxy is using the Execution modules
    delivered with this package.

.. option:: --sync-grains

    .. versionadded:: 2019.10.0

    Synchronise the Grains modules you may have in your own environment.

.. option:: --sync-all

    .. versionadded:: 2020.2.0

    Load the all extension modules provided with salt-sproxy, as well as your
    own extension modules from your environment.

.. option:: --saltenv

    .. versionadded:: 2020.2.0

    The Salt environment name where to load extension modules and files from.

.. option:: --events

     Whether should put the events on the Salt bus (mostly useful when having a
     Master running). Default: ``False``.

     .. important::

        See :ref:`events` for further details.

.. option:: --use-existing-proxy

    Execute the commands on an existing Proxy Minion whenever available. If one
    or more Minions matched by the target don't exist (or the key is not 
    accepted by the Master), salt-sproxy will fallback and execute the command
    locally, and, implicitly, initiate the connection to the device locally.

    .. note::

        This option requires a Master to be up and running. See 
        :ref:`mixed-environments` for more information.

    .. important::

        When using this option in combination with a Roster, ``salt-sproxy`` 
        will firstly try to match your target based on the provided Roster, and
        then only after that will execute the Salt function on the targets, and
        on the existing Proxy Minions, best efforts. For example, if your target
        matches two devices, say ``router1`` and ``switch1``, and there's an
        available Proxy Minion running for ``router1``, then the Salt function
        would be executed on the ``router1`` existing Minion, over the already 
        established connection, while for ``switch1`` the connection is going to 
        be initialised during run time.

        If you want to bypass the Roster matching, and target *only* existing
        (Proxy) Minions, make sure you don't have the ``roster`` or 
        ``proxy_roster`` options configured, or execute with ``-r None``, e.g.,

        .. code-block:: bash

            $ salt-sproxy \* --preview-target --use-existing-proxy -r None

        The command above would be the equivalent of the following Salt 
        command: ``salt \* --preview-target``.

.. option:: --no-connect

    .. versionadded:: 2019.10.0

    Do not initiate the connection with the remote device. Please use this 
    option with care, as it may lead to unexptected results. The main use case 
    (although not limited to) is executing Salt functions that don't 
    necessarily require the connection, however they may need Pillar or Grains
    that are associated with each individual device. Such examples include HTTP 
    requests, working with files, and so on. Keep in mind that, as the 
    connection is not established, it won't re-compile fresh Grains, therefore 
    it'll be working with cached data. Make sure that the data you have 
    available is already cached before executing with ``--no-connect``, by 
    executing ``grains.items`` and / or ``pillar.items``. The point of this 
    functionality is to speed up the execution when dealing with a large volume 
    of execution events (either from the CLI or through the :ref:`runner`), and 
    when the connection is not actually absolutely necessary.

.. option:: --test-ping

    .. versionadded:: 2019.10.0

    When executing with ``--use-existing-proxy``, you can use this option to 
    verify whether the Minion is responsive, and only then attempt to send out 
    the command to be executed on the Minion, otherwise executed the function 
    locally.

    .. note::

        Keep in mind that this option generates an additional event on the bus
        for every execution.

.. option:: --no-target-cache

    .. versionadded:: 2019.10.0

    Avoid loading the list of targets from the cache.

    .. versionchanged:: 2020.3.0

        This option now defaults to ``True``.

.. option:: --pillar-root

    .. versionadded:: 2020.2.0

    Set a specific directory as the base pillar root.

.. option:: --file-root

    .. versionadded:: 2020.2.0

    Set a specific directory as the base file root.

.. option:: --states-dir

    .. versionadded:: 2020.2.0

    Set a specific directory to search for additional States.

.. option:: -m, --module-dirs

    .. versionadded:: 2020.2.0

    Specify one or more directories where to load the extension modules from.
    Multiple directories can be provided by passing ``-m`` or 
    ``--module-dirs`` multiple times.

.. option:: --file-roots, --display-file-roots

    Display the location of the salt-sproxy installation, where you can point 
    your ``file_roots`` on the Master, to use the :ref:`proxy-runner` and other
    extension modules included in the salt-sproxy package. See also 
    :ref:`runner`.

.. option:: --save-file-roots

    Save the configuration for the ``file_roots`` in the Master configuration
    file, in order to start using the :ref:`proxy-runner` and other extension
    modules included in the salt-sproxy package. See also :ref:`runner`.
    This option is going to add the salt-sproxy installation path to your
    existing ``file_roots``.

.. _logging-opts:

Logging Options
---------------

Logging options which override any settings defined on the configuration files.

.. start-console-output
.. option:: -l LOG_LEVEL, --log-level=LOG_LEVEL

    Console logging log level. One of ``all``, ``garbage``, ``trace``,
    ``debug``, ``info``, ``warning``, ``error``, ``quiet``. Default: ``error``.
.. stop-console-output

.. option:: --log-file=LOG_FILE

    Log file path. Default: ``/var/log/salt/master``.

.. option:: --log-file-level=LOG_LEVEL_LOGFILE

    Logfile logging log level. One of ``all``, ``garbage``, ``trace``,
    ``debug``, ``info``, ``warning``, ``error``, ``quiet``. Default: ``error``.

.. _target-selection:

Target Selection
----------------

The default matching that Salt utilizes is shell-style globbing around the
minion id. See https://docs.python.org/2/library/fnmatch.html#module-fnmatch.

.. seealso:: :ref:`targeting`

.. option:: -E, --pcre

    The target expression will be interpreted as a PCRE regular expression
    rather than a shell glob.

.. option:: -L, --list

    The target expression will be interpreted as a comma-delimited list;
    example: server1.foo.bar,server2.foo.bar,example7.quo.qux

.. option:: -G, --grain

    The target expression matches values returned by the Salt grains system on
    the minions. The target expression is in the format of '<grain value>:<glob
    expression>'; example: 'os:Arch*'

    This was changed in version 0.9.8 to accept glob expressions instead of
    regular expression. To use regular expression matching with grains, use
    the --grain-pcre option.

.. option:: -P, --grain-pcre

    The target expression matches values returned by the Salt grains system on
    the minions. The target expression is in the format of '<grain value>:<
    regular expression>'; example: 'os:Arch.*'

.. option:: -N, --nodegroup

    Use a predefined compound target defined in the Salt master configuration
    file.

.. option:: -R, --range

    Instead of using shell globs to evaluate the target, use a range expression
    to identify targets. Range expressions look like %cluster.

    Using the Range option requires that a range server is set up and the
    location of the range server is referenced in the master configuration
    file.

.. _output-opts:

Output Options
--------------

.. option:: --out

    Pass in an alternative outputter to display the return of data. This
    outputter can be any of the available outputters:

        ``highstate``, ``json``, ``key``, ``overstatestage``, ``pprint``, ``raw``, ``txt``, ``yaml``, ``table``, and many others.

    Some outputters are formatted only for data returned from specific functions.
    If an outputter is used that does not support the data passed into it, then
    Salt will fall back on the ``pprint`` outputter and display the return data
    using the Python ``pprint`` standard library module.

    .. note::
        If using ``--out=json``, you will probably want ``--static`` as well.
        Without the sync option, you will get a separate JSON string per minion
        which makes JSON output invalid as a whole.
        This is due to using an iterative outputter. So if you want to feed it
        to a JSON parser, use ``--static`` as well.

.. option:: --out-indent OUTPUT_INDENT, --output-indent OUTPUT_INDENT

    Print the output indented by the provided value in spaces. Negative values
    disable indentation. Only applicable in outputters that support
    indentation.

.. option:: --out-file=OUTPUT_FILE, --output-file=OUTPUT_FILE

    Write the output to the specified file.

.. option:: --out-file-append, --output-file-append

    Append the output to the specified file.

.. option:: --no-color

    Disable all colored output

.. option:: --force-color

    Force colored output

    .. note::
        When using colored output the color codes are as follows:

        ``green`` denotes success, ``red`` denotes failure, ``blue`` denotes
        changes and success and ``yellow`` denotes a expected future change in configuration.

.. option:: --state-output=STATE_OUTPUT, --state_output=STATE_OUTPUT

    Override the configured state_output value for minion
    output. One of 'full', 'terse', 'mixed', 'changes' or
    'filter'. Default: 'none'.

.. option:: --state-verbose=STATE_VERBOSE, --state_verbose=STATE_VERBOSE

    Override the configured state_verbose value for minion
    output. Set to True or False. Default: none.

Configuration file options
--------------------------

All the previous options can be provided via the CLI, as in-line arguments, as 
well as configured in the configuration file. There are however options that 
are available only through the configuration file:

.. option:: ``target_use_cache_grains``

    .. versionadded: 2020.3.0

    Whether targeting should look up into the existing cache to compute the 
    list of matching devices. This option may be particularly useful when using 
    one of the following targeting mechanisms: ``-G`` (grain), ``-P`` (grain 
    PCRE), or ``-C`` (compound). Default: ``True`` (it will check the cache).


.. option:: ``target_use_cache_pillar``

    .. versionadded: 2020.3.0

    Whether targeting should look up into the existing cache to compute the 
    list of matching devices. This option may be particularly useful when using 
    one of the following targeting mechanisms: ``-I`` (pillar), ``-J`` (pillar 
    PCRE), or ``-C`` (compound). Default:: ``True`` (it will check the cache).
