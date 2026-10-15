#!/usr/bin/env python3
"""抓 YouTube RSS → data/videos.json；掃 posts/ → data/posts.json。免 API 金鑰。"""
import json, os, re, sys, urllib.request, xml.etree.ElementTree as ET, datetime, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(ROOT, *p)
NS = {'a': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015', 'm': 'http://search.yahoo.com/mrss/'}
cfg = json.load(open(D('data', 'feeds.json'), encoding='utf-8'))

def load(p, default):
    try: return json.load(open(p, encoding='utf-8'))
    except Exception: return default

def feed(q):
    url = 'https://www.youtube.com/feeds/videos.xml?' + q
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        root = ET.fromstring(urllib.request.urlopen(req, timeout=30).read())
    except Exception as e:
        print('skip', q, e); return []
    out = []
    for e in root.findall('a:entry', NS):
        vid = e.find('yt:videoId', NS).text
        g = e.find('m:group', NS)
        st = g.find('m:community/m:statistics', NS) if g is not None else None
        out.append({'id': vid, 'title': e.find('a:title', NS).text or '',
                    'published': e.find('a:published', NS).text,
                    'desc': ((g.find('m:description', NS).text if g is not None else '') or '')[:400],
                    'views': int(st.get('views')) if st is not None and st.get('views') else None})
    return out

class NoRedir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None

def is_short(vid):
    # /shorts/ID：是短影音回 200，長片會被轉址（3xx）
    try:
        op = urllib.request.build_opener(NoRedir)
        r = op.open(urllib.request.Request('https://www.youtube.com/shorts/' + vid, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'}), timeout=15)
        return r.status == 200
    except urllib.error.HTTPError as e:
        return False if 300 <= e.code < 400 and '/watch' in (e.headers.get('Location') or '') else None
    except Exception:
        return None

def topics(title, rules, override):
    if override.get('topics'): return override['topics']
    t = [k for k, words in rules.items() if any(w in title for w in words)]
    return t or ['其他']

def main():
    old = {v['id']: v for v in load(D('data', 'videos.json'), {'videos': []})['videos']}
    for v in feed('channel_id=' + cfg['channel_id']):
        old[v['id']] = {**old.get(v['id'], {}), **v}
    lists = {}
    for key, pl in cfg.get('playlists', {}).items():
        items = feed('playlist_id=' + pl['id'])
        if items: lists[key] = [v['id'] for v in items]
        for v in items: old.setdefault(v['id'], v)
    rules = load(D('data', 'topics.json'), {})
    ov = load(D('data', 'overrides.json'), {})
    shorts = set(lists.get('shorts', [])) | set(ov.get('_shorts', []))
    vids = []
    for vid, v in old.items():
        o = ov.get(vid, {})
        if o.get('hide'): continue
        v['topics'] = topics(v['title'], rules, o)
        if 'short' in o: v['short'] = bool(o['short'])
        elif vid in shorts: v['short'] = True
        elif 'short_checked' not in v:
            r = is_short(vid)
            if r is not None: v['short'] = r; v['short_checked'] = True
            else: v['short'] = '#' in v['title']
        if o.get('featured'): v['featured'] = True
        else: v.pop('featured', None)
        vids.append(v)
    vids.sort(key=lambda v: v['published'], reverse=True)
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).replace(microsecond=0).isoformat() + 'Z'
    json.dump({'updated': now, 'playlists': lists, 'videos': vids}, open(D('data', 'videos.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    # posts
    manual = load(D('posts.json'), [])
    auto = []
    for f in sorted(glob.glob(D('posts', '*'))):
        name = os.path.basename(f); stem, ext = os.path.splitext(name); ext = ext.lower()
        if ext not in ('.md', '.pdf') or name.startswith('_') or name.lower() == 'readme.md': continue
        m = re.match(r'(\d{4})-?(\d{2})-?(\d{2})[-_ ]*(.*)', stem)
        date = f'{m[1]}-{m[2]}-{m[3]}' if m else datetime.date.fromtimestamp(os.path.getmtime(f)).isoformat()
        title = (m[4] if m else stem).replace('_', ' ').strip() or stem
        p = {'file': 'posts/' + name, 'type': 'article' if ext == '.md' else 'slides', 'date': date, 'title': title}
        if ext == '.md':
            txt = open(f, encoding='utf-8').read()
            fm = re.match(r'---\n(.*?)\n---\n', txt, re.S)
            if fm:
                for line in fm[1].splitlines():
                    if ':' in line:
                        k, val = line.split(':', 1); p[k.strip()] = val.strip().strip('"')
                txt = txt[fm.end():]
            h = re.search(r'^#\s+(.+)$', txt, re.M)
            if h and not fm: p['title'] = h[1].strip()
            body = re.sub(r'[#>*`\[\]()!-]', '', txt)
            p['summary'] = p.get('summary') or re.sub(r'\s+', ' ', body).strip()[:90]
        auto.append(p)
    posts = sorted(manual + auto, key=lambda p: p.get('date', ''), reverse=True)
    json.dump({'posts': posts}, open(D('data', 'posts.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(len(vids), 'videos', len(posts), 'posts')

main()
