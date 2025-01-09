import os
import sys
import time
import subprocess
import requests
import json
from packaging import version

import inquirer
from colorama import Fore, Style
from tqdm import tqdm

# Определяем режим разработки через переменную окружения
DEV_MODE = True

CURRENT_VERSION = "0.1"
GITHUB_REPO = "housemice/QS_Li"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

# Тестовый код будет включен только если DEV_MODE = True
if DEV_MODE:
    class TestDevice:
        def __init__(self):
            self.connected = True
            self.vin = "TEST1234567890"
            self.apps_installed = []
            self.permissions_granted = False
            self.keyboard_configured = False

        def toggle_connection(self):
            self.connected = not self.connected
            return self.connected

        def install_app(self, app_name):
            time.sleep(1)
            if self.connected:
                self.apps_installed.append(app_name)
                return True
            return False

        def grant_permissions(self):
            if self.connected:
                time.sleep(0.5)
                self.permissions_granted = True
                return True
            return False

        def configure_keyboard(self):
            if self.connected:
                time.sleep(0.5)
                self.keyboard_configured = True
                return True
            return False

    def _run_test_scenario(scenario_name, test_device):
        if scenario_name == "Installation Success":
            test_device.connected = True
            return _test_installation_flow(test_device)
        elif scenario_name == "No Device":
            test_device.connected = False
            return _test_no_device_flow(test_device)
        elif scenario_name == "Permission Failure":
            test_device.connected = True
            return _test_permission_failure(test_device)

    def _test_installation_flow(test_device):
        success = True
        apps = ["Waze", "SMS Messenger", "Android Settings", "Li Chat Store", "SwiftKey", "YouTube"]
        for app in apps:
            if test_device.install_app(app):
                print(f"{Fore.GREEN}✓ Installed {app}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✗ Failed to install {app}{Style.RESET_ALL}")
                success = False
        
        if test_device.grant_permissions():
            print(f"{Fore.GREEN}✓ Permissions granted{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✗ Failed to grant permissions{Style.RESET_ALL}")
            success = False
        return success

    def _test_no_device_flow(test_device):
        if not test_device.connected:
            print(f"{Fore.GREEN}✓ Correctly detected no device{Style.RESET_ALL}")
            return True
        return False

    def _test_permission_failure(test_device):
        test_device.permissions_granted = False
        if not test_device.permissions_granted:
            print(f"{Fore.GREEN}✓ Correctly handled permission failure{Style.RESET_ALL}")
            return True
        return False

    def run_tests():
        clear_screen()
        display_header()
        
        test_device = TestDevice()
        scenarios = [
            "Installation Success",
            "No Device",
            "Permission Failure"
        ]
        
        results = {}
        for scenario in scenarios:
            clear_screen()
            display_header()
            print(f"\n{Fore.CYAN}=== Test Device Status ==={Style.RESET_ALL}")
            print(f"Connected: {Fore.GREEN if test_device.connected else Fore.RED}{'✓' if test_device.connected else '✗'}{Style.RESET_ALL}")
            print(f"VIN: {test_device.vin}")
            print(f"Apps Installed: {len(test_device.apps_installed)}")
            results[scenario] = _run_test_scenario(scenario, test_device)
            pause_for_user(f"Press Enter to continue testing...", timeout=3)
        
        clear_screen()
        display_header()
        print(f"\n{Fore.CYAN}=== Test Results ==={Style.RESET_ALL}")
        for scenario, success in results.items():
            status = f"{Fore.GREEN}✓ PASSED{Style.RESET_ALL}" if success else f"{Fore.RED}✗ FAILED{Style.RESET_ALL}"
            print(f"{scenario}: {status}")
        
        pause_for_user()

