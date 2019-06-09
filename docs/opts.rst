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

.. option:: -r, --roster

    The Roster module to use to compile the list of targeted devices.

.. option:: --roster-file

    Absolute path to the Roster file to load (when the Roster module requires 
    a file). Default: ``/etc/salt/roster``.

.. option:: --sync

    Whether should return the entire output at once, or for every device 
    separately as they return.

.. option:: --cache-grains

    Cache the collected Grains. Beware that this option overwrites the existing
    Grains. This may be helpful when using the ``salt-sproxy`` only, but may 
    lead to unexpected results when running in a mixed environment.

.. option:: --cache-pillar

    Cache the collected Pillar. Beware that this option overwrites the existing
    Pillar. This may be helpful when using the ``salt-sproxy`` only, but may 
    lead to unexpected results when running in a mixed environment.

.. option:: --no-cached-grains

    Do not use the cached Grains (i.e., recollect regardless).

.. option:: --no-cached-pillar

    Do not use the cached Pillar (i.e., recompile regardless).

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

.. option:: --preview-target

    Show the devices expected to match the target, without executing any 
    function (i.e., just print the list of devices matching, then exit).

.. option:: --sync-roster

    Synchronise the Roster modules (both salt-sproxy native and provided by the
    user in their own environment). Default: ``True``.

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

.. option:: --grain-pcre

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
        If using ``--out=json``, you will probably want ``--sync`` as well.
        Without the sync option, you will get a separate JSON string per minion
        which makes JSON output invalid as a whole.
        This is due to using an iterative outputter. So if you want to feed it
        to a JSON parser, use ``--sync`` as well.

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

