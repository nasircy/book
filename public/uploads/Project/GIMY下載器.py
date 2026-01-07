import os
import re
import time
import requests
import subprocess
import threading
import webbrowser
import json
import queue
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, render_template_string, request, Response, jsonify

# === 設定區 ===
app = Flask(__name__)

# 全局變數控制狀態
STATE = {
    "is_running": False,
    "current_queue": [],
    "log_queue": queue.Queue(),
    "stop_flag": False
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://gimytv.io/',
    'Origin': 'https://gimytv.io'
}

# === 核心邏輯函式 ===

def clean_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename).strip()

def format_seconds(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m}分{s}秒"

def time_str_to_seconds(time_str):
    """將 00:03:20.50 轉為 秒數 (float)"""
    try:
        parts = time_str.split(':')
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    except:
        return 0

def log_to_web(msg, color="white"):
    timestamp = time.strftime("[%H:%M:%S]")
    data = json.dumps({"type": "log", "msg": f"{timestamp} {msg}", "color": color})
    STATE["log_queue"].put(f"data: {data}\n\n")

def update_queue_to_web():
    urls_text = "\n".join(STATE["current_queue"])
    data = json.dumps({"type": "queue_update", "content": urls_text})
    STATE["log_queue"].put(f"data: {data}\n\n")

# 新增：清空前端進度條的指令
def clear_progress_panel():
    data = json.dumps({"type": "clear_progress"})
    STATE["log_queue"].put(f"data: {data}\n\n")

def update_progress_to_web(unique_id, percent, status="downloading", display_name=None, series_name=""):
    if display_name is None:
        display_name = unique_id

    data = json.dumps({
        "type": "progress", 
        "id": unique_id,
        "name": display_name,
        "series": series_name,
        "percent": percent, 
        "status": status
    })
    STATE["log_queue"].put(f"data: {data}\n\n")

def extract_m3u8(html):
    if not html: return None
    patterns = [
        r"var\s+url\s*=\s*['\"](http.*?\.m3u8.*?)['\"]",
        r"[\"']?url[\"']?\s*:\s*['\"](http.*?\.m3u8.*?)['\"]",
        r"src=['\"](http.*?\.m3u8.*?)['\"]",
        r"vid\s*:\s*['\"](http.*?\.m3u8.*?)['\"]"
    ]
    for p in patterns:
        m = re.search(p, html)
        if m: return m.group(1).replace('\\/', '/')
    return None

def get_m3u8_duration(m3u8_url, headers):
    try:
        resp = requests.get(m3u8_url, headers=headers, timeout=6)
        content = resp.text
        if "#EXT-X-STREAM-INF" in content:
            for line in content.splitlines():
                if line.strip().endswith('.m3u8'):
                    return get_m3u8_duration(urljoin(m3u8_url, line.strip()), headers)
        
        total_seconds = 0
        for match in re.finditer(r"#EXTINF:(\d+(\.\d+)?),?", content):
            total_seconds += float(match.group(1))
        return total_seconds
    except:
        return 0

def download_file_with_progress(m3u8_url, output_path, referer, threads, unique_id, display_name, series_name, total_duration):
    cmd = [
        'ffmpeg', 
        '-headers', f'Referer: {referer}',
        '-headers', f'User-Agent: {HEADERS["User-Agent"]}',
        '-reconnect', '1', '-reconnect_at_eof', '1', '-reconnect_streamed', '1',
        '-reconnect_delay_max', '30',
        '-rw_timeout', '15000000',
        '-timeout', '15000000',
        '-threads', str(threads),
        '-i', m3u8_url,
        '-c', 'copy', '-bsf:a', 'aac_adtstoasc',
        '-y', '-loglevel', 'info', 
        '-stats', 
        output_path
    ]

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf-8', errors='ignore')
    
    start_time = time.time()
    last_update_time = 0
    
    time_pattern = re.compile(r'time=(\d+:\d+:\d+\.\d+)')

    for line in process.stdout:
        if STATE["stop_flag"]:
            process.kill()
            raise Exception("使用者強制停止")
        
        match = time_pattern.search(line)
        if match:
            current_time_str = match.group(1)
            current_seconds = time_str_to_seconds(current_time_str)
            
            if total_duration > 0:
                percent = min(99, int((current_seconds / total_duration) * 100))
                
                if time.time() - last_update_time > 0.5:
                    update_progress_to_web(unique_id, percent, "downloading", display_name, series_name)
                    last_update_time = time.time()

    process.wait()
    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, cmd)

