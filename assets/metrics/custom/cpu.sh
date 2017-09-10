#!/bin/bash


collect () {
    # Get the total CPU statistics, discarding the 'cpu ' prefix.
    CPU="`sed -n 's/^cpu\s//p' /proc/stat`"
    IDLE="`echo $CPU | awk '{print $4}'`"


    # Calculate the total CPU time.
    TOTAL="`echo $CPU | tr ' ' '+' | bc`"

    if [ ! -z "$PREV_TOTAL" ]; then
        # Calculate the CPU usage since we last checked.
        DIFF_IDLE="$(($IDLE-$PREV_IDLE))"
        DIFF_TOTAL="$(($TOTAL-$PREV_TOTAL))"
        DIFF_USAGE="$(( (1000*($DIFF_TOTAL-$DIFF_IDLE)/$DIFF_TOTAL+5)/10 ))"

        report $DIFF_USAGE
    fi

    # Remember the total and idle CPU times for the next check.
    PREV_TOTAL="$TOTAL"
    PREV_IDLE="$IDLE"
}

docs () {
  echo "CPU percent usage per second"
}
