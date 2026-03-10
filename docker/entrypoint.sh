#!/bin/bash

#disable event substitution so we can have ! in vars
set +H

#to exec a different entry point, use syntax like: docker run --entrypoint /bin/sh
function exec_script {
    #execute python code, with any docker run cli options
    echo "** Running entrypoint command: ${script} with $# params"
    echo "-------------------------------------------------------"
    echo
    eval ${script}
}

#check out project name and format as a script
if [ -z "${script}" ]; then
    echo "** No project file specified, exiting." && exit
fi

#if env_vars is set in environment, then extract them to CLI
auto_params=""
if [ ! -z "${env_vars}" ]; then
    echo "** Found env_vars: ${env_vars}, converting to cli options."
    for v in ${env_vars//,/ }
    do
        #build a cli arg
        temp="--$v ${!v}"
        #match against underscore to find store-only args
        case $v in _*)
            #echo "V ${!v}"
            temp="${!v}"
        esac
        #append to our list
        auto_params="$auto_params $temp"
    done
fi

#if runonce_*.sh exists, run it in this context (with env vars)
for runonce in runonce_*.sh; do
    if [ -e "$runonce" ]; then
        source $runonce
    fi
done

#start our heartbeat script
if [ ! -z "${heartbeat_url}" ] && [ ! -z "${heartbeat_sec}" ]; then
    echo "** Setup heartbeat at ${heartbeat_sec}s freq to ${heartbeat_url}"
    nohup ./heartbeat.sh $heartbeat_sec $heartbeat_url $heartbeat_key &
fi

service_start=$(date +%s)
#figure out if we're doing a single run or a service
if [ -z "$service_timer" ]; then
    #if not service, run once
    exec_script $@ $auto_params
else
    echo "** Launching as service, polling each ${service_timer}s with limit of ${service_limit}s"
    while true; do
        start=$(date +%s)
        #run the script
        exec_script $@ $auto_params
        end=$(date +%s)
        dur=$((end-start))
        sleep=$((service_timer-dur))
        total=$((end-service_start+sleep))
        if [ ! -z "$service_limit" ] && [ "$service_limit" -gt "0" ] && [ "$total" -ge "$service_limit" ]; then
            echo "** Hit service runtime limit of ${service_limit}s, exiting."
            exit
        else
            echo "** Completed service run in ${dur}s, target of ${service_timer}s, sleeping for ${sleep}s.  Total run: ${total}s"
            [ "$sleep" -gt "0" ] && sleep $sleep
        fi
    done
fi
