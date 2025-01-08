import os
import sys
import time
import subprocess

import inquirer
from colorama import Fore, Style


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
    header = f"""
    {Fore.GREEN}
  ▄████████ ▀█████████▄     ▄████████    ▄████████    ▄█    █▄     ▄█      ███     
  ███    ███   ███    ███   ███    ███   ███    ███   ███    ███   ███  ▀█████████▄ 
  ███    █▀    ███    ███   ███    ███   ███    █▀    ███    ███   ███▌    ▀███▀▀██ 
 ▄███▄▄▄      ▄███▄▄▄██▀    ███    ███   ███         ▄███▄▄▄▄███▄▄ ███▌     ███   ▀ 
▀▀███▀▀▀     ▀▀███▀▀▀██▄  ▀███████████ ▀███████████ ▀▀███▀▀▀▀███▀  ███▌     ███     
  ███    █▄    ███    ██▄   ███    ███          ███   ███    ███   ███      ███     
  ███    ███   ███    ███   ███    ███    ▄█    ███   ███    ███   ███      ███     
  ██████████ ▄█████████▀    ███    █▀   ▄████████▀    ███    █▀    █▀      ▄████▀   
  {Style.RESET_ALL}
    """
    clear_screen()
    print(header)
    if vin:
        print(f"{Fore.YELLOW}Connected Device VIN: {vin}{Style.RESET_ALL}")


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
    for app in apk_files:
        app_path = os.path.join(custom_apps_dir, app)
        print(f"Installing {app}...")
        run_adb_command(f"adb install \"{app_path}\"")


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
    """
    Uninstall all user-installed apps. Asks for confirmation first.
    """
    confirmation = inquirer.confirm("Are you sure you want to delete all user apps?", default=False)
    if not confirmation:
        print(f"{Fore.YELLOW}Operation cancelled.{Style.RESET_ALL}")
        return

    print("Deleting user apps...")
    result = subprocess.run("adb shell pm list packages -3", stdout=subprocess.PIPE, shell=True, text=True)
    packages = [line.split(":")[1].strip() for line in result.stdout.splitlines()]

    for package in packages:
        print(f"Deleting {package}...")
        run_adb_command(f"adb uninstall {package}")

@requires_adb_connection
def install_launcher():
    print("Installing launcher(s)...")
    user_count = get_user_count()

    if user_count == 2:
        run_adb_command("adb install --user 0 Launcher.apk")
        print(f"{Fore.GREEN}Launcher.apk установлен.{Style.RESET_ALL}")
    elif user_count == 3:
        run_adb_command("adb install --user 0 Launcher.apk")
        run_adb_command("adb install --user 0 Rear_App.apk")
        print(f"{Fore.GREEN}Launcher.apk и Rear_App.apk установлены.{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}Неопределённое количество пользователей: {user_count}. "
              f"Ничего не устанавливаем или устанавливаем по умолчанию.{Style.RESET_ALL}")

@requires_adb_connection
def install_reset_app():
    print("Installing reset app...")
    run_adb_command("adb install Reset.apk")

@requires_adb_connection
def install_apps():
    try:
        script_dir = os.path.abspath(os.path.dirname(__file__))
        apps_config = {
            "Waze.apk": "--user 0",
            "SMS_Messenger.apk": "--user 0",
            "Android_Settings.apk": "--user 0",
            "com.lixiang.chat.store.apk": "",
            "SwiftKey.apk": "", 
            "YouTube_CarWizard.apk": "",
        }
        
        missing_files = []
        for app in apps_config.keys():
            if not os.path.exists(os.path.join(script_dir, app)):
                missing_files.append(app)
        
        if missing_files:
            print(f"{Fore.RED}Missing required files:{Style.RESET_ALL}")
            for file in missing_files:
                print(f"- {file}")
            return False

        for app, options in apps_config.items():
            app_path = os.path.join(script_dir, app)
            print(f"{Fore.CYAN}Installing {app}...{Style.RESET_ALL}")
            command = f"adb install {options} \"{app_path}\""
            if not run_adb_command(command):
                print(f"{Fore.RED}Failed to install {app}{Style.RESET_ALL}")
                return False

        # После установки всех приложений выдаем разрешения
        print(f"{Fore.CYAN}All apps installed. Configuring permissions...{Style.RESET_ALL}")
        give_permission()
        
        print(f"{Fore.GREEN}All apps installed and configured successfully!{Style.RESET_ALL}")
        return True
        
    except Exception as e:
        print(f"{Fore.RED}An unexpected error occurred during installation: {e}{Style.RESET_ALL}")
        return False
    finally:
        pause_for_user()

