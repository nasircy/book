# 【GAS】Gmail To Notion 一站式推播

> STEP 1： 建立Notion 資料庫
> 

Notion 有分 新增頁面 跟 新增資料庫，要資料庫才能夠串接一些 API 之類的 

![Screenshot 2025-11-12 at 1.01.51 AM.png](/uploads/Notion/Screenshot_2025-11-12_at_1.01.51_AM.png)

> STEP 2： 建立Notion API 串接金鑰
> 

由於因為 Google 跟 Notion 是不同公司，那他們兩個要串接在一起，就會需要API鑰匙，可以把它想成是一個橋樑 

https://www.notion.so/profile/integrations

從這個連結進去 ，

![Screenshot 2025-11-12 at 1.04.36 AM.png](/uploads/Notion/Screenshot_2025-11-12_at_1.04.36_AM.png)

![Screenshot 2025-11-12 at 1.04.40 AM.png](/uploads/Notion/Screenshot_2025-11-12_at_1.04.40_AM.png)

可以取自己喜歡的名稱 ，然貨關聯空間選自己的Notion 工作空間 

設定完後按下儲存！ 

> STEP 3： 設定整合
> 

建立完整合後我們要建立權限，他目前是在 你的 工作空間，但是並沒有指定哪個頁面哪個資料庫有權限，這裏我們就找要變成 郵件的 資料庫頁面進行勾選 ！ 

![Screenshot 2025-11-12 at 1.07.23 AM.png](/uploads/Notion/Screenshot_2025-11-12_at_1.07.23_AM.png)

> STEP 4： 接著我們要開始紀錄起一些關鍵的資料
> 

我剛剛有說API ，那座橋，那橋在哪裡呢？ 在配置 這裏有個 內部整合密鑰，這個就是橋樑API 

![Screenshot 2025-11-12 at 1.07.49 AM.png](/uploads/Notion/Screenshot_2025-11-12_at_1.07.49_AM.png)

然後還要把Notion 資料庫的網址記住 

![Screenshot 2025-11-12 at 1.10.57 AM.png](/uploads/Notion/Screenshot_2025-11-12_at_1.10.57_AM.png)

這個是等等要用到的Notion 資料庫 ID，他才會知道要存到哪個表！

> STEP 5： 開始設定 Notion 資料庫的 欄位 ：
> 

這個部分就是依照程式碼部分 一定要相同喔！ 

我以我的 為例：

![Screenshot 2025-11-12 at 1.12.34 AM.png](/uploads/Notion/Screenshot_2025-11-12_at_1.12.34_AM.png)

這裏的主旨欄位是 ： 文字

日期時間 欄位是 ： 日期

已讀未讀 欄位是 ： 狀態 

![Screenshot 2025-11-12 at 1.12.39 AM.png](/uploads/Notion/Screenshot_2025-11-12_at_1.12.39_AM.png)

比較特別的是，這裡面記得要一樣的字歐，不然程式會出錯！！

（如果要更改這裏的話，程式碼那邊也要跟著更改 ） 

> STEP 6：Google App script 建立
> 

Notion這邊欄位都建立好後，接著就是要到Google App script 那邊進行程式碼設定了 ！ 

我們剛剛前面拿到了 

Notion API （橋樑 ）、Notion database 連結 （要放到哪個位置）
這著就可以開始 做程式了

![Screenshot 2025-11-12 at 1.17.23 AM.png](/uploads/Notion/Screenshot_2025-11-12_at_1.17.23_AM.png)

從google 雲端硬碟進去，可以建立 Google App script ! 

這是google 的一個強大雲端程式運作工具，可以做很多自動化功能 ！ 

建立完後就可以把下面的代碼貼過去 ！ 

