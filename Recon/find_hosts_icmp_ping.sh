#!/bin/bash

# Example: ./find_hosts_icmp_ping.sh 10.0.0.1

target_subnet=$1
nmap -sn $target_subnet/24 -oG hosts.temp
cat hosts.temp | grep Host: | cut -d' ' -f2  > hosts
rm hosts.temp
