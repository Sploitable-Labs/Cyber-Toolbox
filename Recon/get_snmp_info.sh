#!/bin/bash

hosts_file=$1

for host in $(cat $hosts_file); do
	for oui in $(cat ./lists/snmp_mib_oui | cut -d' ' -f1); do
		snmpwalk -c public -v2c $host $oui >> $host.snmp;
	done
done

# Delete empty files (no results returned)
find $PWD -size  0 -print0 | xargs -0 rm