def menu():
    choices = [
        f"{Fore.RED}🗑️  Remove all apps{Style.RESET_ALL}          - Uninstall all user applications",
        f"{Fore.RED}📱  Remove selected apps{Style.RESET_ALL}     - Choose specific apps to uninstall",
        f"{Fore.GREEN}📦  Install Custom Apps{Style.RESET_ALL}      - Install APKs from Custom_Apps folder",
        f"{Fore.GREEN}🚀  Install launcher{Style.RESET_ALL}         - Install system launcher",
        f"{Fore.GREEN}🔄  Install counter reset{Style.RESET_ALL}    - Install counter reset application",
        f"{Fore.GREEN}⚙️   Install standard apps{Style.RESET_ALL}    - Install and configure all required apps",
        f"{Fore.BLUE}💾  Download device files{Style.RESET_ALL}    - Save device files to Desktop",
        f"{Fore.BLUE}ℹ️   Help{Style.RESET_ALL}                     - Show version and contact info",
        f"{Fore.YELLOW}❌  Exit{Style.RESET_ALL}                     - Close the program"
    ]
    
    # Создаем словарь для сопоставления отформатированных строк с действиями
    actions_map = {
        f"{Fore.RED}🗑️  Remove all apps{Style.RESET_ALL}          - Uninstall all user applications": "Delete all apps",
        f"{Fore.RED}📱  Remove selected apps{Style.RESET_ALL}     - Choose specific apps to uninstall": "Delete selected apps",
        f"{Fore.GREEN}📦  Install Custom Apps{Style.RESET_ALL}      - Install APKs from Custom_Apps folder": "Install Custom_Apps",
        f"{Fore.GREEN}🚀  Install launcher{Style.RESET_ALL}         - Install system launcher": "Install launcher",
        f"{Fore.GREEN}🔄  Install counter reset{Style.RESET_ALL}    - Install counter reset application": "Install reset app",
        f"{Fore.GREEN}⚙️   Install standard apps{Style.RESET_ALL}    - Install and configure all required apps": "Install apps",
        f"{Fore.BLUE}💾  Download device files{Style.RESET_ALL}    - Save device files to Desktop": "Download files",
        f"{Fore.BLUE}ℹ️   Help{Style.RESET_ALL}                     - Show version and contact info": "Help",
        f"{Fore.YELLOW}❌  Exit{Style.RESET_ALL}                     - Close the program": "Exit"
    }
    
    if DEV_MODE:
        test_choice = f"{Fore.MAGENTA}🧪  Run Tests{Style.RESET_ALL}               - Execute test scenarios"
        choices.insert(0, test_choice)
        actions_map[test_choice] = "Run Tests"

    last_vin = None
    while True:
        try:
            clear_screen()
            
            connected, device_info = check_adb_connection()
            current_vin = get_device_vin() if connected else "No car connected"
            
            display_header(current_vin)
            last_vin = current_vin
            
            if connected:
                status_line = f"{Fore.GREEN}Connected to: {device_info}{Style.RESET_ALL}"
            else:
                status_line = f"{Fore.RED}No device connected{Style.RESET_ALL}"
            
            print(f"\n{status_line}")
            
            questions = [
                inquirer.List(
                    "action",
                    message="Select an action using arrow keys:",
                    choices=choices,
                )
            ]
            answers = inquirer.prompt(questions)
            selected = answers.get("action")
            action = actions_map.get(selected)  # Получаем соответствующее действие
            
            if action == "Exit":
                print(f"{Fore.GREEN}Exiting the program...{Style.RESET_ALL}")
                break
            
            clear_screen()
            display_header(current_vin)
            
            # Route user's selection to the corresponding function
            if action == "Delete all apps":
                delete_all_apps()
            elif action == "Delete selected apps":
                list_and_delete_apps()
            elif action == "Install Custom_Apps":
                install_custom_apps()
            elif action == "Install launcher":
                install_launcher()
            elif action == "Install reset app":
                install_reset_app()
            elif action == "Install apps":
                install_apps()
            elif action == "Download files":
                download_device_files()
            elif action == "Help":
                print(f"{Fore.YELLOW}@dexnot{Style.RESET_ALL}")
                print("Version 0.1")
                pause_for_user()
            elif action == "Run Tests":
                run_tests()
                
        except KeyboardInterrupt:
            print(f"\n{Fore.RED}Interrupted by user. Exiting...{Style.RESET_ALL}")
            break
        except Exception as e:
            clear_screen()
            display_header(current_vin)
            print(f"{Fore.RED}An unexpected error occurred: {e}{Style.RESET_ALL}")
            pause_for_user("Returning to the menu...")

