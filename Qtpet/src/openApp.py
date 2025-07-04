import os
import glob
import winreg
from difflib import get_close_matches
import subprocess
from win32com.client import Dispatch

def collect_shortcut_apps():
    """从开始菜单收集快捷方式信息"""
    app_list = []
    start_menu_dirs = [
        os.path.join(os.environ['ALLUSERSPROFILE'], 'Microsoft', 'Windows', 'Start Menu', 'Programs'),
        os.path.join(os.environ['USERPROFILE'], 'AppData', 'Roaming', 'Microsoft', 'Windows', 'Start Menu', 'Programs')
    ]
    for menu_dir in start_menu_dirs:
        if not os.path.exists(menu_dir):
            continue
        for root, _, files in os.walk(menu_dir):
            for file in files:
                if file.lower().endswith('.lnk'):
                    shortcut_path = os.path.join(root, file)
                    try:
                        shell = Dispatch('WScript.Shell')
                        shortcut = shell.CreateShortcut(shortcut_path)
                        target_path = shortcut.TargetPath
                        if target_path.lower().endswith('.exe'):
                            app_name = os.path.splitext(file)[0]  # 去除.lnk扩展名
                            app_list.append((app_name, target_path))
                    except Exception as e:
                        print(f"Error reading shortcut {shortcut_path}: {e}")
    return app_list

def collect_registry_apps():
    """从注册表获取安装的应用信息"""
    app_list = []
    reg_keys = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall")
    ]
    for hkey, key_path in reg_keys:
        try:
            reg_key = winreg.OpenKey(hkey, key_path)
            subkeys_count = winreg.QueryInfoKey(reg_key)[0]
            subkeys = [winreg.EnumKey(reg_key, i) for i in range(subkeys_count)]
            for subkey in subkeys:
                try:
                    sub_key = winreg.OpenKey(hkey, f"{key_path}\\{subkey}")
                    name = winreg.QueryValueEx(sub_key, 'DisplayName')[0]
                    try:
                        path = winreg.QueryValueEx(sub_key, 'InstallLocation')[0]
                    except FileNotFoundError:
                        path = None
                    if path and os.path.exists(path) and os.path.isdir(path):
                        app_list.append((name, path))
                except Exception as e:
                    continue
        except Exception as e:
            pass
    return app_list

def find_application(query):
    """模糊匹配应用名称"""
    if query.endswith(".exe"):
        return query
    # 收集应用信息
    shortcut_apps = collect_shortcut_apps()
    registry_apps = collect_registry_apps()
    all_apps = shortcut_apps + [(name, path) for name, path in registry_apps]
    
    # 处理用户输入
    query_processed = query.strip().lower()
    if not query_processed:
        return None
    
    # 提取应用名称进行匹配
    app_names = [name.lower() for name, _ in all_apps]
    matches = get_close_matches(query_processed, app_names, n=5, cutoff=0.5)
    
    if not matches:
        return None
    
    best_match_index = app_names.index(matches[0])
    return all_apps[best_match_index][1]

def launch_application(path):
    """启动匹配的应用"""
    if not path:
        return False
    try:
        # 直接启动exe文件
        os.startfile(path)
        return True
    except:
        try:
            # 如果路径是目录，尝试查找exe文件
            if os.path.isdir(path):
                for file in os.listdir(path):
                    if file.lower().endswith('.exe'):
                        exe_path = os.path.join(path, file)
                        os.startfile(exe_path)
                        return True
                return False
            else:
                subprocess.Popen([path])
                return True
        except Exception as e:
            print(f"启动失败: {e}")
            return False

# 示例使用
if __name__ == "__main__":
    user_input = r"E:\myDemo\DoroPet\DoroPet_V2\Qtpet\dist\DoroPet\DoroPet.exe"
    print(f"user_input = \"{user_input}\"")
    app_path = find_application(user_input)
    if app_path:
        if launch_application(app_path):
            print(f"成功启动应用: {app_path}")
        else:
            print(f"启动应用失败:{app_path}")
    else:
        print(f"未找到匹配的应用{app_path}")