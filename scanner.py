import os
import sys
import re
import time
import logging
import argparse
import signal
import platform
from pathlib import Path
from typing import List, Tuple, Optional, Generator, Dict, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    GRAY = '\033[90m'
    WHITE = '\033[97m'
    BLACK = '\033[30m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

    @staticmethod
    def disable():
        if platform.system() == 'Windows':
            os.system('')
        else:
            pass

    @staticmethod
    def colorize(text: str, color: str = WHITE, bold: bool = False, underline: bool = False) -> str:
        result = ""
        if bold:
            result += Colors.BOLD
        if underline:
            result += Colors.UNDERLINE
        result += color + text + Colors.END
        return result

    @staticmethod
    def box(text: str, color: str = CYAN, width: int = 60) -> str:
        border = color + "=" * width + Colors.END
        return f"{border}\n{color}|{Colors.END} {text} {color}|{Colors.END}\n{border}"

    @staticmethod
    def progress_bar(percent: float, width: int = 50, color: str = GREEN) -> str:
        filled = int(width * percent / 100)
        empty = width - filled
        bar = color + "[" + "=" * filled + Colors.GRAY + "." * empty + Colors.END + "]"
        return f"{bar} {percent:.1f}%"

@dataclass
class ParseResult:
    matches: List[Tuple[str, str, str]] = field(default_factory=list)
    total_lines: int = 0
    error_lines: int = 0
    error_details: List[str] = field(default_factory=list)
    parse_time: float = 0.0
    memory_usage: float = 0.0
    start_time: float = 0.0
    end_time: float = 0.0
    bytes_processed: int = 0
    match_rate: float = 0.0

@dataclass
class Config:
    file_path: str = ""
    mode: int = 1
    pattern: str = ""
    output: str = "result.txt"
    lang: str = "en"
    quiet: bool = False
    verbose: bool = False
    no_log: bool = False
    limit: int = 0
    encoding: str = "utf-8"
    buffer_size: int = 8192
    max_errors_display: int = 10
    interactive: bool = True
    no_write: bool = False
    show_stats: bool = True

    def validate(self) -> None:
        if not self.file_path:
            raise ValueError("File path cannot be empty")
        if not Path(self.file_path).exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        if self.mode not in (1, 2):
            raise ValueError("Mode must be 1 or 2")
        if not self.pattern:
            raise ValueError("Pattern cannot be empty")
        if self.lang not in ('en', 'tr'):
            raise ValueError("Language must be 'en' or 'tr'")
        if self.limit < 0:
            raise ValueError("Limit cannot be negative")
        if self.buffer_size < 1:
            raise ValueError("Buffer size must be positive")

class SecurityValidator:
    @staticmethod
    def validate_path(path: str) -> Tuple[bool, str]:
        try:
            p = Path(path).resolve()
            if not p.exists():
                return False, "File does not exist"
            if not p.is_file():
                return False, "Path is not a file"
            if p.stat().st_size == 0:
                return False, "File is empty"
            if p.stat().st_size > 10 * 1024 * 1024 * 1024:
                return False, "File too large (>10GB)"
            try:
                with open(p, 'rb') as test:
                    test.read(1)
            except Exception:
                return False, "File is not readable"
            return True, "Valid"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    @staticmethod
    def validate_pattern(pattern: str, mode: int) -> Tuple[bool, str]:
        if not pattern:
            return False, "Pattern cannot be empty"
        if len(pattern) > 1024:
            return False, "Pattern too long (max 1024 characters)"
        if mode == 2:
            if not pattern.startswith('.'):
                return False, "Domain extension must start with '.'"
            if '.' in pattern[1:]:
                return False, "Domain extension must contain only one dot"
        return True, ""

    @staticmethod
    def validate_mode(mode: int) -> bool:
        return mode in (1, 2)

