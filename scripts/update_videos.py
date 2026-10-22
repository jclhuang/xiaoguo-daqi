#!/usr/bin/env python3
"""小國大棋：每日匯入新影片（只收已公開；預約首播/未公開會跳過，公開後下次再加入）、
抓播放清單分系列、依 data/topics.json 分主題、（可選）匯入 Podcast RSS。永不刪除既有影片。
本機補齊整個頻道：python scripts/update_videos.py --backfill   （需 yt-dlp）"""
import json, re, sys, time, os, subprocess, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda f: os.path.join(ROOT, f)
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015", "m": "http://search.yahoo.com/mrss/",
      "itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"}
UA = {"User-Agent": "Mozilla/5.0", "Accept-Language": "en"}
SITE = None

def load(f, default=None):
    try: return json.load(open(P(f), encoding="utf-8"))
    except FileNotFoundError: return default
def save(f, d): open(P(f), "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
def get(url, tries=5, wait=3):
    err = None
    for i in range(tries):
        try: return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
        except Exception as e: err = e; time.sleep(wait + i)
    raise err
def utc(d):
    try: return datetime.fromisoformat(d.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
    except Exception: return d
def ytdlp(*args):
    return subprocess.run(["yt-dlp", "--flat-playlist", *args], capture_output=True, text=True, timeout=300).stdout.splitlines()

def item(vid, title, short, published=None, thumb=None):
    return dict(id=vid, title=title, type="short" if short else "video",
                url=f"https://www.youtube.com/shorts/{vid}" if short else f"https://www.youtube.com/watch?v={vid}",
                published=published, thumbnail=thumb or f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg")

def fetch_feed():
    out = []
    for e in ET.fromstring(get(f"https://www.youtube.com/feeds/videos.xml?channel_id={SITE['channelId']}", 12, 2)).findall("a:entry", NS):
        link = e.find("a:link", NS).get("href", ""); g = e.find("m:group", NS); th = g.find("m:thumbnail", NS) if g is not None else None
        it = item(e.find("yt:videoId", NS).text, e.find("a:title", NS).text or "", "/shorts/" in link,
                  e.find("a:published", NS).text, th.get("url") if th is not None else None)
        st = g.find("m:community/m:statistics", NS) if g is not None else None
        it["views"] = int(st.get("views") or 0) if st is not None else 0
        out.append(it)
    return out

def fallback_list(n=15):
    out = []
    for tab in ("videos", "shorts"):
        for l in ytdlp("-I", f"1:{n}", "--print", "%(id)s\t%(title)s", f"{SITE['channelUrl']}/{tab}"):
            vid, title = l.split("\t", 1); out.append(item(vid, title, tab == "shorts"))
    if not out: raise RuntimeError("yt-dlp 也拿不到清單")
    return out

_LIVE = {}
def channel_live_map(url, n=40):
    """yt-dlp 頻道清單（不需開影片頁）：{影片ID: live_status}。用來在影片頁被 YouTube 擋時判斷是否為首播前。"""
    global _LIVE
    if url not in _LIVE:
        _LIVE[url] = {}
        for tab in ("videos", "shorts", "streams"):
            try:
                r = subprocess.run(["yt-dlp", "--flat-playlist", "-I", f"1:{n}", "--print", "%(id)s\t%(live_status)s", f"{url}/{tab}"], capture_output=True, text=True, timeout=180)
                for l in r.stdout.splitlines():
                    i, st = l.split("\t", 1); _LIVE[url][i] = st
            except Exception as e: print("yt-dlp live map failed", e)
    return _LIVE[url]

def decide(f, url):
    """回傳 (是否收錄, 公開日期)。影片頁可判斷就用影片頁；被擋（無法判斷）時改看頻道清單的 live_status。"""
    ok, d = public_status(f["id"])
    if ok is not None: return ok, d
    st = channel_live_map(url).get(f["id"])
    if st is None: return (f.get("views", 0) > 20), None   # 清單裡也沒有：只在 RSS 觀看數明顯大於 0 時收錄
    return st not in ("is_upcoming", "is_live"), None

def public_status(vid):
    """(已公開?, 公開日期)。看不出來 → (None, None)，這次先跳過。"""
    try: h = get(f"https://www.youtube.com/watch?v={vid}", 2).decode("utf-8", "ignore")
    except Exception: return None, None
    st = re.search(r'"playabilityStatus":\{"status":"([A-Z_]+)"', h)
    if not st: return None, None
    if '"isUpcoming":true' in h or '"isUnlisted":true' in h or st.group(1) != "OK": return False, None
    d = re.search(r'"(?:publishDate|uploadDate)":"([^"]+)"', h)
    return True, d.group(1) if d else None

def topics_for(title):
    return [k for k, words in (load("data/topics.json", {}) or {}).items() if any(w in title for w in words)]

def update_series(vids):
    """播放清單 → data/series.json；抓不到時保留舊的。"""
    lists = []
    for l in ytdlp("--print", "%(id)s\t%(title)s", f"{SITE['channelUrl']}/playlists"):
        pid, title = l.split("\t", 1)
        ids = [x.split("\t")[0] for x in ytdlp("--print", "%(id)s", f"https://www.youtube.com/playlist?list={pid}")]
        if ids: lists.append(dict(id=pid, title=title, url=f"https://www.youtube.com/playlist?list={pid}", videos=ids))
    if not lists: print("播放清單抓不到，保留舊資料"); return False
    old = load("data/series.json", [])
    if old != lists: save("data/series.json", lists); return True
    return False

def update_podcast_feed():
    url = SITE.get("podcastFeed")
    if not url: return False
    try: root = ET.fromstring(get(url))
    except Exception as e: print("Podcast RSS 失敗", e); return False
    eps = []
    for it in root.iter("item"):
        enc = it.find("enclosure")
        eps.append(dict(id="feed-" + re.sub(r"\W", "", (it.findtext("guid") or it.findtext("link") or it.findtext("title") or ""))[-40:],
                        title=it.findtext("title") or "", date=utc(it.findtext("pubDate") and datetime.strptime(it.findtext("pubDate")[:25].strip(), "%a, %d %b %Y %H:%M:%S").replace(tzinfo=timezone.utc).isoformat() or "")[:10],
                        summary=re.sub(r"<[^>]+>", "", it.findtext("description") or "")[:300], audio=enc.get("url") if enc is not None else None,
                        link=it.findtext("link"), source="feed"))
    old = load("data/podcast_feed.json", [])
    if eps != old: save("data/podcast_feed.json", eps); return True
    return False

def bump_sw():
    sw = open(P("sw.js"), encoding="utf-8").read()
    sw = re.sub(r"const C='xgdq-v(\d+)'", lambda m: f"const C='xgdq-v{int(m.group(1))+1}'", sw, count=1)
    open(P("sw.js"), "w", encoding="utf-8").write(sw)

def main():
    global SITE; SITE = load("data/site.json")
    data = load("data/videos.json", {"videos": []}); vids = data["videos"]; byid = {v["id"]: v for v in vids}
    changed = False; now = datetime.now(timezone.utc); cands = []
    if "--backfill" in sys.argv:
        for tab in ("videos", "shorts"):
            for l in ytdlp("--print", "%(id)s\t%(title)s", f"{SITE['channelUrl']}/{tab}"):
                vid, title = l.split("\t", 1); cands.append(item(vid, title, tab == "shorts"))
    try: cands += fetch_feed()
    except Exception as e:
        print("RSS 失敗 → 改用 yt-dlp", e)
        try: cands += fallback_list()
        except Exception as e2: print("備援也失敗", e2)
    for f in cands:
        v = byid.get(f["id"])
        if v:
            if not v.get("published") and f.get("published"): v["published"] = utc(f["published"]); changed = True
            continue
        if f["published"] and datetime.fromisoformat(f["published"]) > now: print("skip future", f["id"]); continue
        ok, d = decide(f, SITE["channelUrl"]); f.pop("views", None)
        if not ok: print("skip（尚未公開/首播前/無法判斷）", f["id"], f["title"][:30]); continue
        if d and (len(d) > 10 or not f["published"]): f["published"] = d
        if not f["published"]: continue
        f["published"] = utc(f["published"]); f["topics"] = topics_for(f["title"])
        vids.append(f); byid[f["id"]] = f; changed = True; print("NEW", f["id"], f["title"][:40], f["topics"])
    if changed:
        vids.sort(key=lambda v: v.get("published") or "", reverse=True); save("data/videos.json", data)
    s = update_series(vids) if "--no-series" not in sys.argv else False
    p = update_podcast_feed()
    if changed or s or p: bump_sw(); print("changed; sw bumped")
    else: print("no changes")

if __name__ == "__main__": main()
