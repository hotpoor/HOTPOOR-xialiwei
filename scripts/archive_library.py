"""Local document index. Private paths and state remain outside the repository."""
import json
import re
import uuid
from datetime import date
from pathlib import Path


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


class Library:
    def __init__(self, root, config_path, draft, legacy_state, record_id):
        self.root, self.config_path = root, config_path
        self.directory = draft.resolve().parent
        self.index_path = self.directory / '.archive-records.json'
        self.records = json.loads(self.index_path.read_text(encoding='utf-8')) if self.index_path.exists() else {}
        config = self.config()
        metadata = {k: config[k] for k in ('title', 'summary', 'date', 'chapter')}
        if legacy_state.exists():
            prior = json.loads(legacy_state.read_text(encoding='utf-8'))
            if prior.get('id') == record_id:
                metadata.update(prior.get('metadata', {}))
        if record_id not in self.records:
            self.records[record_id] = dict(metadata, draft=str(draft.resolve()), public=config.get('public', False))
        self.selected = record_id
        self.persist()
        self.save_state(record_id)

    def config(self):
        return json.loads(self.config_path.read_text(encoding='utf-8'))

    def persist(self):
        write_json(self.index_path, self.records)

    def catalog(self):
        return json.loads((self.root / 'content/catalog.json').read_text(encoding='utf-8'))['entries']

    def all_records(self):
        records = {e['id']: dict(e, public=not bool(e.get('encrypted_file'))) for e in self.catalog()}
        for key, record in self.records.items():
            records[key] = dict(record, id=key, public=record.get('public', False))
        return records

    def listing(self):
        return [{'id': key, 'title': record['title'], 'date': record['date'],
                 'mode': 'public' if record['public'] else 'encrypted',
                 'status': '公开文章' if record['public'] else ('已加密' if self.envelope(key).exists() else '本地草稿')}
                for key, record in sorted(self.all_records().items(), key=lambda pair: pair[1]['date'], reverse=True)]

    def envelope(self, record_id):
        if not re.fullmatch(r'[a-z0-9-]+', record_id):
            raise ValueError('Invalid record ID')
        return self.root / 'content/encrypted' / (record_id + '.json')

    def state_path(self, record_id):
        self.envelope(record_id)
        return self.directory / (record_id + '.state.json')

    def save_state(self, record_id):
        record = self.all_records()[record_id]
        metadata = {k: record[k] for k in ('title', 'summary', 'date', 'chapter')}
        write_json(self.state_path(record_id), {'id': record_id, 'saved': Path(record.get('draft', '')).is_file() if record['public'] else self.envelope(record_id).exists(), 'metadata': metadata, 'mode': 'public' if record['public'] else 'encrypted', 'draft': record.get('draft', '')})

    def select(self, record_id):
        record = self.all_records().get(record_id)
        if record is None:
            raise ValueError('Unknown record')
        if record_id not in self.records:
            self.records[record_id] = {k: record[k] for k in ('title', 'summary', 'date', 'chapter')}
            self.records[record_id].update(public=record['public'], draft=str(self.directory / (record_id + ('.public.md' if record['public'] else '.md'))))
            if record.get('file'):
                self.records[record_id]['file'] = record['file']
            self.persist()
        config = self.config()
        config.update(self.records[record_id], id=record_id)
        write_json(self.config_path, config)
        self.save_state(record_id)
        self.selected = record_id
        return self.current()

    def current(self):
        record = self.all_records()[self.selected]
        encrypted = self.envelope(self.selected).exists()
        if record['public']:
            local = Path(record.get('draft', '')).resolve()
            if local.is_file() and not local.is_relative_to(self.root):
                text = local.read_text(encoding='utf-8')
            elif record.get('file'):
                file = (self.root / 'content' / record['file']).resolve()
                if not file.is_relative_to((self.root / 'content/stories').resolve()):
                    raise ValueError('Invalid public document path')
                text = file.read_text(encoding='utf-8')
            else:
                text = ''
        elif encrypted:
            text = ''
        else:
            file = Path(record['draft']).resolve()
            if file.is_relative_to(self.root):
                raise ValueError('Private draft must stay outside repository')
            text = file.read_text(encoding='utf-8') if file.exists() else ''
        return {'id': self.selected, 'metadata': {k: record[k] for k in ('title', 'summary', 'date', 'chapter')},
                'text': text, 'has_encrypted': encrypted, 'readonly': False, 'mode': 'public' if record['public'] else 'encrypted', 'saved': Path(record.get('draft', '')).is_file() if record['public'] else encrypted}

    def create(self, mode='encrypted'):
        if mode not in ('public', 'encrypted'):
            raise ValueError('Invalid document mode')
        record_id = date.today().isoformat() + '-' + uuid.uuid4().hex[:8]
        self.records[record_id] = {'title': '新的记录', 'summary': '一份公开记录。' if mode == 'public' else '一份加密记录，输入口令后阅读。', 'public': mode == 'public',
            'date': date.today().isoformat(), 'chapter': 'dialogue', 'draft': str(self.directory / (record_id + '.md'))}
        self.persist()
        return self.select(record_id)

    def save_public(self, text, metadata):
        if not self.all_records()[self.selected]['public']:
            raise ValueError('Cannot save encrypted document as plaintext')
        target = Path(self.records[self.selected]['draft']).resolve()
        if target.is_relative_to(self.root):
            raise ValueError('Draft must stay outside repository')
        temporary = target.with_suffix(target.suffix + '.tmp')
        temporary.write_text(text, encoding='utf-8')
        temporary.replace(target)
        self.saved(metadata)

    def saved(self, public):
        self.records[self.selected].update(public)
        self.persist()
        self.save_state(self.selected)
