#/bin/sh

set -e

VENV_PATH=${VENV_PATH:-$HOME/venvs}

printf "\nInstalling salt-sproxy under $VENV_PATH/salt-sproxy\n\n"

mkdir -p $VENV_PATH

if [ -f /etc/debian_version ]; then
# Debian-like
apt-get update
apt-get install -y python3 python3-pip python3-virtualenv python3-zmq gcc
virtualenv -p python3 $VENV_PATH/salt-sproxy
$VENV_PATH/salt-sproxy/bin/pip install salt-sproxy

elif [ -f /etc/centos-release ]; then
# CentOS is always different
yum update -y
yum install -y python36 python36-virtualenv python36-zmq gcc
virtualenv-3.6 $VENV_PATH/salt-sproxy
$VENV_PATH/salt-sproxy/bin/pip3.6 install salt-sproxy

elif [ -f /etc/redhat-release ]; then
# other RedHat
yum update -y
yum install -y python3 python3-virtualenv python3-zmq gcc
virtualenv -p python3 $VENV_PATH/salt-sproxy
$VENV_PATH/salt-sproxy/bin/pip install salt-sproxy

elif [ $(uname) = FreeBSD ]; then
# FreeBSD
pkg update
pkg install -y python36 py36-virtualenv py36-pyzmq gcc
virtualenv-3.6 $VENV_PATH/salt-sproxy
$VENV_PATH/salt-sproxy/bin/pip3.6 install salt-sproxy

elif [ $(uname) = Darwin ]; then
# MacOS
brew update
brew install python3 gcc
pip3 install virtualenv
virtualenv -p python3 $VENV_PATH/salt-sproxy
$VENV_PATH/salt-sproxy/bin/pip3 install salt-sproxy

else
echo 'It looks like your operating system is not currently supported. Please file an issue with the details, or submit a pull request to add it here. Thanks!'

fi

printf "\n Installation complete, now you can start using by executing the following command: \n . $VENV_PATH/salt-sproxy/bin/activate\n\n"
