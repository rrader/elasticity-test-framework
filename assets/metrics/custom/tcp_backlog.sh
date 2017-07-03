#!/bin/sh

collect () {
  report "recv" $(ss -lnt | awk '{print $2}' | grep -v Recv | jq -s 'add')
  report "send" $(ss -lnt | awk '{print $3}' | grep -v Send | jq -s 'add')
}

docs () {
  echo "Send-Q backlog size."
}
