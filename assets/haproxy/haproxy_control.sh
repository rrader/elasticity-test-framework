#!/usr/bin/env bash

# $1 should contain num. of server entries should be uncommented

HAPROXY=/etc/haproxy/haproxy.cfg

echo Set servers number to $1

sed -i.bak -r 's/^( +)(server .*)$/\1#\2/g' ${HAPROXY}

for i in `seq 1 $1`
do
    sed -i.bak -r '0,/^ +#server/ s/^( +)#(server .*)$/\1\2/' ${HAPROXY}
done

service haproxy reload

echo Done
