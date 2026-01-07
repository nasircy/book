import subprocess
import sys
import os

class MacCleaner:
    def __init__(self):
        self.green = '\033[92m'
        self.yellow = '\033[93m'
        self.red = '\033[91m'
        self.reset = '\033[0m'

    def run_cmd(self, cmd, capture=True):
        """執行終端機指令並回傳結果"""
        try:
            result = subprocess.run(
                cmd, shell=True, text=True, 
                stdout=subprocess.PIPE if capture else None, 
                stderr=subprocess.PIPE if capture else None
            )
            return result.stdout.strip() if capture else ""
        except Exception:
            return None

    def print_header(self, title):
        print(f"\n{self.yellow}=== {title} ==={self.reset}")

    def check_macfuse(self):
        self.print_header("正在檢查 MacFUSE")
        brew_check = self.run_cmd("brew list --cask | grep macfuse")
        kext_check = self.run_cmd("kextstat | grep -i fuse")
        
        found = []
        if brew_check: found.append("Brew Cask: macfuse")
        if kext_check: found.append("System Kext: macfuse (Kernel Extension)")
        
        if not found:
            print("未偵測到 MacFUSE 相關元件。")
        else:
            for item in found:
                print(f"• {item}")
        print("-" * 30)

    def get_packages(self, manager):
        print(f"正在讀取 {manager} 清單...", end="\r")
        packages = []
        
        if manager == 'brew':
            raw = self.run_cmd("brew list --formula")
            if raw: packages = raw.split('\n')
            
        elif manager == 'pip':
            raw = self.run_cmd("pip3 list --format=columns")
            if raw: 
                lines = raw.split('\n')[2:]
                packages = [line.split()[0] for line in lines if line]
                
        elif manager == 'npm':
            # 只讀取全域第一層
            raw = self.run_cmd("npm list -g --depth=0 --json")
            import json
            try:
                data = json.loads(raw)
                packages = list(data.get('dependencies', {}).keys())
            except:
                pass

        return packages

    def delete_package(self, manager, package):
        """執行刪除指令 (含自動 Sudo 救援)"""
        cmd = ""
        print(f"\n正在刪除 {package} ...")
        
        if manager == 'brew':
            cmd = f"brew uninstall {package}"
        elif manager == 'pip':
            cmd = f"pip3 uninstall -y {package}"
        elif manager == 'npm':
            cmd = f"npm uninstall -g {package}"
            
        # 第一次嘗試：普通刪除
        res = subprocess.run(cmd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if res.returncode == 0:
            print(f"{self.green}🎉 恭喜成功刪除 {package}{self.reset}")
        else:
            # 檢查是否為權限錯誤 (EACCES 或 Permission denied)
            err_msg = res.stderr.lower()
            if "eacces" in err_msg or "permission denied" in err_msg or "root-owned" in err_msg:
                print(f"{self.yellow}⚠️  權限不足 (因為檔案是 Root 擁有的)。{self.reset}")
                print(f"{self.yellow}>>> 正在嘗試切換管理者權限 (Sudo) 強制刪除...{self.reset}")
                
                # 第二次嘗試：Sudo 刪除
                # 這裡不 capture output，讓使用者可以看到 sudo 的密碼提示
                sudo_cmd = f"sudo {cmd}"
                sudo_res = subprocess.run(sudo_cmd, shell=True)
                
                if sudo_res.returncode == 0:
                     print(f"\n{self.green}🎉 恭喜成功 (已強制刪除) {package}{self.reset}")
                else:
                     print(f"\n{self.red}❌ 還是失敗，可能需要手動修復 npm 權限。{self.reset}")
            else:
                print(f"{self.red}❌ 刪除失敗: {res.stderr}{self.reset}")

    def interactive_menu(self):
        while True:
            print(f"\n{self.green}請選擇要檢測與管理的類別：{self.reset}")
            print("1. Homebrew (brew)")
            print("2. Python (pip3)")
            print("3. Node.js (npm global)")
            print("4. 檢查 MacFUSE 狀態")
            print("q. 離開")
            
            choice = input("輸入選項 > ").strip().lower()
            
            if choice == 'q':
                print("掰掰！")
                break
            
            if choice == '4':
                self.check_macfuse()
                input("按 Enter 繼續...")
                continue
                
            manager_map = {'1': 'brew', '2': 'pip', '3': 'npm'}
            target_manager = manager_map.get(choice)
            
            if target_manager:
                pkgs = self.get_packages(target_manager)
                if not pkgs:
                    print(f"目前沒有安裝任何 {target_manager} 套件。")
                    continue
                
                print(f"\n--- {target_manager} 已安裝列表 ---")
                for idx, pkg in enumerate(pkgs):
                    print(f"{idx + 1}. {pkg}")
                
                print(f"\n{self.yellow}輸入編號來刪除套件 (例如 5)，或輸入 0 返回選單{self.reset}")
                try:
                    del_idx = int(input("輸入 > "))
                    if del_idx == 0: continue
                    
                    if 1 <= del_idx <= len(pkgs):
                        target_pkg = pkgs[del_idx - 1]
                        confirm = input(f"確定要刪除 {target_pkg}? (y/n) > ")
                        if confirm.lower() == 'y':
                            self.delete_package(target_manager, target_pkg)
                    else:
                        print("無效的編號")
                except ValueError:
                    print("請輸入數字")

if __name__ == "__main__":
    app = MacCleaner()
    app.interactive_menu()