class MemoryMonitor:
    @staticmethod
    def get_usage() -> float:
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0

    @staticmethod
    def get_system_memory() -> Dict[str, float]:
        try:
            import psutil
            mem = psutil.virtual_memory()
            return {
                'total': mem.total / 1024 / 1024 / 1024,
                'available': mem.available / 1024 / 1024 / 1024,
                'used': mem.used / 1024 / 1024 / 1024,
                'percent': mem.percent
            }
        except Exception:
            return {'total': 0, 'available': 0, 'used': 0, 'percent': 0}

class FileHandler:
    @staticmethod
    def safe_open(file_path: str, mode: str = 'r', encoding: str = 'utf-8', buffer_size: int = 8192):
        try:
            return open(file_path, mode, encoding=encoding, errors='replace', buffering=buffer_size)
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except PermissionError:
            raise PermissionError(f"Permission denied: {file_path}")
        except Exception as e:
            raise Exception(f"Cannot open file: {str(e)}")

    @staticmethod
    def write_safe(file_path: str, data: List[str]) -> Tuple[bool, str]:
        try:
            temp_path = f"{file_path}.tmp_{int(time.time())}"
            with open(temp_path, 'w', encoding='utf-8') as f:
                for line in data:
                    f.write(line + '\n')
            if os.path.exists(file_path):
                backup_path = f"{file_path}.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.rename(file_path, backup_path)
            os.rename(temp_path, file_path)
            return True, f"Successfully written to {file_path}"
        except Exception as e:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass
            return False, f"Write error: {str(e)}"

    @staticmethod
    def estimate_line_count(file_path: str) -> int:
        try:
            with open(file_path, 'rb') as f:
                count = 0
                chunk = f.read(1024 * 1024)
                while chunk:
                    count += chunk.count(b'\n')
                    chunk = f.read(1024 * 1024)
                return count
        except Exception:
            return -1

    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        try:
            p = Path(file_path)
            stat = p.stat()
            return {
                'size': stat.st_size,
                'size_mb': stat.st_size / 1024 / 1024,
                'size_gb': stat.st_size / 1024 / 1024 / 1024,
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'created': datetime.fromtimestamp(stat.st_ctime),
                'lines': FileHandler.estimate_line_count(file_path)
            }
        except Exception:
            return {'size': 0, 'size_mb': 0, 'size_gb': 0, 'modified': None, 'created': None, 'lines': -1}

class LoggerManager:
    def __init__(self, config: Config):
        self.config = config
        self.log_file = f"ulp_parser_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.logger = logging.getLogger('ULPParser')
        self.logger.setLevel(logging.ERROR)
        if not config.no_log:
            handler = logging.FileHandler(self.log_file, encoding='utf-8')
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)

    def log_error(self, message: str) -> None:
        self.logger.error(message)

    def log_critical(self, message: str) -> None:
        self.logger.critical(message)

