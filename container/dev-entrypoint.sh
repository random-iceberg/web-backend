#!/usr/bin/env bash

function sync() {
    while true; do
        sleep 1
        (
            cd /to_sync
            rsync -a --delete --exclude-from=.dockerignore . /app
        )
        
    done
}

sync &

exec "$@"
