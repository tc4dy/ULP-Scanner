#IMPORTANT: EDUCATIONAL, RESEARCH TOOL ONLY, USE ETHICALLY

import os
import sys
import re
import time
import logging
import argparse
import platform
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

__version__ = "vAlien-hardened"


class Colors:
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

    @staticmethod
    def enable_ansi() -> None:
        if platform.system() == 'Windows':
            os.system('')

    @staticmethod
    def colorize(text: str, color: str = WHITE, bold: bool = False,
                 underline: bool = False) -> str:
        prefix = ""
        if bold:
            prefix += Colors.BOLD
        if underline:
            prefix += Colors.UNDERLINE
        return f"{prefix}{color}{text}{Colors.END}"

    @staticmethod
    def progress_bar(percent: float, width: int = 50,
                     color: str = GREEN) -> str:
        percent = max(0.0, min(100.0, percent))
        filled = int(width * percent / 100)
        empty = width - filled
        bar = (color + "[" + "=" * filled + Colors.GRAY + "." * empty
               + Colors.END + "]")
        return f"{bar} {percent:.1f}%"


class I18n:
    _lang = 'en'
    _data: Dict[str, Dict[str, str]] = {
        'en': {
            'app_title': 'Advanced U:L:P Parser',
            'app_subtitle': 'Ethical & Educational Using Only',
            'main_menu': 'MAIN MENU',
            'menu_parse': 'Parse ULP File',
            'menu_view_config': 'View Current Configuration',
            'menu_change_config': 'Change Configuration',
            'menu_view_stats': 'View Statistics',
            'menu_exit': 'Exit',
            'select_option': 'Select option',
            'results': 'RESULTS',
            'found_matches': 'Found {n:,} matches',
            'no_matches': 'No matches found.',
            'statistics': 'Statistics',
            'total_lines': 'Total lines processed:',
            'error_lines': 'Error lines:',
            'error_rate': 'Error rate:',
            'match_rate': 'Match rate:',
            'parse_time': 'Parse time:',
            'memory_usage': 'Memory usage:',
            'speed': 'Processing speed:',
            'matches_first': 'Matches (first {n}):',
            'more_matches': '... and {n} more matches',
            'output_saved': 'Output saved to:',
            'file_size': 'File size:',
            'estimated_lines': 'Estimated lines:',
            'processing': 'Processing',
            'reached_limit': 'Reached limit of {n} matches',
            'interrupted': 'Processing interrupted by user',
            'config_saved': 'Configuration updated successfully',
            'exiting': 'Exiting...',
            'press_enter': 'Press Enter to continue...',
            'error_details': 'Error details:',
            'and_more_errors': '... and {n} more errors',
        },
        'tr': {
            'app_title': 'Gelismis U:L:P Ayristirici',
            'app_subtitle': 'Yalnizca Etik ve Egitim Amacli',
            'main_menu': 'ANA MENU',
            'menu_parse': 'ULP Dosyasini Ayristir',
            'menu_view_config': 'Mevcut Yapilandirmayi Goruntule',
            'menu_change_config': 'Yapilandirmayi Degistir',
            'menu_view_stats': 'Istatistikleri Goruntule',
            'menu_exit': 'Cikis',
            'select_option': 'Secenek secin',
            'results': 'SONUCLAR',
            'found_matches': '{n:,} eslesme bulundu',
            'no_matches': 'Eslesme bulunamadi.',
            'statistics': 'Istatistikler',
            'total_lines': 'Islenen toplam satir:',
            'error_lines': 'Hatali satirlar:',
            'error_rate': 'Hata orani:',
            'match_rate': 'Eslesme orani:',
            'parse_time': 'Ayristirma suresi:',
            'memory_usage': 'Bellek kullanimi:',
            'speed': 'Isleme hizi:',
            'matches_first': 'Eslesmeler (ilk {n}):',
            'more_matches': '... ve {n} eslesme daha',
            'output_saved': 'Cikti kaydedildi:',
            'file_size': 'Dosya boyutu:',
            'estimated_lines': 'Tahmini satir sayisi:',
            'processing': 'Isleniyor',
            'reached_limit': '{n} eslesme sinirina ulasildi',
            'interrupted': 'Isleme kullanici tarafindan durduruldu',
            'config_saved': 'Yapilandirma basariyla guncellendi',
            'exiting': 'Cikiliyor...',
            'press_enter': 'Devam etmek icin Enter\'a basin...',
            'error_details': 'Hata detaylari:',
            'and_more_errors': '... ve {n} hata daha',
        },
    }

    @classmethod
    def set_lang(cls, lang: str) -> None:
        cls._lang = lang if lang in cls._data else 'en'

    @classmethod
    def t(cls, key: str, **kwargs: Any) -> str:
        lang_data = cls._data.get(cls._lang, cls._data['en'])
        s = lang_data.get(key)
        if s is None:
            s = cls._data['en'].get(key, key)
        if kwargs:
            try:
                return s.format(**kwargs)
            except (KeyError, IndexError):
                return s
        return s


