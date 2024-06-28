#!/bin/bash
#
# Usage: ./robot_whisperer -s <HTTP_SERVER_IP> -p <HTTP_PORT> [-g] [-h]
#
# Mandatory arguments:
# -s = HTTP server IP address
# -p = HTTP port e.g. 80 or 8080
# 
# Optional arguments:
# -h = help
# -g = Also do GET request on each result using netcat.
#
# Example: ./robot_whisperer 192.168.56.101 80 1 -g
#
# Different robots.txt files have different formats. Please check which is in use.
#
# Format=1:
#
#   User-agent: *
#   Allow:
#   /lame
#   /bar
#   Disallow:
#   /foo
#   /bar
#   /lol
#
# Format=2:
#
#   User-agent: *
#   Allow: /lame
#   Disallow: /foo
#   Disallow: /lol
#   Allow: /catz
#   Disallow: /bar
#

# ASCII art :)
cat robot.txt

# Parse command-line arguments.
IP=
HTTP_PORT=
FORMAT=1
GET=false

# Parse command-line arguments.
while [[ $# -gt 1 ]]
do
key="$1"
  case $key in
    -s|--server)
      IP="$2"
      shift # past argument
      ;;
    -p|--port)
      HTTP_PORT="$2"
      shift # past argument
      ;;
    -g|--get)
      GET=true
      shift # past argument
      ;;
    -h|--help)
      echo "Usage: $0 -s <server_ip> -p <http_port> -f <robots_format> [-g] [-h]"
      exit 0
      ;;
    *)
      # unknown option
    ;;
  esac
  shift # past argument or value
done

echo "Target HTTP server = $IP"
echo "HTTP port          = $HTTP_PORT"
echo "GET results        = $GET"
echo ""

# Get robots.txt.
echo -e "GET /robots.txt HTTP/1.0\r\n" | nc $IP $HTTP_PORT > /tmp/robots.txt

# Get user to select the format of robots.txt.
cat /tmp/robots.txt
echo "Which format is the robots.txt? (1 or 2):"
read FORMAT

# Filter out the disallowed entries.
if [ $FORMAT = '1' ]; then
  cat /tmp/robots.txt | sed -n '/^Disallow:$/ { s///; :a; n; p; ba; }' | cut -d "/" -f 2 > /tmp/robots_disallowed.txt
elif [ $FORMAT = '2' ]; then
  cat /tmp/robots.txt | grep 'Disallow:' | awk '{print $2}'
else
  echo "Invalid format - choose either '1' or '2'."
  exit 1
fi

# Test each entry with dirb.
results=$(dirb http://$IP /tmp/robots_disallowed.txt -S -X /,htm,html,php | grep '200' | sed -e 's/(.*)//g' -e 's/+ //g')

for result in $results
do
  # If the 'get' option is specified then allow request each result with netcat.
  if [ $GET = true ]; then
    echo -e "Requesting '$result' ...\n"
    query=$(echo -e $result | awk -F"$IP" '{print $2}')     
    echo -e "GET $query HTTP/1.0\r\n" | nc $IP $HTTP_PORT
    echo -e "====================================================================="
  else
    echo $result
  fi
done
