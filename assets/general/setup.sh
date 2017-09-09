#!/usr/bin/env bash
set -x

if [ -f /opt/.is_general_setup ]
then
    echo "General already set up"
    exit 0
fi

apt-get update --fix-missing
apt-get install -y git jq python3 python3-pip

touch /opt/.is_general_setup
