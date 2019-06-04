.. _install:

Installation
============

The base installation is pretty much straightforward, ``salt-sproxy`` is 
installable using ``pip``. See 
https://packaging.python.org/tutorials/installing-packages/ for a comprehensive 
guide on the installing Python packages.

Either when installing in a virtual environment, or directly on the base 
system, execute the following:

.. code-block:: bash

    $ pip install salt-sproxy

If you would like to install a specific Salt version, you will firstly need to
instal Salt (via pip) pinning to the desired version, e.g.,

.. code-block:: bash

    $ pip install salt==2018.3.4
    $ pip install salt-sproxy

Easy installation
-----------------

We also provide a script to install the system requirements:
https://raw.githubusercontent.com/mirceaulinic/salt-sproxy/master/install.sh

Usage example:

- Using curl

.. code-block:: bash

    $ curl sproxy-install.sh -L https://raw.githubusercontent.com/mirceaulinic/salt-sproxy/master/install.sh
    # check the contents of sproxy-install.sh
    $ sudo sh sproxy-install.sh

- Using wget

.. code-block:: bash

    $ wget -O sproxy-install.sh https://raw.githubusercontent.com/mirceaulinic/salt-sproxy/master/install.sh
    # check the contents of sproxy-install.sh
    $ sudo sh sproxy-install.sh

- Using fetch (on FreeBSD)

.. code-block:: bash

    $ fetch -o sproxy-install.sh https://raw.githubusercontent.com/mirceaulinic/salt-sproxy/master/install.sh
    # check the contents of sproxy-install.sh
    $ sudo sh sproxy-install.sh

One liner:

.. warning::

    This method can be dangerous and it is not recommended on production systems.

.. code-block:: bash

    $ curl -L https://raw.githubusercontent.com/mirceaulinic/salt-sproxy/master/install.sh | sudo sh

The script ensures Python 3 is installed on your system, together with the 
virtualenv package, and others required for Salt, under a virtual 
environment under the ``$HOME/venvs/salt-sproxy`` path. In fact, when 
executing, you will see that the script will tell where it's going to try to 
install, e.g.,

.. code-block:: bash

    $ sudo sh install.sh

    Installing salt-sproxy under /home/mircea/venvs/salt-sproxy

    Reading package lists... Done
    
    ~~~ snip ~~~

    Installation complete, now you can start using by executing the following command: 
    . /home/mircea/venvs/salt-sproxy/bin/activate

After that, you can start using it:

.. code-block:: bash

    $ . /home/mircea/venvs/salt-sproxy/bin/activate
    (salt-sproxy) $
    (salt-sproxy) $ salt-sproxy -V
    Salt Version:
               Salt: 2019.2.0
        Salt SProxy: 2019.6.0b1

    Dependency Versions:
            Ansible: Not Installed
               cffi: 1.12.3
           dateutil: Not Installed
          docker-py: Not Installed
              gitdb: Not Installed
          gitpython: Not Installed
             Jinja2: 2.10.1
         junos-eznc: 2.2.1
           jxmlease: 1.0.1
            libgit2: Not Installed
           M2Crypto: Not Installed
               Mako: Not Installed
       msgpack-pure: Not Installed
     msgpack-python: 0.6.1
             NAPALM: 2.4.0
           ncclient: 0.6.4
            Netmiko: 2.3.3
           paramiko: 2.4.2
          pycparser: 2.19
           pycrypto: 2.6.1
       pycryptodome: Not Installed
             pyeapi: 0.8.2
             pygit2: Not Installed
           PyNetBox: 4.0.6
              PyNSO: Not Installed
             Python: 3.6.7 (default, Oct 22 2018, 11:32:17)
       python-gnupg: Not Installed
             PyYAML: 5.1
              PyZMQ: 18.0.1
                scp: 0.13.2
              smmap: Not Installed
            textfsm: 0.4.1
            timelib: Not Installed
            Tornado: 4.5.3
                ZMQ: 4.3.1

    System Versions:
               dist: Ubuntu 18.04 bionic
             locale: UTF-8
            machine: x86_64
            release: 4.18.0-20-generic
             system: Linux
            version: Ubuntu 18.04 bionic

Upgrading
---------

To install a newer version, you can execute ``pip install -U salt-sproxy``, 
however this is also going to upgrade your Salt installation. So in case you 
would like to use a specific Salt version, it might be a better idea to install 
the specific salt-sproxy version you want. You can check at 
https://pypi.org/project/salt-sproxy/#history the list of available salt-sproxy 
versions.

Example:

.. code-block:: bash

    $ pip install salt-sproxy==2019.6.0
