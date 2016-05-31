#!/bin/bash

trap clean_exit SIGINT

function clean_exit() {
    echo "Shutting down..."
    pkill -x -f "python server.py"
    exit 0
}

while [ 1 ]
do
    # start python script and detach
    echo "Starting python server"
    python server.py &
    echo "Python server started as $!"
    # wait until the script is modified
    echo "Waiting for the file to be modified"
    inotifywait -e modify server.py session.py burrow_logging.py
    echo "The file was modified!"
    # send SIGTERM to the script
    echo "Sending SIGTERM to the script"
    pgrep -x -f "python server.py" -l
    kill $!
    echo "Waiting two seconds..."
    sleep 2
    pgrep -x -f "server.py" -l
done

