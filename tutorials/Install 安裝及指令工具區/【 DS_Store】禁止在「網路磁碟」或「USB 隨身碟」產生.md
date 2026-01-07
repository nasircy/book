# 【.DS_Store】禁止在「網路磁碟」或「USB 隨身碟」產生

禁止在網路磁碟 (Network Stores) 產生：

```jsx
defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool TRUE
```

禁止在 USB 隨身碟 (USB Stores) 產生：

```jsx
defaults write com.apple.desktopservices DSDontWriteUSBStores -bool TRUE
```

最後，重啟 Finder 讓設定生效：

```jsx
killall Finder
```