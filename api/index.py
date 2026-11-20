import os
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url_path = self.path.split('?')[0]
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        if url_path in ('', '/'):
            target = os.path.join(base_dir, 'index.html')
        else:
            target = os.path.join(base_dir, url_path.lstrip('/'))
            
        if os.path.exists(target) and os.path.isfile(target):
            self.send_response(200)
            if target.endswith('.html'):
                self.send_header('Content-Type', 'text/html; charset=utf-8')
            elif target.endswith('.css'):
                self.send_header('Content-Type', 'text/css')
            elif target.endswith('.js'):
                self.send_header('Content-Type', 'application/javascript')
            elif target.endswith('.png'):
                self.send_header('Content-Type', 'image/png')
            elif target.endswith(('.jpg', '.jpeg')):
                self.send_header('Content-Type', 'image/jpeg')
            self.end_headers()
            with open(target, 'rb') as f:
                self.wfile.write(f.read())
        else:
            index_path = os.path.join(base_dir, 'index.html')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            with open(index_path, 'rb') as f:
                self.wfile.write(f.read())

app = handler