class InteractiveMenu:
    @staticmethod
    def clear_screen() -> None:
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def display_header() -> None:
        Colors.disable()
        print("\n" + Colors.colorize("=" * 70, Colors.CYAN, bold=True))
        print(Colors.colorize("|", Colors.CYAN, bold=True) + " " * 68 + Colors.colorize("|", Colors.CYAN, bold=True))
        print(Colors.colorize("|", Colors.CYAN, bold=True) + " " * 10 + Colors.colorize("Advanced U:L:P Parser", Colors.BLUE, bold=True) + " " * 27 + Colors.colorize("|", Colors.CYAN, bold=True))
        print(Colors.colorize("|", Colors.CYAN, bold=True) + " " * 10 + Colors.colorize("Ethical & Educational Using Only", Colors.GREEN) + " " * 27 + Colors.colorize("|", Colors.CYAN, bold=True))
        print(Colors.colorize("|", Colors.CYAN, bold=True) + " " * 10 + Colors.colorize("@tc4dy", Colors.YELLOW) + " " * 37 + Colors.colorize("|", Colors.CYAN, bold=True))
        print(Colors.colorize("|", Colors.CYAN, bold=True) + " " * 68 + Colors.colorize("|", Colors.CYAN, bold=True))
        print(Colors.colorize("+" + "=" * 68 + "+", Colors.CYAN, bold=True) + "\n")

    @staticmethod
    def get_input(prompt: str, default: str = "", required: bool = True, input_type: type = str) -> Any:
        while True:
            if default:
                full_prompt = f"{Colors.colorize(prompt, Colors.WHITE)} {Colors.colorize(f'[{default}]', Colors.GRAY)}: "
            else:
                full_prompt = f"{Colors.colorize(prompt, Colors.WHITE)}: "
            
            value = input(full_prompt).strip()
            if not value and default:
                value = default
            if not value and required:
                print(Colors.colorize("Error: Input is required", Colors.RED))
                continue
            try:
                if input_type == int:
                    return int(value)
                elif input_type == bool:
                    return value.lower() in ('y', 'yes', 'true', 't', '1')
                else:
                    return value
            except ValueError:
                print(Colors.colorize(f"Error: Invalid {input_type.__name__} format", Colors.RED))
                continue

    @staticmethod
    def display_menu(options: List[Tuple[str, str]], title: str = "Select Option") -> int:
        print("\n" + Colors.colorize("-" * 50, Colors.GRAY))
        print(Colors.colorize(f">> {title}", Colors.CYAN, bold=True))
        print(Colors.colorize("-" * 50, Colors.GRAY))
        for idx, (key, desc) in enumerate(options, 1):
            print(f"  {Colors.colorize(str(idx), Colors.YELLOW, bold=True)}. {Colors.colorize(desc, Colors.WHITE)}")
        print(Colors.colorize("-" * 50, Colors.GRAY))
        
        while True:
            choice = input(Colors.colorize("Select [1-{}]: ".format(len(options)), Colors.CYAN)).strip()
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(options):
                    return choice_num
            except ValueError:
                pass
            print(Colors.colorize("Invalid choice. Please try again.", Colors.RED))

    @staticmethod
    def display_progress(current: int, total: int, prefix: str = "Processing") -> None:
        if total <= 0:
            return
        percent = min(100, (current / total) * 100)
        bar = Colors.progress_bar(percent)
        print(f"\r{Colors.colorize(prefix, Colors.CYAN)} {bar} {Colors.colorize(f'{current}/{total}', Colors.GRAY)}", end='', flush=True)

    @staticmethod
    def display_success(message: str) -> None:
        print(Colors.colorize("[+] " + message, Colors.GREEN))

    @staticmethod
    def display_error(message: str) -> None:
        print(Colors.colorize("[-] " + message, Colors.RED))

    @staticmethod
    def display_info(message: str, color: str = Colors.WHITE) -> None:
        print(Colors.colorize("[?] " + message, color))

    @staticmethod
    def display_warning(message: str) -> None:
        print(Colors.colorize("[!] " + message, Colors.YELLOW))

    @staticmethod
    def display_result(match: Tuple[str, str, str], index: int) -> None:
        url, login, pwd = match
        print(f"{Colors.colorize(str(index), Colors.YELLOW)}. {Colors.colorize(url, Colors.CYAN)}:{Colors.colorize(login, Colors.GREEN)}:{Colors.colorize(pwd, Colors.GRAY)}")

