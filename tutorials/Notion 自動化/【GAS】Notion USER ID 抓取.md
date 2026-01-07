# 【GAS】Notion USER ID 抓取

程式代碼 ：

```jsx
/**
 * 【暫時用】執行此函式以取得您自己的 Notion User ID
 */
function getMyNotionUserId() {
  // 在這裡貼上您自己的 API 金鑰
  const NOTION_API_KEY = "ntn_1"; 

  const url = "https://api.notion.com/v1/users/me";
  const options = {
    "method": "GET",
    "headers": {
      "Authorization": "Bearer " + NOTION_API_KEY,
      "Notion-Version": "2022-06-28"
    }
  };

  try {
    const response = UrlFetchApp.fetch(url, options);
    const json = JSON.parse(response.getContentText());
    Logger.log("您的 Notion User ID 是：" + json.id);
    // 執行後請查看日誌 (View > Logs 或「執行紀錄」)
  } catch (e) {
    Logger.log("無法取得 User ID：" + e.message);
  }
}
```