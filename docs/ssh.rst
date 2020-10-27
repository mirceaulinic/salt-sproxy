.. _ssh:

Managing remote Unix and Windows machines via SSH
=================================================

.. versionadded:: 2020.7.0

Using *salt-sproxy*, besides regular Minions, regular Proxy Minions, and 
standalone Proxy Minions (managed by *salt-sproxy* itself), you can also manage 
arbitrary machines via SSH, in the same way as you'd normally do through 
`salt-ssh <https://docs.saltstack.com/en/latest/topics/ssh/>`__. In fact, this
is actually done through the :ref:`ssh-proxy` shipped together with this 
package, which in turn invokes *salt-ssh* internals. While *salt-ssh* has 
been part of the Salt suite for years, it has always been decoupled from the 
rest. One of the evident implications is that you manage some devices by 
running ``salt``, and others by running ``salt-ssh``. *salt-sproxy* aims to 
abstract that away, and provide a single, uniform methodology for managing 
whatever flavours of Salt you want, through the same command and offering the 
same features.

In essence, using the :ref:`ssh-proxy`, *salt-sproxy* spins up a temporary 
Proxy Minion locally, which means you can use it to manage arbitrary machines 
over SSH, and you can continue using the usual :ref:`targeting` mechanisms, or
execute Salt commands over the REST API (see also :ref:`salt-sapi`).

.. important::

    As this feature depends on two external modules, provides with 
    *salt-sproxy*, you will need to make sure your installation is aware of 
    those. You ave multiple options here:

    - Execute passing the ``--sync-proxy`` and ``--sync-executors`` on the 
      command line.
    - Set ``sync_proxy: true`` and ``sync_executors: true`` in the Master 
      config file.
    - Configure the ``file_roots`` on the Master, as detailed in :ref:`runner`, 
      then execute ``salt-run saltutil.sync_all`` (or 
      ``saltutil.sync_proxymodules`` + ``saltutil.sync_executors``, if you only
      want the SSH code, ignorning anything else). See also 
      :ref:`best-practices`.

Pillar
------

The configuration is aligned to the general Proxy Minion standards: put the
connection details and credentials under the ``proxy`` key in the Proxy config
or Pillar.

.. important:

    Local (i.e., per Proxy) option override the global configuration or CLI
    options.

``host``
    The IP address or the hostname of the remove machine to manage.

``port``
    Integer, the port number to use when establishing he connection
    (defaults to 22).

``user``
    The username required for authentication.

``passwd``
    The password used for authentication.

``priv``
    Absolute path to the private SSH key used for authentication.

``priv_passwd``
    The SSH private key password.

``timeout``: 30
    The SSH timeout. Defaults to 30 seconds.

``sudo``: ``False``
    Execute commands as sudo.

``tty``: ``False``
    Connect over tty.

``sudo_user``
    The username that should execute the commands as sudo.

``remote_port_forwards``
    Enable remote port forwarding. Example: ``8888:my.company.server:443``.
    Multiple remote port forwardings are supported, using comma-separated
    values, e.g., ``8888:my.company.server:443,9999:my.company.server:80``.

``identities_only``: ``False``
    Execute SSH with ``-o IdentitiesOnly=yes``. This option is intended for
    situations where ssh-agent offers many different identities and allow ssh
    to ignore those identities and use the only one specified in options.

``ignore_host_keys``: ``False``
    By default ssh host keys are honored and connections will ask for approval.
    Use this option to disable ``StrictHostKeyChecking``.

``no_host_keys``: ``False``
    Fully ignores ssh host keys which by default are honored and connections
    would ask for approval. Useful if the host key of a remote server has
    changed and would still error with ``ignore_host_keys``.

``winrm``: ``False``
    Flag that tells Salt to connect to a Windows machine. This option requires
    the ``saltwinshell`` to be installed.

For example, let's say you put the following in the Pillar:

``/srv/salt/pillar/ssh.sls``

.. code-block:: yaml

  proxy:
    proxytype: ssh
    host: srv.example.com
    user: test
    passwd: test

``/srv/salt/pillar/top.sls``

.. code-block:: yaml

  base:
    srv:
      - ssh

Assuming that your configuration is correct, you can then start executing Salt
commands as usual, to manage the remote machine:

.. code-block:: bash

  $ salt-sproxy 'srv' pkg.install ack
  srv:
      ----------
      ack:
          ----------
          new:
              2.24-1
          old:
      libfile-next-perl:
          ----------
          new:
              1.16-2
          old:
      libgdbm-compat4:
          ----------
          new:
              1.18.1-4
          old:
      libgdbm6:
          ----------
          new:
              1.18.1-4
          old:
      libperl5.28:
          ----------
          new:
              5.28.1-6
          old:
      perl:
          ----------
          new:
              5.28.1-6
          old:
      perl-modules-5.28:
          ----------
          new:
              5.28.1-6
          old:

  $ salt-sproxy 'srv' state.apply
  srv:
  ----------
            ID: vim
      Function: pkg.installed
        Result: True
       Comment: All specified packages are already installed
       Started: 16:38:22.981459
      Duration: 57.998 ms
       Changes:   
  ----------
            ID: ack
      Function: pkg.installed
        Result: True
       Comment: All specified packages are already installed
       Started: 16:38:23.039783
      Duration: 42.267 ms
       Changes:   

  Summary for sproxy
  ------------
  Succeeded: 2
  Failed:    0
  ------------
  Total states run:     2
  Total run time: 100.265 ms
