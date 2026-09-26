"""Build the public reading site and Markdown editions from the same stories."""
from pathlib import Path
import html
import json
import math
import posixpath
import shutil

import markdown
from markdown.extensions.toc import slugify_unicode

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '_site'
CAT = json.loads((ROOT / 'content/catalog.json').read_text(encoding='utf-8'))
ENTRIES = sorted(CAT['entries'], key=lambda e: e['date'])
CHAPTERS = {c['id']: c for c in CAT['chapters']}
REPO = 'https://github.com/hotpoor/HOTPOOR-xialiwei'
PUBLIC = 'https://hotpoor.github.io/HOTPOOR-xialiwei/'
esc = html.escape


def rel(current, target):
    return posixpath.relpath(target, posixpath.dirname(current) or '.')


def body(entry):
    return (ROOT / 'content' / entry['file']).read_text(encoding='utf-8').strip()


def article_path(entry):
    return f"stories/{entry['id']}/index.html"


def listing_path(mode, page):
    return f'{mode}/index.html' if page == 1 else f'{mode}/page/{page}/index.html'


def md_path(mode, page):
    return f'{mode}/README.md' if page == 1 else f'{mode}/page-{page}.md'


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + '\n', encoding='utf-8')


def navlink(current, target, label, active=False):
    return f'<a href="{rel(current, target)}"' + (' aria-current="page"' if active else '') + f'>{label}</a>'


def timeline(current, selected=None):
    nodes = []
    for e in ENTRIES:
        active = ' aria-current="step"' if e['id'] == selected else ''
        nodes.append(f'<li><a href="{rel(current, article_path(e))}"{active}><span class="dot"></span><time datetime="{e["date"]}">{e["date"].replace("-", ".")}</time><strong>{esc(e["title"])}</strong><span class="timeline-kind">{esc(e["kind"])}</span></a></li>')
    return '<section class="timeline-section" aria-label="横向时间轴"><div class="section-line"><span>时间轴 <small>2012 — 2026</small></span><div class="timeline-tools"><span class="timeline-hint">按记录节点排列 · 可横向滑动</span><button type="button" data-scroll="-1" aria-label="向前浏览时间轴" aria-controls="timeline">←</button><button type="button" data-scroll="1" aria-label="向后浏览时间轴" aria-controls="timeline">→</button></div></div><ol id="timeline" class="timeline" tabindex="0" aria-label="从左向右按时间正序排列">' + ''.join(nodes) + '</ol></section>'


def sidebar(current, selected=None, extra=''):
    links = ''
    for i, c in enumerate(CAT['chapters'], 1):
        label = f'<span>{i:02d}</span>{esc(c["title"])}'
        links += '<li>' + navlink(current, 'chapters/' + c['id'] + '/index.html', label, selected == c['id']) + '</li>'
    return f'<aside class="sidebar"><details open><summary>章节目录 <span>04</span></summary><ol>{links}</ol></details>{extra}<div class="sidebar-note">记录可以补充，判断可以修正。<br>让来路有迹可循。</div></aside>'


