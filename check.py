import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import init, Fore, Style
import time
import os
from threading import Lock

init(autoreset=True)
print_lock = Lock()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    clear_screen()

    banner = r"""
┌───────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                       │
│                                ___                    _               _               _               │
│   _ __  _ __ _____  ___   _   ( _ )    ___  ___   ___| | _____    ___| |__   ___  ___| | _____ _ __   │
│  | '_ \| '__/ _ \ \/ / | | |  / _ \/\ / __|/ _ \ / __| |/ / __|  / __| '_ \ / _ \/ __| |/ / _ \ '__|  │
│  | |_) | | | (_) >  <| |_| | | (_>  < \__ \ (_) | (__|   <\__ \ | (__| | | |  __/ (__|   <  __/ |     │
│  | .__/|_|  \___/_/\_\\__, |  \___/\/ |___/\___/ \___|_|\_\___/  \___|_| |_|\___|\___|_|\_\___|_|     │
│  |_|                  |___/                                                                           │
│                                                                                                       │ 
│                                                                   - github.com/vijayshankar22         │
└───────────────────────────────────────────────────────────────────────────────────────────────────────┘

"""
    with print_lock:
        print(Fore.MAGENTA + banner + Style.RESET_ALL, flush=True)

def detect_anonymity(response, real_ip):
    headers = response.headers
    text = response.text
    if real_ip and real_ip in text:
        return "Transparent"
    proxy_headers = ["Via", "X-Forwarded-For", "Forwarded", "Proxy-Connection"]
    if any(h in headers for h in proxy_headers):
        return "Anonymous"
    return "Elite"

def check_proxy(proxy, timeout, real_ip):
    try:
        ip, port = proxy.strip().split(':', 1)
        port = int(port)
    except ValueError:
        with print_lock:
            print(Fore.RED + f"[INVALID] {proxy}", flush=True)
        return proxy, False, None, None

    urls = ["http://httpbin.org/ip", "https://httpbin.org/ip"]
    proxy_types = {
        "HTTP": {"http": f"http://{ip}:{port}", "https": f"http://{ip}:{port}"},
        "SOCKS4": {"http": f"socks4://{ip}:{port}", "https": f"socks4://{ip}:{port}"},
        "SOCKS5": {"http": f"socks5://{ip}:{port}", "https": f"socks5://{ip}:{port}"}
    }

    for ptype, proxies in proxy_types.items():
        try:
            for url in urls:
                response = requests.get(url, proxies=proxies, timeout=timeout)
                if response.status_code == 200:
                    anonymity = detect_anonymity(response, real_ip)
                    level_color = (Fore.YELLOW if anonymity == "Transparent" else
                                   Fore.CYAN if anonymity == "Anonymous" else
                                   Fore.MAGENTA)
                    with print_lock:
                        print(Fore.GREEN + f"[WORKING] {ip}:{port} ({ptype}) " +
                              level_color + f"{anonymity}", flush=True)
                    return proxy, True, ptype, anonymity
        except Exception:
            pass

    with print_lock:
        print(Fore.RED + f"[DEAD] {ip}:{port}", flush=True)
    return proxy, False, None, None

def load_proxies(file_path):
    try:
        with open(file_path, 'r') as file:
            return [line.strip() for line in file if ':' in line]
    except FileNotFoundError:
        with print_lock:
            print(Fore.RED + f"Error: {file_path} file not found!", flush=True)
        return []

def save_working_proxies(working_proxies):
    with open('working-proxies.txt', 'w') as http_file, open('working-socks.txt', 'w') as socks_file:
        for proxy, proxy_type, _ in working_proxies:
            (http_file if proxy_type == "HTTP" else socks_file).write(f"{proxy}\n")
    with print_lock:
        print(Fore.GREEN + "\nWorking proxies saved to working-proxies.txt and working-socks.txt", flush=True)

def main_menu():
    while True:
        print_banner()

        file_path = input(Fore.CYAN + "Enter the path to proxies.txt (default 'proxies.txt'): ").strip()
        if not file_path:
            file_path = 'proxies.txt'

        proxies = load_proxies(file_path)
        if not proxies:
            with print_lock:
                print(Fore.RED + "No proxies found. Please add proxies and try again.", flush=True)
            break

        try:
            threads = int(input(Fore.CYAN + "Enter number of threads (default 50): ") or 50)
        except ValueError:
            threads = 50

        try:
            timeout = int(input(Fore.CYAN + "Enter request timeout in seconds (default 5): ") or 5)
        except ValueError:
            timeout = 5

        try:
            real_ip = requests.get("http://httpbin.org/ip", timeout=timeout).json().get("origin", "")
        except Exception:
            real_ip = None

        start_time = time.time()
        with print_lock:
            print(Fore.CYAN + f"\nChecking {len(proxies)} proxies using {threads} threads and {timeout}s timeout...\n", flush=True)

        working_proxies, dead_proxies = [], 0
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {executor.submit(check_proxy, proxy, timeout, real_ip): proxy for proxy in proxies}
            for future in as_completed(futures):
                proxy, is_working, ptype, anonymity = future.result()
                if is_working:
                    working_proxies.append((proxy, ptype, anonymity))
                else:
                    dead_proxies += 1

        end_time = time.time()
        with print_lock:
            print(Fore.CYAN + f"\nCheck completed in {end_time - start_time:.2f} seconds", flush=True)
            print(Fore.CYAN + f"Summary: {len(working_proxies)} working proxies, {dead_proxies} dead proxies", flush=True)

        if working_proxies:
            save_working_proxies(working_proxies)

            transparent = [p for p in working_proxies if p[2] == "Transparent"]
            anonymous = [p for p in working_proxies if p[2] == "Anonymous"]
            elite = [p for p in working_proxies if p[2] == "Elite"]

            with print_lock:
                print(Fore.YELLOW + "\n---- Transparent ----")
                [print(Fore.YELLOW + f"{p[0]} ({p[1]})") for p in transparent]
                print(Fore.CYAN + "\n---- Anonymous ----")
                [print(Fore.CYAN + f"{p[0]} ({p[1]})") for p in anonymous]
                print(Fore.MAGENTA + "\n---- Elite ----")
                [print(Fore.MAGENTA + f"{p[0]} ({p[1]})") for p in elite]

        restart_choice = input(Fore.CYAN + "\nDo you want to restart the program? (y/n): ").lower()
        if restart_choice == 'n':
            break

if __name__ == "__main__":
    main_menu()
