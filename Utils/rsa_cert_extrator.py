################################################################################
#
# Name: rsa_cert_extractor
#
# Author: Autonomoid
#
# Modification date: 2017-02-14
#
# Descriptions:
#  * Extract X.509 SSL certifiactes from a packet capture file.
#  * Facilitate the reconstruction of the private keys.
#
# Licence: GPL2
#
################################################################################

import gmpy2
import pyshark
import sys
import urllib2
from bs4 import BeautifulSoup
from Crypto.PublicKey import RSA
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa

def save_public_key_only(cert, filename):
  f = open(filename, 'wb')
  f.write(cert)
  f.close()

def get_factors(n):
  print "[+] get_factors"
  factors = []
  url = "https://factordb.com/index.php?query=" + str(n)
  resp = urllib2.urlopen(url)
  soup = BeautifulSoup(resp, "lxml", from_encoding=resp.info().getparam('charset'))
  for link in soup.find_all('a', href=True):
    if "index.php?id=" in link.attrs['href']:
      if "..." in link.text:
        id = link.attrs['href'][13:]
        url2 = "https://factordb.com/index.php?showid=" + id
        resp2 = urllib2.urlopen(url2)
        soup2 = BeautifulSoup(resp2, "lxml", from_encoding=resp.info().getparam('charset'))
        factor = int(soup2.find_all('td')[-1].text.replace('\n',''))
        if factor != n:
          factors.append(factor)
      else:
        factor = int(link.text)
        if factor != n:
          factors.append(factor)
  return factors

class rsa_certificate_extractor:

  def extract(self, capture_file):
    print "[+] rsa_certificate_extractor.extract"
    certs = []
    [raw_certs, ip_log] = self.extract_raw_certificates(capture_file)
    for raw_cert, ip in zip(raw_certs, ip_log):
      cert = self.process_raw_certificate(raw_cert, 'der')
      # Extract RSAPublicKey and not DSAPublicKey or EllipticCurvePublicKey.
      if isinstance(cert.public_key(), rsa.RSAPublicKey):
        certs.append(cert)
        save_public_key_only(raw_cert, ip + ".pub")
    return [certs, ip_log]

  def extract_raw_certificates(self, capture_file):
    print "[+] rsa_certificate_extractor.extract_raw_certificates"
    raw_certs = []
    ip_log = []
    cap = pyshark.FileCapture(capture_file, display_filter='ssl.handshake.certificate')
    for pkt in cap:
      src_ip = pkt[1].src
      if src_ip not in ip_log:
        ssl_layer = ''
        for layer in pkt.layers:
          if 'handshake_certificate' in layer.field_names:
            ssl_layer = layer
            raw_cert = ssl_layer.get_field('handshake_certificate')
            raw_certs.append(raw_cert.replace(':','').decode('hex'))
            ip_log.append(src_ip)
    return [raw_certs, ip_log]

  def process_raw_certificate(self, raw_cert, format):
    print "[+] rsa_certificate_extractor.process_raw_certificate"
    if format == 'pem':
      cert = x509.load_pem_x509_certificate(raw_cert, default_backend())
    else:
      cert = x509.load_der_x509_certificate(raw_cert, default_backend())
    return cert


class keypair:
  def __init__(self, cert, ip):
    print "[+] keypair.__init__"
    self.ip = ip
    self.hostname = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
    self.issuer = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
    self.serial_number = str(cert.serial)
    self.valid_from = cert.not_valid_before.isoformat()
    self.valid_until = cert.not_valid_after.isoformat()
    self.key_excess = cert.public_key().key_size % 256
    self.key_length = cert.public_key().key_size - self.key_excess
    self.keypair = RSA.generate(self.key_length)
    self.keypair.n = cert.public_key().public_numbers().n
    self.keypair.e = cert.public_key().public_numbers().e
    factors = get_factors(self.keypair.n)
    if len(factors) > 1:
      self.keypair.p = factors[0]
      self.keypair.q = factors[1]
      self.keypair.d = self.private_exponent(self.keypair.p, self.keypair.q, self.keypair.e)
    else:
      self.keypair.p = '?'
      self.keypair.q = '?'
      self.keypair.d = '?'

  def info(self):
    print "[+] keypair.info"
    print ""
    print "IP: " + self.ip + " (" + self.hostname + ")"
    print "Issuer: " + self.issuer
    print "Serial number: " + self.serial_number
    print "Valid from " + self.valid_from
    print "Valid until " + self.valid_until
    print "Key length: " + str(self.key_length) + " bits"
    if self.key_excess > 0:
      print "Key excess: " + str(self.key_excess) + " bits"
    print "(n = public modulus, e = public exponent, [p, q] = private factors, d = private exponent)"
    print "n = " + str(self.keypair.n)
    print "e = " + str(self.keypair.e)
    print "p = " + str(self.keypair.p)
    print "q = " + str(self.keypair.q)
    print "d = " + str(self.keypair.d)

  def export(self, filename='keypair.pem', format='PEM'):
    print "[+] keypair.export"
    x = self.keypair.exportKey(format)
    f = open(filename,'w')
    f.write(x)
    f.close()

  def set_factors(self, p, q):
    print "[+] keypair.set_factors"
    self.keypair.p = p
    self.keypair.q = q
    self.keypair.d = self.private_exponent(self.keypair.p, self.keypair.q, self.keypair.e)

  def totient(self, p, q):
    print "[+] keypair.totient"
    return (p-1)*(q-1)

  def private_exponent(self, p, q, e):
    print "[+] keypair.private_exponent"
    phi = self.totient(p, q)
    return gmpy2.invert(e, phi)

def main():
  print "[+] main"
  capture_file = sys.argv[1]
  x = rsa_certificate_extractor()
  [certs, ip_log] = x.extract(capture_file)
  for cert, ip in zip(certs, ip_log):
    kp = keypair(cert, ip)
    #p = 0
    #q = 0
    #kp.set_factors(p, q)
    kp.info()
    #kp.export('exported_keypair.pem', 'PEM')

if __name__ == "__main__":
  if len(sys.argv) == 1:
    exit(1)
  main()

