# 【Project】NTUB 學分計算機

> **備註：私人使用，不公開**

專為北商大資管系（技優專班）開發。整合 Firebase 雲端資料庫，支援帳號註冊與資料自動同步，能即時計算總學分、專業選修進度及畢業門檻判定。

<iframe 
    src="/uploads/Project/ntub_credit.html" 
    style="width:100%; height:800px; border:1px solid #eee; border-radius:12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);"
    frameborder="0">
</iframe>

---

### 專案開發筆記
* **技術棧**：原生 HTML/CSS/JS + Firebase (Auth & Realtime Database)。
* **自動化計算**：內建 113 學年度最新課程資料庫，勾選即自動更新儀表板狀態。
* **資料同步**：使用者登入後，所有勾選狀態會即時存儲於雲端，更換裝置也能讀取進度。