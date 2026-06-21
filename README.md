# 🔍 ULP-Scanner (Filter, Parser)

**Enterprise-Grade ULP (URL:Login:Password) Parser with Advanced Filtering, Memory Management, and Interactive Controls**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/badge/release-vAlien-brightgreen.svg)](https://github.com/tc4dy/ULP-Scanner/releases/tag/vAlien)
[![Platform](https://img.shields.io/badge/platform-All%20Platforms-blue.svg)](https://github.com/tc4dy/ULP-Scanner)

---

## 📖 Table of Contents

- [🚨 Legal & Ethical Notice](#-legal--ethical-notice) — **Read this first**
- [📌 Overview](#-overview)
- [✨ Core Features](#-core-features)
- [🏗️ Architecture](#️-architecture)
- [💻 Usage Modes](#-usage-modes)
- [📋 Parameter Reference](#-parameter-reference)
- [📊 Performance Benchmarks](#-performance-benchmarks)
- [🔍 Filtering Examples](#-filtering-examples)
- [⚙️ Advanced Configuration](#️-advanced-configuration)
- [🔒 Security Architecture](#-security-architecture)
- [🛠️ Troubleshooting](#️-troubleshooting)
- [📁 Output & Files](#-output--files)
- [💡 Tips & Tricks](#-tips--tricks)
- [🎯 Use Cases](#-use-cases)
- [📊 Technical Details](#-technical-details)
- [📜 License & Attribution](#-license--attribution)
- [Installation](#-installation)

---

## 🚨 Legal & Ethical Notice

**⚠️ IMPORTANT: Read before using this tool**

This tool is designed for and may **ONLY** be used on:
- ✓ Data you own
- ✓ Systems you have explicit written permission to analyze
- ✓ Educational environments (sandboxed, non-production)
- ✓ Authorized security testing/penetration tests
- ✓ Legitimate incident response within your organization

### Prohibited Uses:
- ✗ Analyzing data without authorization
- ✗ Processing others' private information
- ✗ Accessing or analyzing systems without consent
- ✗ Any activity violating computer crime laws
- ✗ Data trafficking or sale

### Compliance Requirements:
You must comply with applicable regulations in your jurisdiction:
- **GDPR** (European Union)
- **KVKK** (Turkey)
- **CCPA** (California, USA)
- **PIPEDA** (Canada)
- **Local data protection laws** in your country

### Your Responsibility:
**Users bear all responsibility for their use of this tool.** The author provides no warranty and assumes no liability for misuse. By using ULP-Scanner, you acknowledge:
1. You have legal authority to process the data
2. You understand and accept all legal consequences
3. You will not violate any laws or regulations
4. You will not use this for unauthorized access or data theft

**Violation of these terms may result in civil and criminal liability.**

---

## 📌 Overview

ULP-Scanner is a production-ready command-line tool designed for parsing, filtering, and analyzing ULP-formatted credential files. Built with security-first architecture, it handles everything from small datasets to multi-gigabyte files without breaking a sweat. The dual-mode interface (CLI + Interactive) makes it work for both automation scripts and manual exploration.

Think of it as grep on steroids, but specifically engineered for credential analysis, security auditing, and authorized data validation.

---

## ✨ Core Features

| Feature | What It Actually Does |
|---------|----------------------|
| **Dual-Mode Operation** | Run from command line for automation, or launch interactive menu for exploration. Switch between modes on the fly. |
| **Two Parsing Strategies** | Mode 1: Deep URL text search (finds "gmail" in any part of URL). Mode 2: Domain-specific filtering (.com, .gov, .edu). |
| **Memory-Optimized Processing** | Chunks large files into 8KB buffers. Processes multi-GB files without RAM explosion. Real-time memory monitoring. |
| **Security-First Architecture** | Path validation, pattern sanitization, automatic backups before writing, corrupted line detection, graceful error handling. |
| **Regex Pattern Support** | Full regex support with automatic fallback to simple matching if compilation fails. Case-insensitive by default. |
| **Real-Time Progress Tracking** | Visual progress bar with line/file size estimates. Process 1M lines and actually know where you are. |
| **Comprehensive Error Logging** | Timestamped log files capture corrupted lines, encoding issues, and parsing failures without stopping execution. |
| **Customizable Output Control** | Limit results, disable file writing (console-only mode), skip statistics display, adjust verbosity levels. |
| **Multi-Language UI** | English and Turkish support across all menus and output messages. |
| **Performance Metrics** | Know exactly what happened: lines processed, error rate, match rate, parse time, memory consumed, processing speed. |

---

## 🏗️ Architecture

The tool is built around several interconnected components:

### Core Processing Pipeline
```
Input File → Path Validation → Encoding Detection → 
Chunked Reading → Pattern Matching → Result Collection → 
Safe File Writing
```

### Key Components

| Component | Responsibility |
|-----------|-----------------|
| **SecurityValidator** | Validates file paths (exists, readable, size limits), pattern safety (length checks, domain format for mode 2), mode correctness |
| **FileHandler** | Safe file operations with automatic backups, atomic writes using temp files, line estimation for progress bars |
| **MemoryMonitor** | Tracks process memory usage and system resources (requires psutil, but gracefully degrades) |
| **LoggerManager** | Timestamped error logging to disk, separate file per run, captures all parsing errors without halting |
| **InteractiveMenu** | Colored terminal UI (Windows-compatible), input validation, progress display, result formatting |
| **ULPParser** | Main orchestrator: reads config, processes file line-by-line, applies filters, manages results |

### Data Flow Architecture
```
Config (CLI args or Interactive)
    ↓
ULPParser.parse_file()
    ├→ SecurityValidator.validate_path() [File exists, readable, size OK]
    ├→ SecurityValidator.validate_pattern() [Pattern safe, correct format]
    ├→ FileHandler.estimate_line_count() [For progress bar]
    └→ Line-by-line processing
        ├→ FileHandler.safe_open() [Smart encoding handling]
        ├→ Pattern matching (Regex or simple)
        ├→ Error logging [Timestamped, non-blocking]
        └→ Result collection
    ↓
ParseResult (stats, matches, errors)
    ↓
FileHandler.write_safe() [Atomic write with backup]
```

---

## 💻 Usage Modes

### Mode 1: Interactive (Recommended for Exploration)
```bash
python scanner.py
# Menu appears with options:
# 1. Parse ULP File
# 2. View Current Configuration
# 3. Change Configuration
# 4. View Statistics
# 5. Exit
```

When you choose "Parse ULP File", it:
- Validates the file and pattern
- Shows file information (size, line count estimate)
- Displays live progress bar
- Shows results with statistics
- Optionally writes to file

### Mode 2: Command-Line (For Automation)
```bash
# Basic filtering
python scanner.py -f creds.ulp -m 1 -p "amazon"

# With all options
python scanner.py \
  -f large_breach.ulp \
  -m 2 \
  -p ".gov" \
  -o government_sites.txt \
  --encoding utf-8 \
  --limit 10000 \
  -v
```

### Mode 3: Advanced Command-Line (Scripting)
```bash
# Console output only, no file write, suppress stats
python scanner.py -f data.ulp -m 1 -p "test" --no-write -q

# Verbose mode with all details
python scanner.py -f data.ulp -m 1 -p "test" -v --no-log

# Custom buffer size for slow storage
python scanner.py -f data.ulp -m 1 -p "test" --buffer-size 65536
```

---

## 📋 Parameter Reference

| Parameter | Type | Default | What It Does |
|-----------|------|---------|--------------|
| `-f, --file` | str | - | Path to ULP file to process |
| `-m, --mode` | int | - | Filtering mode: 1=URL text, 2=Domain extension |
| `-p, --pattern` | str | - | Search pattern (case-insensitive, supports regex) |
| `-o, --output` | str | result.txt | Output filename for matches |
| `--lang` | str | en | UI language: en (English) or tr (Turkish) |
| `-q, --quiet` | flag | off | Minimal output mode (results only) |
| `-v, --verbose` | flag | off | Detailed output (error details, full stats) |
| `--limit` | int | 0 | Stop after N matches (0=all matches) |
| `--encoding` | str | utf-8 | File encoding (utf-8, iso-8859-1, cp1252, etc.) |
| `--buffer-size` | int | 8192 | Read buffer size in bytes (increase for slow drives) |
| `--max-errors` | int | 10 | How many error details to display |
| `--no-log` | flag | off | Disable timestamped error log file |
| `--no-write` | flag | off | Don't create output file (console only) |
| `--no-stats` | flag | off | Skip statistics display |
| `--interactive` | flag | off | Force interactive mode |
| `--no-interactive` | flag | off | Force CLI mode (skip menu) |

### Mode Explanation in Detail

**Mode 1 (URL Text Filtering):**
Searches for your pattern anywhere within the URL field. Case-insensitive and regex-aware.

```
Pattern: "gmail"
Input: https://mail.gmail.com:user@example.com:password123
Match: ✓ YES (contains "gmail")

Pattern: "^https://.*facebook"
Input: https://facebook.com:user:pass
Match: ✓ YES (regex matches)
```

**Mode 2 (Domain Extension Filtering):**
Matches the domain extension at the end of the URL. Useful for finding all .gov sites, all .edu, etc.

```
Pattern: ".com"
Input: https://example.com:user:pass
Match: ✓ YES (ends with ".com")

Pattern: ".edu"
Input: https://university.edu:student:pass
Match: ✓ YES (ends with ".edu")
```

---

## 📊 Performance Benchmarks

Tested on modern hardware (SSD, 16GB RAM):

| File Size | Lines | Parse Time | Speed | Memory Peak |
|-----------|-------|------------|-------|-------------|
| 10 MB | ~100K | 0.3s | 333K lines/s | 15 MB |
| 100 MB | ~1M | 1.8s | 555K lines/s | 45 MB |
| 1 GB | ~10M | 18s | 555K lines/s | 85 MB |
| 5 GB | ~50M | 95s | 526K lines/s | 150 MB |

*Note: Speed varies with pattern complexity and match rate. Regex patterns are slower than simple text matching.*

---

## 🔍 Filtering Examples

### Example 1: Find All Gmail Accounts
```bash
python scanner.py -f breach_2024.ulp -m 1 -p "gmail" -o gmail_creds.txt -v
```
Output: Finds every entry with "gmail" in the URL field, shows statistics.

### Example 2: Extract Government Domains
```bash
python scanner.py -f mixed_data.ulp -m 2 -p ".gov" -o government.txt
```
Output: Every credential ending with .gov domain.

### Example 3: Find Educational Institutions (First 5000)
```bash
python scanner.py -f large_breach.ulp -m 2 -p ".edu" --limit 5000 -q
```
Output: First 5000 .edu entries, minimal output.

### Example 4: Complex Regex Pattern
```bash
python scanner.py -f data.ulp -m 1 -p "^https://.*\.(bank|finance)" -v
```
Output: URLs matching bank or finance sites with HTTPS protocol.

### Example 5: Non-UTF8 Encoding
```bash
python scanner.py -f legacy_data.ulp -m 1 -p "test" --encoding iso-8859-1
```
Output: Processes file with legacy Latin-1 encoding instead of UTF-8.

---

## 📁 Output & Files

### Generated Files

| File Name | Purpose |
|-----------|---------|
| `result.txt` (or custom name) | Filtered credentials in ULP format (URL:Login:Password) |
| `ulp_parser_error_[timestamp].log` | Timestamped error log with line numbers and issues |
| `result.txt.bak_[timestamp]` | Automatic backup if output file already exists |
| `result.txt.tmp_[timestamp]` | Temporary file during write (deleted on completion) |

### Output File Format
```
https://mail.gmail.com:john.doe@gmail.com:SecurePass123
https://accounts.google.com:jane.smith@gmail.com:Pass456Xyz
https://drive.google.com:admin@gmail.com:AdminPass789
```

### Error Log Format
```
ulp_parser_error_20240115_143022.log:
2024-01-15 14:30:22,445 - ERROR - Line 1247: Invalid format (less than 3 fields)
2024-01-15 14:30:23,112 - ERROR - Line 3891: Empty field detected
2024-01-15 14:30:24,556 - ERROR - Line 5234: Regex compilation error
```

---

## ⚙️ Advanced Configuration

### Tuning for Different Scenarios

**Processing Slow USB Drive:**
```bash
python scanner.py -f /mnt/usb/data.ulp -m 1 -p "test" --buffer-size 65536
# Larger buffer = fewer disk seeks
```

**Memory-Constrained System:**
```bash
python scanner.py -f huge.ulp -m 1 -p "test" --buffer-size 1024 -q --no-log
# Smaller buffer, minimal output, no logging overhead
```

**High-Performance SSD:**
```bash
python scanner.py -f fast_drive.ulp -m 1 -p "test" --buffer-size 131072 -v
# Aggressive buffering, detailed output
```

**Batch Processing Multiple Files:**
```bash
#!/bin/bash
for file in *.ulp; do
  python scanner.py \
    -f "$file" \
    -m 1 \
    -p "gmail" \
    -o "${file%.ulp}_gmail.txt" \
    -q
done
```

---

## 🔒 Security Architecture

The tool implements multiple layers of security:

### Input Validation
- **Path Validation**: Checks file exists, is readable, size between 0-10GB
- **Pattern Validation**: Length limit (1024 chars), domain format validation for Mode 2
- **Encoding Validation**: Supports multiple encodings, gracefully handles invalid bytes

### Safe File Operations
- **Atomic Writes**: Uses temp file + rename pattern (no partial writes)
- **Automatic Backups**: Creates timestamped backup before overwriting files
- **Permission Preservation**: Respects file system permissions

### Error Handling
- **Graceful Degradation**: Regex error? Falls back to simple matching
- **Partial Failure**: One bad line doesn't stop processing
- **Memory Safety**: Large files chunked, not loaded into RAM
- **Signal Handling**: Ctrl+C stops gracefully with partial results saved

### What It Doesn't Do
- Network access (fully offline)
- System commands (no exec/shell)
- Write outside target directory
- Execute user-supplied code

---

## 📈 Statistics & Metrics

After processing, you get detailed metrics:

```
=== RESULTS ===
Found 1,247 matches
Statistics:
  = Total lines processed: 50,000
  = Error lines: 23
  = Error rate: 0.05%
  = Match rate: 2.49%
  = Parse time: 2.847s
  = Memory usage: 12.34 MB
  = Processing speed: 17,575 lines/s
```

What each metric tells you:
- **Error Rate**: Data quality indicator (high % = corrupted file)
- **Match Rate**: Pattern effectiveness (low % = too specific pattern)
- **Parse Time**: Performance baseline for this file size
- **Memory Usage**: Actual RAM consumed (useful for resource planning)

---

## 🛠️ Troubleshooting

### Problem: "File too large (>10GB)"
**Solution**: Tool has a 10GB safety limit. Split file and process in chunks.
```bash
split -l 10000000 huge.ulp chunk_
```

### Problem: "Permission denied: /path/file.ulp"
**Solution**: Check read permissions
```bash
chmod 644 file.ulp
# Or run with appropriate user
```

### Problem: High error rate (>5%)
**Diagnosis**: File likely corrupted or wrong encoding
```bash
# Try different encoding
python scanner.py -f data.ulp -m 1 -p "test" --encoding iso-8859-1 -v

# Or check file format
head -20 data.ulp | od -c
```

### Problem: Out of memory
**Solution**: Use streaming mode (already default) and add limits
```bash
python scanner.py -f data.ulp -m 1 -p "test" --limit 100000 -q
```

### Problem: Slow processing
**Diagnosis**: Could be pattern complexity, disk speed, or CPU
```bash
# Measure baseline with simple pattern
time python scanner.py -f data.ulp -m 1 -p "a" -q --no-log

# Try different buffer size
python scanner.py -f data.ulp -m 1 -p "test" --buffer-size 131072
```

### Problem: Regex pattern not working
**Solution**: Pattern validation happens, but test in Python first
```python
import re
pattern = "^https://.*gmail"
test = "https://mail.gmail.com"
print(bool(re.search(pattern, test, re.IGNORECASE)))
```

---

## 🎯 Use Cases

### Security Auditing
Find all compromised accounts from a specific organization in a large breach dump.
```bash
python scanner.py -f breach.ulp -m 2 -p ".company.com" -v
```

### Data Validation
Check credential file integrity before importing to security tools.
```bash
python scanner.py -f creds.ulp -m 1 -p "test" -q --no-write
# Check error log for data quality
```

### Compliance Analysis
Extract credentials matching specific domain patterns for compliance reporting.
```bash
python scanner.py -f data.ulp -m 2 -p ".gov" -o government.txt
```

### Incident Response
Quickly search through leaked data during active incident to determine exposure scope.
```bash
python scanner.py -f leaked.ulp -m 1 -p "company_name" -v
```

---

## 📊 Technical Details

### File Format Support
- **Input Format**: ULP (URL:Login:Password) with colons as delimiters
- **Encoding Support**: UTF-8 (default), ISO-8859-1, CP1252, and any Python-supported encoding
- **Line Handling**: Automatic newline detection (LF, CRLF), handles trailing spaces
- **Invalid Data**: Corrupted lines logged, not processed

### Processing Strategy
1. **Pre-flight Check**: File validation, encoding test
2. **Line Estimation**: Quick scan for progress bar baseline
3. **Chunked Reading**: 8KB default buffer, configurable up to 256KB
4. **Pattern Matching**: Regex with fallback, case-insensitive
5. **Result Collection**: Stored in memory (limited by --limit)
6. **Safe Writing**: Atomic operation with backup

### Memory Characteristics
- **Per-Match Storage**: ~200 bytes per credential tuple
- **Buffer Memory**: Configurable (8-256 KB)
- **Overhead**: ~10 MB for structures and logging
- **Scaling**: Linear with file size, not match count

---

## 💡 Tips & Tricks

### Get Results Count Without Output File
```bash
python scanner.py -f data.ulp -m 1 -p "test" --no-write -q | tail -1
```

### Process Until Limit, Skip Statistics
```bash
python scanner.py -f huge.ulp -m 1 -p "test" --limit 50000 --no-stats -q
```

### Save Results with Timestamp
```bash
python scanner.py -f data.ulp -m 1 -p "test" -o "results_$(date +%s).txt"
```

### Dry Run (Check Pattern Without Processing)
```bash
python scanner.py -f data.ulp -m 1 -p "test" --no-write -q --no-log
```

### Capture Both Success and Errors
```bash
python scanner.py -f data.ulp -m 1 -p "test" -v 2>&1 | tee output.log
```

---

## ⬇️ Installation

### Quick Start
```bash
# Clone the repository
git clone https://github.com/tc4dy/ULP-Scanner.git
cd ULP-Scanner

# No dependencies needed (uses Python standard library)
# Just run the scanner
python scanner.py
```

### Optional: Install psutil for Advanced Monitoring
```bash
pip install psutil
```

The tool works perfectly without psutil, but having it enables real-time system memory monitoring in the statistics display.

---

## 📜 License & Attribution

**MIT License** - Free to use, modify, and distribute for authorized purposes.

**Created by**: [@tc4dy](https://github.com/tc4dy)

**GitHub**: [https://github.com/tc4dy/ULP-Scanner](https://github.com/tc4dy/ULP-Scanner)
