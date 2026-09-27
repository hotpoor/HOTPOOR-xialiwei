"""Publish one public or encrypted record; GitHub credentials remain in the local process."""
import argparse
import base64
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REMOTE = 'https://github.com/hotpoor/HOTPOOR-xialiwei.git'
PUBLIC = 'https://github.xialiwei.com/HOTPOOR-xialiwei/'


def run(args, env=None, label='操作'):
    result = subprocess.run(args, cwd=ROOT, env=env, capture_output=True,
                            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    if result.returncode:
        raise RuntimeError(label + '失败；文件仍保留在本机，请检查后继续。')
    return result.stdout.decode('utf-8', errors='replace').strip()


def publish(config_path, state_path):
    config = json.loads(config_path.read_text(encoding='utf-8'))
    state = json.loads(state_path.read_text(encoding='utf-8'))
    record_id = config['id']
    if not re.fullmatch(r'[a-z0-9-]+', record_id) or state.get('id') != record_id or not state.get('saved'):
        raise RuntimeError('请先在客户端保存正文。')
    if run(['git', 'remote', 'get-url', 'origin']) != REMOTE or run(['git', 'branch', '--show-current']) != 'main':
        raise RuntimeError('仓库或分支与预期不符，未发布。')
    envelope_name = 'content/encrypted/' + record_id + '.json'
    is_public = state.get('mode', 'encrypted') == 'public'
    envelope = None if is_public else json.loads((ROOT / envelope_name).read_text(encoding='utf-8'))
    spec = importlib.util.spec_from_file_location('private_editor', ROOT / 'scripts/private-editor.py')
    editor = importlib.util.module_from_spec(spec); spec.loader.exec_module(editor)
    if not is_public:
        editor.validate_envelope(envelope, record_id)
    placeholder = 'content/stories/' + record_id + '.md'
    def allowed(name):
        # Other encrypted drafts can stay unstaged while publishing this document.
        if name == envelope_name:
            return True
        match = re.fullmatch(r'content/encrypted/([a-z0-9-]+)\.json', name)
        if not match:
            return False
        try:
            editor.validate_envelope(json.loads((ROOT / name).read_text(encoding='utf-8')), match[1])
            return True
        except (ValueError, OSError, TypeError, KeyError):
            return False
    staged = set(run(['git', 'diff', '--cached', '--name-only']).splitlines())
    if staged - {envelope_name}:
        raise RuntimeError('暂存区还有其他文档或代码，未混入本篇发布。')
    dirty = set(run(['git', 'diff', '--name-only']).splitlines())
    dirty.update(staged)
    dirty.update(run(['git', 'ls-files', '--others', '--exclude-standard']).splitlines())
    if any(not allowed(name) for name in dirty):
        raise RuntimeError('还有本篇以外的未提交改动，未自动混入发布。请先处理这些改动。')
    metadata = state['metadata']
    catalog_path = ROOT / 'content/catalog.json'
    catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
    if metadata['chapter'] not in {c['id'] for c in catalog['chapters']} or not re.fullmatch(r'\d{4}(-\d{2}(-\d{2})?)?', metadata['date']):
        raise RuntimeError('公开目录信息无效。')
    existing = next((item for item in catalog['entries'] if item['id'] == record_id), None)
    if existing and bool(existing.get('encrypted_file')) == is_public:
        raise RuntimeError('记录类型不一致；不能把加密记录直接改为公开正文。')
    if existing:
        entry = dict(existing, title=metadata['title'], summary=metadata['summary'])
    else:
        entry = {'id': record_id, 'date': metadata['date'], 'date_label': metadata['date'] + ' · 记录日期',
                 'chapter': metadata['chapter'], 'title': metadata['title'], 'summary': metadata['summary'],
                 'kind': '公开记录' if is_public else '加密记录', 'recorded': metadata['date'], 'file': 'stories/' + record_id + '.md'}
        if not is_public:
            entry['encrypted_file'] = 'encrypted/' + record_id + '.json'
    if is_public:
        draft = Path(state['draft']).resolve()
        if draft.is_relative_to(ROOT) or not draft.is_file():
            raise RuntimeError('公开草稿位置无效。')
        public_text = draft.read_text(encoding='utf-8')
        if not public_text.strip():
            raise RuntimeError('正文不能为空。')
        placeholder = 'content/' + entry['file']
        if not (ROOT / placeholder).resolve().is_relative_to((ROOT / 'content/stories').resolve()):
            raise RuntimeError('文章路径无效。')
    for i, item in enumerate(catalog['entries']):
        if item['id'] == record_id:
            catalog['entries'][i] = entry
            break
    else:
        catalog['entries'].append(entry)
    catalog['updated'] = max(catalog['updated'], metadata['date'])
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if is_public:
        (ROOT / placeholder).write_text(public_text, encoding='utf-8')
    else:
        (ROOT / placeholder).write_text('## 加密保存的记录\n\n正文已加密，Git 和网页仅保存密文。\n\n请在本篇网页输入作者单独提供的口令，在浏览器本地解密阅读。口令不会发送到网站，也不会保存到浏览器存储。\n\n公开标题、日期和说明不在加密范围内。\n', encoding='utf-8')
    run([sys.executable, 'scripts/build.py'], label='网页构建')
    run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests'], label='网页验证')
    node = config.get('node', 'node')
    run([node, 'scripts/test-encryption.cjs'], label='加密验证')
    run(['git', 'diff', '--check'], label='差异检查')
    run(['git', 'add', '--', *([] if is_public else [envelope_name]), placeholder, 'content/catalog.json', 'history', 'news', 'chapters'], label='暂存本篇')
    if run(['git', 'diff', '--cached', '--name-only']):
        run(['git', 'commit', '-m', 'Update archive record ' + record_id], label='提交本篇')
    credential = Path(config['github_token_file'])
    if not credential.is_file():
        raise RuntimeError('本机登记的 GitHub 凭证文件不存在；本地提交已保留。')
    token = credential.read_text(encoding='utf-8').strip()
    auth_env = dict(os.environ, GIT_CONFIG_COUNT='2', GIT_CONFIG_KEY_0='credential.helper', GIT_CONFIG_VALUE_0='',
                    GIT_CONFIG_KEY_1='http.https://github.com/.extraheader',
                    GIT_CONFIG_VALUE_1='Authorization: Basic ' + base64.b64encode(('x-access-token:' + token).encode()).decode(),
                    GIT_TERMINAL_PROMPT='0')
    run(['git', 'fetch', 'origin'], env=auth_env, label='获取远端更新')
    before_merge = run(['git', 'rev-parse', 'HEAD'])
    run(['git', 'merge', '--no-edit', 'origin/main'], label='合并远端更新')
    if run(['git', 'rev-parse', 'HEAD']) != before_merge:
        run([sys.executable, 'scripts/build.py'], label='合并后网页构建')
        run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests'], label='合并后网页验证')
        run([node, 'scripts/test-encryption.cjs'], label='合并后加密验证')
        run(['git', 'diff', '--exit-code', '--', 'history', 'news', 'chapters'], label='合并后生成目录一致性检查')
    run(['git', 'push', 'origin', 'HEAD:main'], env=auth_env, label='推送 GitHub')
    sha = run(['git', 'rev-parse', 'HEAD'])
    remote_sha = run(['git', 'ls-remote', 'origin', 'refs/heads/main'], env=auth_env, label='核对远端提交').split()[0]
    if sha != remote_sha:
        raise RuntimeError('远端提交与本地不一致，请核对发布状态。')
    url = PUBLIC + 'stories/' + record_id + '/'
    for _ in range(30):
        request = urllib.request.Request('https://api.github.com/repos/hotpoor/HOTPOOR-xialiwei/actions/runs?head_sha=' + sha,
                                         headers={'Authorization': 'Bearer ' + token, 'User-Agent': 'HOTPOOR-Archive'})
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                runs = json.load(response)['workflow_runs']
            job = next((r for r in runs if r['name'] == 'Publish reading archive'), None)
            if job and job['status'] == 'completed':
                if job['conclusion'] != 'success':
                    return {'ok': True, 'deployed': False, 'sha': sha, 'message': '记录已推送，但网页部署失败。请检查 GitHub Actions。'}
                with urllib.request.urlopen(PUBLIC + (placeholder if is_public else envelope_name) + '?v=' + sha, timeout=15) as response:
                    published = response.read().decode('utf-8').replace('\r\n', '\n') if is_public else json.load(response)
                if published == (public_text.replace('\r\n', '\n') if is_public else envelope):
                    return {'ok': True, 'deployed': True, 'sha': sha, 'url': url, 'message': '已发布并核对线上正文。提交 ' + sha[:7] if is_public else '已发布并核对线上密文。提交 ' + sha[:7] + '，网页需输入口令阅读。'}
        except (OSError, ValueError, KeyError):
            pass
        time.sleep(10)
    return {'ok': True, 'deployed': False, 'sha': sha, 'message': '记录已推送，网页部署尚未核实完成。请稍后查看 GitHub Actions。'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--state', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = publish(args.config, args.state)
    except Exception as error:
        result = {'ok': False, 'message': str(error) if isinstance(error, RuntimeError) else '发布未完成，请检查本地配置；文件仍保留在本机。'}
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
