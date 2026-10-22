#!/usr/bin/env python3
"""文章與簡報＋Podcast：處理 content/inbox/ → 產生 data/articles.json。
- inbox 支援：.md / .docx（pandoc 轉 md）/ .pdf / .pptx / .ppt（LibreOffice 轉 PDF，兩者都保留）/
  .txt 或 .url（內含 Google Slides / Docs 連結 → 建立連結文章）
- content/articles/*.md 用 front-matter：title, date, summary, tags, video, link, file, sample
- 音檔 .mp3/.m4a/.aac/.ogg/.wav → content/podcast/（同檔名的 .md/.txt 當節目說明；說明裡「00:00 標題」的行會變成章節）
- .txt 內含 Spotify / Apple Podcasts / SoundCloud / YouTube 連結 → Podcast 外部集數
- content/files/ 裡沒有被任何 md 引用的 PDF 會自動成為一篇（標題取檔名）
用法：python scripts/build_articles.py   （本機與 GitHub Action 共用）"""
import os, re, json, shutil, subprocess, sys, datetime, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
P = lambda *a: os.path.join(ROOT, *a)
ART, FILES, INBOX, THUMBS, POD = P("content/articles"), P("content/files"), P("content/inbox"), P("content/files/thumbs"), P("content/podcast")
TODAY = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)).strftime("%Y-%m-%d")  # 台北日期
for d in (ART, FILES, INBOX, THUMBS, POD): os.makedirs(d, exist_ok=True)

def slug(name):
    s = re.sub(r"[\s　]+", "-", os.path.splitext(name)[0].strip())
    s = re.sub(r"[^\w\-\u3400-\u9fff]", "", s)
    return s or "article"

def unique(path):
    base, ext = os.path.splitext(path); i = 2
    while os.path.exists(path): path = f"{base}-{i}{ext}"; i += 1
    return path

def parse_fm(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.S)
    if not m: return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" not in line or line.strip().startswith("#"): continue
        k, v = line.split(":", 1); k, v = k.strip(), v.strip()
        if v.startswith("[") and v.endswith("]"):
            v = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
        elif v.lower() in ("true", "false"): v = v.lower() == "true"
        else: v = v.strip("'\"")
        meta[k] = v
    return meta, text[m.end():]

def fm(meta):
    out = ["---"]
    for k, v in meta.items():
        out.append(f"{k}: [{', '.join(v)}]" if isinstance(v, list) else f"{k}: {str(v).lower() if isinstance(v, bool) else v}")
    return "\n".join(out + ["---", ""])

def first_heading(body):
    m = re.search(r"^#{1,3}\s+(.+)$", body, re.M); return m.group(1).strip() if m else None

