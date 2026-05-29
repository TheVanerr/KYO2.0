"""
KYO 2.0 - Yerel CORS Proxy  (Yahoo Finance crumb destekli)
Kullanim: python proxy.py
Port: 8765

Ozellikler:
  - Genel CORS proxy: GET /https://...
  - /hisse-batch?syms=SYM1,SYM2,...  →  Yahoo Finance ile 606 hisseyi crumb+cookie ile ceker
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.error
import urllib.parse
import http.cookiejar
import threading
import time
import json
import re
import os

# ── Yahoo Finance crumb cache ─────────────────────────────────────
_yahoo_lock    = threading.Lock()
_yahoo_crumb   = None
_yahoo_cookies = None  # CookieJar
_yahoo_opener  = None
_yahoo_ts      = 0
_CRUMB_TTL     = 3600  # 1 saat

_BASE_HEADERS = {
    'User-Agent':      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept':          'application/json, text/plain, */*',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'identity',
    'Referer':         'https://finance.yahoo.com/',
    'Origin':          'https://finance.yahoo.com',
}


def _get_yahoo_session():
    """Yahoo Finance cookie + crumb alir; 1 saat cache'ler."""
    global _yahoo_crumb, _yahoo_cookies, _yahoo_opener, _yahoo_ts

    with _yahoo_lock:
        if _yahoo_crumb and (time.time() - _yahoo_ts) < _CRUMB_TTL:
            return _yahoo_crumb, _yahoo_opener

        print('  [yahoo] Yeni crumb aliniyor...')
        jar    = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

        # 1. fc.yahoo.com → temel cookie seti
        try:
            req = urllib.request.Request('https://fc.yahoo.com', headers=_BASE_HEADERS)
            opener.open(req, timeout=10)
        except Exception:
            pass

        # 2. finance.yahoo.com → A1/GUC cookie
        try:
            req = urllib.request.Request('https://finance.yahoo.com', headers=_BASE_HEADERS)
            opener.open(req, timeout=10)
        except Exception:
            pass

        # 3. Crumb al
        crumb = None
        for endpoint in [
            'https://query1.finance.yahoo.com/v1/test/getcrumb',
            'https://query2.finance.yahoo.com/v1/test/getcrumb',
        ]:
            try:
                req = urllib.request.Request(endpoint, headers=_BASE_HEADERS)
                resp = opener.open(req, timeout=10)
                crumb = resp.read().decode('utf-8').strip()
                if crumb and crumb != 'null' and len(crumb) > 2:
                    break
            except Exception:
                pass

        if not crumb:
            print('  [yahoo] UYARI: crumb alinamadi, cookie olmadan denenecek.')
            crumb = ''

        _yahoo_crumb   = crumb
        _yahoo_opener  = opener
        _yahoo_cookies = jar
        _yahoo_ts      = time.time()
        print(f'  [yahoo] crumb OK ({crumb[:12]}...)')
        return crumb, opener


def _yahoo_quote_batch(symbols):
    """
    Yahoo Finance v7/finance/quote ile bir sembol listesini sorgular.
    Geri donus: { 'SYM': {price, change, changePct, volume, time}, ... }
    """
    crumb, opener = _get_yahoo_session()
    url = (
        'https://query1.finance.yahoo.com/v7/finance/quote'
        f'?symbols={",".join(s + ".IS" for s in symbols)}'
        f'&crumb={urllib.parse.quote(crumb)}'
    )
    req  = urllib.request.Request(url, headers=_BASE_HEADERS)
    resp = opener.open(req, timeout=20)
    raw  = json.loads(resp.read().decode('utf-8'))

    result = {}
    for item in (raw.get('quoteResponse') or {}).get('result') or []:
        sym = re.sub(r'\.IS$', '', item.get('symbol', ''), flags=re.IGNORECASE)
        price = item.get('regularMarketPrice')
        if price is None:
            continue
        result[sym] = {
            'symbol':    sym,
            'shortName': item.get('shortName') or item.get('longName') or sym,
            'longName':  item.get('longName')  or item.get('shortName') or sym,
            'regularMarketPrice':         price,
            'regularMarketChange':        item.get('regularMarketChange', 0),
            'regularMarketChangePercent': item.get('regularMarketChangePercent', 0),
            'regularMarketVolume':        item.get('regularMarketVolume', 0),
            'regularMarketTime':          item.get('regularMarketTime'),
        }
    return result