@dataclass
class ParseResult:
    matches: List[Tuple[str, str, str]] = field(default_factory=list)
    total_lines: int = 0
    error_lines: int = 0
    error_details: List[str] = field(default_factory=list)
    parse_time: float = 0.0
    memory_usage: float = 0.0
    memory_delta: float = 0.0
    start_time: float = 0.0
    end_time: float = 0.0
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
        if not SecurityValidator.validate_mode(self.mode):
            raise ValueError("Mode must be 1 or 2")
        if not self.pattern:
            raise ValueError("Pattern cannot be empty")
        if self.mode == 2 and not self.pattern.startswith('.'):
            raise ValueError("Mode 2 pattern must start with '.'")
        if self.lang not in ('en', 'tr'):
            raise ValueError("Language must be 'en' or 'tr'")
        if self.limit < 0:
            raise ValueError("Limit cannot be negative")
        if self.buffer_size < 1:
            raise ValueError("Buffer size must be positive")
        if self.max_errors_display < 0:
            raise ValueError("Max errors cannot be negative")


class SecurityValidator:
    MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024
    MAX_PATTERN_LEN = 1024

    @staticmethod
    def validate_path(path: str) -> Tuple[bool, str]:
        try:
            p = Path(path).resolve()
            if not p.exists():
                return False, "File does not exist"
            if not p.is_file():
                return False, "Path is not a file"
            size = p.stat().st_size
            if size == 0:
                return False, "File is empty"
            if size > SecurityValidator.MAX_FILE_SIZE:
                return False, "File too large (>10GB)"
            try:
                with open(p, 'rb') as f:
                    f.read(1)
            except Exception:
                return False, "File is not readable"
            return True, "Valid"
        except Exception as e:
            return False, f"Validation error: {e}"

    @staticmethod
    def validate_pattern(pattern: str, mode: int) -> Tuple[bool, str]:
        if not pattern:
            return False, "Pattern cannot be empty"
        if len(pattern) > SecurityValidator.MAX_PATTERN_LEN:
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
            import psutil  # type: ignore
            return psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0

    @staticmethod
    def get_system_memory() -> Dict[str, float]:
        try:
            import psutil  # type: ignore
            m = psutil.virtual_memory()
            return {
                'total': m.total / 1024 / 1024 / 1024,
                'available': m.available / 1024 / 1024 / 1024,
                'used': m.used / 1024 / 1024 / 1024,
                'percent': m.percent,
            }
        except Exception:
            return {'total': 0, 'available': 0, 'used': 0, 'percent': 0}


class FileHandler:
    @staticmethod
    def safe_open(file_path: str, mode: str = 'r', encoding: str = 'utf-8',
                  buffer_size: int = 8192):
        try:
            return open(file_path, mode, encoding=encoding,
                        errors='replace', buffering=buffer_size)
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except PermissionError:
            raise PermissionError(f"Permission denied: {file_path}")
        except LookupError as e:
            raise ValueError(f"Unknown encoding '{encoding}': {e}")
        except Exception as e:
            raise Exception(f"Cannot open file: {e}")

    @staticmethod
    def write_safe(file_path: str, data: List[str]) -> Tuple[bool, str]:
        temp_path = f"{file_path}.tmp_{int(time.time() * 1000)}"
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                for line in data:
                    f.write(line + '\n')
                f.flush()
                try:
                    os.fsync(f.fileno())
                except OSError:
                    pass
            if os.path.exists(file_path):
                backup_path = (f"{file_path}.bak_"
                               f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}")
                os.replace(file_path, backup_path)
            os.replace(temp_path, file_path)
            return True, f"Successfully written to {file_path}"
        except Exception as e:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass
            return False, f"Write error: {e}"

    @staticmethod
    def estimate_line_count(file_path: str) -> int:
        try:
            count = 0
            last_byte = b''
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(1024 * 1024)
                    if not chunk:
                        break
                    count += chunk.count(b'\n')
                    last_byte = chunk[-1:]
            if last_byte and last_byte != b'\n':
                count += 1
            return count
        except Exception:
            return -1

    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        try:
            p = Path(file_path)
            st = p.stat()
            return {
                'size': st.st_size,
                'size_mb': st.st_size / 1024 / 1024,
                'size_gb': st.st_size / 1024 / 1024 / 1024,
                'modified': datetime.fromtimestamp(st.st_mtime),
                'lines': FileHandler.estimate_line_count(file_path),
            }
        except Exception:
            return {'size': 0, 'size_mb': 0, 'size_gb': 0,
                    'modified': None, 'lines': -1}