def plain_summary(body, n=90):
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)|<[^>]+>|[#>*_`\[\]]|\(http[^)]*\)", "", body)
    t = re.sub(r"\s+", " ", t).strip(); return t[:n] + ("…" if len(t) > n else "")

def soffice_pdf(src):
    out = os.path.dirname(src)
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", out, src], check=True, capture_output=True, timeout=300)
    return os.path.splitext(src)[0] + ".pdf"

# ---------- 1. 處理 inbox ----------
AUDIO = (".mp3", ".m4a", ".aac", ".ogg", ".wav", ".opus")
PODHOST = re.compile(r"open\.spotify\.com|podcasts\.apple\.com|soundcloud\.com|youtube\.com|youtu\.be|podbean|firstory|soundon|anchor\.fm|kkbox", re.I)

def process_inbox():
    done = []
    names = sorted(os.listdir(INBOX))
    audio_stems = {os.path.splitext(n)[0] for n in names if os.path.splitext(n)[1].lower() in AUDIO}
    for name in names:  # 先處理音檔與它的同名說明
        stem, ext = os.path.splitext(name); ext = ext.lower()
        if ext not in AUDIO: continue
        s = slug(name); dst = unique(os.path.join(POD, s + ext)); shutil.move(os.path.join(INBOX, name), dst)
        s2 = os.path.splitext(os.path.basename(dst))[0]; meta, body = {}, ""
        for nx in (".md", ".txt"):
            np_ = os.path.join(INBOX, stem + nx)
            if os.path.exists(np_):
                meta, body = parse_fm(open(np_, encoding="utf-8", errors="ignore").read()); os.remove(np_); break
        meta.setdefault("title", first_heading(body) or stem); meta.setdefault("date", TODAY); meta["audio"] = os.path.basename(dst)
        open(os.path.join(POD, s2 + ".md"), "w", encoding="utf-8").write(fm(meta) + body)
        done.append(name); print("podcast →", name)
    for name in sorted(os.listdir(INBOX)):
        src = os.path.join(INBOX, name)
        if name.startswith(".") or name.lower() in ("readme.md",) or not os.path.isfile(src): continue
        ext = os.path.splitext(name)[1].lower(); s = slug(name)
        if ext == ".md":
            meta, body = parse_fm(open(src, encoding="utf-8").read())
            meta.setdefault("title", first_heading(body) or os.path.splitext(name)[0]); meta.setdefault("date", TODAY)
            dst = unique(os.path.join(ART, s + ".md")); open(dst, "w", encoding="utf-8").write(fm(meta) + body); os.remove(src)
        elif ext == ".docx":
            keep = unique(os.path.join(FILES, s + ".docx")); shutil.move(src, keep)
            dst = unique(os.path.join(ART, s + ".md")); s2 = os.path.splitext(os.path.basename(dst))[0]
            body = subprocess.run(["pandoc", keep, "-t", "gfm", "--wrap=none", f"--extract-media=media/{s2}"], cwd=ART,
                                  capture_output=True, text=True, check=True).stdout
            meta = {"title": first_heading(body) or os.path.splitext(name)[0], "date": TODAY, "file": os.path.basename(keep)}
            open(dst, "w", encoding="utf-8").write(fm(meta) + body)
        elif ext in (".pdf", ".pptx", ".ppt", ".odp"):
            shutil.move(src, unique(os.path.join(FILES, s + ext)))
        elif ext in (".txt", ".url", ".webloc"):
            t = open(src, encoding="utf-8", errors="ignore").read(); m = re.search(r"https?://\S+", t)
            if not m: continue
            meta = {"title": os.path.splitext(name)[0], "date": TODAY, "link": m.group(0).rstrip(")>\"'")}
            folder = POD if PODHOST.search(meta["link"]) else ART
            open(unique(os.path.join(folder, s + ".md")), "w", encoding="utf-8").write(fm(meta) + t.replace(m.group(0), "").strip() + "\n"); os.remove(src)
        else:
            print("略過不支援的檔案:", name); continue
        done.append(name); print("inbox →", name)
    return done

# ---------- 2. 轉檔與縮圖 ----------
def convert_files():
    for name in os.listdir(FILES):
        ext = os.path.splitext(name)[1].lower()
        if ext in (".pptx", ".ppt", ".odp"):
            pdf = os.path.join(FILES, os.path.splitext(name)[0] + ".pdf")
            if not os.path.exists(pdf):
                if shutil.which("soffice"): soffice_pdf(os.path.join(FILES, name)); print("pptx → pdf:", name)
                else: print("需要 LibreOffice 才能轉:", name)
    for name in os.listdir(FILES):
        if name.lower().endswith(".pdf"):
            th = os.path.join(THUMBS, os.path.splitext(name)[0] + ".png")
            if not os.path.exists(th) and shutil.which("pdftoppm"):
                subprocess.run(["pdftoppm", "-f", "1", "-l", "1", "-png", "-scale-to", "480", "-singlefile",
                                os.path.join(FILES, name), th[:-4]], capture_output=True)

def git_date(path):
    try:
        d = subprocess.run(["git", "log", "--diff-filter=A", "--format=%cs", "--", path], cwd=ROOT, capture_output=True, text=True).stdout.split()
        if d: return d[-1]
    except Exception: pass
    return TODAY

def embed_url(link):
    m = re.match(r"https://docs\.google\.com/(presentation|document|spreadsheets)/d/([\w-]+)", link or "")
    if not m: return None
    kind, i = m.groups()
    return f"https://docs.google.com/presentation/d/{i}/embed" if kind == "presentation" else f"https://docs.google.com/{kind}/d/{i}/preview"

def pod_embed(link):
    link = link or ""
    m = re.search(r"open\.spotify\.com/(episode|show)/(\w+)", link)
    if m: return f"https://open.spotify.com/embed/{m.group(1)}/{m.group(2)}"
    if "podcasts.apple.com" in link: return link.replace("podcasts.apple.com", "embed.podcasts.apple.com")
    if "soundcloud.com" in link: return "https://w.soundcloud.com/player/?url=" + urllib.parse.quote(link, safe="") + "&color=%23b3202a"
    m = re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{11})", link)
    if m: return f"https://www.youtube.com/embed/{m.group(1)}"
    return None

