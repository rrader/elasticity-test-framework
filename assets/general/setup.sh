#!/usr/bin/env bash
set -x

VERSION=1

if [ -f /opt/.is_general_setup.${VERSION} ]
then
    echo "General already set up"
    exit 0
fi

add-apt-repository -y ppa:vbernat/haproxy-1.7
apt-get update --fix-missing
apt-get install -y git jq python3 python3-pip
apt-get install build-essential libssl-dev libffi-dev python3-dev

touch /opt/.is_general_setup.${VERSION}
