#!/usr/bin/env python3
# =============================================
# HCXFLOW - Capture. Extract. Crack.
# =============================================

import os
import subprocess
import sys
import time
import itertools
import signal
import readline
from datetime import datetime
from pathlib import Path
from threading import Thread

# Colors
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

# Configuration
class Config:
    INTERFACE = None
    BASE_DIR = Path(__file__).resolve().parent
    TARGETS_FILE = BASE_DIR / "targets.txt"
    
    # Auto-detect wordlist - check common locations
    WORDLIST = None
    @classmethod
    def init_wordlist(cls):
        wordlist_paths = [
            "/usr/share/wordlists/rockyou.txt",
            "/usr/share/wordlists/rockyou.txt.gz",
            "/usr/share/passwords.txt",
            "/usr/share/john/password.lst",
            "/opt/wordlists/rockyou.txt",
        ]
        for wp in wordlist_paths:
            if os.path.exists(wp):
                cls.WORDLIST = wp
                break
        if cls.WORDLIST is None:
            cls.WORDLIST = wordlist_paths[0]

    @classmethod
    def get_base_dir(cls):
        path = cls.BASE_DIR
        path.mkdir(parents=True, exist_ok=True)
        return path

# Initialize wordlist on import
Config.init_wordlist()

def get_monitor_interfaces():
    result = subprocess.run("iwconfig 2>/dev/null", shell=True, capture_output=True, text=True)
    monitors = []
    for line in result.stdout.split('\n'):
        if "Mode:Monitor" in line:
            monitors.append(line.strip().split()[0])
    return monitors

def check_interface():
    if not Config.INTERFACE:
        monitors = get_monitor_interfaces()
        if not monitors:
            print(f"{Colors.RED}[!] No wireless adapter in monitor mode found!{Colors.NC}")
            print(f"{Colors.YELLOW}    Options 1 (Full) and 2 (Capture) require a monitor mode interface{Colors.NC}")
            print(f"{Colors.YELLOW}    Options 3 (Extract) and 4 (Crack) do not need monitor mode{Colors.NC}")
            input(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.NC}")
            return False
        if len(monitors) == 1:
            Config.INTERFACE = monitors[0]
            print(f"{Colors.GREEN}[+] Auto-selected {Config.INTERFACE}{Colors.NC}")
        else:
            print(f"{Colors.YELLOW}[*] Multiple monitor interfaces found:{Colors.NC}")
            for i, mon in enumerate(monitors):
                print(f"  {i+1}. {mon}")
            choice = input(f"{Colors.YELLOW}Select interface (1-{len(monitors)}): {Colors.NC}")
            if choice.isdigit() and 1 <= int(choice) <= len(monitors):
                Config.INTERFACE = monitors[int(choice)-1]
            else:
                print(f"{Colors.RED}[!] Invalid choice.{Colors.NC}")
                return False
    
    # Verify it still has mode
    result = subprocess.run(f"iwconfig {Config.INTERFACE} 2>/dev/null", shell=True, capture_output=True, text=True)
    if "Mode:Monitor" not in result.stdout:
        print(f"{Colors.RED}[!] {Config.INTERFACE} is NOT in monitor mode!{Colors.NC}")
        Config.INTERFACE = None
        return False
    
    print(f"{Colors.GREEN}[+] Interface {Config.INTERFACE} is ready.{Colors.NC}")
    return True

def print_banner():
    banner = r"""
 ██╗  ██╗ ██████╗██╗  ██╗███████╗██╗      ██████╗ ██╗    ██╗
 ██║  ██║██╔════╝╚██╗██╔╝██╔════╝██║     ██╔═══██╗██║    ██║
 ███████║██║      ╚███╔╝ █████╗  ██║     ██║   ██║██║ █╗ ██║
 ██╔══██║██║      ██╔██╗ ██╔══╝  ██║     ██║   ██║██║███╗██║
 ██║  ██║╚██████╗██╔╝ ██╗██║     ███████╗╚██████╔╝╚███╔███╔╝
 ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝ 
                                           by Ebisu
    """
    print(f"{Colors.GREEN}{banner}{Colors.NC}")
    print(f"{Colors.YELLOW}                 Capture. Extract. Crack.{Colors.NC}\n")

