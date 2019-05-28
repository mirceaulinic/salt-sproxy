salt-sproxy 101
===============

This is the first example from the
`Quick Start <https://salt-sproxy.readthedocs.io/en/latest/#quick-start>`__
section of the documentation.

.. raw:: html

  <a href="https://asciinema.org/a/247697" target="_blank"><img src="https://asciinema.org/a/247697.svg" /></a>

Using the Master configuration file under `examples/master 
<https://github.com/mirceaulinic/salt-sproxy/tree/master/examples/master>`__:


``/etc/salt/master``:

.. code-block:: yaml

  pillar_roots:
    base:
      - /srv/salt/pillar

The ``pillar_roots`` option points to ``/srv/salt/pillar``, so to be able to 
use this example, either create a symlink to the ``pillar`` directory in this 
example, or copy the files.
For example, if you just cloned this repository:

.. code-block:: bash

  $ mkdir -p /srv/salt/pillar
  $ git clone git@github.com:mirceaulinic/salt-sproxy.git
  $ cp salt-sproxy/examples/master /etc/salt/master
  $ cp salt-sproxy/examples/101/pillar/*.sls /srv/salt/pillar/

The contents of these two files:

``/srv/salt/pillar/top.sls``:

.. code-block:: yaml

  base:
    mininon1:
      - dummy

``/srv/salt/pillar/dummy.sls``:

.. code-block:: yaml

  proxy:
    proxytype: dummy

Having this setup ready, you can go ahead an execute:

.. code-block:: bash

  $ salt-sproxy minion1 test.ping
  minion1:
      True

  # let's display the list of packages installed via pip on this computer
  $ salt-sproxy minion1 pip.list
  minion1:
      ----------
      Jinja2:
          2.10.1
      MarkupSafe:
          1.1.1
      PyNaCl:
          1.3.0
      PyYAML:
          5.1
      Pygments:
          2.4.0
      asn1crypto:
          0.24.0
      bcrypt:
          3.1.6
      bleach:
          3.1.0
      certifi:
          2019.3.9
      cffi:
          1.12.3
