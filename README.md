<div align="center">
  <img src="hcx.png" alt="HCXFlow Logo" width="300"/>

```text
 ██╗  ██╗ ██████╗██╗  ██╗███████╗██╗      ██████╗ ██╗    ██╗
 ██║  ██║██╔════╝╚██╗██╔╝██╔════╝██║     ██╔═══██╗██║    ██║
 ███████║██║      ╚███╔╝ █████╗  ██║     ██║   ██║██║ █╗ ██║
 ██╔══██║██║      ██╔██╗ ██╔══╝  ██║     ██║   ██║██║███╗██║
 ██║  ██║╚██████╗██╔╝ ██╗██║     ███████╗╚██████╔╝╚███╔███╔╝
 ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝ 
```

  <h3>Capture. Extract. Crack.</h3>
  <p><i>An advanced, automated framework for WiFi packet capture, extraction, and cracking.</i></p>
  <p><b>by Ebisu</b></p>
</div>

---

## ⚡ Overview

**HCXFlow** is a comprehensive WiFi auditing framework that simplifies complex wireless security assessment workflows into an intuitive CLI interface. By wrapping powerful tools like `hcxdumptool`, `hcxpcapngtool`, `hcxhashtool`, and `hashcat`, it provides a seamless experience from capturing packets to cracking hashes.

## ✨ Key Features

### Auto-Detection
- **🔍 Dependency Check:** Automatically verifies required tools (hcxdumptool, hcxpcapngtool, hashcat) on startup
- **📂 Auto Wordlist Detection:** Automatically finds wordlist from common locations:
  - `/usr/share/wordlists/rockyou.txt`
  - `/usr/share/wordlists/rockyou.txt.gz`
  - `/usr/share/passwords.txt`
  - `/usr/share/john/password.lst`
  - `/opt/wordlists/rockyou.txt`

### Capture & Extraction
- **📡 Dynamic Interface Selection:** Automatically detects and lets you choose available monitor-mode interfaces
- **🎯 Targeted Capture:** Filter captures by specific ESSID or capture all nearby traffic
- **⏱️ Flexible Capture Duration:** Set custom capture time (minutes) or manually stop with Ctrl+C
- **🔄 Automatic Conversion:** Auto-converts captured packets to hashcat format after capture
- **💾 Session Persistence:** Capture files are saved even if interrupted by Ctrl+C

### Cracking Options
- **📖 Dictionary Attack:** Use rockyou.txt or custom wordlists
- **🔗 Combination Attack:** Combine two wordlists
- **🎭 Bruteforce (Mask) Attack:** Custom mask patterns (e.g., ?d?d?d?d?d?d?d?d)
- **🧬 Hybrid Attack:** Dictionary with mask prefix/suffix

### Session Management
- **⏸️ Pause & Resume:** Interrupt cracking with Ctrl+C and resume later
- **💾 Persistent Sessions:** Hashcat sessions are saved and can be resumed anytime
- **📂 Multiple Input Sources:** Resume from saved hashcat sessions OR crack extracted hash files

### File Management
- **📋 Smart File Selection:** Choose from list with:
  - File size and date information
  - Hash count (for extracted files) and ESSID count (for capture files)
  - Pagination for large file lists (10 items per page)
- **🔍 Navigation:** Use `N` for next page, `P` for previous page, `0` to go back

---

## 🚀 Getting Started

### Prerequisites

Install the required tools:

```bash
# Install hcxtools (includes hcxdumptool, hcxpcapngtool, hcxhashtool)
apt-get install hcxtools

# Install hashcat
apt-get install hashcat

# Verify installations
hcxdumptool --version
hashcat --version
```

### Execution

Run the script with root privileges:

```bash
sudo python3 hcx.py
```

---

## 🛠️ Menu Options

### Main Menu

| Option | Description | Requires Monitor Mode |
|--------|-------------|----------------------|
| **1. Full** | Automated workflow: Capture (5 min) → Extract → Crack | ✅ Yes |
| **2. Capture** | Start packet capture with optional ESSID filter | ✅ Yes |
| **3. Extract** | Convert .pcapng files to .hc22000 hash format | ❌ No |
| **4. Crack** | Open cracking menu with attack options | ❌ No |
| **5. Settings** | Configure interface and wordlist | ❌ No |
| **0. Exit** | Exit the program | ❌ No |