def main_menu():
    while True:
        os.system('clear')
        print_banner()
        
        print("1. Full")
        print("2. Capture")
        print("3. Extract")
        print("4. Crack")
        print("5. Settings")
        print("0. Exit")
        
        choice = input(f"\n{Colors.YELLOW}Select option (0-5): {Colors.NC}").strip()

        if choice == "1":
            full()
        elif choice == "2":
            capture()
        elif choice == "3":
            hashes()
        elif choice == "4":
            crack()
        elif choice == "5":
            settings()
        elif choice == "0":
            print(f"{Colors.GREEN}Goodbye!{Colors.NC}")
            sys.exit(0)
        else:
            print(f"{Colors.RED}Invalid option!{Colors.NC}")
            input(f"{Colors.YELLOW}Press Enter to continue...{Colors.NC}")

def get_next_capture_file(out_dir, prefix="capture"):
    """Finds the next available filename like capture1.pcapng, capture2.pcapng..."""
    existing = list(out_dir.glob(f"{prefix}*.pcapng"))
    highest = 0
    for f in existing:
        try:
            num = int(f.stem.replace(prefix, ""))
            if num > highest:
                highest = num
        except ValueError:
            continue
    return out_dir / f"{prefix}{highest + 1}.pcapng"

def run_command(cmd, description="", live_output=True, cwd=None):
    # Remove 'sudo' if already running as root (only at start)
    if os.geteuid() == 0 and cmd.startswith("sudo "):
        cmd = cmd[5:]  # Remove first 5 characters ("sudo ")
        
    if description:
        print(f"{Colors.YELLOW}[*] {description}...{Colors.NC}")
    
    try:
        # Use shell=True cautiously
        if live_output:
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, preexec_fn=os.setsid, cwd=cwd)
            try:
                for line in process.stdout:
                    print(line.strip())
                process.wait()
                return process.returncode == 0
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}[*] Stopping capture gracefully...{Colors.NC}")
                # Send SIGINT to the process group to ensure it terminates gracefully
                os.killpg(os.getpgid(process.pid), signal.SIGINT)
                process.wait()
                return True # Treat as success so it can be converted
        else:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
            if result.stdout:
                print(result.stdout)
            return result.returncode == 0
    except Exception as e:
        print(f"{Colors.RED}[!] Error: {e}{Colors.NC}")
        return False

def capture():
    out_dir = Config.get_base_dir()
    if not check_interface():
        return
    
    # Optional Targeted ESSID
    target_essid = input(f"{Colors.YELLOW}Enter target ESSID (leave blank to capture ALL): {Colors.NC}").strip()
    
    try:
        minutes = int(input(f"{Colors.YELLOW}Enter capture time in minutes (or 0 for manual stop): {Colors.NC}"))
    except ValueError:
        print(f"{Colors.RED}[!] Invalid input. Defaulting to manual stop.{Colors.NC}")
        minutes = 0
    
    scan_file = get_next_capture_file(out_dir, prefix="capture")
    
    cmd = f"hcxdumptool -i {Config.INTERFACE} -w {scan_file} --rds=3"
    
    # Handle ESSID filter if provided
    essid_file = None
    if target_essid:
        essid_file = out_dir / "temp_target_essid.txt"
        essid_file.write_text(target_essid)
        cmd += f" --essidlist={essid_file}"
        
    if minutes > 0:
        cmd += f" --tot={minutes}"
    
    print(f"{Colors.BLUE}=== Starting Capture ==={Colors.NC}")
    success = run_command(
        cmd,
        f"Capturing ({minutes if minutes > 0 else 'manual'} min) to {scan_file.name}"
    )
    
    # Cleanup filter file
    if essid_file and essid_file.exists():
        essid_file.unlink()
    
    if success and scan_file.exists():
        base_name = scan_file.stem
        run_command(
            f"hcxpcapngtool -o {out_dir}/{base_name}.hc22000 -E {out_dir}/essids_{base_name}.txt "
            f"-I {out_dir}/identities_{base_name}.txt -U {out_dir}/usernames_{base_name}.txt {scan_file}",
            "Extracting ESSIDs, identities and usernames"
        )
        print(f"{Colors.GREEN}[+] Capture completed successfully!{Colors.NC}")
    else:
        print(f"{Colors.RED}[!] Capture file {scan_file} not found or failed.{Colors.NC}")
    
    input("\nPress Enter to return to menu...")

