#!/bin/sh

start () {
    readonly divisor=$(($INTERVAL * 1024))

    get_nonvol_cs () {
        grep "^nonvoluntary_ctxt_switches:" /proc/*/status | awk '{ print $2 }' | jq -s 'add'
    }

    get_vol_cs () {
        grep "^voluntary_ctxt_switches:" /proc/*/status | awk '{ print $2 }' | jq -s 'add'
    }

    calc_csps() {
        echo $1 $2 | awk -v divisor=$divisor \
                     '{ printf "%.2f", ($1 - $2) / divisor }'
    }
}


collect () {
    local sample
    nonvol_cs=$(get_nonvol_cs)
    vol_cs=$(get_vol_cs)
    if [ ! -z "$prev_nonvol" ]; then
        report "nonvol" $(calc_csps ${nonvol_cs} ${prev_nonvol})
    fi
    if [ ! -z "$prev_vol" ]; then
        report "vol" $(calc_csps ${vol_cs} ${prev_vol})
    fi
    if [ ! -z "$prev_nonvol" -a ! -z "$prev_vol" ]; then
        report "sum" $(echo $(calc_csps ${vol_cs} ${prev_vol}) $(calc_csps ${nonvol_cs} ${prev_nonvol}) \
                        awk -v divisor=$divisor '{ printf "%.2f", $1 + $2 }')
    fi
    prev_nonvol="$nonvol_cs"
    prev_vol="$vol_cs"
}

docs () {
  echo "Context switches per second."
}
