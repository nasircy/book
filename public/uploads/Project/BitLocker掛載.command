#!/bin/bash

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

MOUNT_ROOT="/tmp/bitlocker_mount"
DISLOCKER_FILE="/tmp/bitlocker_file"

function gui_choose() {
    osascript -e "choose from list $2 with title \"BitLocker 管理器\" with prompt \"$1\""
}

function gui_ask_pass() {
    osascript -e "display dialog \"$1\" default answer \"\" with title \"BitLocker 安全解鎖\" with icon caution with hidden answer" | sed 's/text returned://' | sed 's/, button returned:.*//'
}

function gui_alert() {
    osascript -e "display dialog \"$1\" buttons {\"確定\"} default button \"確定\" with icon note with title \"BitLocker 管理器\"" > /dev/null 2>&1
}

function gui_error() {
    osascript -e "display dialog \"$1\" buttons {\"離開\"} default button \"離開\" with icon stop with title \"錯誤\"" > /dev/null 2>&1
    exit 1
}

function do_unmount() {
    if [ ! -d "$MOUNT_ROOT" ] && [ ! -d "$DISLOCKER_FILE" ]; then
        gui_alert "目前似乎沒有掛載任何 BitLocker 磁碟喔！"
        exit 0
    fi

    if [ -d "$MOUNT_ROOT" ]; then
        hdiutil detach "$MOUNT_ROOT" -force 2>/dev/null
    fi
    
    if [ -d "$DISLOCKER_FILE" ]; then
        hdiutil detach "$DISLOCKER_FILE" -force 2>/dev/null
    fi
    
    rm -rf "$MOUNT_ROOT"
    rm -rf "$DISLOCKER_FILE"
    
    gui_alert "✅ 卸載成功！\n您可以安全拔除隨身碟了。"
    exit 0
}

function do_mount() {
    DISK_LIST=$(diskutil list | grep "Windows_NTFS")
    
    if [ -z "$DISK_LIST" ]; then
        gui_error "找不到任何 NTFS 裝置！\n請確認隨身碟是否插好。"
    fi

    MENU_ITEMS="{"
    while read -r line; do
        ID=$(echo "$line" | awk '{print $NF}')
        SIZE=$(echo "$line" | awk '{print $(NF-2) $(NF-1)}')
        MENU_ITEMS="$MENU_ITEMS\"$ID ($SIZE)\","
    done <<< "$DISK_LIST"
    MENU_ITEMS="${MENU_ITEMS%?}}"

    CHOICE=$(gui_choose "請選擇要讀取的隨身碟：" "$MENU_ITEMS")
    if [ "$CHOICE" == "false" ]; then exit 0; fi

    DISK_ID=$(echo "$CHOICE" | awk '{print $1}')
    TARGET_DEV="/dev/$DISK_ID"

    BL_PASS=$(gui_ask_pass "請輸入 BitLocker 密碼：")
    if [ -z "$BL_PASS" ]; then exit 0; fi

    hdiutil detach "$MOUNT_ROOT" -force 2>/dev/null
    hdiutil detach "$DISLOCKER_FILE" -force 2>/dev/null
    mkdir -p "$DISLOCKER_FILE"
    mkdir -p "$MOUNT_ROOT"

    printf '%s\n' "$BL_PASS" | sudo dislocker -V "$TARGET_DEV" -u -- "$DISLOCKER_FILE" --

    if [ ! -f "$DISLOCKER_FILE/dislocker-file" ]; then
        gui_error "❌ 解密失敗！\n可能是密碼錯誤，或是硬體權限問題。"
    fi

    sudo hdiutil attach "$DISLOCKER_FILE/dislocker-file" \
        -imagekey diskimage-class=CRawDiskImage \
        -mountpoint "$MOUNT_ROOT"

    if [ $? -eq 0 ]; then
        open "$MOUNT_ROOT"
        osascript -e "display notification \"隨身碟已掛載成功！\" with title \"BitLocker\""
    else
        gui_error "掛載映像檔失敗 (hdiutil error)。"
    fi
}

sudo -v

if ! command -v dislocker &> /dev/null; then
    gui_error "找不到 dislocker 環境，請先執行先前的安裝腳本。"
fi

ACTION=$(gui_choose "歡迎使用 BitLocker 管理器" "{\"📂 讀取隨身碟 (Mount)\", \"⏏️ 卸載/退出 (Unmount)\"}")

if [[ "$ACTION" == *"讀取"* ]]; then
    do_mount
elif [[ "$ACTION" == *"卸載"* ]]; then
    do_unmount
fi