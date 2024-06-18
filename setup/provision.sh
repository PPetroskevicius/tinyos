#!/usr/bin/env bash

sleep 2

echo "atext,Waiting for NIC.. ,Waiting for NIC ..,Waiting for NIC. ." | nc -U /run/tinybox-screen.sock
while ! ip ad | grep -q enp65s0f0np0; do
  sleep 1
done

echo "text,Found NIC" | nc -U /run/tinybox-screen.sock

bash /opt/tinybox/setup/populateraid.sh
sleep 1

echo "text,RAID Populated,Starting ResNet Train" | nc -U /run/tinybox-screen.sock
sleep 1

sudo systemctl stop tinychat

if ! bash /opt/tinybox/setup/trainresnet.sh; then
  exit 1
fi

sudo systemctl start tinychat
sleep 1

# check that tinychat is up and working

sleep 1
echo "text,Provisioning Complete" | nc -U /run/tinybox-screen.sock
sleep 1