def full():
    print(f"{Colors.BLUE}=== Starting Full Workflow ==={Colors.NC}")
    
    # 1. Capture
    out_dir = Config.get_base_dir()
    if not check_interface():
        return
    capture_file = get_next_capture_file(out_dir, prefix="capture")
    
    print(f"{Colors.YELLOW}[*] Starting capture (5 min)...{Colors.NC}")
    success = run_command(f"hcxdumptool -i {Config.INTERFACE} -w {capture_file} --rds=3 --tot=5", 
                          f"Capturing to {capture_file.name}")
    
    # Even if Ctrl+C was pressed or capture failed, check if pcap file exists and try to convert
    if not capture_file.exists():
        print(f"{Colors.RED}[!] No capture file created.{Colors.NC}")
        return
    
    # 2. Conversion - try even if capture was interrupted
    base_name = capture_file.stem
    hash_file = out_dir / f"{base_name}.hc22000"
    essid_file = out_dir / f"{base_name}.essids"
    
    print(f"{Colors.YELLOW}[*] Converting to hashes...{Colors.NC}")
    run_command(f"hcxpcapngtool -o {hash_file} -E {essid_file} {capture_file}",
                "Converting to Hashcat format")
    
    # 3. Cracking - try even if previous step was interrupted
    if hash_file.exists():
        print(f"{Colors.YELLOW}[*] Auto-starting crack...{Colors.NC}")
        if not os.path.exists(Config.WORDLIST):
             print(f"{Colors.RED}[!] Wordlist {Config.WORDLIST} not found!{Colors.NC}")
             return
        run_command(f"hashcat -m 22000 {hash_file} {Config.WORDLIST} --force", 
                   f"Running Dictionary Attack with {Config.WORDLIST}")


def hashes():
    out_dir = Config.get_base_dir()
    PAGE_SIZE = 10
    
    # Find all .pcapng files
    pcap_files = sorted(list(out_dir.glob("*.pcapng")), key=os.path.getmtime, reverse=True)
    
    if not pcap_files:
        print(f"{Colors.RED}[!] No pcapng file found in {out_dir}! Run Capture first.{Colors.NC}")
        input("Press Enter...")
        return
    
    # Build list with info about each file
    file_info = []
    for f in pcap_files:
        size_kb = f.stat().st_size / 1024
        mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        base_name = f.stem
        hash_file = out_dir / f"{base_name}.hc22000"
        essid_file = out_dir / f"essids_{base_name}.txt"
        
        # Count hashes if hash file exists
        hash_count = 0
        if hash_file.exists():
            try:
                with open(hash_file, 'r', encoding='utf-8', errors='ignore') as hf:
                    hash_count = sum(1 for line in hf if line.strip())
            except:
                pass
        
        # Count ESSIDs if essid file exists
        essid_count = 0
        if essid_file.exists():
            try:
                with open(essid_file, 'r', encoding='utf-8', errors='ignore') as ef:
                    essid_count = sum(1 for line in ef if line.strip())
            except:
                pass
        
        file_info.append({
            'file': f,
            'size': size_kb,
            'mtime': mtime,
            'hash_count': hash_count,
            'essid_count': essid_count,
            'base_name': base_name
        })
    
    total_pages = (len(file_info) + PAGE_SIZE - 1) // PAGE_SIZE
    current_page = 0
    
    while True:
        start_idx = current_page * PAGE_SIZE
        end_idx = min(start_idx + PAGE_SIZE, len(file_info))
        
        print(f"\n{Colors.BLUE}=== Select File to Extract (Page {current_page + 1}/{total_pages + 1}) ==={Colors.NC}")
        
        for i in range(start_idx, end_idx):
            info = file_info[i]
            hash_info = f"{info['hash_count']} hashes" if info['hash_count'] > 0 else "not extracted"
            essid_info = f"{info['essid_count']} ESSIDs" if info['essid_count'] > 0 else "no ESSIDs"
            print(f"  {i+1}. {info['file'].name}")
            print(f"      Size: {info['size']:.1f} KB | Date: {info['mtime']}")
            print(f"      {hash_info} | {essid_info}")
        
        print()
        if current_page > 0:
            print("  P. Previous page")
        if current_page < total_pages:
            print("  N. Next page")
        print("  0. Back to menu")
        
        choice = input(f"{Colors.YELLOW}Select file (0/{'N' if current_page < total_pages else ''}/{'P' if current_page > 0 else ''}): {Colors.NC}").strip().upper()
        
        if choice == "0":
            return
        elif choice == "P" and current_page > 0:
            current_page -= 1
        elif choice == "N" and current_page < total_pages:
            current_page += 1
        elif choice.isdigit() and 1 <= int(choice) <= len(file_info):
            pcap = file_info[int(choice) - 1]['file']
            break
        else:
            print(f"{Colors.RED}[!] Invalid choice.{Colors.NC}")
    
    print(f"{Colors.BLUE}=== Converting Capture: {pcap.name} ==={Colors.NC}")
    base_name = pcap.stem
    
    run_command(f"hcxpcapngtool -o {out_dir}/{base_name}.hc22000 -E {out_dir}/essids_{base_name}.txt "
                f"-I {out_dir}/identities_{base_name}.txt -U {out_dir}/usernames_{base_name}.txt {pcap}",
                "Converting to Hashcat format")
    
    run_command(f"hcxhashtool -o {out_dir}/clean_{base_name}.hc22000 {out_dir}/{base_name}.hc22000", 
                "Cleaning and analyzing hashes")
    
    print(f"{Colors.GREEN}[+] Conversion completed!{Colors.NC}")
    input("\nPress Enter...")