def shell(current, title, description, content, active='', selected=None):
    nav = ''.join(navlink(current, target, label, active == key) for target, label, key in [('history/index.html', 'History <span>顺时而读</span>', 'history'), ('news/index.html', 'News <span>从近处看</span>', 'news'), ('chapters/index.html', '目录', 'chapters')])
    canonical = PUBLIC + (current[:-10] if current.endswith('index.html') else current)
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · HOTPOOR XIALIWEI</title><meta name="description" content="{esc(description)}"><meta name="theme-color" content="#f7f5ee">
<link rel="canonical" href="{canonical}"><link rel="icon" href="{rel(current, 'assets/favicon.svg')}" type="image/svg+xml"><link rel="stylesheet" href="{rel(current, 'assets/style.css')}"><script defer src="{rel(current, 'assets/site.js')}"></script></head>
<body><a class="skip" href="#main">跳到正文</a><div class="site-wrap"><header class="header"><a class="brand" href="{rel(current, 'index.html')}"><span class="brand-mark">H<span>·</span></span><span>HOTPOOR<small>XIALIWEI / 个人记录</small></span></a><nav aria-label="主导航">{nav}<a class="repo-link" href="{REPO}">GitHub ↗</a></nav></header>
<div class="masthead"><p class="eyebrow">名字 · 实践 · 证据 · 对话</p><div class="masthead-row"><h1>{esc(title)}</h1><p>{esc(description)}</p></div></div>
{timeline(current, selected)}
{content}
<footer><span>HOTPOOR · XIALIWEI <small>燃烧吧，平民们。</small></span><div><a href="{rel(current, 'about/index.html')}">关于这些记录</a><a href="{REPO}">Markdown 与版本记录 ↗</a><span>整理于 {CAT['updated']}</span></div></footer></div></body></html>'''


def card(current, e, index):
    return f'''<article class="entry-card" data-entry="{e['id']}"><div class="entry-meta"><span class="entry-number">{index:02d}</span><time datetime="{e['date']}">{esc(e['date_label'])}</time><span class="badge">{esc(e['kind'])}</span></div><h3><a href="{rel(current, article_path(e))}">{esc(e['title'])}</a></h3><p>{esc(e['summary'])}</p><div class="entry-bottom"><a class="chapter-label" href="{rel(current, 'chapters/' + e['chapter'] + '/index.html')}">{esc(CHAPTERS[e['chapter']]['title'])}</a><a class="read-link" href="{rel(current, article_path(e))}">阅读全文 <span>↗</span></a></div></article>'''


def pager(current, mode, page, count):
    if count <= 1:
        return ''
    links = []
    if page > 1:
        links.append(navlink(current, listing_path(mode, page - 1), '← 上一页'))
    for n in range(1, count + 1):
        links.append(navlink(current, listing_path(mode, n), str(n), n == page))
    if page < count:
        links.append(navlink(current, listing_path(mode, page + 1), '下一页 →'))
    return '<nav class="pagination" aria-label="分页">' + ''.join(links) + f'<span>第 {page} / {count} 页</span></nav>'


def build_listing(mode, page=1, root=False):
    ordered = ENTRIES if mode == 'history' else list(reversed(ENTRIES))
    size = CAT['page_size']
    pages = math.ceil(len(ordered) / size)
    selected = ordered[(page - 1) * size: page * size]
    current = 'index.html' if root else listing_path(mode, page)
    title = '一路走来' if mode == 'history' else '最近的记录'
    desc = CAT['subtitle'] if mode == 'history' else '从最近一次思考出发，回看它怎样走到今天。'
    switch = navlink(current, 'history/index.html', 'History · 时间正序', mode == 'history') + navlink(current, 'news/index.html', 'News · 时间逆序', mode == 'news')
    cards = ''.join(card(current, e, (page - 1) * size + i) for i, e in enumerate(selected, 1))
    content = f'<main id="main" class="reading-layout">{sidebar(current)}<section class="entries" aria-labelledby="entries-title"><div class="reading-bar"><h2 id="entries-title">{len(ordered):02d} 篇记录</h2><div class="mode-switch">{switch}</div></div><p class="reading-order">{"从最早的记录读起" if mode == "history" else "最新记录在前"} · 本页 {len(selected)} 篇 <a href="{rel(current, md_path(mode, page))}">本页 Markdown ↓</a></p>{cards}{pager(current, mode, page, pages)}</section></main>'
    write(OUT / current, shell(current, title, desc, content, mode))


def markdown_collection(path, title, entries, before=''):
    text = f'# {title}\n\n{before}\n\n## 目录\n\n'
    text += '\n'.join(f'- [{e["date"]} · {e["title"]}](#{e["id"]})' for e in entries)
    for e in entries:
        text += f'\n\n---\n\n<a id="{e["id"]}"></a>\n\n## {e["title"]}\n\n{e["date_label"]} · {e["kind"]} · 整理于 {e["recorded"]}\n\n'
        text += f'[独立原稿]({rel(path, "content/" + e["file"])}) · [网页阅读]({PUBLIC + article_path(e)})\n\n'
        text += '\n'.join('#' + line if line.startswith('## ') else line for line in body(e).splitlines())
    write(ROOT / path, text)
    write(OUT / path, text)


def build_article(e):
    current = article_path(e)
    converter = markdown.Markdown(extensions=['toc', 'fenced_code', 'tables'], extension_configs={'toc': {'slugify': slugify_unicode}})
    rendered = converter.convert(body(e))
    toc = '<details class="article-toc" open><summary>本篇目录</summary>' + converter.toc + '</details>'
    at = ENTRIES.index(e)
    adjacent = ''
    if at > 0:
        prev = ENTRIES[at - 1]
        adjacent += navlink(current, article_path(prev), '← 上一篇<br><strong>' + esc(prev['title']) + '</strong>')
    if at < len(ENTRIES) - 1:
        nxt = ENTRIES[at + 1]
        adjacent += navlink(current, article_path(nxt), '下一篇 →<br><strong>' + esc(nxt['title']) + '</strong>')
    content = f'<main id="main" class="reading-layout">{sidebar(current, e["chapter"], toc)}<article class="story"><div class="story-meta"><span class="badge">{e["kind"]}</span><time datetime="{e["date"]}">{esc(e["date_label"])}</time><span>整理于 {e["recorded"]}</span><a href="{rel(current, "content/" + e["file"])}" download>Markdown ↓</a></div><div class="prose">{rendered}</div><nav class="adjacent" aria-label="按时间继续阅读">{adjacent}</nav></article></main>'
    write(OUT / current, shell(current, e['title'], e['summary'], content, selected=e['id']))


def build_chapters():
    current = 'chapters/index.html'
    cards = ''
    mdindex = '# 章节目录\n\n[History · 时间正序](../history/README.md) · [News · 时间逆序](../news/README.md)\n\n'
    for i, c in enumerate(CAT['chapters'], 1):
        chapter_entries = [e for e in ENTRIES if e['chapter'] == c['id']]
        chapterpath = f'chapters/{c["id"]}/index.html'
        links = ''.join(f'<li>{navlink(current, article_path(e), "<time>" + e["date"] + "</time>" + esc(e["title"]))}</li>' for e in chapter_entries)
        cards += f'<section class="chapter-card"><span class="eyebrow">CHAPTER {i:02d} / {len(chapter_entries)} 篇</span><h2>{navlink(current, chapterpath, esc(c["title"]))}</h2><p>{esc(c["description"])}</p><ol>{links}</ol></section>'
        subcards = ''.join(card(chapterpath, e, n) for n, e in enumerate(chapter_entries, 1))
        content = f'<main id="main" class="reading-layout">{sidebar(chapterpath, c["id"])}<section class="entries" aria-label="章节文章"><div class="reading-bar"><h2>本章 {len(chapter_entries)} 篇 · 时间正序</h2><a href="README.md">整章 Markdown ↓</a></div>{subcards}</section></main>'
        write(OUT / chapterpath, shell(chapterpath, c['title'], c['description'], content, 'chapters'))
        markdown_collection(f'chapters/{c["id"]}/README.md', c['title'], chapter_entries, '[返回章节目录](../README.md)\n\n' + c['description'])
        mdindex += f'## {i:02d} · [{c["title"]}]({c["id"]}/README.md)\n\n{c["description"]}\n\n'
        mdindex += '\n'.join(f'- [{e["date"]} · {e["title"]}](../content/{e["file"]})' for e in chapter_entries) + '\n\n'
    write(ROOT / 'chapters/README.md', mdindex)
    write(OUT / 'chapters/README.md', mdindex)
    content = f'<main id="main" class="chapter-grid">{cards}</main>'
    write(OUT / current, shell(current, '记录的目录', '按章节阅读，也可以沿着时间把它们连起来。', content, 'chapters'))


def main():
    assert len({e['id'] for e in ENTRIES}) == len(ENTRIES), 'Duplicate entry id'
    assert CAT['page_size'] > 0
    OUT.mkdir(exist_ok=True)
    shutil.copytree(ROOT / 'assets', OUT / 'assets', dirs_exist_ok=True)
    shutil.copytree(ROOT / 'content', OUT / 'content', dirs_exist_ok=True)
    write(OUT / '.nojekyll', '')
    for mode in ('history', 'news'):
        ordered = ENTRIES if mode == 'history' else list(reversed(ENTRIES))
        pages = math.ceil(len(ordered) / CAT['page_size'])
        for page in range(1, pages + 1):
            build_listing(mode, page)
            currentmd = md_path(mode, page)
            navigation = f'{"按时间正序" if mode == "history" else "按时间逆序"} · 第 {page} / {pages} 页。同日条目按编辑顺序排列，不推断日内时间。\n\n'
            navigation += f'[章节目录]({rel(currentmd, "chapters/README.md")}) · [{"News" if mode == "history" else "History"}]({rel(currentmd, md_path("news" if mode == "history" else "history", 1))})\n\n'
            navigation += ' · '.join(f'[第 {n} 页]({rel(currentmd, md_path(mode, n))})' for n in range(1, pages + 1))
            markdown_collection(currentmd, f'{mode.title()} · {"一路走来" if mode == "history" else "最近的记录"}', ordered[(page - 1) * CAT['page_size']:page * CAT['page_size']], navigation)
    build_listing('history', root=True)
    for e in ENTRIES:
        build_article(e)
    build_chapters()
    current = 'about/index.html'
    about = '''<main id="main" class="about prose"><h2>本人授权，持续整理</h2><p>这是 HOTPOOR · XIALIWEI 的经历、产品实践与协作记录。由本人提供经历与立场，AI 协助整理和搭建，经本人要求公开。本版整理于 2026 年 9 月 26 日。</p><h2>日期与证据</h2><p>每篇标明本人自述、共同约定、项目核验或对话整理等来源类型，正文保留具体来源和范围。只知道年份时不补写月日；约定记录日、产品定位记录日与实际起始时间分别说明。同日记录按编辑顺序排列，时间轴节点等距展示，不按真实时间跨度缩放。</p><h2>阅读与修订</h2><p>History 按时间正序，News 按时间逆序，每页四篇。章节目录按主题汇集文章，每篇另有正文目录。网页和 Markdown 从同一批原稿生成；修订通过 GitHub 的版本记录保留。</p><h2>公开内容范围</h2><p>收录本人已讲述并要求公开的内容与已有公开项目证据，不包含凭证、私人录音、第三方私人聊天或身份信息。转写不清楚的片段没有被补写成事实。新证据出现时，可以补充与修正。</p></main>'''
    write(OUT / current, shell(current, '关于这些记录', '保留原意，注明来处，也留下修正的空间。', about))
    print(f'Built {len(ENTRIES)} stories, {len(CHAPTERS)} chapters, {len(list(OUT.rglob("*.html")))} HTML pages.')


if __name__ == '__main__':
    main()