class ULPParser:
    def __init__(self, config: Config):
        self.config = config
        self.logger = LoggerManager(config)
        self.memory_monitor = MemoryMonitor()
        self.file_handler = FileHandler()
        self.security = SecurityValidator()
        self.result = ParseResult()
        self.menu = InteractiveMenu()
        self.interrupted = False

    def parse_file(self) -> ParseResult:
        self.result.start_time = time.time()
        self.result.memory_usage = self.memory_monitor.get_usage()
        
        try:
            is_valid, error_msg = self.security.validate_path(self.config.file_path)
            if not is_valid:
                raise ValueError(error_msg)
            
            is_valid, error_msg = self.security.validate_pattern(self.config.pattern, self.config.mode)
            if not is_valid:
                raise ValueError(error_msg)

            if not self.config.quiet:
                self._display_file_info()

            pattern_lower = self.config.pattern.lower()
            regex = self._create_regex(pattern_lower)
            
            total_lines_estimate = self.file_handler.estimate_line_count(self.config.file_path)
            if total_lines_estimate > 0:
                self.result.total_lines = total_lines_estimate
            
            if not self.config.quiet and total_lines_estimate > 0:
                self.menu.display_info(f"Processing {total_lines_estimate:,} lines...", Colors.CYAN)

            with self.file_handler.safe_open(
                self.config.file_path, 
                'r', 
                self.config.encoding,
                self.config.buffer_size
            ) as f:
                processed = 0
                for line_num, line in enumerate(f, 1):
                    if self.interrupted:
                        raise KeyboardInterrupt()
                    self._process_line(line.strip(), line_num, pattern_lower, regex)
                    processed += 1
                    if not self.config.quiet and total_lines_estimate > 0 and processed % 1000 == 0:
                        self.menu.display_progress(processed, total_lines_estimate)

            if not self.config.quiet and total_lines_estimate > 0:
                self.menu.display_progress(total_lines_estimate, total_lines_estimate)
                print()

            self.result.memory_usage = self.memory_monitor.get_usage() - self.result.memory_usage
            if self.result.total_lines > 0 and self.result.total_lines > 0:
                self.result.match_rate = (len(self.result.matches) / self.result.total_lines) * 100

        except KeyboardInterrupt:
            self.interrupted = True
            self.menu.display_warning("Processing interrupted by user")
        except Exception as e:
            self.logger.log_critical(f"Parser error: {str(e)}")
            raise

        self.result.end_time = time.time()
        self.result.parse_time = self.result.end_time - self.result.start_time
        return self.result

    def _create_regex(self, pattern_lower: str) -> Optional[re.Pattern]:
        try:
            if self.config.mode == 1:
                return re.compile(re.escape(pattern_lower), re.IGNORECASE)
            else:
                return re.compile(re.escape(pattern_lower) + r'$', re.IGNORECASE)
        except re.error as e:
            self.logger.log_error(f"Regex compile error: {str(e)}")
            if not self.config.quiet:
                self.menu.display_warning(f"Regex error: {str(e)}. Using simple matching.")
            return None

    def _process_line(self, line: str, line_num: int, pattern_lower: str, regex: Optional[re.Pattern]) -> None:
        if not line:
            return
        
        try:
            parts = line.split(':', 2)
            if len(parts) < 3:
                self._handle_error(line_num, f"Invalid format (less than 3 fields) -> {line[:100]}")
                return
            
            url, login, pwd = parts[0], parts[1], parts[2]
            if not url or not login or not pwd:
                self._handle_error(line_num, f"Empty field -> {line[:100]}")
                return
            
            if self._is_match(url.lower(), pattern_lower, regex):
                self.result.matches.append((url, login, pwd))
                if self.config.limit > 0 and len(self.result.matches) >= self.config.limit:
                    if not self.config.quiet:
                        self.menu.display_info(f"Reached limit of {self.config.limit} matches", Colors.YELLOW)
                    return

        except Exception as e:
            self._handle_error(line_num, f"Processing error ({str(e)}) -> {line[:100]}")
            self.logger.log_error(f"Line {line_num}: {str(e)}")

    def _is_match(self, url_lower: str, pattern_lower: str, regex: Optional[re.Pattern]) -> bool:
        if regex:
            return bool(regex.search(url_lower))
        if self.config.mode == 1:
            return pattern_lower in url_lower
        return url_lower.endswith(pattern_lower)

    def _handle_error(self, line_num: int, error_msg: str) -> None:
        self.result.error_lines += 1
        if len(self.result.error_details) < self.config.max_errors_display:
            self.result.error_details.append(f"Line {line_num}: {error_msg}")

    def _display_file_info(self) -> None:
        info = self.file_handler.get_file_info(self.config.file_path)
        if info['size_mb'] > 0:
            size_str = f"{info['size_mb']:.2f} MB" if info['size_mb'] < 1024 else f"{info['size_gb']:.2f} GB"
            self.menu.display_info(f"File size: {size_str}", Colors.GRAY)
        if info['lines'] > 0:
            self.menu.display_info(f"Estimated lines: {info['lines']:,}", Colors.GRAY)

    def write_results(self) -> Tuple[bool, str]:
        if not self.result.matches:
            return False, "No matches found"
        if self.config.no_write:
            return True, "Write disabled by --no-write option"
        
        try:
            output_lines = [f"{url}:{login}:{pwd}" for url, login, pwd in self.result.matches]
            success, message = self.file_handler.write_safe(self.config.output, output_lines)
            return success, message
        except Exception as e:
            self.logger.log_critical(f"Write error: {str(e)}")
            return False, f"Write error: {str(e)}"

    def display_results(self) -> None:
        if self.config.quiet:
            return
        
        print("\n" + Colors.colorize("=" * 70, Colors.CYAN))
        print(Colors.colorize(">> RESULTS", Colors.BLUE, bold=True))
        print(Colors.colorize("=" * 70, Colors.CYAN))
        
        if not self.result.matches:
            self.menu.display_warning("No matches found.")
            return
        
        self.menu.display_success(f"Found {len(self.result.matches):,} matches")
        
        if self.config.show_stats:
            print(Colors.colorize("\n[+] Statistics:", Colors.YELLOW, bold=True))
            print(f"  = {Colors.colorize('Total lines processed:', Colors.GRAY)} {self.result.total_lines:,}")
            print(f"  = {Colors.colorize('Error lines:', Colors.GRAY)} {self.result.error_lines:,}")
            if self.result.total_lines > 0:
                error_rate = (self.result.error_lines / self.result.total_lines) * 100
                print(f"  = {Colors.colorize('Error rate:', Colors.GRAY)} {error_rate:.2f}%")
            print(f"  = {Colors.colorize('Match rate:', Colors.GRAY)} {self.result.match_rate:.2f}%")
            print(f"  = {Colors.colorize('Parse time:', Colors.GRAY)} {self.result.parse_time:.3f}s")
            if self.result.memory_usage > 0:
                print(f"  = {Colors.colorize('Memory usage:', Colors.GRAY)} {self.result.memory_usage:.2f} MB")
        
        if self.result.error_lines > 0 and self.config.verbose:
            print(Colors.colorize("\n[!] Error details:", Colors.YELLOW, bold=True))
            for det in self.result.error_details[:5]:
                print(f"  = {Colors.colorize(det, Colors.RED)}")
            if len(self.result.error_details) > 5:
                print(f"  = {Colors.colorize(f'... and {len(self.result.error_details) - 5} more errors', Colors.GRAY)}")
        
        if self.result.matches:
            print(Colors.colorize("\n[+] Matches (first 50):", Colors.GREEN, bold=True))
            display_limit = 50 if self.config.limit == 0 else min(self.config.limit, 50)
            for i, match in enumerate(self.result.matches[:display_limit], 1):
                self.menu.display_result(match, i)
            if len(self.result.matches) > display_limit:
                print(Colors.colorize(f"... and {len(self.result.matches) - display_limit} more matches", Colors.GRAY))
        
        if not self.config.no_write and self.result.matches:
            print(Colors.colorize(f"\n[+] Output saved to: {self.config.output}", Colors.CYAN))
        
        print(Colors.colorize("=" * 70, Colors.CYAN))

    def run_interactive(self) -> None:
        self.menu.clear_screen()
        self.menu.display_header()
        
        while True:
            print(Colors.colorize("MAIN MENU", Colors.BLUE, bold=True))
            print(Colors.colorize("-" * 40, Colors.GRAY))
            print(f"  {Colors.colorize('1', Colors.YELLOW)}. {Colors.colorize('Parse ULP File', Colors.WHITE)}")
            print(f"  {Colors.colorize('2', Colors.YELLOW)}. {Colors.colorize('View Current Configuration', Colors.WHITE)}")
            print(f"  {Colors.colorize('3', Colors.YELLOW)}. {Colors.colorize('Change Configuration', Colors.WHITE)}")
            print(f"  {Colors.colorize('4', Colors.YELLOW)}. {Colors.colorize('View Statistics', Colors.WHITE)}")
            print(f"  {Colors.colorize('5', Colors.YELLOW)}. {Colors.colorize('Exit', Colors.WHITE)}")
            print(Colors.colorize("-" * 40, Colors.GRAY))
            
            choice = self.menu.get_input("Select option", "5", input_type=int)
            
            if choice == 1:
                self._execute_parse()
            elif choice == 2:
                self._display_config()
            elif choice == 3:
                self._change_config()
            elif choice == 4:
                self._display_stats()
            elif choice == 5:
                self.menu.display_info("Exiting...", Colors.CYAN)
                break
            else:
                self.menu.display_error("Invalid option")
            
            if not self.config.quiet:
                input(Colors.colorize("\nPress Enter to continue...", Colors.GRAY))

    def _execute_parse(self) -> None:
        self.menu.clear_screen()
        self.menu.display_header()
        
        self.menu.display_info("Starting parsing operation...", Colors.CYAN)
        try:
            self.parse_file()
            if not self.config.quiet:
                self.display_results()
            if self.result.matches and not self.config.no_write:
                success, message = self.write_results()
                if success:
                    self.menu.display_success(message)
                else:
                    self.menu.display_error(message)
        except Exception as e:
            self.menu.display_error(f"Parsing failed: {str(e)}")

    def _display_config(self) -> None:
        self.menu.clear_screen()
        self.menu.display_header()
        print(Colors.colorize("CURRENT CONFIGURATION", Colors.BLUE, bold=True))
        print(Colors.colorize("=" * 50, Colors.CYAN))
        print(f"  = {Colors.colorize('File:', Colors.GRAY)} {self.config.file_path}")
        print(f"  = {Colors.colorize('Mode:', Colors.GRAY)} {'URL' if self.config.mode == 1 else 'Domain'}")
        print(f"  = {Colors.colorize('Pattern:', Colors.GRAY)} {self.config.pattern}")
        print(f"  = {Colors.colorize('Output:', Colors.GRAY)} {self.config.output}")
        print(f"  = {Colors.colorize('Language:', Colors.GRAY)} {self.config.lang}")
        print(f"  = {Colors.colorize('Quiet:', Colors.GRAY)} {self.config.quiet}")
        print(f"  = {Colors.colorize('Verbose:', Colors.GRAY)} {self.config.verbose}")
        print(f"  = {Colors.colorize('Limit:', Colors.GRAY)} {'Unlimited' if self.config.limit == 0 else self.config.limit}")
        print(f"  = {Colors.colorize('Encoding:', Colors.GRAY)} {self.config.encoding}")
        print(Colors.colorize("=" * 50, Colors.CYAN))

    def _change_config(self) -> None:
        self.menu.clear_screen()
        self.menu.display_header()
        print(Colors.colorize("CONFIGURATION SETUP", Colors.BLUE, bold=True))
        print(Colors.colorize("=" * 50, Colors.CYAN))
        
        self.config.file_path = self.menu.get_input("File path", self.config.file_path)
        
        mode_options = [
            ("1", "URL text (e.g., fatflix.fom, tmail.com)"),
            ("2", "Domain extension (e.g., .gov, .com)")
        ]
        mode_choice = self.menu.display_menu(mode_options, "Select parsing mode")
        self.config.mode = mode_choice
        
        self.config.pattern = self.menu.get_input("Search pattern", self.config.pattern)
        self.config.output = self.menu.get_input("Output file", self.config.output)
        
        lang_options = [
            ("1", "English"),
            ("2", "Türkçe")
        ]
        lang_choice = self.menu.display_menu(lang_options, "Select language")
        self.config.lang = 'en' if lang_choice == 1 else 'tr'
        
        self.config.quiet = self.menu.get_input("Quiet mode (y/n)", "n", input_type=bool)
        self.config.verbose = self.menu.get_input("Verbose mode (y/n)", "n", input_type=bool)
        self.config.limit = self.menu.get_input("Result limit (0=unlimited)", "0", input_type=int)
        self.config.no_log = self.menu.get_input("Disable logging (y/n)", "n", input_type=bool)
        self.config.no_write = self.menu.get_input("Disable file writing (y/n)", "n", input_type=bool)
        
        self.menu.display_success("Configuration updated successfully")

    def _display_stats(self) -> None:
        self.menu.clear_screen()
        self.menu.display_header()
        print(Colors.colorize("SYSTEM STATISTICS", Colors.BLUE, bold=True))
        print(Colors.colorize("=" * 50, Colors.CYAN))
        
        sys_mem = self.memory_monitor.get_system_memory()
        print(f"  = {Colors.colorize('System Memory:', Colors.GRAY)} {sys_mem['used']:.2f}GB / {sys_mem['total']:.2f}GB ({sys_mem['percent']:.1f}%)")
        print(f"  = {Colors.colorize('Process Memory:', Colors.GRAY)} {self.memory_monitor.get_usage():.2f} MB")
        
        if self.result.total_lines > 0:
            print(f"  = {Colors.colorize('Last parse results:', Colors.GRAY)}")
            print(f"    - {Colors.colorize('Lines:', Colors.WHITE)} {self.result.total_lines:,}")
            print(f"    - {Colors.colorize('Matches:', Colors.WHITE)} {len(self.result.matches):,}")
            print(f"    - {Colors.colorize('Errors:', Colors.WHITE)} {self.result.error_lines:,}")
            if self.result.parse_time > 0:
                print(f"    - {Colors.colorize('Parse time:', Colors.WHITE)} {self.result.parse_time:.3f}s")
                print(f"    - {Colors.colorize('Speed:', Colors.WHITE)} {self.result.total_lines / self.result.parse_time:.0f} lines/s")
        
        print(Colors.colorize("=" * 50, Colors.CYAN))

