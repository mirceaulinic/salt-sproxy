.. _runner:

The Proxy Runner
================

The :ref:`proxy-runner` is the core functionality of ``salt-sproxy`` and can be
used to trigger jobs in response to :ref:`events`, or invoked when
:ref:`salt-api`.

In both cases mentioned above you are going to need to have a Salt Master 
running, that allows you to set up the Reactors and the Salt API; that means, 
the ``proxy`` Runner needs to be available on your Master. To do so, you have 
two options:

1. Reference it from the salt-sproxy installation
-------------------------------------------------

After installing salt-sproxy, you can execute the following command:

.. code-block:: bash

    $ salt-sproxy --file-roots
    salt-sproxy is installed at: /home/mircea/venvs/salt-sproxy/lib/python3.6/site-packages/salt_sproxy

    You can configure the file_roots on the Master, e.g.,

    file_roots:
      base:
        - /home/mircea/venvs/salt-sproxy/lib/python3.6/site-packages/salt_sproxy

    Or only for the Runners:

    runner_dirs:
      - /home/mircea/venvs/salt-sproxy/lib/python3.6/site-packages/salt_sproxy/_runners

As suggested in the output, you can directly reference the salt-sproxy 
installation path to start using the ``proxy`` Runner (and other extension 
modules included in the package).

2. Copy the source file
-----------------------

You can either download it from 
https://github.com/mirceaulinic/salt-sproxy/blob/master/salt_sproxy/_runners/proxy.py,
e.g., if your ``file_roots`` configuration on the Master looks like:

.. code-block:: yaml

    file_roots:
      base:
        - /srv/salt

You are going to need to create a directory under ``/srv/salt/_runners``, then 
download the ``proxy`` Runner there:

.. code-block:: bash

    $ mkdir -p /srv/salt/_runners
    $ curl -o /srv/salt/_runners/proxy.py -L \
      https://raw.githubusercontent.com/mirceaulinic/salt-sproxy/master/salt_sproxy/_runners/proxy.py

.. note::

    In the above I've used the *raw* like from GitHub to ensure the source code 
    is preserved.

Alternatively, you can also put it under an arbitrary path, e.g., 
(configuration on the Master)

.. code-block:: yaml

    runner_dirs:
      - /path/to/runners

Downloading the ``proxy`` Runner under that specific path:

.. code-block:: bash

    $ curl -o /path/to/runners/proxy.py -L \
      https://raw.githubusercontent.com/mirceaulinic/salt-sproxy/master/salt_sproxy/_runners/proxy.py