import binascii

def crack():
    out_dir = Config.get_base_dir()
    cracked_dir = out_dir / "cracked_passwords"
    cracked_dir.mkdir(exist_ok=True)
    potfile = cracked_dir / "cracked.txt"
    
    # FIRST: Show the crack menu
    print(f"\n{Colors.BLUE}=== Crack Menu ==={Colors.NC}")
    print("1. Resume Hashcat")
    print("2. Dictionary Attack")
    print("3. Combination Attack")
    print("4. Bruteforce (Mask) Attack")
    print("5. Hybrid Attack (Dict + Mask)")
    print("6. Back")
    
    ch = input(f"{Colors.YELLOW}Choose (1-6): {Colors.NC}")
    
    if ch == "6" or ch == "0":
        return
    
    # THEN: Show file selection based on choice
    PAGE_SIZE = 10
    
    if ch == "1":
        # Resume: show ONLY hashcat session files (no extracted hashes)
        restore_dirs = [out_dir, Path.home() / ".local/share/hashcat/sessions/", Path.home() / ".hashcat/sessions/"]
        
        restore_files = []
        for d in restore_dirs:
            if d.exists():
                restore_files.extend(list(d.glob("*.restore")))
        
        if not restore_files:
            print(f"{Colors.RED}[!] No saved sessions found! Start a crack first.{Colors.NC}")
            input("Press Enter...")
            return
        
        # Build list of restore files only
        file_info = []
        for f in restore_files:
            mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            file_info.append({
                'type': 'restore',
                'name': f.name,
                'size': 0,
                'mtime': mtime,
                'count': 0,
                'path': str(f.parent),
                'session': f.stem,
                'is_restore': True
            })
        
        # Sort by time
        file_info.sort(key=lambda x: x['mtime'], reverse=True)
        
        title = "Select Hashcat Session to Resume"
    else:
        # New crack: show only hash files
        hash_files = sorted(list(out_dir.glob("*.hc22000")), key=os.path.getmtime, reverse=True)
        
        if not hash_files:
            print(f"{Colors.RED}[!] No hash file found! Run Extract first.{Colors.NC}")
            input("Press Enter...")
            return
        
        file_info = []
        for f in hash_files:
            size_kb = f.stat().st_size / 1024
            mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            hash_count = 0
            try:
                with open(f, 'r', encoding='utf-8', errors='ignore') as hf:
                    hash_count = sum(1 for line in hf if line.strip())
            except:
                pass
            file_info.append({
                'type': 'hash',
                'name': f.name,
                'size': size_kb,
                'mtime': mtime,
                'count': hash_count,
                'path': str(f),
                'is_restore': False
            })
        
        title = "Select Hash File to Crack"
    
    # File selection with pagination
    total_pages = (len(file_info) + PAGE_SIZE - 1) // PAGE_SIZE
    current_page = 0
    
    while True:
        start_idx = current_page * PAGE_SIZE
        end_idx = min(start_idx + PAGE_SIZE, len(file_info))
        
        print(f"\n{Colors.BLUE}=== {title} (Page {current_page + 1}/{total_pages + 1}) ==={Colors.NC}")
        
        for i in range(start_idx, end_idx):
            info = file_info[i]
            if info['is_restore']:
                print(f"  {i+1}. {info['name']}")
                print(f"      Date: {info['mtime']}")
            else:
                print(f"  {i+1}. {info['name']}")
                print(f"      Size: {info['size']:.1f} KB | Date: {info['mtime']}")
                print(f"      {info['count']} hashes")
        
        print()
        if current_page > 0:
            print("  P. Previous page")
        if current_page < total_pages:
            print("  N. Next page")
        print("  0. Back to menu")
        
        choice = input(f"{Colors.YELLOW}Select (0/{'N' if current_page < total_pages else ''}/{'P' if current_page > 0 else ''}): {Colors.NC}").strip().upper()
        
        if choice == "0":
            return
        elif choice == "P" and current_page > 0:
            current_page -= 1
        elif choice == "N" and current_page < total_pages:
            current_page += 1
        elif choice.isdigit() and 1 <= int(choice) <= len(file_info):
            selected = file_info[int(choice) - 1]
            break
        else:
            print(f"{Colors.RED}[!] Invalid choice.{Colors.NC}")
    
    # Execute based on choice
    if ch == "1":
        # Resume session - only restore files, no hash files
        session_name = selected['session']
        run_command(f"hashcat --session={session_name} --restore --potfile-path={potfile} --force", 
                    f"Resuming session: {session_name}", cwd=selected['path'])
        
        print(f"\n{Colors.GREEN}=== Session Resume Complete ==={Colors.NC}")
        input("\nPress Enter to return to menu...")
        return
    
    # New crack attacks (options 2-5)
    session_name = input("Enter a name for this session: ").strip() or "hcx_session"
    hashfile = selected['path']
    cmd_base = f"hashcat -m 22000 {hashfile} -w 3 --session={session_name} --potfile-path={potfile} --force"
    
    if ch == "2":  # Dictionary
        if not os.path.exists(Config.WORDLIST):
            print(f"{Colors.RED}[!] Wordlist {Config.WORDLIST} not found!{Colors.NC}")
            return
        run_command(f"{cmd_base} {Config.WORDLIST}", "Running Dictionary Attack", cwd=str(out_dir))
        
    elif ch == "3":  # Combination
        w1 = input("Path to first wordlist: ").strip()
        w2 = input("Path to second wordlist: ").strip()
        run_command(f"{cmd_base} -a 1 {w1} {w2}", "Running Combination Attack", cwd=str(out_dir))
        
    elif ch == "4":  # Bruteforce/Mask
        mask = input("Enter mask (e.g., ?d?d?d?d?d?d?d?d): ")
        run_command(f"{cmd_base} -a 3 {mask}", f"Running Mask Attack: {mask}", cwd=str(out_dir))
        
    elif ch == "5":  # Hybrid
        if not os.path.exists(Config.WORDLIST):
            print(f"{Colors.RED}[!] Wordlist {Config.WORDLIST} not found!{Colors.NC}")
            return
        mask = input("Enter mask to append/prepend (e.g., ?d?d?d): ")
        run_command(f"{cmd_base} -a 6 {Config.WORDLIST} {mask}", f"Running Hybrid Attack with mask: {mask}", cwd=str(out_dir))
    
    print(f"\n{Colors.GREEN}=== Cracking Complete ==={Colors.NC}")
    input("\nPress Enter to return to menu...")