```
const GMAIL_NOTION_API_KEY = "Notion 橋樑請在這裡輸入";

const GMAIL_NOTION_DATABASE_ID = "Notion 資料庫連結";

const STATUS_OPTION_NAME = "未讀";

const GMAIL_NOTION_HEADERS = {
  "Authorization": "Bearer " + GMAIL_NOTION_API_KEY,
  "Notion-Version": "2022-06-28",
  "Content-Type": "application/json"
};

const GMAIL_SYNC_API_RATE_LIMIT_DELAY = 350; 

function checkGmailAndSendToNotion() {
  Logger.log("開始檢查新郵件...");
  
  const threads = GmailApp.search('is:unread in:inbox', 0, 10);
  
  if (threads.length === 0) {
    Logger.log("沒有未讀郵件。");
    return;
  }

  Logger.log(`發現 ${threads.length} 個未讀會話。`);
  let successCount = 0;
  let failCount = 0;

  threads.forEach(thread => {
    const messages = thread.getMessages().filter(m => m.isUnread());

    messages.forEach(message => {
      const subject = message.getSubject();
      const date = message.getDate();
      
      const htmlBody = message.getBody();

      let body = htmlBody;

      body = body.replace(/<style([\s\S]*?)<\/style>/gi, '');
      body = body.replace(/<script([\s\S]*?)<\/script>/gi, '');

      body = body.replace(/<br\s*\/?>/gi, '\n');
      body = body.replace(/<(p|div)[^>]*>/gi, '\n');

      body = body.replace(/<img[^>]*>/gi, ' [圖片] '); 

      body = body.replace(/<a[^>]+href="([^">]+)"[^>]*>([\s\S]*?)<\/a>/gi, (match, url, innerHtml) => {
        
        let text = innerHtml.replace(/<[^>]*>/g, ' ').trim();
        
        if (!text || text.indexOf('[圖片]') !== -1) {
          return ' ';
        }
        
        let urlDisplay = url;
        if (url.length > 100) {
          urlDisplay = "連結過長，已隱藏";
        }

        return `${text} (${urlDisplay})`;
      });

      body = body.replace(/<[^>]*>/g, ' ');

      body = body.replace(/&nbsp;/gi, ' ')
                 .replace(/&amp;/gi, '&')
                 .replace(/&lt;/gi, '<')
                 .replace(/&gt;/gi, '>')
                 .replace(/&quot;/gi, '"');

      body = body.replace(/[ \t]+/g, ' ');
      body = body.replace(/^[ \t]*$/gm, '');
      body = body.replace(/(\r\n|\r|\n){3,}/g, '\n\n');
      body = body.replace(/(\n\[圖片\]\s*)+/g, '\n');
      
      body = body.trim();

      body = body.substring(0, 1900); 
      
      const attachments = message.getAttachments();
      let attachmentNames = [];
      if (attachments.length > 0) {
        attachments.forEach(att => {
          attachmentNames.push(att.getName());
        });
      }

      try {
        createNotionPageFromEmail(subject, date, body, attachmentNames, htmlBody);
        successCount++;
        Logger.log(`成功寫入: ${subject}`);
        
      } catch (e) {
        failCount++;
        Logger.log(`寫入 Notion 失敗: ${subject}, 錯誤: ${e.message}`);
        return; 
      }
    });

    if (failCount === 0) {
      thread.markRead();
    }
  });

  Logger.log(`處理完成。成功 ${successCount} 筆, 失敗 ${failCount} 筆。`);
}

function createNotionPageFromEmail(subject, date, body, attachmentNames, htmlBody) {
  const url = "https://api.notion.com/v1/pages";

  const pageProperties = {
    "主旨": { "title": [{ "text": { "content": subject } }] },
    "日期時間": { "date": { "start": date.toISOString() } },
    "已讀未讀": { "status": { "name": STATUS_OPTION_NAME } }
  };

  const pageChildren = [
    {
      "object": "block",
      "type": "paragraph",
      "paragraph": {
        "rich_text": [
          { "type": "text", "text": { "content": body || "(此郵件無內文)" } }
        ]
      }
    }
  ];

  if (htmlBody) {
    const imgRegex = /<img[^>]+src="([^">]+)"/g;
    let match;
    let imageUrls = [];
    
    while ((match = imgRegex.exec(htmlBody)) !== null) {
      imageUrls.push(match[1]);
    }

    if (imageUrls.length > 0) {
      const uniqueImageUrls = [...new Set(imageUrls)];

      pageChildren.push({
        "object": "block",
        "type": "heading_3",
        "heading_3": {
          "rich_text": [{ "type": "text", "text": { "content": "偵測到的圖片 (Images)" } }]
        }
      });

      uniqueImageUrls.forEach(url => {
        if (url.startsWith("http://") || url.startsWith("https://")) {
          try {
            pageChildren.push({
              "object": "block",
              "type": "image",
              "image": {
                "type": "external",
                "external": {
                  "url": url
                }
              }
            });
          } catch (e) {
            Logger.log(`無法插入圖片 URL: ${url}`);
          }
        }
      });
    }
  }

  if (attachmentNames && attachmentNames.length > 0) {
    pageChildren.push({
      "object": "block",
      "type": "divider",
      "divider": {}
    });
    pageChildren.push({
      "object": "block",
      "type": "heading_3",
      "heading_3": {
        "rich_text": [{ "type": "text", "text": { "content": "附件 (Attachments)" } }]
      }
    });
    attachmentNames.forEach(name => {
      pageChildren.push({
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
          "rich_text": [{ "type": "text", "text": { "content": name } }]
        }
      });
    });
  }

  const payload = {
    "parent": { "database_id": GMAIL_NOTION_DATABASE_ID },
    "properties": pageProperties,
    "children": pageChildren
  };

  const options = {
    "method": "POST",
    "headers": GMAIL_NOTION_HEADERS,
    "payload": JSON.stringify(payload),
    "muteHttpExceptions": true
  };

  const response = UrlFetchApp.fetch(url, options);
  const responseCode = response.getResponseCode();
  const responseBody = response.getContentText();

  if (responseCode !== 200) {
    Logger.log(responseBody);
    throw new Error(`Notion API 錯誤 (Code: ${responseCode}): ${responseBody}`);
  }
}
```

> STEP 7：Google App script 貼上後，把API 跟 Database 接入後，按下儲存，然後按下執行，如果有遇到權限問題，就一路給他權限！
> 

![Screenshot 2025-11-12 at 1.24.39 AM.png](/uploads/Notion/Screenshot_2025-11-12_at_1.24.39_AM.png)

這是執行按鈕！ 

> STEP 8：設定自動推到Notion
> 

剛剛前面都只是做串接動作，那要讓程式一直運作，就需要藉由 Trigger ！ 

這個是自動觸發器，不可能每次手動按執行所以我們要設定 每一分鐘運行一次！（GoogleAppScript 限制）

所以郵件寄送過來，可能要等程式運行時才會收到（1分鐘以內）

依照圖片設定就可以咯～～ 

![Screenshot 2025-11-12 at 1.27.56 AM.png](/uploads/Notion/Screenshot_2025-11-12_at_1.27.56_AM.png)

![Screenshot 2025-11-12 at 1.27.59 AM.png](/uploads/Notion/Screenshot_2025-11-12_at_1.27.59_AM.png)

![Screenshot 2025-11-12 at 1.28.20 AM.png](/uploads/Notion/Screenshot_2025-11-12_at_1.28.20_AM.png)

完成～～～～～

![Screenshot 2025-11-12 at 1.28.22 AM.png](/uploads/Notion/Screenshot_2025-11-12_at_1.28.22_AM.png)