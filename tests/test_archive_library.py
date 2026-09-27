import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('archive_library', Path(__file__).resolve().parents[1] / 'scripts/archive_library.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class LibraryTests(unittest.TestCase):
    def test_migration_switching_and_isolated_document_state(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = base / 'repo'
            (root / 'content/stories').mkdir(parents=True)
            (root / 'content/encrypted').mkdir()
            (root / 'content/catalog.json').write_text(json.dumps({'entries': []}))
            private = base / 'private'
            private.mkdir()
            draft = private / 'first.md'
            draft.write_text('Private fixture', encoding='utf-8')
            config = root / 'config.json'
            module.write_json(config, {'id': 'first', 'title': 'First', 'summary': 'Summary', 'date': '2026-09-27', 'chapter': 'dialogue', 'draft': str(draft), 'github_token_file': 'original-path'})
            legacy = private / 'legacy.json'
            module.write_json(legacy, {'id': 'first', 'metadata': {'title': 'Previously saved title'}})
            library = module.Library(root, config, draft, legacy, 'first')
            self.assertEqual(library.current()['metadata']['title'], 'Previously saved title')
            second = library.create()['id']
            self.assertNotEqual(second, 'first')
            self.assertEqual(library.current()['text'], '')
            changed = library.config()
            changed['github_token_file'] = 'new-path'
            module.write_json(config, changed)
            library.select('first')
            self.assertEqual(library.config()['github_token_file'], 'new-path')
            self.assertEqual(library.current()['text'], 'Private fixture')
            library.envelope('first').write_text('{}')
            library.saved({'title': 'Renamed', 'summary': 'Updated'})
            self.assertEqual(library.current()['text'], '')
            self.assertTrue(json.loads(library.state_path('first').read_text(encoding='utf-8'))['saved'])
            self.assertFalse(json.loads(library.state_path(second).read_text(encoding='utf-8'))['saved'])
            self.assertNotIn('Private fixture', library.index_path.read_text(encoding='utf-8'))
            with self.assertRaises(ValueError):
                library.select('../outside')
            restarted = module.Library(root, config, draft, legacy, 'first')
            self.assertEqual(restarted.current()['metadata']['title'], 'Renamed')

            public_id = library.create('public')['id']
            library.save_public('Public draft fixture', {'title': 'Public', 'summary': 'Public summary'})
            self.assertEqual(library.current()['mode'], 'public')
            self.assertTrue(library.current()['saved'])
            self.assertEqual(library.current()['text'], 'Public draft fixture')
            self.assertFalse((root / 'content/stories' / (public_id + '.md')).exists())
            library.select('first')
            with self.assertRaises(ValueError):
                library.save_public('Must not leak', {'title': 'X', 'summary': 'X'})
            library.select(public_id)
            self.assertEqual(library.current()['text'], 'Public draft fixture')