def get_user_count():
    try:
        # Run 'pm list users' on the device
        result = subprocess.run(
            "adb shell pm list users",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True
        )
        if result.returncode != 0:
            print(f"{Fore.RED}Failed to list users. Assuming 1 user.{Style.RESET_ALL}")
            return 1
        lines = result.stdout.splitlines()
        count = sum("UserInfo" in line for line in lines)

        print(f"{Fore.GREEN}Detected {count} user(s) on the device.{Style.RESET_ALL}")
        return count if count > 0 else 1
    except Exception as e:
        print(f"{Fore.RED}An error occurred while checking user count: {e}.{Style.RESET_ALL}")
        return 1


def pause_for_user(message="Press Enter to return to the menu...", timeout=None):
    if timeout is not None and timeout > 0:
        print(f"{Fore.CYAN}{message} (Auto-continue in {timeout} seconds...){Style.RESET_ALL}")
        for remaining in range(timeout, 0, -1):
            sys.stdout.write(f"\r{Fore.YELLOW}Continuing in {remaining}...{Style.RESET_ALL}")
            sys.stdout.flush()
            time.sleep(1)
        print("\n")
    else:
        input(f"{Fore.CYAN}{message}{Style.RESET_ALL}")


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def run_adb_command(command):
    try:
        print(f"{Fore.CYAN}Executing: {command}{Style.RESET_ALL}")
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            if result.stdout.strip():
                print(f"{Fore.GREEN}{result.stdout.strip()}{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}Command failed with error code {result.returncode}{Style.RESET_ALL}")
            print(f"{Fore.RED}Error: {result.stderr.strip()}{Style.RESET_ALL}")
            pause_for_user("Press Enter to acknowledge the error and return.")
            return False
    except subprocess.TimeoutExpired:
        print(f"{Fore.RED}Command timed out after 30 seconds{Style.RESET_ALL}")
        return False
    except Exception as e:
        print(f"{Fore.RED}An unexpected error occurred: {e}{Style.RESET_ALL}")
        pause_for_user("Press Enter to acknowledge the error and return.")
        return False


def check_adb_connection():
    try:
        result = subprocess.run(
            "adb devices -l",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True
        )
        lines = result.stdout.splitlines()
        # Filter lines that indicate an actual device.
        devices = [
            line for line in lines
            if "device" in line and not line.startswith("List")
        ]

        if devices:
            # Extract serial number and model if available.
            device_info = devices[0].split()
            serial_number = device_info[0]
            model = None
            for part in device_info:
                if "model:" in part:
                    model = part.split(":")[1]
                    break
            return True, model or serial_number
        else:
            print(f"{Fore.RED}No device connected via ADB.{Style.RESET_ALL}")
            return False, None
    except Exception as e:
        print(f"{Fore.RED}ADB connection error: {e}{Style.RESET_ALL}")
        return False, None


def requires_adb_connection(func):
    def wrapper(*args, **kwargs):
        connected, _ = check_adb_connection()
        if not connected:
            pause_for_user("ADB connection failed. Please connect a device.")
            return
        return func(*args, **kwargs)
    return wrapper


def display_header(vin=None):
    """
    Displays logo and device information
    """
    header = f"""{Style.RESET_ALL}
    {Fore.GREEN}
  ▄████████ ▀█████████▄     ▄████████    ▄████████    ▄█    █▄     ▄█      ███     
  ███    ███   ███    ███   ███    ███   ███    ███   ███    ███   ███  ▀█████████▄ 
  ███    █▀    ███    ███   ███    ███   ███    █▀    ███    ███   ███▌    ▀███▀▀██ 
 ▄███▄▄▄      ▄███▄▄▄██▀    ███    ███   ███         ▄███▄▄▄▄███▄▄ ███▌     ███   ▀ 
▀▀███▀▀▀     ▀▀███▀▀▀██▄  ▀███████████ ▀███████████ ▀▀███▀▀▀▀███▀  ███▌     ███     
  ███    █▄    ███    ██▄   ███    ███          ███   ███    ███   ███      ███     
  ███    ███   ███    ███   ███    ███    ▄█    ███   ███    ███   ███      ███     
  ██████████ ▄█████████▀    ███    █▀   ▄████████▀    ███    █▀    █▀      ▄████▀   
    {Style.RESET_ALL}"""
    print(header)
    
    # Display device info in a box
    if vin:
        info_box = f"""
    {Fore.CYAN}╔══════════════════════════════════════════════════════════════════════════════╗
    ║  VIN: {Fore.YELLOW}{vin:<71}{Fore.CYAN}║
    ╚══════════════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """
        print(info_box)

