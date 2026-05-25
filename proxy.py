"""
KYO 2.0 - Yerel CORS Proxy
Kullanim: python proxy.py
Port: 8765
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.error
import urllib.parse


class CORSProxyHandler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def do_GET(self):
        path = self.path.lstrip('/')

        # /https://... veya /?url=https://... formatini destekle
        if path.startswith('?url='):
            url = urllib.parse.unquote(path[5:])
        elif path.startswith('http'):
            url = path
        else:
            self.send_response(400)
            self._cors()
            self.end_headers()
            self.wfile.write(b'URL gerekli: http://127.0.0.1:8765/https://...')
            return

        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0',
                'Accept': 'application/json, text/csv, text/plain, */*',
                'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
            })
            resp = urllib.request.urlopen(req, timeout=15)
            data = resp.read()

            self.send_response(200)
            self._cors()
            ct = resp.headers.get('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Content-Type', ct)
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        except urllib.error.HTTPError as e:
            body = e.read()
            self.send_response(e.code)
            self._cors()
            self.end_headers()
            self.wfile.write(body)

        except Exception as e:
            self.send_response(502)
            self._cors()
            self.end_headers()
            self.wfile.write(str(e).encode())

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')

    def log_message(self, fmt, *args):
        # Sadece hatalari logla
        if args and str(args[1]) not in ('200', '204'):
            print(f'  [{args[1]}] {args[0]}')


if __name__ == '__main__':
    PORT = 8765
    server = HTTPServer(('127.0.0.1', PORT), CORSProxyHandler)
    print(f'KYO 2.0 CORS Proxy calisiyor -> http://127.0.0.1:{PORT}/')
    print('Durdurmak icin Ctrl+C basin.\n')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nProxy durduruldu.')