class LoggerManager:
    _LOGGER_NAME = 'ULPParser'

    def __init__(self, config: Config):
        self.config = config
        self.log_file = ""
        self.logger = logging.getLogger(self._LOGGER_NAME)
        self.logger.setLevel(logging.ERROR)
        self.logger.propagate = False
        for h in list(self.logger.handlers):
            self.logger.removeHandler(h)
            try:
                h.close()
            except Exception:
                pass
        if config.no_log:
            self.logger.addHandler(logging.NullHandler())
        else:
            try:
                self.log_file = (f"ulp_parser_error_"
                                 f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.log")
                handler = logging.FileHandler(self.log_file, encoding='utf-8')
                handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(levelname)s - %(message)s'))
                self.logger.addHandler(handler)
            except Exception:
                self.logger.addHandler(logging.NullHandler())
                self.log_file = ""

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
        print("\n" + Colors.colorize("=" * 70, Colors.CYAN, bold=True))
        print(Colors.colorize("|", Colors.CYAN, bold=True) + " " * 68
              + Colors.colorize("|", Colors.CYAN, bold=True))
        print(Colors.colorize("|", Colors.CYAN, bold=True) + " " * 10
              + Colors.colorize(I18n.t('app_title'), Colors.BLUE, bold=True)
              + " " * 27 + Colors.colorize("|", Colors.CYAN, bold=True))
        print(Colors.colorize("|", Colors.CYAN, bold=True) + " " * 10
              + Colors.colorize(I18n.t('app_subtitle'), Colors.GREEN)
              + " " * 27 + Colors.colorize("|", Colors.CYAN, bold=True))
        print(Colors.colorize("|", Colors.CYAN, bold=True) + " " * 10
              + Colors.colorize("@tc4dy", Colors.YELLOW) + " " * 37
              + Colors.colorize("|", Colors.CYAN, bold=True))
        print(Colors.colorize("|", Colors.CYAN, bold=True) + " " * 68
              + Colors.colorize("|", Colors.CYAN, bold=True))
        print(Colors.colorize("+" + "=" * 68 + "+", Colors.CYAN, bold=True) + "\n")

    @staticmethod
    def get_input(prompt: str, default: str = "", required: bool = True,
                  input_type: type = str) -> Any:
        while True:
            if default:
                full = (f"{Colors.colorize(prompt, Colors.WHITE)} "
                        f"{Colors.colorize(f'[{default}]', Colors.GRAY)}: ")
            else:
                full = f"{Colors.colorize(prompt, Colors.WHITE)}: "
            value = input(full).strip()
            if not value and default:
                value = default
            if not value and required:
                print(Colors.colorize("Error: Input is required", Colors.RED))
                continue
            try:
                if input_type == int:
                    return int(value)
                if input_type == bool:
                    return value.lower() in ('y', 'yes', 'true', 't', '1')
                return value
            except ValueError:
                print(Colors.colorize(
                    f"Error: Invalid {input_type.__name__} format", Colors.RED))

    @staticmethod
    def display_menu(options: List[Tuple[str, str]],
                     title: str = "Select Option") -> int:
        print("\n" + Colors.colorize("-" * 50, Colors.GRAY))
        print(Colors.colorize(f">> {title}", Colors.CYAN, bold=True))
        print(Colors.colorize("-" * 50, Colors.GRAY))
        for idx, (_key, desc) in enumerate(options, 1):
            print(f"  {Colors.colorize(str(idx), Colors.YELLOW, bold=True)}. "
                  f"{Colors.colorize(desc, Colors.WHITE)}")
        print(Colors.colorize("-" * 50, Colors.GRAY))
        while True:
            choice = input(Colors.colorize(
                f"Select [1-{len(options)}]: ", Colors.CYAN)).strip()
            try:
                n = int(choice)
                if 1 <= n <= len(options):
                    return n
            except ValueError:
                pass
            print(Colors.colorize("Invalid choice. Please try again.", Colors.RED))

    @staticmethod
    def display_progress(current: int, total: int,
                         prefix: str = "Processing") -> None:
        if total <= 0:
            return
        percent = min(100.0, (current / total) * 100)
        bar = Colors.progress_bar(percent)
        print(f"\r{Colors.colorize(prefix, Colors.CYAN)} {bar} "
              f"{Colors.colorize(f'{current}/{total}', Colors.GRAY)}",
              end='', flush=True)

    @staticmethod
    def display_success(msg: str) -> None:
        print(Colors.colorize("[+] " + msg, Colors.GREEN))

    @staticmethod
    def display_error(msg: str) -> None:
        print(Colors.colorize("[-] " + msg, Colors.RED), file=sys.stderr)

    @staticmethod
    def display_info(msg: str, color: str = Colors.WHITE) -> None:
        print(Colors.colorize("[?] " + msg, color))

    @staticmethod
    def display_warning(msg: str) -> None:
        print(Colors.colorize("[!] " + msg, Colors.YELLOW))

    @staticmethod
    def display_result(match: Tuple[str, str, str], index: int) -> None:
        url, login, pwd = match
        print(f"{Colors.colorize(str(index), Colors.YELLOW)}. "
              f"{Colors.colorize(url, Colors.CYAN)}:"
              f"{Colors.colorize(login, Colors.GREEN)}:"
              f"{Colors.colorize(pwd, Colors.GRAY)}")


class ULPParser:
    def __init__(self, config: Config):
        self.config = config
        I18n.set_lang(config.lang)
        self.logger = LoggerManager(config)
        self.memory_monitor = MemoryMonitor()
        self.file_handler = FileHandler()
        self.security = SecurityValidator()
        self.result = ParseResult()
        self.menu = InteractiveMenu()
        self.interrupted = False

    def _create_regex(self, pattern: str) -> re.Pattern:
        if self.config.mode == 1:
            try:
                return re.compile(pattern, re.IGNORECASE)
            except re.error as e:
                self.logger.log_error(
                    f"Regex compile error: {e}; falling back to literal match")
                if not self.config.quiet:
                    self.menu.display_warning(
                        f"Regex error: {e}. Using literal matching.")
                return re.compile(re.escape(pattern), re.IGNORECASE)
        return re.compile(re.escape(pattern) + r'$', re.IGNORECASE)

    def parse_file(self) -> ParseResult:
        self.result = ParseResult()
        self.interrupted = False
        self.result.start_time = time.time()
        mem_start = self.memory_monitor.get_usage()
        processed = 0

        try:
            ok, msg = self.security.validate_path(self.config.file_path)
            if not ok:
                raise ValueError(msg)
            ok, msg = self.security.validate_pattern(
                self.config.pattern, self.config.mode)
            if not ok:
                raise ValueError(msg)

            if not self.config.quiet:
                self._display_file_info()

            regex = self._create_regex(self.config.pattern)
            estimate = self.file_handler.estimate_line_count(self.config.file_path)
            if not self.config.quiet and estimate > 0:
                self.menu.display_info(
                    f"{I18n.t('estimated_lines')} {estimate:,}", Colors.CYAN)

            with self.file_handler.safe_open(
                    self.config.file_path, 'r',
                    self.config.encoding, self.config.buffer_size) as f:
                for line_num, line in enumerate(f, 1):
                    self._process_line(line.strip(), line_num, regex)
                    processed += 1
                    if (self.config.limit > 0
                            and len(self.result.matches) >= self.config.limit):
                        if not self.config.quiet:
                            self.menu.display_info(
                                I18n.t('reached_limit', n=self.config.limit),
                                Colors.YELLOW)
                        break
                    if (not self.config.quiet and estimate > 0
                            and processed % 1000 == 0):
                        self.menu.display_progress(
                            processed, estimate, I18n.t('processing'))

            if not self.config.quiet and estimate > 0:
                if processed >= estimate:
                    self.menu.display_progress(
                        processed, estimate, I18n.t('processing'))
                print()

        except KeyboardInterrupt:
            self.interrupted = True
            if not self.config.quiet:
                self.menu.display_warning(I18n.t('interrupted'))
        except Exception as e:
            self.logger.log_critical(f"Parser error: {e}")
            raise
        finally:
            self.result.total_lines = processed
            if processed > 0:
                self.result.match_rate = (
                    len(self.result.matches) / processed) * 100
            mem_end = self.memory_monitor.get_usage()
            self.result.memory_usage = mem_end
            self.result.memory_delta = mem_end - mem_start
            self.result.end_time = time.time()
            self.result.parse_time = self.result.end_time - self.result.start_time

        return self.result

    def _process_line(self, line: str, line_num: int,
                      regex: re.Pattern) -> None:
        if not line:
            return
        try:
            parts = line.rsplit(':', 2)
            if len(parts) < 3:
                self._handle_error(
                    line_num, f"Invalid format (less than 3 fields) -> {line[:100]}")
                return
            url, login, pwd = parts[0], parts[1], parts[2]
            if not url or not login or not pwd:
                self._handle_error(
                    line_num, f"Empty field -> {line[:100]}")
                return
            if regex.search(url):
                self.result.matches.append((url, login, pwd))
        except Exception as e:
            self._handle_error(
                line_num, f"Processing error ({e}) -> {line[:100]}")

    def _handle_error(self, line_num: int, error_msg: str) -> None:
        self.result.error_lines += 1
        if len(self.result.error_details) < self.config.max_errors_display:
            self.result.error_details.append(f"Line {line_num}: {error_msg}")
        self.logger.log_error(f"Line {line_num}: {error_msg}")

    def _display_file_info(self) -> None:
        info = self.file_handler.get_file_info(self.config.file_path)
        size = info['size']
        if size > 0:
            if size < 1024 * 1024:
                size_str = f"{size / 1024:.2f} KB"
            elif info['size_mb'] < 1024:
                size_str = f"{info['size_mb']:.2f} MB"
            else:
                size_str = f"{info['size_gb']:.2f} GB"
            self.menu.display_info(f"{I18n.t('file_size')} {size_str}", Colors.GRAY)
        if info['lines'] > 0:
            self.menu.display_info(
                f"{I18n.t('estimated_lines')} {info['lines']:,}", Colors.GRAY)

    def write_results(self) -> Tuple[bool, str]:
        if not self.result.matches:
            return False, "No matches found"
        if self.config.no_write:
            return True, "Write disabled by --no-write option"
        try:
            lines = [f"{u}:{l}:{p}" for u, l, p in self.result.matches]
            return self.file_handler.write_safe(self.config.output, lines)
        except Exception as e:
            self.logger.log_critical(f"Write error: {e}")
            return False, f"Write error: {e}"

    def display_results(self) -> None:
        if self.config.quiet:
            return
        print("\n" + Colors.colorize("=" * 70, Colors.CYAN))
        print(Colors.colorize(f">> {I18n.t('results')}", Colors.BLUE, bold=True))
        print(Colors.colorize("=" * 70, Colors.CYAN))

        if not self.result.matches:
            self.menu.display_warning(I18n.t('no_matches'))
            return

        self.menu.display_success(
            I18n.t('found_matches', n=len(self.result.matches)))

        if self.config.show_stats:
            print(Colors.colorize(f"\n[+] {I18n.t('statistics')}:",
                                  Colors.YELLOW, bold=True))
            r = self.result
            print(f"  = {Colors.colorize(I18n.t('total_lines'), Colors.GRAY)} "
                  f"{r.total_lines:,}")
            print(f"  = {Colors.colorize(I18n.t('error_lines'), Colors.GRAY)} "
                  f"{r.error_lines:,}")
            if r.total_lines > 0:
                err_rate = (r.error_lines / r.total_lines) * 100
                print(f"  = {Colors.colorize(I18n.t('error_rate'), Colors.GRAY)} "
                      f"{err_rate:.2f}%")
            print(f"  = {Colors.colorize(I18n.t('match_rate'), Colors.GRAY)} "
                  f"{r.match_rate:.2f}%")
            print(f"  = {Colors.colorize(I18n.t('parse_time'), Colors.GRAY)} "
                  f"{r.parse_time:.3f}s")
            if r.memory_usage > 0:
                print(f"  = {Colors.colorize(I18n.t('memory_usage'), Colors.GRAY)} "
                      f"{r.memory_usage:.2f} MB")
                if self.config.verbose:
                    print(f"  = {Colors.colorize('Memory delta:', Colors.GRAY)} "
                          f"{r.memory_delta:+.2f} MB")
            if r.parse_time > 0 and r.total_lines > 0:
                print(f"  = {Colors.colorize(I18n.t('speed'), Colors.GRAY)} "
                      f"{r.total_lines / r.parse_time:,.0f} lines/s")

        if self.result.error_lines > 0 and self.config.verbose:
            print(Colors.colorize(f"\n[!] {I18n.t('error_details')}",
                                  Colors.YELLOW, bold=True))
            shown = self.result.error_details[:self.config.max_errors_display]
            for det in shown:
                print(f"  = {Colors.colorize(det, Colors.RED)}")
            remaining = self.result.error_lines - len(shown)
            if remaining > 0:
                print(f"  = {Colors.colorize(I18n.t('and_more_errors', n=remaining), Colors.GRAY)}")

        if self.result.matches:
            print(Colors.colorize(
                f"\n[+] {I18n.t('matches_first', n=min(50, len(self.result.matches)))}",
                Colors.GREEN, bold=True))
            display_limit = 50 if self.config.limit == 0 else min(self.config.limit, 50)
            for i, match in enumerate(self.result.matches[:display_limit], 1):
                self.menu.display_result(match, i)
            if len(self.result.matches) > display_limit:
                print(Colors.colorize(
                    I18n.t('more_matches', n=len(self.result.matches) - display_limit),
                    Colors.GRAY))

        print(Colors.colorize("=" * 70, Colors.CYAN))

    def run_interactive(self) -> None:
        self.menu.clear_screen()
        self.menu.display_header()
        while True:
            print(Colors.colorize(I18n.t('main_menu'), Colors.BLUE, bold=True))
            print(Colors.colorize("-" * 40, Colors.GRAY))
            print(f"  {Colors.colorize('1', Colors.YELLOW)}. "
                  f"{Colors.colorize(I18n.t('menu_parse'), Colors.WHITE)}")
            print(f"  {Colors.colorize('2', Colors.YELLOW)}. "
                  f"{Colors.colorize(I18n.t('menu_view_config'), Colors.WHITE)}")
            print(f"  {Colors.colorize('3', Colors.YELLOW)}. "
                  f"{Colors.colorize(I18n.t('menu_change_config'), Colors.WHITE)}")
            print(f"  {Colors.colorize('4', Colors.YELLOW)}. "
                  f"{Colors.colorize(I18n.t('menu_view_stats'), Colors.WHITE)}")
            print(f"  {Colors.colorize('5', Colors.YELLOW)}. "
                  f"{Colors.colorize(I18n.t('menu_exit'), Colors.WHITE)}")
            print(Colors.colorize("-" * 40, Colors.GRAY))
            choice = self.menu.get_input(
                I18n.t('select_option'), "5", input_type=int)
            if choice == 1:
                self._execute_parse()
            elif choice == 2:
                self._display_config()
            elif choice == 3:
                self._change_config()
            elif choice == 4:
                self._display_stats()
            elif choice == 5:
                self.menu.display_info(I18n.t('exiting'), Colors.CYAN)
                break
            else:
                self.menu.display_error("Invalid option")
            if not self.config.quiet:
                input(Colors.colorize(f"\n{I18n.t('press_enter')}", Colors.GRAY))

    def _execute_parse(self) -> None:
        self.menu.clear_screen()
        self.menu.display_header()
        I18n.set_lang(self.config.lang)
        self.logger = LoggerManager(self.config)
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
            self.menu.display_error(f"Parsing failed: {e}")

    def _display_config(self) -> None:
        self.menu.clear_screen()
        self.menu.display_header()
        print(Colors.colorize("CURRENT CONFIGURATION", Colors.BLUE, bold=True))
        print(Colors.colorize("=" * 50, Colors.CYAN))
        print(f"  = {Colors.colorize('File:', Colors.GRAY)} {self.config.file_path}")
        print(f"  = {Colors.colorize('Mode:', Colors.GRAY)} "
              f"{'URL' if self.config.mode == 1 else 'Domain'}")
        print(f"  = {Colors.colorize('Pattern:', Colors.GRAY)} {self.config.pattern}")
        print(f"  = {Colors.colorize('Output:', Colors.GRAY)} {self.config.output}")
        print(f"  = {Colors.colorize('Language:', Colors.GRAY)} {self.config.lang}")
        print(f"  = {Colors.colorize('Quiet:', Colors.GRAY)} {self.config.quiet}")
        print(f"  = {Colors.colorize('Verbose:', Colors.GRAY)} {self.config.verbose}")
        print(f"  = {Colors.colorize('Limit:', Colors.GRAY)} "
              f"{'Unlimited' if self.config.limit == 0 else self.config.limit}")
        print(f"  = {Colors.colorize('Encoding:', Colors.GRAY)} {self.config.encoding}")
        print(Colors.colorize("=" * 50, Colors.CYAN))

    def _change_config(self) -> None:
        self.menu.clear_screen()
        self.menu.display_header()
        print(Colors.colorize("CONFIGURATION SETUP", Colors.BLUE, bold=True))
        print(Colors.colorize("=" * 50, Colors.CYAN))
        self.config.file_path = self.menu.get_input(
            "File path", self.config.file_path)
        mode_choice = self.menu.display_menu(
            [("1", "URL text (e.g., fatflix.fom, tmail.com)"),
             ("2", "Domain extension (e.g., .gov, .com)")],
            "Select parsing mode")
        self.config.mode = mode_choice
        self.config.pattern = self.menu.get_input(
            "Search pattern", self.config.pattern)
        if self.config.mode == 2 and not self.config.pattern.startswith('.'):
            self.config.pattern = '.' + self.config.pattern
        self.config.output = self.menu.get_input(
            "Output file", self.config.output)
        lang_choice = self.menu.display_menu(
            [("1", "English"), ("2", "Turkce")], "Select language")
        self.config.lang = 'en' if lang_choice == 1 else 'tr'
        I18n.set_lang(self.config.lang)
        self.config.quiet = self.menu.get_input(
            "Quiet mode (y/n)", "n", input_type=bool)
        self.config.verbose = self.menu.get_input(
            "Verbose mode (y/n)", "n", input_type=bool)
        self.config.limit = self.menu.get_input(
            "Result limit (0=unlimited)", "0", input_type=int)
        self.config.no_log = self.menu.get_input(
            "Disable logging (y/n)", "n", input_type=bool)
        self.config.no_write = self.menu.get_input(
            "Disable file writing (y/n)", "n", input_type=bool)
        self.menu.display_success(I18n.t('config_saved'))

    def _display_stats(self) -> None:
        self.menu.clear_screen()
        self.menu.display_header()
        print(Colors.colorize("SYSTEM STATISTICS", Colors.BLUE, bold=True))
        print(Colors.colorize("=" * 50, Colors.CYAN))
        sys_mem = self.memory_monitor.get_system_memory()
        print(f"  = {Colors.colorize('System Memory:', Colors.GRAY)} "
              f"{sys_mem['used']:.2f}GB / {sys_mem['total']:.2f}GB "
              f"({sys_mem['percent']:.1f}%)")
        print(f"  = {Colors.colorize('Process Memory:', Colors.GRAY)} "
              f"{self.memory_monitor.get_usage():.2f} MB")
        if self.result.total_lines > 0:
            print(f"  = {Colors.colorize('Last parse results:', Colors.GRAY)}")
            print(f"    - {Colors.colorize('Lines:', Colors.WHITE)} "
                  f"{self.result.total_lines:,}")
            print(f"    - {Colors.colorize('Matches:', Colors.WHITE)} "
                  f"{len(self.result.matches):,}")
            print(f"    - {Colors.colorize('Errors:', Colors.WHITE)} "
                  f"{self.result.error_lines:,}")
            if self.result.parse_time > 0:
                print(f"    - {Colors.colorize('Parse time:', Colors.WHITE)} "
                      f"{self.result.parse_time:.3f}s")
                print(f"    - {Colors.colorize('Speed:', Colors.WHITE)} "
                      f"{self.result.total_lines / self.result.parse_time:,.0f} lines/s")
        print(Colors.colorize("=" * 50, Colors.CYAN))


class ArgumentParser:
    @staticmethod
    def parse_args() -> Config:
        parser = argparse.ArgumentParser(
            description="U:L:P Parser - Educational ULP File Processor",
            epilog="Example: python scanner.py -f breach.ulp -m 1 -p gmail -o out.txt",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        parser.add_argument('-f', '--file', help='Path to ULP file')
        parser.add_argument('-m', '--mode', type=int, choices=[1, 2],
                            help='Mode: 1=URL text, 2=Domain extension')
        parser.add_argument('-p', '--pattern', help='Search pattern (case-insensitive)')
        parser.add_argument('-o', '--output', default='result.txt',
                            help='Output filename (default: result.txt)')
        parser.add_argument('--lang', choices=['en', 'tr'], default='en',
                            help='Language: en/tr (default: en)')
        parser.add_argument('-q', '--quiet', action='store_true',
                            help='Quiet mode (only results)')
        parser.add_argument('-v', '--verbose', action='store_true',
                            help='Verbose output')
        parser.add_argument('--no-log', action='store_true',
                            help='Disable log file creation')
        parser.add_argument('--limit', type=int, default=0,
                            help='Stop after N matches (0=unlimited)')
        parser.add_argument('--encoding', default='utf-8',
                            help='File encoding (default: utf-8)')
        parser.add_argument('--buffer-size', type=int, default=8192,
                            help='Buffer size for reading (default: 8192)')
        parser.add_argument('--max-errors', type=int, default=10,
                            help='Max error details (default: 10)')
        parser.add_argument('--no-write', action='store_true',
                            help='Do not write output file')
        parser.add_argument('--no-stats', action='store_true',
                            help='Do not display statistics')
        parser.add_argument('--interactive', action='store_true',
                            help='Force interactive mode')
        parser.add_argument('--no-interactive', action='store_true',
                            help='Force non-interactive mode')

        args = parser.parse_args()
        I18n.set_lang(args.lang)

        config = Config(
            file_path=args.file or "",
            mode=args.mode if args.mode is not None else 1,
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
            no_write=args.no_write,
            show_stats=not args.no_stats,
        )

        has_required = bool(args.file and args.mode is not None and args.pattern)
        if args.no_interactive:
            config.interactive = False
        elif args.interactive:
            config.interactive = True
        elif has_required:
            config.interactive = False
        else:
            config.interactive = True

        if config.interactive:
            config = InteractiveSetup.run(config)
        config.validate()
        return config


class InteractiveSetup:
    @staticmethod
    def run(base_config: Optional[Config] = None) -> Config:
        menu = InteractiveMenu()
        menu.clear_screen()
        menu.display_header()
        print(Colors.colorize("INTERACTIVE SETUP", Colors.BLUE, bold=True))
        print(Colors.colorize("=" * 50, Colors.CYAN))
        config = base_config or Config()
        config.interactive = True

        lang_choice = menu.display_menu(
            [("1", "English"), ("2", "Turkce")], "Select language")
        config.lang = 'en' if lang_choice == 1 else 'tr'
        I18n.set_lang(config.lang)

        config.file_path = menu.get_input("File path", config.file_path)
        mode_choice = menu.display_menu(
            [("1", "URL text (e.g., fatflix.fom, tmail.com)"),
             ("2", "Domain extension (e.g., .gov, .com)")],
            "Select parsing mode")
        config.mode = mode_choice
        config.pattern = menu.get_input("Search pattern", config.pattern)
        if config.mode == 2 and not config.pattern.startswith('.'):
            config.pattern = '.' + config.pattern
        config.output = menu.get_input("Output file", config.output)
        config.quiet = menu.get_input("Quiet mode (y/n)", "n", input_type=bool)
        config.verbose = menu.get_input("Verbose mode (y/n)", "n", input_type=bool)
        config.limit = menu.get_input("Result limit (0=unlimited)", "0", input_type=int)
        config.no_log = menu.get_input("Disable logging (y/n)", "n", input_type=bool)
        config.no_write = menu.get_input("Disable file writing (y/n)", "n", input_type=bool)
        config.show_stats = not menu.get_input(
            "Disable statistics (y/n)", "n", input_type=bool)

        menu.display_success(I18n.t('config_saved'))
        return config


def main() -> None:
    try:
        Colors.enable_ansi()
        config = ArgumentParser.parse_args()
        I18n.set_lang(config.lang)
        parser = ULPParser(config)

        if config.interactive:
            parser.run_interactive()
            return

        if not config.quiet:
            parser.menu.clear_screen()
            parser.menu.display_header()
            parser.menu.display_info(f"File: {config.file_path}", Colors.CYAN)
            parser.menu.display_info(
                f"Mode: {'URL' if config.mode == 1 else 'Domain'}", Colors.CYAN)
            parser.menu.display_info(f"Pattern: {config.pattern}", Colors.CYAN)
            parser.menu.display_info(f"Output: {config.output}", Colors.CYAN)
            print()

        result = parser.parse_file()
        if not config.quiet:
            parser.display_results()
        if not config.no_write and result.matches:
            success, message = parser.write_results()
            if success:
                if not config.quiet:
                    parser.menu.display_success(message)
            else:
                parser.menu.display_error(message)
        sys.exit(0)

    except KeyboardInterrupt:
        print("\n" + Colors.colorize("Interrupted by user", Colors.RED))
        sys.exit(130)
    except SystemExit:
        raise
    except Exception as e:
        print(Colors.colorize(f"Fatal error: {e}", Colors.RED), file=sys.stderr)
        logging.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
