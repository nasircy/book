# 【Project】My 小專案專區

| 工具名稱 | 功能與技術特色摘要 | 傳送門 |
| :--- | :--- | :--- |
| **MAC BitLocker 掛載** | 專為 macOS 設計的自動化工具。透過 `dislocker` 結合 `hdiutil` 技術，讓 Mac 能夠解密並掛載 Windows 特有的 BitLocker NTFS 加密磁碟，並提供介面化選單輸入密碼。 | <a href="/nynotelab/uploads/Project/BitLocker掛載.command" download>🔗 下載</a> |
| **Gimy Downloader** | 基於 Flask 開發的網頁下載介面。支援多線程併發解析與進度追蹤，能自動調用 FFmpeg 下載 m3u8 串流並整合為 MP4。**（註記：本工具僅供學術用途及技術交流使用）** | <a href="/nynotelab/uploads/Project/GIMY下載器.py" download>🔗 下載</a> |
| **Mac Cleaner** | 互動式管理腳本。可檢測 MacFUSE 狀態，並針對 Homebrew、pip3 及 npm 套件進行管理與清理，具備自動 Sudo 救援機制以強制移除權限檔案。 | <a href="/nynotelab/uploads/Project/mac_cleaner.py" download>🔗 下載</a> |

---

### 📂 專案開發筆記
* **MAC BitLocker 掛載**：解決 macOS 無法原生存取加密隨身碟的痛點，整合 Shell 與 AppleScript 提供直覺體驗。
* **Gimy Downloader**：具備強大的錯誤處理與換線機制，下載過程透明化且支援即時進度更新。
* **Mac Cleaner**：幫助開發者快速盤點開發環境中的冗餘套件，保持系統磁碟空間。