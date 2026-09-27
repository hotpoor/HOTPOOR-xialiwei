"""Loopback-only editor: read a private draft, accept ciphertext only; never accept a password."""
import argparse
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import secrets

ROOT = Path(__file__).resolve().parents[1]
FIELDS = {'version', 'algorithm', 'kdf', 'iterations', 'id', 'salt', 'iv', 'ciphertext'}


def validate_envelope(value, record_id):
    if not isinstance(value, dict) or set(value) != FIELDS:
        raise ValueError('Ciphertext fields only')
    if (value['version'] != 1 or value['algorithm'] != 'AES-256-GCM'
            or value['kdf'] != 'PBKDF2-SHA256' or value['iterations'] != 600000
            or value['id'] != record_id):
        raise ValueError('Unsupported envelope')
    for field, length in [('salt', 16), ('iv', 12), ('ciphertext', None)]:
        text = value[field]
        if not isinstance(text, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', text):
            raise ValueError('Invalid encoding')
        decoded = base64.urlsafe_b64decode(text + '=' * (-len(text) % 4))
        if length and len(decoded) != length or field == 'ciphertext' and len(decoded) < 17:
            raise ValueError('Invalid ciphertext')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', required=True)
    parser.add_argument('--draft', type=Path, required=True)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--metadata', type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z0-9-]+', args.id):
        parser.error('Invalid record ID')
    for private in (args.draft.resolve(), args.state.resolve()):
        if private.is_relative_to(ROOT):
            parser.error('Private draft and state must be outside repository')
    from archive_library import Library
    library = Library(ROOT, args.metadata, args.draft, args.state, args.id)
    metadata = json.loads(args.metadata.read_text(encoding='utf-8'))
    metadata = {key: metadata[key] for key in ('title', 'summary', 'date', 'chapter')}
    token = secrets.token_urlsafe(32)
    assets = {'/': ('scripts/private-editor.html', 'text/html'),
              '/editor.css': ('scripts/private-editor.css', 'text/css'),
              '/editor.mjs': ('scripts/private-editor.mjs', 'text/javascript'),
              '/crypto.mjs': ('assets/private-crypto.mjs', 'text/javascript')}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *values):
            pass

        def allowed(self, protected=False):
            if self.headers.get('Host') != address:
                return False
            if self.headers.get('Sec-Fetch-Site') not in (None, 'none', 'same-origin'):
                return False
            if self.headers.get('Origin') not in (None, origin):
                return False
            return not protected or secrets.compare_digest(self.headers.get('X-Editor-Token', ''), token)

        def respond(self, value, content_type='application/json', status=200):
            data = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', content_type + '; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; frame-ancestors 'none'; form-action 'none'; base-uri 'none'")
            self.send_header('Referrer-Policy', 'no-referrer')
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if not self.allowed(self.path in ('/draft', '/envelope', '/records')):
                return self.respond({'error': 'Forbidden'}, status=403)
            if self.path in assets:
                file, mime = assets[self.path]
                return self.respond((ROOT / file).read_bytes(), mime)
            if self.path == '/session':
                return self.respond({'token': token, 'id': library.selected, 'metadata': library.current()['metadata']})
            if self.path == '/draft':
                return self.respond(library.current())
            if self.path == '/records':
                return self.respond({'records': library.listing()})
            if self.path == '/envelope' and library.envelope(library.selected).exists():
                return self.respond(library.envelope(library.selected).read_bytes())
            return self.respond({'error': 'Not found'}, status=404)

        def do_POST(self):
            if self.path not in ('/save', '/save-public', '/select', '/new') or not self.allowed(True) or self.headers.get('Origin') != origin:
                return self.respond({'error': 'Forbidden'}, status=403)
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 2000000:
                    raise ValueError('Size')
                body = json.loads(self.rfile.read(length))
                if self.path == '/select':
                    return self.respond(library.select(body['id']))
                if self.path == '/new':
                    return self.respond(library.create(body.get('mode', 'encrypted')))
                if self.path == '/save-public':
                    if set(body) != {'text', 'metadata'} or not isinstance(body['text'], str) or not body['text'].strip():
                        raise ValueError('Invalid public document')
                    public = body['metadata']
                    if set(public) != {'title', 'summary'} or any(not isinstance(public[k], str) or not 0 < len(public[k]) <= limit for k, limit in [('title', 120), ('summary', 300)]):
                        raise ValueError('Invalid metadata')
                    library.save_public(body['text'], public)
                    return self.respond({'saved': True})
                if library.current()['mode'] != 'encrypted':
                    raise ValueError('Wrong document mode')
                envelope_path = library.envelope(library.selected)
                if set(body) != {'envelope', 'metadata'}:
                    raise ValueError('Ciphertext only')
                envelope = body['envelope']
                validate_envelope(envelope, library.selected)
                public = body['metadata']
                if set(public) != {'title', 'summary'} or any(not isinstance(public[k], str) or not 0 < len(public[k]) <= limit for k, limit in [('title', 120), ('summary', 300)]):
                    raise ValueError('Invalid public metadata')
                envelope_path.parent.mkdir(exist_ok=True)
                temporary = envelope_path.with_suffix('.tmp')
                temporary.write_text(json.dumps(envelope, indent=2) + '\n', encoding='utf-8')
                temporary.replace(envelope_path)
                library.saved(public)
                return self.respond({'saved': True})
            except (ValueError, OSError, TypeError, KeyError):
                return self.respond({'error': 'Ciphertext was not saved'}, status=400)

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    address = '127.0.0.1:' + str(server.server_port)
    origin = 'http://' + address
    if args.state.exists():
        prior = json.loads(args.state.read_text(encoding='utf-8'))
        if prior.get('id') == args.id and prior.get('metadata'):
            metadata.update(prior['metadata'])
    args.state.write_text(json.dumps({'saved': library.envelope(library.selected).exists(), 'id': library.selected, 'url': origin, 'metadata': metadata}), encoding='utf-8')
    print('Local editor ready: ' + origin, flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
