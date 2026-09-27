import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publisher', ROOT / 'scripts/publish-record.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


class PublicPublishTests(unittest.TestCase):
    def test_public_publish_preserves_historical_metadata_and_stages_only_selected_record(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = base / 'repo'
            (root / 'scripts').mkdir(parents=True)
            (root / 'content/stories').mkdir(parents=True)
            shutil.copyfile(ROOT / 'scripts/private-editor.py', root / 'scripts/private-editor.py')
            original = {'id': 'history', 'date': '2012', 'date_label': '2012 年', 'chapter': 'dialogue', 'title': 'Old', 'summary': 'Old summary', 'file': 'stories/history.md', 'source_page': 3, 'kind': '本人自述'}
            catalog = {'updated': '2026-09-27', 'chapters': [{'id': 'dialogue'}], 'entries': [original]}
            (root / 'content/catalog.json').write_text(json.dumps(catalog), encoding='utf-8')
            draft = base / 'draft.md'
            draft.write_text('## Public fixture\n\nUpdated public content.', encoding='utf-8')
            credential = base / 'fake.token'
            credential.write_text('synthetic-not-a-credential')
            config = base / 'config.json'
            config.write_text(json.dumps({'id': 'history', 'github_token_file': str(credential)}))
            state = base / 'state.json'
            state.write_text(json.dumps({'id': 'history', 'saved': True, 'mode': 'public', 'draft': str(draft), 'metadata': dict(original, title='Revised', summary='Revised summary')}))
            calls = []
            def fake_run(args, **kwargs):
                calls.append(args)
                if args[:3] == ['git', 'remote', 'get-url']:
                    return publisher.REMOTE
                if args[:2] == ['git', 'branch']:
                    return 'main'
                if args[:2] == ['git', 'fetch']:
                    raise RuntimeError('stop before any network')
                return ''
            with patch.object(publisher, 'ROOT', root), patch.object(publisher, 'run', fake_run):
                with self.assertRaisesRegex(RuntimeError, 'stop before any network'):
                    publisher.publish(config, state)
            updated = json.loads((root / 'content/catalog.json').read_text(encoding='utf-8'))['entries'][0]
            self.assertEqual(updated, dict(original, title='Revised', summary='Revised summary'))
            self.assertEqual((root / 'content/stories/history.md').read_text(encoding='utf-8'), draft.read_text(encoding='utf-8'))
            staged = next(args for args in calls if args[:2] == ['git', 'add'])
            self.assertIn('content/stories/history.md', staged)
            self.assertFalse(any('encrypted/' in argument for argument in staged))
            catalog['entries'][0]['encrypted_file'] = 'encrypted/history.json'
            (root / 'content/catalog.json').write_text(json.dumps(catalog), encoding='utf-8')
            with patch.object(publisher, 'ROOT', root), patch.object(publisher, 'run', fake_run):
                with self.assertRaisesRegex(RuntimeError, '记录类型不一致'):
                    publisher.publish(config, state)
