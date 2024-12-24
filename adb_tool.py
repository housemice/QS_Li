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
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True
        )
        if result.returncode == 0:
            if result.stdout.strip():
                print(f"{Fore.GREEN}{result.stdout.strip()}{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}Error: {result.stderr.strip()}{Style.RESET_ALL}")
            pause_for_user("Press Enter to acknowledge the error and return.")
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


def display_header(device_name=None):
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
    if device_name:
        print(f"{Fore.YELLOW}Connected Device: {device_name}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}No device connected.{Style.RESET_ALL}")


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



def give_permission_for_keyboard():
        user_count = get_user_count()
        if user_count == 1:
            user_indexes = [0]
        else:
            user_indexes = [0, 21473, 6174]

        for user in user_indexes:
            print(f"Configuring IME for user {user}...")
            run_adb_command(
                f"adb shell ime enable --user {user} com.touchtype.swiftkey/com.touchtype.KeyboardService"
            )
            run_adb_command(
                f"adb shell ime set --user {user} com.touchtype.swiftkey/com.touchtype.KeyboardService"
            )
            
            

@requires_adb_connection
def install_apps():
    try:
        script_dir = os.path.abspath(os.path.dirname(__file__))
        apps = [
            "com.lixiang.chat.store.apk",
            "SwiftKey.apk",
            "YouTube_CarWizard.apk",
        ]
        run_adb_command("adb install --user 0 Waze.apk")
        run_adb_command("adb install --user 0 SMS_Messenger.apk")
        run_adb_command("adb install --user 0 Android_Settings.apk")
        give_permission_for_keyboard()
        install_launcher()
        # Install apps
        print(f"{Fore.GREEN}Starting app installation...{Style.RESET_ALL}")
        for app in apps:
            app_path = os.path.join(script_dir, app)
            if os.path.exists(app_path):
                print(f"Installing {app}...")
                success = run_adb_command(f"adb install \"{app_path}\"")
                if not success:
                    print(f"{Fore.RED}Failed to install {app}. Skipping...{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}File {app} not found in {script_dir}. Skipping...{Style.RESET_ALL}")

        print(f"{Fore.GREEN}App installation process completed successfully!{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}An unexpected error occurred: {e}{Style.RESET_ALL}")
    finally:
        pause_for_user()



def menu():
    while True:
        try:
            # Check device connection and get device info
            connected, device_info = check_adb_connection()
            device_name = device_info if connected else None
            display_header(device_name)

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
                print(f"{Fore.YELLOW}Help is under construction. Please check back soon.{Style.RESET_ALL}")
                pause_for_user()
        except KeyboardInterrupt:
            # Gracefully handle CTRL+C
            print(f"\n{Fore.RED}Interrupted by user. Exiting...{Style.RESET_ALL}")
            break
        except Exception as e:
            print(f"{Fore.RED}An unexpected error occurred: {e}{Style.RESET_ALL}")
            pause_for_user("Returning to the menu...")


if __name__ == "__main__":
    menu()