def settings():
    global Config
    print(f"\n{Colors.BLUE}=== Settings ==={Colors.NC}")
    print(f"1. Interface     → {Config.INTERFACE}")
    print(f"2. Wordlist      → {Config.WORDLIST}")
    print("0. Back")
    
    ch = input(f"\n{Colors.YELLOW}Choose what to change: {Colors.NC}")
    if ch == "1":
        Config.INTERFACE = input("New interface name: ").strip() or Config.INTERFACE
    elif ch == "2":
        Config.WORDLIST = input("Full path to wordlist: ").strip() or Config.WORDLIST
    
    print(f"{Colors.GREEN}Settings updated.{Colors.NC}")
    input("Press Enter...")

def check_dependencies():
    """Check that required tools are installed"""
    missing = []
    tools = ['hcxdumptool', 'hcxpcapngtool', 'hashcat']
    
    for tool in tools:
        result = subprocess.run(f"which {tool}", shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            missing.append(tool)
    
    if missing:
        print(f"{Colors.RED}[!] Missing required tools: {', '.join(missing)}{Colors.NC}")
        print(f"{Colors.YELLOW}    Install with: apt-get install hcxtools hashcat{Colors.NC}")
        return False
    
    if not os.path.exists(Config.WORDLIST):
        print(f"{Colors.YELLOW}[!] Default wordlist not found: {Config.WORDLIST}{Colors.NC}")
        print(f"{Colors.YELLOW}    You can set a custom wordlist in Settings menu{Colors.NC}")
        print(f"{Colors.YELLOW}    Or download rockyou.txt from GitHub{Colors.NC}")
    
    return True

# ===================== START =====================
if __name__ == "__main__":
    # Check dependencies first
    if not check_dependencies():
        sys.exit(1)
    
    if os.geteuid() != 0:
        print(f"{Colors.RED}Please run with: sudo python3 hcx.py{Colors.NC}")
        sys.exit(1)
    
    Config.get_base_dir().mkdir(parents=True, exist_ok=True)
    check_interface()
    main_menu()