def process_episode(task, series_title, ffmpeg_threads):
    if STATE["stop_flag"]: return
    
    ep_name = task['name'] 
    short_name = ep_name.replace(series_title, "").strip("- ") 
    output_path = os.path.join(series_title, f"{ep_name}.mp4")

    if os.path.exists(output_path):
        if os.path.getsize(output_path) > 1024*1024:
            update_progress_to_web(ep_name, 100, "finished", short_name, series_title)
            log_to_web(f"[{series_title}] {short_name} 已存在，跳過", "gray")
            return
        else:
            os.remove(output_path)

    try:
        update_progress_to_web(ep_name, 0, "starting", short_name, series_title)

        full_url = urljoin(task['base'], task['href'])
        r = requests.get(full_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        raw_links = []
        tabs = soup.select('#playTab li a') or soup.select('.play_list li a')
        for t in tabs:
            if t.get('href'): raw_links.append(t.get('href'))
        
        for iframe in soup.select('iframe'):
            src = iframe.get('src')
            if src and 'http' in src and 'google' not in src: raw_links.append(src)
        
        if not raw_links: raw_links.append(task['href'])
        raw_links = list(dict.fromkeys(raw_links))[:8] 

        success = False
        
        for idx, link in enumerate(raw_links):
            if STATE["stop_flag"]: return
            if success: break

            target_url = urljoin(task['base'], link)
            try:
                rr = requests.get(target_url, headers=HEADERS, timeout=6)
                m3u8 = extract_m3u8(rr.text)
                final_referer = target_url

                if not m3u8:
                    soup_in = BeautifulSoup(rr.text, 'html.parser')
                    iframe = soup_in.select_one('iframe')
                    if iframe and iframe.get('src'):
                        iframe_url = urljoin(target_url, iframe.get('src'))
                        rr2 = requests.get(iframe_url, headers={'Referer': target_url, 'User-Agent': HEADERS['User-Agent']}, timeout=6)
                        m3u8 = extract_m3u8(rr2.text)
                        final_referer = iframe_url

                if m3u8:
                    try:
                        log_to_web(f"正在計算 {short_name} 時長...", "gray")
                        total_duration = get_m3u8_duration(m3u8, {'User-Agent': HEADERS['User-Agent'], 'Referer': final_referer})
                        if total_duration < 10: continue 
                    except: continue

                    start_t = time.time()
                    try:
                        download_file_with_progress(m3u8, output_path, final_referer, ffmpeg_threads, ep_name, short_name, series_title, total_duration)
                        
                        if os.path.exists(output_path) and os.path.getsize(output_path) > 500*1024:
                            cost = time.time() - start_t
                            update_progress_to_web(ep_name, 100, "finished", short_name, series_title)
                            log_to_web(f"[{series_title}] {short_name} 下載完成 ({format_seconds(cost)})", "#50FA7B")
                            success = True
                            break
                    except Exception as e:
                        if "使用者強制停止" in str(e): raise e
                        log_to_web(f"⚠️ [{series_title}] {short_name} 線路 {idx+1} 斷線或錯誤，換線中...", "#FFB86C")
                        continue

            except Exception:
                continue
        
        if not success:
            update_progress_to_web(ep_name, 0, "error", short_name, series_title)
            log_to_web(f"❌ [{series_title}] {short_name} 下載失敗", "#FF5555")

    except Exception as e:
        log_to_web(f"[{series_title}] {short_name} 系統錯誤: {e}", "#FF5555")

def worker_thread(batch_size, ffmpeg_threads):
    log_to_web(f"🚀 排程啟動 (每部劇自動清空)", "#8BE9FD")

    while STATE["current_queue"] and not STATE["stop_flag"]:
        current_url = STATE["current_queue"][0]
        
        try:
            log_to_web(f"正在解析: {current_url}", "#BD93F9")
            r = requests.get(current_url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            title = soup.select_one('.player_title h1 a') or soup.select_one('title')
            series_name = clean_filename(title.text.strip().replace("線上看",""))
            
            if not os.path.exists(series_name): os.makedirs(series_name)

            playlist = soup.select_one('ul[id^="con_playlist_"].active') or soup.select_one('.playlist ul')
            if not playlist:
                log_to_web(f"[錯誤] 無法讀取播放列表，跳過: {series_name}", "#FF5555")
                STATE["current_queue"].pop(0)
                update_queue_to_web()
                continue

            tasks = []
            for a in playlist.find_all('a'):
                if a.get('href'):
                    tasks.append({
                        'name': f"{series_name} - {a.text.strip()}",
                        'href': a.get('href'),
                        'base': "https://gimytv.io"
                    })
            
            # === 關鍵修改：在開始新的一部劇下載前，清空前端進度條 ===
            clear_progress_panel()
            # ===================================================

            log_to_web(f"[{series_name}] 共 {len(tasks)} 集。開始下載...", "#FFB86C")

            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                futures = [executor.submit(process_episode, t, series_name, ffmpeg_threads) for t in tasks]
                for future in as_completed(futures):
                    if STATE["stop_flag"]: break
            
            if STATE["stop_flag"]:
                log_to_web("🛑 任務強制停止", "#FF5555")
                break
            
            log_to_web(f"✅ [{series_name}] 完工！準備下一部...", "#50FA7B")
            time.sleep(2) # 稍微停頓一下讓使用者看到完工訊息
            
            if STATE["current_queue"]:
                STATE["current_queue"].pop(0)
                update_queue_to_web()

        except Exception as e:
            log_to_web(f"[系統錯誤] {e}", "#FF5555")
            if STATE["current_queue"]:
                STATE["current_queue"].pop(0)
                update_queue_to_web()

    STATE["is_running"] = False
    log_to_web("💤 所有任務結束。", "white")

# === Flask 路由 ===

@app.route('/')
def index():
    html = """
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gimy Web 下載器 v3.3 自動清空版</title>
        <style>
            body { background-color: #121212; color: #e0e0e0; font-family: 'Microsoft JhengHei', sans-serif; margin: 0; padding: 20px; }
            .container { max-width: 950px; margin: 0 auto; }
            h1 { color: #007AFF; text-align: center; margin-bottom: 5px; }
            .subtitle { text-align: center; color: #666; font-size: 12px; margin-bottom: 20px; }
            .card { background-color: #1e1e1e; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); margin-bottom: 20px; }
            label { display: block; margin-bottom: 8px; font-weight: bold; color: #bbb; }
            textarea { width: 100%; height: 100px; background: #2d2d2d; color: #fff; border: 1px solid #444; border-radius: 5px; padding: 10px; font-family: monospace; resize: vertical; box-sizing: border-box; }
            
            .row { display: flex; gap: 20px; }
            .col { flex: 1; }
            input[type="number"] { width: 100%; padding: 10px; background: #2d2d2d; color: #fff; border: 1px solid #444; border-radius: 5px; box-sizing: border-box; }
            
            .btn-group { display: flex; gap: 10px; margin-top: 20px; }
            button { flex: 1; padding: 12px; font-size: 16px; border: none; border-radius: 5px; cursor: pointer; transition: 0.2s; font-weight: bold; }
            
            #btn-start { background-color: #007AFF; color: white; }
            #btn-start:hover { background-color: #005bb5; }
            #btn-start:disabled { background-color: #444; cursor: not-allowed; }
            
            #btn-stop { background-color: #FF3B30; color: white; }
            #btn-stop:hover { background-color: #cc2f26; }

            /* Grid 佈局 */
            #progress-area { 
                display: grid; 
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); 
                gap: 12px; 
            }
            .progress-card { 
                background: #252525; 
                border-radius: 6px; 
                padding: 12px; 
                border: 1px solid #333; 
                position: relative;
                transition: transform 0.2s;
            }
            .progress-card:hover { border-color: #555; }
            
            .series-tag {
                font-size: 10px;
                color: #888;
                margin-bottom: 4px;
                white-space: nowrap; 
                overflow: hidden; 
                text-overflow: ellipsis;
            }

            .progress-header { display: flex; justify-content: space-between; font-size: 15px; margin-bottom: 8px; font-weight: bold; }
            
            .progress-bar-bg { width: 100%; height: 6px; background: #444; border-radius: 3px; overflow: hidden; }
            /* 預設藍色 (下載中) */
            .progress-bar-fill { height: 100%; width: 0%; background: #007AFF; transition: width 0.3s ease-out; }
            
            /* 完成狀態 (綠色) */
            .status-finished .progress-bar-fill { background: #50FA7B !important; }
            .status-finished .status-text { color: #50FA7B !important; }
            
            /* 錯誤狀態 (紅色) */
            .status-error .progress-bar-fill { background: #FF5555 !important; }
            .status-error .status-text { color: #FF5555 !important; }

            .status-text { font-size: 12px; color: #007AFF; margin-top: 6px; text-align: right; }

            .log-window { height: 300px; background: #000; border: 1px solid #333; border-radius: 5px; padding: 10px; overflow-y: auto; font-family: 'Consolas', monospace; font-size: 13px; white-space: pre-wrap; line-height: 1.4; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Gimy Web 下載器</h1>
            <div class="subtitle">v3.3 自動清空舊進度</div>
            
            <div class="card">
                <label>下載進度 (換劇時自動清空)</label>
                <div id="progress-area">
                    <div style="color: #666; font-size: 14px; grid-column: 1 / -1; text-align: center; padding: 20px;">
                        等待任務啟動...
                    </div>
                </div>
            </div>

            <div class="card">
                <label>影片網址隊列</label>
                <textarea id="urlInput" placeholder="請貼上 Gimytv 網址..."></textarea>
                
                <div class="row" style="margin-top: 15px;">
                    <div class="col">
                        <label>併發下載數 (Batch)</label>
                        <input type="number" id="batchSize" value="4" min="1" max="10">
                    </div>
                    <div class="col">
                        <label>FFmpeg 線程 (Threads)</label>
                        <input type="number" id="threads" value="8" min="1" max="32">
                    </div>
                </div>

                <div class="btn-group">
                    <button id="btn-start" onclick="startDownload()">🚀 開始隊列下載</button>
                    <button id="btn-stop" onclick="stopDownload()" disabled>🛑 停止</button>
                </div>
            </div>

            <div class="card">
                <label>詳細日誌</label>
                <div class="log-window" id="logBox"></div>
            </div>
        </div>

        <script>
            const logBox = document.getElementById('logBox');
            const urlInput = document.getElementById('urlInput');
            const progressArea = document.getElementById('progress-area');
            const btnStart = document.getElementById('btn-start');
            const btnStop = document.getElementById('btn-stop');

            const evtSource = new EventSource("/stream");
            
            evtSource.onmessage = function(e) {
                const data = JSON.parse(e.data);
                
                if (data.type === 'log') {
                    const div = document.createElement('div');
                    div.style.color = data.color;
                    div.textContent = data.msg;
                    logBox.appendChild(div);
                    logBox.scrollTop = logBox.scrollHeight;
                } 
                else if (data.type === 'queue_update') {
                    urlInput.value = data.content;
                }
                else if (data.type === 'clear_progress') {
                    // 收到後端指令：清空所有進度卡片
                    progressArea.innerHTML = '';
                }
                else if (data.type === 'progress') {
                    updateProgressCard(data.id, data.name, data.percent, data.status, data.series);
                }
            };

            function updateProgressCard(uniqueId, displayName, percent, status, seriesName) {
                // 使用 btoa 將中文ID轉為 Base64
                const safeId = 'prog-' + btoa(unescape(encodeURIComponent(uniqueId)));
                let card = document.getElementById(safeId);
                
                if (!card) {
                    if (progressArea.innerHTML.includes('等待任務啟動')) {
                        progressArea.innerHTML = ''; 
                    }
                    
                    card = document.createElement('div');
                    card.id = safeId;
                    card.className = 'progress-card';
                    card.innerHTML = `
                        <div class="series-tag">${seriesName}</div>
                        <div class="progress-header">
                            <span>${displayName}</span>
                            <span class="percent-text">0%</span>
                        </div>
                        <div class="progress-bar-bg">
                            <div class="progress-bar-fill" style="width: 0%"></div>
                        </div>
                        <div class="status-text">準備下載...</div>
                    `;
                    progressArea.appendChild(card);
                }

                const fill = card.querySelector('.progress-bar-fill');
                const percentText = card.querySelector('.percent-text');
                const statusText = card.querySelector('.status-text');

                fill.style.width = percent + '%';
                percentText.textContent = percent + '%';

                card.classList.remove('status-finished', 'status-error');

                if (status === 'finished') {
                    card.classList.add('status-finished');
                    statusText.textContent = '✅ 完成';
                } else if (status === 'error') {
                    card.classList.add('status-error');
                    statusText.textContent = '❌ 失敗';
                } else {
                    statusText.textContent = '⏬ 下載中...';
                    statusText.style.color = '#007AFF';
                }
            }

            function startDownload() {
                const urls = urlInput.value.trim();
                const batch = document.getElementById('batchSize').value;
                const threads = document.getElementById('threads').value;

                if (!urls) { alert("請輸入網址！"); return; }

                fetch('/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ urls: urls, batch: batch, threads: threads })
                }).then(res => res.json()).then(data => {
                    if (data.status === 'started') {
                        btnStart.disabled = true;
                        btnStop.disabled = false;
                        urlInput.readOnly = true;
                    }
                });
            }

            function stopDownload() {
                fetch('/stop').then(res => res.json()).then(data => {
                    btnStart.disabled = false;
                    btnStop.disabled = true;
                    urlInput.readOnly = false;
                });
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/stream')
def stream():
    def event_stream():
        while True:
            msg = STATE["log_queue"].get()
            yield msg
    return Response(event_stream(), mimetype="text/event-stream")

@app.route('/start', methods=['POST'])
def start_process():
    if STATE["is_running"]: return jsonify({"status": "already_running"})
    
    data = request.json
    raw_urls = data.get('urls', '')
    STATE["current_queue"] = [line.strip() for line in raw_urls.split('\n') if line.strip()]
    
    if not STATE["current_queue"]: return jsonify({"status": "empty"})

    batch_size = int(data.get('batch', 4))
    ffmpeg_threads = int(data.get('threads', 8))
    
    STATE["is_running"] = True
    STATE["stop_flag"] = False
    
    t = threading.Thread(target=worker_thread, args=(batch_size, ffmpeg_threads))
    t.daemon = True
    t.start()
    
    return jsonify({"status": "started"})

@app.route('/stop')
def stop_process():
    STATE["stop_flag"] = True
    STATE["is_running"] = False
    return jsonify({"status": "stopped"})

if __name__ == '__main__':
    threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    print("啟動 Web 伺服器... 請等待瀏覽器自動開啟")
    app.run(port=5000, debug=False, threaded=True)