#!/bin/bash

    ###NAGIOS ITEMS###
NAGIOS_SERVER_IP="" #the nagios server IP.
NRPE_PORT=  #update this to whatever works for you - or comment out so that the default port 5666 is
#note that this must, obviously, match the NRPE config in the Nagios server.

    ###DISK CONFIGURATION###
#volume configuration for monitoring the disk space.
root_disk='command[check_disk_1]=/usr/local/nagios/libexec/check_disk -w 6000 -c 3000 -p /dev/sda1' #or vda1 or whatever the root disk is.
#volume1='command[check_disk_2]=/usr/local/nagios/libexec/check_disk -w 6000 -c 3000 -p /dev/sdb'
#volume2='command[check_disk_3]=/usr/local/nagios/libexec/check_disk -w 6000 -c 3000 -p /dev/sdc'
#etc.
DISK_LIST=("$root_disk") #ex: ("$root_disk" "$volume1" "$volume2"). No comma.

    ###VALIDATOR CONFIGURATION###
VALIDATORS='-i cosmos 26657' #for example. You can add multiple validators in the format '-i name port'


    ###PROMETHEUS###
#if you are going to use prometheus, update the below variable and run the prometheus_install.sh script.
prometheus_port=26660 #in config/app.toml, sent prometheus to True and update the port as required.
#prometheus_port1=36660 #if you have multiple validators on the same server
#etc.

PROMETHEUS_PORTS=("$prometheus_port") #ex: ("$prometheus_port" "$prometheus_port1" "$prometheus_port2")