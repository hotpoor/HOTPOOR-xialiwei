from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import importlib.util
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build', ROOT / 'scripts/build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class Document(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids, self.links, self.entries, self.resources = [], [], [], []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if 'data-entry' in attrs:
            self.entries.append(attrs['data-entry'])
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])
        if tag == 'link' and attrs.get('rel') != 'canonical':
            self.resources.append(attrs.get('href', ''))
        if tag in ('script', 'img'):
            self.resources.append(attrs.get('src', ''))


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build.main()
        cls.docs = {p.resolve(): Document(p.read_text(encoding='utf-8')) for p in build.OUT.rglob('*.html')}

    def test_all_local_links_resources_and_fragments(self):
        for path, doc in self.docs.items():
            self.assertEqual(len(doc.ids), len(set(doc.ids)), str(path))
            for link in doc.links + doc.resources:
                parts = urlsplit(link)
                if parts.scheme or parts.netloc:
                    continue
                target = (path.parent / unquote(parts.path)).resolve() if parts.path else path
                self.assertTrue(target.is_relative_to(build.OUT), (path, link))
                self.assertTrue(target.is_file(), (path, link))
                if parts.fragment and target.suffix == '.html':
                    self.assertIn(unquote(parts.fragment), self.docs[target].ids, (path, link))

    def test_complete_ordered_pagination_both_modes(self):
        for mode in ('history', 'news'):
            actual = []
            pages = (len(build.ENTRIES) + build.CAT['page_size'] - 1) // build.CAT['page_size']
            for page in range(1, pages + 1):
                doc = self.docs[(build.OUT / build.listing_path(mode, page)).resolve()]
                actual += doc.entries
                self.assertLessEqual(len(doc.entries), build.CAT['page_size'])
                md = (ROOT / build.md_path(mode, page)).read_text(encoding='utf-8')
                self.assertEqual(doc.entries, re.findall(r'<a id="([^"]+)"', md))
            expected = [e['id'] for e in build.ENTRIES]
            if mode == 'news':
                expected.reverse()
            self.assertEqual(actual, expected)

    def test_chapters_cover_each_story_once(self):
        seen = []
        for chapter in build.CHAPTERS:
            doc = self.docs[(build.OUT / f'chapters/{chapter}/index.html').resolve()]
            expected = [e['id'] for e in build.ENTRIES if e['chapter'] == chapter]
            self.assertEqual(doc.entries, expected)
            seen.extend(doc.entries)
        self.assertCountEqual(seen, [e['id'] for e in build.ENTRIES])

    def test_markdown_source_copies_and_date_precision(self):
        for entry in build.ENTRIES:
            self.assertRegex(entry['date'], r'^\d{4}(-\d{2}(-\d{2})?)?$')
            original = ROOT / 'content' / entry['file']
            published = build.OUT / 'content' / entry['file']
            self.assertEqual(original.read_bytes(), published.read_bytes())
            page = (build.OUT / build.article_path(entry)).read_text(encoding='utf-8')
            self.assertIn(entry['title'], page)
            self.assertIn('本篇目录', page)
        self.assertEqual(next(e for e in build.ENTRIES if e['id'] == '2012-hotpoor')['date'], '2012')

    def test_pdf_periods_and_provisional_end_dates(self):
        entries = [e for e in build.ENTRIES if e.get('source_page')]
        self.assertEqual(sorted(e['source_page'] for e in entries), list(range(3, 19)))
        provisional = [e for e in entries if e.get('date_end_provisional')]
        self.assertEqual({e['source_page'] for e in provisional}, {12, 13, 15, 18})
        for entry in provisional:
            self.assertEqual(entry['date_end'], '2026-09-26')
            self.assertIn('2026-09-26', entry['date_label'])
            self.assertIn('暂', entry['date_label'])
            self.assertIn('2026-09-26', build.body(entry))
        home = (build.OUT / 'index.html').read_text(encoding='utf-8')
        self.assertIn('2007 — 2026', home)
        self.assertIn(f'章节目录 <span>{len(build.CHAPTERS):02d}</span>', home)

    def test_public_site_contains_no_local_paths_or_credentials(self):
        for path in build.OUT.rglob('*'):
            if path.is_file():
                text = path.read_text(encoding='utf-8')
                self.assertNotRegex(text, r'(?i)([CJ]:[/\\]|github_pat_|ghp_[a-zA-Z0-9]{20}|\.secrets|10205)')


if __name__ == '__main__':
    unittest.main()