def build_podcast():
    eps = []
    rel = lambda p: os.path.relpath(p, ROOT).replace(os.sep, "/")
    for name in sorted(os.listdir(POD)):
        if not name.endswith(".md"): continue
        path = os.path.join(POD, name); meta, body = parse_fm(open(path, encoding="utf-8").read())
        chapters = [dict(t=sum(int(x) * 60 ** i for i, x in enumerate(reversed(m.group(1).split(":")))), title=m.group(2).strip())
                    for m in re.finditer(r"^\s*[-*]?\s*((?:\d{1,2}:)?\d{1,2}:\d{2})\s+(.+)$", body, re.M)]
        ep = dict(id=name[:-3], title=meta.get("title") or name[:-3], date=str(meta.get("date") or git_date(path)),
                  summary=meta.get("summary") or plain_summary(re.sub(r"^\s*[-*]?\s*(?:\d{1,2}:)?\d{1,2}:\d{2}.*$", "", body, flags=re.M)),
                  notes=rel(path) if body.strip() else None, chapters=chapters, tags=meta.get("tags") or [], source="local")
        if meta.get("audio"):
            a = os.path.join(POD, meta["audio"])
            if os.path.exists(a): ep["audio"] = rel(a); ep["size"] = os.path.getsize(a)
        if meta.get("link"): ep["link"] = meta["link"]; ep["embed"] = pod_embed(meta["link"])
        if meta.get("video"): ep["video"] = meta["video"]
        eps.append(ep)
    return sorted(eps, key=lambda x: x["date"], reverse=True)

# ---------- 3. 建索引 ----------
def build_index():
    T = json.load(open(P("data/topics.json"), encoding="utf-8")) if os.path.exists(P("data/topics.json")) else {}
    auto = lambda text: [k for k, ws in T.items() if any(w in text for w in ws)]
    items, used = [], set()
    rel = lambda p: os.path.relpath(p, ROOT).replace(os.sep, "/")
    def files_for(stem_or_file):
        stem = os.path.splitext(stem_or_file)[0]; out = {}
        for ext in (".pdf", ".pptx", ".ppt", ".odp", ".docx"):
            f = os.path.join(FILES, stem + ext)
            if os.path.exists(f): out[ext[1:]] = rel(f); used.add(stem + ext)
        th = os.path.join(THUMBS, stem + ".png")
        if os.path.exists(th): out["thumb"] = rel(th)
        return out
    for name in sorted(os.listdir(ART)):
        if not name.endswith(".md"): continue
        path = os.path.join(ART, name); meta, body = parse_fm(open(path, encoding="utf-8").read())
        it = dict(id=name[:-3], kind="md", title=meta.get("title") or first_heading(body) or name[:-3], date=str(meta.get("date") or git_date(path)),
                  summary=meta.get("summary") or plain_summary(body), tags=meta.get("tags") or [], sample=bool(meta.get("sample")))
        if body.strip(): it["md"] = rel(path)
        if meta.get("file"): it.update(files_for(meta["file"]))
        if meta.get("link"):
            it["link"] = meta["link"]; e = embed_url(meta["link"])
            if e: it["embed"] = e
            if not body.strip(): it["kind"] = "slides" if "presentation" in meta["link"] else "link"
        if "pdf" in it and not body.strip(): it["kind"] = "pdf"
        if not it["tags"]: it["tags"] = auto(it["title"] + " " + body[:1500])
        if meta.get("video"):
            v = meta["video"]; m = re.search(r"(?:v=|shorts/|youtu\.be/)([\w-]{11})", v); it["video"] = m.group(1) if m else v
        items.append(it)
    for name in sorted(os.listdir(FILES)):
        stem, ext = os.path.splitext(name)
        if ext.lower() not in (".pdf", ".pptx", ".ppt", ".odp") or name in used: continue
        if ext.lower() != ".pdf" and os.path.exists(os.path.join(FILES, stem + ".pdf")): continue
        f = files_for(name); text = ""
        if "pdf" in f and shutil.which("pdftotext"):
            text = subprocess.run(["pdftotext", "-l", "2", os.path.join(ROOT, f["pdf"]), "-"], capture_output=True, text=True).stdout
        it = dict(id="file-" + stem, kind="pdf" if "pdf" in f else "file", title=stem.replace("_", " "), date=git_date(os.path.join(FILES, name)),
                  summary=plain_summary(text), tags=["簡報"] if ext.lower() != ".pdf" else ["PDF"], sample=False, **f)
        it["tags"] += auto(stem + " " + text[:1500])
        items.append(it)
    items.sort(key=lambda x: x["date"], reverse=True)
    pods = build_podcast()
    ch = False
    for out, obj in ((P("data/articles.json"), items), (P("data/podcast.json"), pods)):
        new = json.dumps(obj, ensure_ascii=False, indent=1) + "\n"
        old = open(out, encoding="utf-8").read() if os.path.exists(out) else ""
        if new != old: open(out, "w", encoding="utf-8").write(new); ch = True
    if ch:
        sw = open(P("sw.js"), encoding="utf-8").read()
        sw = re.sub(r"const C='xgdq-v(\d+)'", lambda m: f"const C='xgdq-v{int(m.group(1))+1}'", sw, count=1)
        open(P("sw.js"), "w", encoding="utf-8").write(sw); print(f"articles.json 更新（{len(items)} 篇）、podcast.json（{len(pods)} 集），sw 版本 +1")
    else: print("articles.json 無變更")

if __name__ == "__main__":
    process_inbox(); convert_files(); build_index()
