# 【Github】Github Git 操作

git clone 之後，日常工作流程（在終端機中）會是：

git status (看一下改了什麼)

git add . (把所有變更都加進來)

git commit -m "我新增了某某功能" (在本機存檔)

git push (上傳到 GitHub)

---

切換專案的話 ： 

假設你**目前在 `專案A`** 裡面工作，然後想**切換到 `專案B`** 去 PUSH 一些東西。

1. (你正在 `.../GitHub/專案A` 資料夾裡)
2. 輸入 `cd ..`
    - (你現在退回到了 `.../GitHub` 資料夾)
3. 輸入 `cd 專案B`
    - (你現在成功**切換到 `專案B`** 了！)
4. 現在可以在 `專案B` 裡面使用 `git status`, `git pull`, `git push` 等所有指令了。