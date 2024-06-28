#!/bin/bash

hosts_file=$1
nmap -Pn -sU -p161 -iL $hosts_file --open -oG hosts.snmp.temp
cat hosts.snmp.temp | grep Ports: | cut -d' ' -f2 > hosts.snmp
rm hosts.snmp.temp