class ArgumentParser:
    @staticmethod
    def parse_args() -> Config:
        parser = argparse.ArgumentParser(
            description="U:L:P Parser - Educational ULP File Processor",
            epilog="Example: python ulp.py -f breach.ulp -m 1 -p gmail -o gmail_list.txt",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        parser.add_argument('-f', '--file', help='Path to ULP file')
        parser.add_argument('-m', '--mode', type=int, choices=[1, 2], help='Mode: 1=URL text, 2=Domain extension')
        parser.add_argument('-p', '--pattern', help='Pattern to search (case-insensitive)')
        parser.add_argument('-o', '--output', default='result.txt', help='Output filename (default: result.txt)')
        parser.add_argument('--lang', choices=['en', 'tr'], default='en', help='Language: en/tr (default: en)')
        parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode (only results)')
        parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
        parser.add_argument('--no-log', action='store_true', help='Disable log file creation')
        parser.add_argument('--limit', type=int, default=0, help='Limit matches to display/write (0=unlimited)')
        parser.add_argument('--encoding', default='utf-8', help='File encoding (default: utf-8)')
        parser.add_argument('--buffer-size', type=int, default=8192, help='Buffer size for reading (default: 8192)')
        parser.add_argument('--max-errors', type=int, default=10, help='Max errors to display (default: 10)')
        parser.add_argument('--no-write', action='store_true', help='Do not write output file')
        parser.add_argument('--no-stats', action='store_true', help='Do not display statistics')
        parser.add_argument('--interactive', action='store_true', help='Force interactive mode')
        parser.add_argument('--no-interactive', action='store_true', help='Force non-interactive mode')
        
        args = parser.parse_args()
        
        has_required = args.file and args.mode is not None and args.pattern
        
        config = Config(
            file_path=args.file or "",
            mode=args.mode or 1,
            pattern=args.pattern or "",
            output=args.output,
            lang=args.lang,
            quiet=args.quiet,
            verbose=args.verbose,
            no_log=args.no_log,
            limit=args.limit,
            encoding=args.encoding,
            buffer_size=args.buffer_size,
            max_errors_display=args.max_errors,
            interactive=args.interactive if not args.no_interactive else False,
            no_write=args.no_write,
            show_stats=not args.no_stats
        )
        
        if not has_required and not args.no_interactive:
            config.interactive = True
        
        if config.interactive:
            config = InteractiveSetup.run()
        
        config.validate()
        return config

class InteractiveSetup:
    @staticmethod
    def run() -> Config:
        menu = InteractiveMenu()
        menu.clear_screen()
        menu.display_header()
        
        print(Colors.colorize("INTERACTIVE SETUP", Colors.BLUE, bold=True))
        print(Colors.colorize("=" * 50, Colors.CYAN))
        
        config = Config()
        config.interactive = True
        
        config.file_path = menu.get_input("File path")
        
        mode_options = [
            ("1", "URL text (e.g., fatflix.fom, tmail.com)"),
            ("2", "Domain extension (e.g., .gov, .com)")
        ]
        mode_choice = menu.display_menu(mode_options, "Select parsing mode")
        config.mode = mode_choice
        
        config.pattern = menu.get_input("Search pattern")
        if config.mode == 2 and not config.pattern.startswith('.'):
            config.pattern = '.' + config.pattern
        
        config.output = menu.get_input("Output file", "result.txt")
        
        lang_options = [
            ("1", "English"),
            ("2", "Türkçe")
        ]
        lang_choice = menu.display_menu(lang_options, "Select language")
        config.lang = 'en' if lang_choice == 1 else 'tr'
        
        config.quiet = menu.get_input("Quiet mode (y/n)", "n", input_type=bool)
        config.verbose = menu.get_input("Verbose mode (y/n)", "n", input_type=bool)
        config.limit = menu.get_input("Result limit (0=unlimited)", "0", input_type=int)
        config.no_log = menu.get_input("Disable logging (y/n)", "n", input_type=bool)
        config.no_write = menu.get_input("Disable file writing (y/n)", "n", input_type=bool)
        config.show_stats = not menu.get_input("Disable statistics (y/n)", "n", input_type=bool)
        
        menu.display_success("Configuration completed")
        return config

def main() -> None:
    try:
        signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
        
        Colors.disable()
        config = ArgumentParser.parse_args()
        
        if config.interactive:
            parser = ULPParser(config)
            parser.run_interactive()
        else:
            parser = ULPParser(config)
            
            if not config.quiet:
                parser.menu.clear_screen()
                parser.menu.display_header()
                parser.menu.display_info(f"File: {config.file_path}", Colors.CYAN)
                parser.menu.display_info(f"Mode: {'URL' if config.mode == 1 else 'Domain'}", Colors.CYAN)
                parser.menu.display_info(f"Pattern: {config.pattern}", Colors.CYAN)
                parser.menu.display_info(f"Output: {config.output}", Colors.CYAN)
                print()
            
            result = parser.parse_file()
            
            if not config.quiet:
                parser.display_results()
            
            if not config.no_write and result.matches:
                success, message = parser.write_results()
                if not config.quiet:
                    if success:
                        parser.menu.display_success(message)
                    else:
                        parser.menu.display_error(message)
            
            sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n" + Colors.colorize("Interrupted by user", Colors.RED))
        sys.exit(1)
    except Exception as e:
        print(Colors.colorize(f"Fatal error: {str(e)}", Colors.RED), file=sys.stderr)
        logging.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()