# ── HTTP Handler ──────────────────────────────────────────────────
class CORSProxyHandler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def do_GET(self):
        path = self.path.split('?')[0].rstrip('/')

        # ── Statik dosya sunumu ───────────────────────────────────
        static_map = {
            '':           'kyo20.html',
            '/':          'kyo20.html',
            '/index.html':'index.html',
            '/kyo20.html':'kyo20.html',
        }
        if path in static_map or self.path in static_map:
            filename = static_map.get(path) or static_map.get(self.path)
            filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
            try:
                with open(filepath, 'rb') as f:
                    data = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(data)))
                self._cors()
                self.end_headers()
                self.wfile.write(data)
            except FileNotFoundError:
                self.send_response(404)
                self._cors()
                self.end_headers()
                self.wfile.write(b'Dosya bulunamadi')
            return

        path = self.path

        # ── Ozel endpoint: /hisse-batch?syms=... ─────────────────
        if path.startswith('/hisse-batch'):
            self._handle_hisse_batch(path)
            return

        path = path.lstrip('/')

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

        # Yahoo Finance URL'lerini crumb ile proxy'le
        if 'finance.yahoo.com' in url:
            self._proxy_yahoo(url)
        else:
            self._proxy_generic(url)

    def _handle_hisse_batch(self, path):
        """GET /hisse-batch?syms=SYM1,SYM2,...  →  JSON"""
        qs   = urllib.parse.parse_qs(urllib.parse.urlparse(path).query)
        syms_raw = qs.get('syms', [''])[0]
        symbols  = [s.strip().upper() for s in syms_raw.split(',') if s.strip()]

        if not symbols:
            self._json_error(400, 'syms parametresi bos')
            return

        try:
            data = _yahoo_quote_batch(symbols)
            body = json.dumps(data, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self._cors()
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except urllib.error.HTTPError as e:
            body_err = e.read()
            # crumb süresi dolmuş olabilir — sıfırla ve bir daha dene
            if e.code in (401, 403):
                global _yahoo_ts
                _yahoo_ts = 0
                try:
                    data = _yahoo_quote_batch(symbols)
                    body = json.dumps(data, ensure_ascii=False).encode('utf-8')
                    self.send_response(200)
                    self._cors()
                    self.send_header('Content-Type', 'application/json; charset=utf-8')
                    self.send_header('Content-Length', str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                except Exception:
                    pass
            self._json_error(e.code, body_err.decode('utf-8', errors='replace'))
        except Exception as e:
            self._json_error(502, str(e))

    def _proxy_yahoo(self, url):
        """Yahoo Finance URL'sini crumb + cookie ile proxy'le."""
        try:
            crumb, opener = _get_yahoo_session()
            sep = '&' if '?' in url else '?'
            if 'crumb=' not in url:
                url = url + sep + 'crumb=' + urllib.parse.quote(crumb)
            req  = urllib.request.Request(url, headers=_BASE_HEADERS)
            resp = opener.open(req, timeout=20)
            data = resp.read()
            self.send_response(200)
            self._cors()
            ct = resp.headers.get('Content-Type', 'application/json')
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

    def _proxy_generic(self, url):
        """Genel URL proxy'leme."""
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent':      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0',
                'Accept':          'application/json, text/csv, text/plain, */*',
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

    def _json_error(self, code, msg):
        body = json.dumps({'error': msg}, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self._cors()
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')

    def log_message(self, fmt, *args):
        if args and str(args[1]) not in ('200', '204'):
            print(f'  [{args[1]}] {args[0]}')


if __name__ == '__main__':
    PORT = 8765
    server = HTTPServer(('127.0.0.1', PORT), CORSProxyHandler)
    print(f'KYO 2.0 CORS Proxy (crumb destekli) calisiyor -> http://127.0.0.1:{PORT}/')
    print('Endpoints:')
    print(f'  GET http://127.0.0.1:{PORT}/https://...            (genel proxy)')
    print(f'  GET http://127.0.0.1:{PORT}/hisse-batch?syms=...   (Yahoo Finance + crumb)')
    print('Durdurmak icin Ctrl+C basin.\n')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nProxy durduruldu.')
