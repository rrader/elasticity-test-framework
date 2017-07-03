#!/bin/sh

collect () {
  report "allocated" $(cat /proc/sys/fs/file-nr | awk '{print $1}')
  report "max" $(cat /proc/sys/fs/file-nr | awk '{print $3}')
}

docs () {
  echo "Allocated file handles."
}
