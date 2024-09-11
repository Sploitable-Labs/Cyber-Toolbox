import base64

with open('web_shell.py', 'r') as file:
    data = file.read().strip()

    key = 42
    xor_encoded_data = bytearray([b ^ key for b in data.encode('utf-8')])

    base64_encoded_xor = base64.b64encode(xor_encoded_data)

    with open('encoded_shell.txt', 'w') as output_file:
        output_file.write(base64_encoded_xor.decode())