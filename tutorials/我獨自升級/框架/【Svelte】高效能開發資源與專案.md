# 【Svelte】高效能開發資源相關連結重點整理

| 資源名稱 | 內容與特色簡介 | 傳送門 |
| :--- | :--- | :--- |
| **SvelteKit 1.0 釋出新聞** | iThome 報導：SvelteKit 正式進入 1.0 穩定版，標誌著全端框架的成熟，具備極致效能與靈活部署特性 | [🔗 點我](https://www.ithome.com.tw/news/154781) |
| **SvelteKit 路由教學** | Li Hau 影片教學：深入淺出講解「文件即路由」概念，教你如何配置靜態路徑與 `[slug]` 動態參數 | [🔗 點我](https://www.youtube.com/watch?v=9BUf_Bf-xHA) |
| **青山 Qingshan Team** | 實際應用案例：結合數位科技與傳統信仰的萬華文化專案，展示了流暢的互動網頁設計與 Svelte 網站實作的成果 | [🔗 點我](https://qing-shan.vercel.app/team) |

---

###  Svelte / SvelteKit 核心優勢
* **編譯時處理：** 不使用 Virtual DOM，編譯階段即轉為原生 DOM 操作，載入速度極快。
* **檔案即路由：** 在 `src/routes` 資料夾下建立 `+page.svelte` 即可自動生成頁面，開發直覺。
* **動態參數支援：** 使用 `[id]` 等中括號語法即可處理動態 URL，非常適合內容型網站。
* **全端整合：** 內建 SSR (伺服器端渲染) 與 SSG (靜態生成)，完美平衡 SEO 與使用者體驗。