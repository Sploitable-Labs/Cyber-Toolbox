#!/bin/bash

# Run within ./results/{TARGET_IP}/snmp/

for file in $(find *.snmp); do
	cat $file | grep 3.6.1.2.1.4.21.1.7.0.0.0.0 | cut -d' ' -f4;
done
