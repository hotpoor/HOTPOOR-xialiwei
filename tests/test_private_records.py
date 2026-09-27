import base64
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('private_editor', ROOT / 'scripts/private-editor.py')
editor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(editor)


def fixture():
    b64 = lambda data: base64.urlsafe_b64encode(data).decode().rstrip('=')
    return {'version': 1, 'algorithm': 'AES-256-GCM', 'kdf': 'PBKDF2-SHA256', 'iterations': 600000,
            'id': 'test-fixture', 'salt': b64(bytes(16)), 'iv': b64(bytes(12)), 'ciphertext': b64(bytes(20))}


class PrivateRecordTests(unittest.TestCase):
    def test_supported_envelope(self):
        editor.validate_envelope(fixture(), 'test-fixture')

    def test_reject_plaintext_password_and_unknown_fields(self):
        for field in ('password', 'plaintext', 'key', 'body'):
            with self.assertRaises(ValueError):
                editor.validate_envelope({**fixture(), field: 'not allowed'}, 'test-fixture')

    def test_reject_invalid_parameters_and_wrong_record(self):
        for field, value in [('version', 2), ('iterations', 1), ('id', 'other'), ('salt', 'AA'), ('iv', 'AA'), ('ciphertext', 'AA')]:
            with self.assertRaises(ValueError):
                editor.validate_envelope({**fixture(), field: value}, 'test-fixture')

    def test_no_client_or_authoring_service_in_public_build(self):
        self.assertFalse((ROOT / '_site/scripts/private-editor.html').exists())
        self.assertFalse((ROOT / '_site/.local').exists())
        self.assertFalse((ROOT / '_site/desktop').exists())


if __name__ == '__main__':
    unittest.main()
