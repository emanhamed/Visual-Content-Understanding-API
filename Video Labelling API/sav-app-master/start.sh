#!/bin/bash

sudo echo "Start Redis Server"
sudo redis-server &
REDIS_PID=`expr $! + 2`
echo $REDIS_PID
sails lift &
SAILS_PID=`expr $! + 2`
echo $SAILS_PID

echo "waiting for CTRL-C"
while :
do
	sleep 1
done
