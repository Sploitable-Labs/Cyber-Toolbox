#!/bin/bash
key_file=$1
modulus=$(python -c "print int('`openssl rsa -noout -text -inform PEM -pubin -in $key_file|awk '/Exponent/{f=0}f;/Modulus/{f=1}'|tr -d '\n'|sed -e's/ //g' -e's/://g'`',16)")
exponent=$(openssl rsa -noout -text -inform PEM -pubin -in /tmp/public.key|grep Exponent|cut -d' ' -f2)

echo "Get the primte factors (p and q) from: http://www.factordb.com/index.php?query=$modulus"
firefox http://www.factordb.com/index.php?query=$modulus

echo -n "Enter p: "
read p

echo -n "Enter q: "
read q

# Use the rsa tool (https://github.com/ius/rsatool) to generate the private key.
# sudo pip install gmpy pyasn1
# git clone https://github.com/ius/rsatool.git
# cd rsatool
# sudo python ./setup.py install
python /usr/local/bin/rsatool.py -f PEM -o /tmp/private_key.pem -p $p -q $q