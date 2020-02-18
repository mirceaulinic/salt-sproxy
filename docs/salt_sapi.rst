.. _salt-sapi:

salt-sapi
=========

.. versionadded:: 2020.2.0

``salt-sapi`` is a program distributed together with *salt-sproxy*, to 
ease the usage of the Salt API by providing two additional clients: ``sproxy`` 
and ``sproxy_async``.

The usage is the exact same as the native ``salt-api`` entry point, just 
enhanced with the mentioned clients for the ``/run`` URI.

See :ref:`salt-api` or 
https://salt-sproxy.readthedocs.io/en/latest/salt_api.html for more details and 
usage examples.

.. important::

    At the time being, ``salt-sapi`` is simply available as a Python program 
    entry point, without providing the system service files. That said, in 
    order for you to use the *salt-sapi* clients, you wlll need to provide 
    a service file or edit the one you might have for ``salt-api`` already by 
    configuring the path to ``salt-sapi`` (run ``$ which salt-sapi`` to find 
    the installation path), e.g., ``ExecStart=/usr/local/bin/salt-sapi``.


Example - start ``salt-sapi`` in debug mode:

.. code-block:: bash

    $ salt-sapi -l debug

See the complete list of options by executing ``salt-sapi --help``:

.. code-block:: bash

    $ salt-sapi --help
    Usage: salt-sapi [options]
    salt-sapi is an enhanced Salt API system that provides additional sproxy and
    sproxy_async clients, to simplify the usage of salt-sproxy through the Salt
    REST API

    Options:
      --version             show program's version number and exit
      -V, --versions-report
                            Show program's dependencies version number and exit.
      -h, --help            show this help message and exit
      -c CONFIG_DIR, --config-dir=CONFIG_DIR
                            Pass in an alternative configuration directory.
                            Default: '/etc/salt'.
      -d, --daemon          Run the salt-sapi as a daemon.
      --pid-file=PIDFILE    Specify the location of the pidfile. Default:
                            '/var/run/salt-sapi.pid'.

      Logging Options:
        Logging options which override any settings defined on the
        configuration files.

        -l LOG_LEVEL, --log-level=LOG_LEVEL
                            Console logging log level. One of 'all', 'garbage',
                            'trace', 'debug', 'profile', 'info', 'warning',
                            'error', 'critical', 'quiet'. Default: 'warning'.
        --log-file=API_LOGFILE
                            Log file path. Default: '/var/log/salt/api'.
        --log-file-level=LOG_LEVEL_LOGFILE
                            Logfile logging log level. One of 'all', 'garbage',
                            'trace', 'debug', 'profile', 'info', 'warning',
                            'error', 'critical', 'quiet'. Default: 'warning'.

    You can find additional help about salt-sapi issuing "man salt-sapi" or on
    https://salt-sproxy.readthedocs.io and
    https://docs.saltstack.com/en/latest/ref/cli/salt-api.html.
