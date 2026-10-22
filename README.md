# 小國大棋 App（PWA）
網址：https://jclhuang.github.io/xiaoguo-daqi/ ｜ YouTube：https://www.youtube.com/@jameshuang4096 ｜ 姊妹站：內觀與宇宙 https://jclhuang.github.io/inner-cosmos/

分頁：首頁（最新影片、精選系列、最新文章與 Podcast）／影片（依播放清單分系列）／文章與簡報／Podcast。
- 改名、簡介、首頁精選系列、Podcast 平台按鈕：`config.js`
- 個別影片手動隱藏／精選：`data/overrides.json`（`{"影片ID":{"hide":true}}`）
- 主題標籤規則：`data/topics.json`

## 自動匯入新影片
- `.github/workflows/update-videos.yml`：每天台北 03:00（19:00 UTC；GitHub 排程常延遲 1–3 小時），也可在 Actions 頁手動 Run。
- `scripts/update_videos.py`：讀頻道 RSS（失敗時改用 yt-dlp），合併進 `data/videos.json`（不刪舊的）；**預約首播、未公開影片會跳過，等真的公開後下一次執行才加入**。同時抓播放清單到 `data/series.json`（影片頁依此分系列）。
- 若日後有 Podcast RSS，把網址填到 `data/site.json` 的 `podcastFeed`，每天會自動匯入集數。
- GitHub 會在 60 天沒有 repo 活動時停用排程；workflow 在 50 天無 commit 時會自動做一個 keepalive 空 commit。

## 如何新增文章或 Podcast
**方法一：傳給助理**（聊天裡傳檔案或連結）。

**方法二：GitHub 網頁拖拉上傳**
1. 打開 https://github.com/jclhuang/xiaoguo-daqi/upload/main/content/inbox
2. 拖進檔案：
   - 文章：`.docx`（Word）、`.pdf`、`.pptx`、`.md`，或內含 Google 簡報／文件連結的 `.txt`
   - Podcast：`.mp3`／`.m4a` 音檔；同檔名的 `.txt` 或 `.md` 會變成節目說明（例：`EP01.mp3` + `EP01.txt`）。說明裡像 `00:00 開場`、`12:30 新加坡的組屋` 這樣的行會變成可點的章節。
   - Podcast 外部平台：內含 Spotify／Apple Podcasts／SoundCloud／YouTube 連結的 `.txt`（會內嵌播放器）
3. 按綠色「Commit changes」，1–3 分鐘後自動上線（進度：https://github.com/jclhuang/xiaoguo-daqi/actions）。

自訂標題、摘要、標籤：在 .md 開頭加 front-matter：
```
---
title: 標題
date: 2026-10-22
summary: 一兩句摘要
tags: [新加坡, 台灣]
video: https://www.youtube.com/watch?v=XXXXXXXXXXX
---
```
刪除：刪掉 `content/articles/`、`content/files/` 或 `content/podcast/` 裡的檔案即可，索引會自動更新。

### ⚠ 音檔大小限制
- GitHub 單一檔案上限 **100 MB**（網頁上傳上限 25 MB）。超過請先壓成 64–96 kbps 的 mp3（1 小時約 30–45 MB），或放到 Spotify／SoundCloud 等平台，再用連結 .txt 方式加入。
- GitHub Pages 的 repo 建議總量 **1 GB** 以內；音檔多了建議改用外部平台或 Podcast RSS。
- 音檔不會預先存進手機快取。
