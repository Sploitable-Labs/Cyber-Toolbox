#!/bin/bash
##
## Name: BirdNest
##
## Author: Autonomoid
##
## Last modified: 2017-01-20
##
## Licence:
##    This program is free software: you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation, either version 3 of the License, or
##    (at your option) any later version.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
## Description: dirb nested twice (2 layers).
##
## Example: ./birdnest 10.45.115.42
##

## HTTP Status Codes (https://httpstatuses.com/):
## 200 = OK
## 302 = Found (redirection)
## 403 = Forbidden

IP=$1
EXTENSIONS="/,.htm,.html,.php"

echo "[+] Scanning with generic wordlist ..."
cp /usr/share/dirb/wordlists/big.txt /tmp/wordlist
WORDLIST=/tmp/wordlist
results=$(dirb http://$IP $WORDLIST -S -X $EXTENSIONS | grep $IP/. | grep -v 'Scanning' | grep -v '404' | sed -e 's/(.*)//g' -e 's/+ //g')

for result in $results
do
  echo $result
done

echo "[+] Using first round of results to harvest words for new wordlist ..."
for result in $results
do
  wget http://$IP/$result -rq -O /tmp/result.out
  html2dic /tmp/result.out | sort -u >> /tmp/result.dict
done
uniq /tmp/result.dict > /tmp/wordlist

echo "[+] Scanning with the new wordlist ..."
results2=$(dirb http://$IP $WORDLIST -S -X $EXTENSIONS | grep $IP/. | grep -v 'Scanning' | grep -v '404' | sed -e 's/(.*)//g' -e 's/+ //g')

for result in $results2
do
  echo $result
done
