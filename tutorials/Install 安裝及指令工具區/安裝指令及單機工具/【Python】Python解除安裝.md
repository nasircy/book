# 【Python】解除安裝Python

這個是清理Home Brew 的指令

```css
brew cleanup
```

## HomeBrew 解除使用 HomeBrew安裝的 Python

```css
brew list | grep python
brew uninstall [another-python-version]
brew uninstall python@3.13
brew cleanup
```

### 如果是從官方 PKG檔解除安裝的話：

1. **刪除 Python 框架 (Framework)：**
    
    ```css
    # 查看你安裝了哪些版本
    ls /Library/Frameworks/Python.framework/Versions/
    # 假設你看到了 3.11，就刪除它。請自行替換 3.11
    sudo rm -rf /Library/Frameworks/Python.framework/Versions/3.11
    ```
    
    *(如果你有多個版本，請重複執行 `rm -rf` 指令)*
    
2. **刪除應用程式資料夾：**Bash
    
    ```css
    # 同樣，請自行替換 3.11
    sudo rm -rf "/Applications/Python 3.11"
    ```
    
3. **刪除 `/usr/local/bin` 中的符號連結 (Symlinks)：**
官方安裝程式會在這裡建立捷徑 (symlinks) 來讓你執行 `python3` 和 `pip3`。Bash
    
    ```css
    # 執行 ls -l /usr/local/bin/python* 來查看有哪些連結
    # 它們會顯示 -> /Library/Frameworks/Python.framework/...
    
    # 刪除這些連結 (請小心確認！)：
    sudo rm /usr/local/bin/python3
    sudo rm /usr/local/bin/pip3
    sudo rm /usr/local/bin/idle3
    sudo rm /usr/local/bin/pydoc3
    
    # 你可能還需要刪除有版本號的連結
    sudo rm /usr/local/bin/python3.11
    sudo rm /usr/local/bin/pip3.11
    ```
    

---

### 第 3 步：刪除 pip3 安裝的「全域套件」

這就是你提到的 `pip3` 安裝的套件。如果你是按照「全域安裝」（沒有用虛擬環境）的方式，套件會在這裡：

1. **刪除使用者層級的 `pip` 套件：**Bash
    
    ```css
    # 這是使用者家目錄下的 Python 函式庫
    # 同樣，請替換 3.11 為你安裝的版本
    rm -rf ~/Library/Python/3.11/
    ```
    
2. **刪除 `pip` 的快取 (Cache)：**Bash
    
    ```css
    rm -rf ~/Library/Python/3.11/
    ```
    

---

### 第 4 步：清理你的 Shell 設定檔 (非常重要)

安裝程式（尤其是 `pyenv` 或 Homebrew）很可能會修改你的 shell 設定檔（例如 `.zshrc`），把它的路徑（`$PATH`）加到最前面，導致系統混亂。

1. **編輯你的設定檔：**
（絕大多數 Mac 現在預設使用 Zsh）Bash
    
    `nano ~/.zshrc`
    
    *(如果你使用 Bash，請編輯 `~/.bash_profile`)*
    
2. **尋找並刪除** 任何跟 Homebrew 或 Python 相關的 `PATH` 設定。Bash
    - 刪除看起來像這樣的行：
    
    ```css
    # 可能是 Homebrew 的
    export PATH="/opt/homebrew/bin:$PATH"
    export PATH="/opt/homebrew/opt/python@3.11/libexec/bin:$PATH"
    
    # 可能是 pyenv 的
    eval "$(pyenv init -)"
    
    # 可能是官方安裝程式的
    PATH="/Library/Frameworks/Python.framework/Versions/3.11/bin:${PATH}"
    ```
    
3. **儲存並退出：**
在 `nano` 編輯器中，按下 `Control + O` (儲存)，然後 `Control + X` (退出)。

---

### 第 5 步：驗證是否已清除乾淨

1. **完全關閉並重新開啟**你的終端機 (Terminal)。
2. **檢查 `python3` 指向哪裡：**Bash
    
    ```css
    which python3
    ```
    
    - **成功：** 你應該會看到 `/usr/bin/python3`。這表示你現在使用的是 Mac 系統內建的安全版本。
    - **失敗：** 如果它顯示 `command not found` (找不到指令) 或指向其他路徑，表示還有殘留。
3. **檢查 `pip3` 指向哪裡：**Bash
    
    ```css
    which pip3
    ```
    
    - **成功：** 你很可能會看到 `command not found`。這是**好事**，因為系統內建的 Python 預設不一定會把 `pip3` 放在 `PATH` 裡。
    - **如果它指向 `/usr/bin/pip3`**：這也是正常的，代表它是系統內建的。