#!/bin/sh

set -eu

# This test requires the jq package in order to execute correctly.

LOG_LEVEL=${SALT_LOG_LEVEL:-error}
export SALT_CONFIG_DIR=$PWD
export SALT_ROSTER_FILE=$PWD/roster
export SALT_SPROXY_PATH=$(salt-sproxy --installation-path)

mkdir -p /tmp/sproxy-run/cache \
         /tmp/sproxy-run/log \
         /tmp/sproxy-run/pki \
         /tmp/sproxy-run/master \
         /tmp/sproxy-run/extmods

echo "Starting a Salt Master"
salt-master --pid-file /tmp/sproxy-run/salt-master.pid -l $LOG_LEVEL &
echo "Starting the Salt SAPI"
salt-sapi --pid-file /tmp/sproxy-run/salt-api.pid -l $LOG_LEVEL &
echo "Syncing the sproxy Runner"
salt-run saltutil.sync_runners

echo "Roster processing correctly with --preview-target"
salt-sproxy \* --preview --out=json | jq -e '. | length == 105'

echo "Grain targeting from Roster"
salt-sproxy -G role:router --preview --out=json | jq -e '. == ["router1", "router2"]'

echo "Grain targeting from Master config file"
salt-sproxy -G salt:role:proxy --preview --out=json | jq -e '. | length == 105'

echo "test.ping against the entire pool"
salt-sproxy \* test.ping -p --static --out=json | jq -e '. | length == 105'

echo "Test invasive targeting"
# the nodename Grain is collected only on Minion startup, which helps validate
# whether the --invasive-targeting works well
salt-sproxy -G nodename:$(hostname) test.ping --invasive-targeting --cache-grains -p --static --out=json | jq -e '. | length == 105'

echo "Test targeting using cached grains"
# The exact query as above, now targeting using the cached Grains (saved earlier
# through the --cache-grains option from the previous run).
salt-sproxy -G nodename:$(hostname) test.ping -p --static --out=json | jq -e '. | length == 105'

echo "Test execution through the salt-sapi"
curl -sS localhost:8080/run -H 'Accept: application/json' \
     -d eauth='auto' \
     -d username='test-usr' \
     -d password='pass' \
     -d client='sproxy' \
     -d tgt='role:router' \
     -d tgt_type='grain' \
     -d fun='test.ping' | jq '.["return"][0] | length == 2'

kill -9 $(cat /tmp/sproxy-run/salt-api.pid)
kill -9 $(cat /tmp/sproxy-run/salt-master.pid)

echo "Done."