def give_permission():
    try:
        user_count = get_user_count()
        if user_count == 1:
            user_indexes = [0]
        else:
            user_indexes = [0, 21473, 6174]

        # Сначала выдаем разрешения для установки пакетов
        for user in user_indexes:
            print(f"{Fore.CYAN}Configuring permissions for user {user}...{Style.RESET_ALL}")
            run_adb_command(f'adb shell "appops set --user {user} com.lixiang.chat.store REQUEST_INSTALL_PACKAGES allow"')

        # Делаем небольшую паузу, чтобы система успела обработать установку клавиатуры
        time.sleep(2)

        # Затем настраиваем клавиатуру
        for user in user_indexes:
            print(f"{Fore.CYAN}Configuring keyboard for user {user}...{Style.RESET_ALL}")
            run_adb_command(
                f"adb shell ime enable --user {user} com.touchtype.swiftkey/com.touchtype.KeyboardService"
            )
            run_adb_command(
                f"adb shell ime set --user {user} com.touchtype.swiftkey/com.touchtype.KeyboardService"
            )
    except Exception as e:
        print(f"{Fore.RED}An error occurred while giving permission: {e}{Style.RESET_ALL}")

def get_device_vin():
    """
    Retrieves the VIN of the connected device using ADB.
    """
    try:
        # Проверяем подключение перед запросом VIN
        connected, _ = check_adb_connection()
        if not connected:
            return "No device connected"
            
        # Пробуем несколько команд для получения VIN
        commands = [
            "adb shell getprop ro.vin",
            "adb shell getprop persist.sys.vin",
            # Добавьте другие возможные команды здесь
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
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
                
        return "VIN not available"
    except Exception as e:
        print(f"{Fore.RED}Failed to retrieve VIN: {e}{Style.RESET_ALL}")
        return "Error getting VIN"

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

def menu():
    while True:
        try:
            # Check device connection and get VIN info
            connected, _ = check_adb_connection()
            vin = get_device_vin() if connected else "No car connected"
            
            display_header(vin)  # Display VIN in the header

            questions = [
                inquirer.List(
                    "action",
                    message="Select an action using arrow keys:",
                    choices=[
                        "Delete all apps",
                        "Delete selected apps",
                        "Install Custom_Apps",
                        "Install launcher",
                        "Install reset app",
                        "Install apps",
                        "Help",
                        "Exit",
                    ],
                )
            ]
            answers = inquirer.prompt(questions)
            action = answers.get("action")

            if action == "Exit":
                print(f"{Fore.GREEN}Exiting the program...{Style.RESET_ALL}")
                break

            # Route user’s selection to the corresponding function
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
            elif action == "Help":
                print(f"{Fore.YELLOW}@dexnot{Style.RESET_ALL}")
                print("Version 0.0.3")
                pause_for_user()
        except KeyboardInterrupt:
            # Gracefully handle CTRL+C
            print(f"\n{Fore.RED}Interrupted by user. Exiting...{Style.RESET_ALL}")
            break
        except Exception as e:
            print(f"{Fore.RED}An unexpected error occurred: {e}{Style.RESET_ALL}")
            pause_for_user("Returning to the menu...")

if __name__ == "__main__":
    if not check_adb_version():
        print(f"{Fore.RED}Please install ADB before running this tool{Style.RESET_ALL}")
        sys.exit(1)
    menu()