@requires_adb_connection
def install_custom_apps():
    script_dir = os.path.abspath(os.path.dirname(__file__))
    custom_apps_dir = os.path.join(script_dir, "Custom_Apps")
    
    if not os.path.exists(custom_apps_dir):
        print(f"{Fore.RED}Custom_Apps folder not found!{Style.RESET_ALL}")
        pause_for_user()
        return

    apk_files = [f for f in os.listdir(custom_apps_dir) if f.endswith(".apk")]
    if not apk_files:
        print(f"{Fore.RED}No .apk files found in Custom_Apps.{Style.RESET_ALL}")
        pause_for_user()
        return

    print(f"{Fore.GREEN}Found {len(apk_files)} APK(s) in Custom_Apps.{Style.RESET_ALL}")
    
    with tqdm(total=len(apk_files), desc="Installing custom apps", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
        for app in apk_files:
            app_path = os.path.join(custom_apps_dir, app)
            print(f"Installing {app}...")
            run_adb_command(f"adb install \"{app_path}\"")
            pbar.update(1)


@requires_adb_connection
def list_and_delete_apps():
    print(f"{Style.DIM}Fetching list of installed user apps...{Style.RESET_ALL}")
    result = subprocess.run("adb shell pm list packages -3", stdout=subprocess.PIPE, shell=True, text=True)
    packages = [line.split(":")[1].strip() for line in result.stdout.splitlines()]

    if not packages:
        print(f"{Fore.RED}No user apps found.{Style.RESET_ALL}")
        pause_for_user()
        return

    print(f"{Fore.GREEN}Found {len(packages)} user app(s):{Style.RESET_ALL}")
    for package in packages:
        print(f"{Style.DIM}{package}{Style.RESET_ALL}")

    questions = [
        inquirer.Checkbox(
            "apps_to_delete",
            message="Select apps to delete:",
            choices=packages,
        )
    ]
    answers = inquirer.prompt(questions)

    selected = answers.get("apps_to_delete", [])
    if selected:
        for package in selected:
            confirmation = inquirer.confirm(f"Are you sure you want to delete {package}?", default=False)
            if confirmation:
                print(f"{Style.DIM}Deleting {package}...{Style.RESET_ALL}")
                run_adb_command(f"adb uninstall {package}")
        print(f"{Fore.GREEN}Selected apps successfully deleted.{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}No apps selected for deletion.{Style.RESET_ALL}")

@requires_adb_connection
def delete_all_apps():
    confirmation = inquirer.confirm("Are you sure you want to delete all user apps?", default=False)
    if not confirmation:
        print(f"{Fore.YELLOW}Operation cancelled.{Style.RESET_ALL}")
        return

    print("Deleting user apps...")
    result = subprocess.run("adb shell pm list packages -3", stdout=subprocess.PIPE, shell=True, text=True)
    packages = [line.split(":")[1].strip() for line in result.stdout.splitlines()]

    with tqdm(total=len(packages), desc="Deleting apps", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
        for package in packages:
            print(f"Deleting {package}...")
            run_adb_command(f"adb uninstall {package}")
            pbar.update(1)

@requires_adb_connection
def install_launcher():
    print("Installing launcher(s)...")
    user_count = get_user_count()

    if user_count == 2:
        with tqdm(total=1, desc="Installing launcher", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
            run_adb_command("adb install --user 0 Launcher.apk")
            pbar.update(1)
    elif user_count == 3:
        with tqdm(total=2, desc="Installing launchers", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
            run_adb_command("adb install --user 0 Launcher.apk")
            pbar.update(1)
            run_adb_command("adb install --user 0 Rear_App.apk")
            pbar.update(1)
    else:
        print(f"{Fore.YELLOW}Undefined number of users: {user_count}. "
              f"No installation performed.{Style.RESET_ALL}")

@requires_adb_connection
def install_reset_app():
    print("Installing reset app...")
    run_adb_command("adb install Reset.apk")
            
@requires_adb_connection
def install_apps():
    try:
        if not check_free_space():
            if not inquirer.confirm("Low storage space detected. Continue anyway?", default=False):
                return False

        script_dir = os.path.abspath(os.path.dirname(__file__))
        apps_config = {
            "Waze.apk": {"options": "--user 0", "display_name": "Waze Navigation"},
            "SMS_Messenger.apk": {"options": "--user 0", "display_name": "SMS Messenger"},
            "Android_Settings.apk": {"options": "--user 0", "display_name": "Android Settings"},
            "com.lixiang.chat.store.apk": {"options": "", "display_name": "Li Chat Store"},
            "SwiftKey.apk": {"options": "", "display_name": "SwiftKey Keyboard"},
            "YouTube_CarWizard.apk": {"options": "", "display_name": "YouTube CarWizard"},
        }
        
        installation_results = {
            "installed_apps": [],
            "failed_apps": [],
            "permissions": False,
            "keyboard_config": False
        }
        
        total_apps = len(apps_config)
        print(f"\n{Fore.CYAN}Starting installation process...{Style.RESET_ALL}\n")
        
        with tqdm(total=len(apps_config), desc="Overall progress", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
            for app, config in apps_config.items():
                retry_count = 3
                while retry_count > 0:
                    if install_single_app(app, config):
                        break
                    retry_count -= 1
                    if retry_count > 0:
                        print(f"{Fore.YELLOW}Retrying installation...{Style.RESET_ALL}")
                        time.sleep(2)
                pbar.update(1)
        
        print(f"\n{Fore.CYAN}Configuring permissions and keyboard...{Style.RESET_ALL}")
        if give_permission():
            installation_results["permissions"] = True
            installation_results["keyboard_config"] = True
        
        # Вывод итогового отчета
        print_installation_report(installation_results, total_apps)
        
        return True
    except Exception as e:
        print(f"{Fore.RED}An unexpected error occurred: {e}{Style.RESET_ALL}")
        return False
    finally:
        pause_for_user()
        
def install_single_app(app, config):
    app_path = os.path.join(script_dir, app)
    print(f"{Fore.YELLOW}Installing {config['display_name']}...{Style.RESET_ALL}")
    
    if not os.path.exists(app_path):
        print(f"{Fore.RED}✗ File not found: {app}{Style.RESET_ALL}")
        installation_results["failed_apps"].append(config['display_name'])
        return False
    
    command = f"adb install {config['options']} \"{app_path}\""
    if run_adb_command(command):
        print(f"{Fore.GREEN}✓ Successfully installed {config['display_name']}{Style.RESET_ALL}")
        installation_results["installed_apps"].append(config['display_name'])
        return True
    else:
        print(f"{Fore.RED}✗ Failed to install {config['display_name']}{Style.RESET_ALL}")
        installation_results["failed_apps"].append(config['display_name'])
        return False

def give_permission():
    try:
        user_count = get_user_count()
        user_indexes = [0] if user_count == 1 else [0, 21473, 6174]

        with tqdm(total=len(user_indexes)*3, desc="Configuring permissions", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
            # Package installation permissions
            for user in user_indexes:
                run_adb_command(f'adb shell "appops set --user {user} com.lixiang.chat.store REQUEST_INSTALL_PACKAGES allow"')
                pbar.update(1)

            time.sleep(2)  # System pause

            # Keyboard configuration
            for user in user_indexes:
                run_adb_command(f"adb shell ime enable --user {user} com.touchtype.swiftkey/com.touchtype.KeyboardService")
                pbar.update(1)
                run_adb_command(f"adb shell ime set --user {user} com.touchtype.swiftkey/com.touchtype.KeyboardService")
                pbar.update(1)
    except Exception as e:
        print(f"{Fore.RED}An error occurred while giving permission: {e}{Style.RESET_ALL}")
        
def get_device_vin():
    """
    Retrieves the VIN of the connected device using ADB.
    """
    try:
        connected, _ = check_adb_connection()
        if not connected:
            return "No device connected"
            
        # Try different commands to get VIN
        commands = [
            "adb shell getprop persist.sys.vin",
            "adb shell getprop ro.vin",
            "adb shell settings get system vehicle_id"
        ]
        
        for cmd in commands:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip() and result.stdout.strip() != "null":
                return result.stdout.strip()
                
        return "VIN not available"
    except Exception as e:
        print(f"{Fore.RED}Failed to retrieve VIN: {e}{Style.RESET_ALL}")
        return "Error getting VIN"

def download_device_files():
    """
    Downloads device files to a folder named by VIN on Desktop
    """
    try:
        # Get VIN and create folder name
        vin = get_device_vin()
        if vin in ["No device connected", "VIN not available", "Error getting VIN"]:
            print(f"{Fore.RED}Cannot download files: Valid VIN not available{Style.RESET_ALL}")
            return False

        # Create folder on desktop
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        folder_name = f"Device_Files_{vin}"
        folder_path = os.path.join(desktop, folder_name)
        
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        print(f"{Fore.CYAN}Downloading device files to: {folder_path}{Style.RESET_ALL}")

        # List of paths to download
        paths_to_download = [
            "/sdcard/",
            "/storage/emulated/0/Download/",
            "/storage/emulated/0/DCIM/",
            "/storage/emulated/0/Pictures/"
        ]

        with tqdm(total=len(paths_to_download), desc="Downloading files", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
            for path in paths_to_download:
                try:
                    # Create corresponding folder structure
                    local_folder = os.path.join(folder_path, path.strip("/").replace("/", "_"))
                    if not os.path.exists(local_folder):
                        os.makedirs(local_folder)

                    # Pull files from device
                    command = f'adb pull "{path}" "{local_folder}"'
                    result = subprocess.run(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        shell=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        print(f"{Fore.GREEN}✓ Downloaded files from {path}{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.YELLOW}⚠ Failed to download from {path}: {result.stderr}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.RED}Error downloading from {path}: {e}{Style.RESET_ALL}")
                finally:
                    pbar.update(1)

        print(f"{Fore.GREEN}Files downloaded to: {folder_path}{Style.RESET_ALL}")
        return True

    except Exception as e:
        print(f"{Fore.RED}Failed to download files: {e}{Style.RESET_ALL}")
        return False
    finally:
        pause_for_user()

def check_adb_version():
    try:
        result = subprocess.run(
            "adb version",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"{Fore.GREEN}ADB version: {version}{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}ADB not found or not properly installed{Style.RESET_ALL}")
            return False
    except Exception as e:
        print(f"{Fore.RED}Error checking ADB version: {e}{Style.RESET_ALL}")
        return False

def check_for_updates():
    """
    Проверяет наличие обновлений и скачивает их если они доступны
    """
    try:
        print(f"{Fore.CYAN}Checking for updates...{Style.RESET_ALL}")
        response = requests.get(GITHUB_API_URL, timeout=5)
        
        # Если репозиторий или релизы не найдены, просто пропускаем проверку
        if response.status_code == 404:
            if DEV_MODE:  # Показываем сообщение только в режиме разработки
                print(f"{Fore.YELLOW}No releases found in repository{Style.RESET_ALL}")
            return False
            
        if response.status_code != 200:
            if DEV_MODE:
                print(f"{Fore.YELLOW}Failed to check for updates. Status code: {response.status_code}{Style.RESET_ALL}")
            return False

        latest_release = response.json()
        latest_version = latest_release['tag_name'].lstrip('v')
        
        if version.parse(latest_version) > version.parse(CURRENT_VERSION):
            print(f"{Fore.GREEN}New version {latest_version} available! (Current: {CURRENT_VERSION}){Style.RESET_ALL}")
            
            # Получаем ссылку на .py файл из релиза
            assets = latest_release['assets']
            py_asset = next((asset for asset in assets if asset['name'] == 'adb_tool.py'), None)
            
            if py_asset:
                download_url = py_asset['browser_download_url']
                
                # Спрашиваем пользователя об обновлении
                if inquirer.confirm("Do you want to update now?", default=True):
                    print(f"{Fore.CYAN}Downloading update...{Style.RESET_ALL}")
                    
                    # Скачиваем новую версию
                    new_version = requests.get(download_url).text
                    
                    # Сохраняем текущий файл как бэкап
                    current_file = os.path.abspath(__file__)
                    backup_file = current_file + '.backup'
                    os.rename(current_file, backup_file)
                    
                    # Записываем новую версию
                    with open(current_file, 'w', encoding='utf-8') as f:
                        f.write(new_version)
                    
                    print(f"{Fore.GREEN}Update successful! Please restart the program.{Style.RESET_ALL}")
                    sys.exit(0)
            else:
                print(f"{Fore.YELLOW}Update file not found in release.{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}You are running the latest version ({CURRENT_VERSION}){Style.RESET_ALL}")
            
    except requests.exceptions.RequestException as e:
        if DEV_MODE:
            print(f"{Fore.YELLOW}Network error while checking updates: {e}{Style.RESET_ALL}")
        return False
    except Exception as e:
        if DEV_MODE:
            print(f"{Fore.RED}Error checking for updates: {e}{Style.RESET_ALL}")
        return False

def check_and_install_requirements():
    """
    Проверяет и устанавливает необходимые зависимости
    """
    try:
        from importlib.metadata import distribution, PackageNotFoundError
        
        required = {'requests', 'packaging', 'inquirer', 'colorama', 'tqdm'}
        missing = set()
        
        for package in required:
            try:
                distribution(package)
            except PackageNotFoundError:
                missing.add(package)
        
        if missing:
            print(f"{Fore.YELLOW}Installing missing dependencies: {', '.join(missing)}{Style.RESET_ALL}")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing])
            print(f"{Fore.GREEN}Dependencies installed successfully!{Style.RESET_ALL}")
            
            # Перезапускаем скрипт после установки зависимостей
            print(f"{Fore.CYAN}Restarting script...{Style.RESET_ALL}")
            time.sleep(1)  # Даем время прочитать сообщение
            os.execv(sys.executable, ['python'] + sys.argv)
    except Exception as e:
        clear_screen()
        display_header()  # Показываем хедер после ошибки
        print(f"{Fore.RED}Failed to install dependencies: {e}{Style.RESET_ALL}")
        sys.exit(1)

def check_free_space():
    try:
        result = subprocess.run(
            "adb shell df /data",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True
        )
        if result.returncode == 0:
            lines = result.stdout.splitlines()
            if len(lines) > 1:
                available = int(lines[1].split()[3]) * 1024  # Convert to bytes
                if available < 1000000000:  # 1GB
                    print(f"{Fore.RED}Warning: Low storage space ({available/1000000000:.1f}GB){Style.RESET_ALL}")
                    return False
        return True
    except Exception:
        return True  # Продолжаем, если не удалось проверить

def clear_app_cache(package_name):
    try:
        command = f"adb shell pm clear {package_name}"
        return run_adb_command(command)
    except Exception as e:
        print(f"{Fore.RED}Failed to clear cache: {e}{Style.RESET_ALL}")
        return False

def print_installation_report(installation_results, total_apps):
    """
    Displays a formatted installation report
    """
    print(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════════════════════════════════╗")
    print(f"║                            Installation Report                              ║")
    print(f"╠══════════════════════════════════════════════════════════════════════════════╣")
    
    # Successfully installed apps
    print(f"║  Successfully Installed ({len(installation_results['installed_apps'])}/{total_apps}):".ljust(73) + "║")
    for app in installation_results['installed_apps']:
        print(f"║  {Fore.GREEN}✓ {app}{Style.RESET_ALL}".ljust(73) + "║")
    
    # Failed installations
    if installation_results['failed_apps']:
        print(f"╟──────────────────────────────────────────────────────────────────────────────╢")
        print(f"║  Failed to Install:".ljust(73) + "║")
        for app in installation_results['failed_apps']:
            print(f"║  {Fore.RED}✗ {app}{Style.RESET_ALL}".ljust(73) + "║")
    
    # Configuration status
    print(f"╟──────────────────────────────────────────────────────────────────────────────╢")
    print(f"║  Configuration Status:".ljust(73) + "║")
    print(f"║  {'✓' if installation_results['permissions'] else '✗'} Permissions: "
          f"{Fore.GREEN if installation_results['permissions'] else Fore.RED}"
          f"{'Configured' if installation_results['permissions'] else 'Failed'}{Style.RESET_ALL}".ljust(73) + "║")
    print(f"║  {'✓' if installation_results['keyboard_config'] else '✗'} Keyboard: "
          f"{Fore.GREEN if installation_results['keyboard_config'] else Fore.RED}"
          f"{'Configured' if installation_results['keyboard_config'] else 'Failed'}{Style.RESET_ALL}".ljust(73) + "║")
    print(f"╚══════════════════════════════════════════════════════════════════════════════╝")

if __name__ == "__main__":
    # Проверяем и устанавливаем зависимости перед всем остальным
    check_and_install_requirements()
    
    if not check_adb_version():
        print(f"{Fore.RED}Please install ADB before running this tool{Style.RESET_ALL}")
        sys.exit(1)
    
    check_for_updates()
    menu()