> **Note:** Options 1 and 2 require a wireless adapter in monitor mode.
> If no monitor mode interface is found, the script will show an error and
> recommend using Options 3 (Extract) or 4 (Crack) instead. |

### Crack Menu (Option 4)

| Option | Description | Input Required |
|--------|-------------|---------------|
| **1. Resume Hashcat** | Resume saved hashcat session | Select from session list |
| **2. Dictionary Attack** | Wordlist-based attack | Select hash file + wordlist |
| **3. Combination Attack** | Combine two wordlists | Select hash file + 2 wordlists |
| **4. Bruteforce (Mask)** | Mask pattern attack | Select hash file + mask |
| **5. Hybrid Attack** | Dictionary + mask | Select hash file + wordlist + mask |
| **6. Back** | Return to main menu | - |

### Settings Menu (Option 5)

| Option | Description |
|--------|-------------|
| **1. Interface** | Change wireless interface |
| **2. Wordlist** | Change default wordlist path |
| **0. Back** | Return to main menu |

---

## 📁 File Structure

```
hcxsuite/
├── hcx.py              # Main script
├── README.md            # This file
├── hcx.png             # Logo
├── targets.txt         # Target ESSIDs (optional)
├── capture*.pcapng     # Captured packet files
├── essids_*.txt        # Extracted ESSIDs
├── identities_*.txt    # Extracted identities
├── usernames_*.txt     # Extracted usernames
├── *.hc22000           # Hash files (hashcat format)
└── cracked_passwords/
    └── cracked.txt    # Cracked passwords
```

---

## 🔧 Workflow Examples

### Example 1: Full Automated Workflow

```
Main Menu → 1. Full
- Captures packets for 5 minutes
- Converts to hash format
- Runs dictionary attack with rockyou.txt
```

### Example 2: Custom Capture

```
Main Menu → 2. Capture
- Select interface
- Enter target ESSID (or blank for all)
- Enter duration (0 for manual stop)
- Press Ctrl+C to stop early
- Files saved automatically
```

### Example 3: Extract from Existing Capture

```
Main Menu → 3. Extract
- Shows list of .pcapng files
- Select file (with pagination)
- Converts to .hc22000 format
```

### Example 4: Resume Previous Session

```
Main Menu → 4. Crack
→ 1. Resume Hashcat
- Shows list of saved sessions
- Select session to resume
```

### Example 5: Dictionary Attack

```
Main Menu → 4. Crack
→ 2. Dictionary Attack
- Shows list of .hc22000 files
- Select hash file
- Runs dictionary attack
```

---

## 🎯 Tips & Tricks

### Finding Your Wireless Interface
```bash
# List monitor-mode interfaces
iwconfig

# Or use hcxdumptool
hcxdumptool -i wlan0 --rds=3
```

### Common Wordlists
```bash
# Kali Linux default wordlists
/usr/share/wordlists/rockyou.txt
/usr/share/wordlists/passwords.txt
/usr/share/john/password.lst
```

### Useful Mask Patterns
```bash
# 8 digit numeric
?d?d?d?d?d?d?d?d

# Mix of digits and lowercase
?d?l?d?l?d?l?d?l

# Custom pattern
 password?d?d = "password00" to "password99"
```

---

## ⚠️ Legal Notice

> **This tool is provided for educational and authorized auditing purposes only.** 
> 
> Unauthorized access to computer systems or wireless networks is illegal and unethical. 
> Ensure you have explicit permission before testing any network or system that you do not own.
> 
> The developers assume no liability for misuse of this tool.

---

## 📋 Changelog

### Version 1.0 (Current)
- Initial release with capture, extract, and crack workflows
- File selection with info display
- Pagination for large file lists
- Session resume functionality
- Multiple attack vectors (Dictionary, Combination, Mask, Hybrid)
- Settings menu for interface and wordlist configuration

## Support ☕

If this project saves you time or helps you learn, you can support development:

[☕ Buy me a coffee](https://ko-fi.com/ebisu1og)
</div>
