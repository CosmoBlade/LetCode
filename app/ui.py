import shutil
import sys

try:
    import termios
    import tty
except ImportError:
    termios = None

try:
    from .config import get_language_label, get_text, save_config, session
    from .constants import C_DARK_PURPLE, C_GRAY, C_LIGHT_PURPLE, C_PURPLE, C_RESET
except ImportError:
    from config import get_language_label, get_text, save_config, session
    from constants import C_DARK_PURPLE, C_GRAY, C_LIGHT_PURPLE, C_PURPLE, C_RESET


def enable_windows_ansi() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        if handle in (0, -1):
            return
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


enable_windows_ansi()


def get_key():
    if not termios or not sys.stdin.isatty():
        return input().strip()

    fd = sys.stdin.fileno()
    try:
        old_settings = termios.tcgetattr(fd)
    except termios.error:
        return input().strip()
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            ch2 = sys.stdin.read(1)
            if ch2 == "[":
                ch3 = sys.stdin.read(1)
                if ch3 == "A": return "up"
                if ch3 == "B": return "down"
                if ch3 == "C": return "right"
                if ch3 == "D": return "left"
            return "esc"
        if ch in ["\r", "\n"]: return "enter"
        if ch in ["\x7f", "\b"]: return "backspace"
        if ch == "\t": return "tab"
        if ch == "\x03": raise KeyboardInterrupt
        return ch
    finally:
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except termios.error:
            pass


def get_command_suggestions(buffer: str) -> list:
    if not buffer.startswith("/"): return []
    commands = ["/help", "/reset", "/provider", "/key", "/model", "/effort", "/language", "/settings", "/exit"]
    prefix = buffer.lower()
    return [cmd for cmd in commands if cmd.lower().startswith(prefix)]


def read_input_line(prompt: str, history: list) -> str:
    rows = shutil.get_terminal_size().lines
    buffer = ""
    cursor = 0
    history_index = len(history)

    while True:
        suggestions = get_command_suggestions(buffer)
        hint = suggestions[0][len(buffer):] if suggestions else ""
        display_text = buffer + f"{C_GRAY}{hint}{C_RESET}"
        sys.stdout.write(f"\033[{rows};1H\033[K{C_PURPLE}{prompt}{C_RESET}{display_text}")
        sys.stdout.flush()
        sys.stdout.write(f"\033[{rows};{len(prompt) + cursor + 1}H")
        sys.stdout.flush()

        key = get_key()
        if key == "up":
            if history and history_index > 0:
                history_index -= 1
                buffer = history[history_index]
                cursor = len(buffer)
        elif key == "down":
            if history_index < len(history):
                history_index += 1
                buffer = history[history_index] if history_index < len(history) else ""
                cursor = len(buffer)
        elif key == "left": cursor = max(0, cursor - 1)
        elif key == "right": cursor = min(len(buffer), cursor + 1)
        elif key == "backspace":
            if cursor > 0:
                buffer = buffer[:cursor - 1] + buffer[cursor:]
                cursor -= 1
        elif key == "tab":
            if suggestions:
                buffer = suggestions[0]
                cursor = len(buffer)
        elif key in ["enter", ""]:
            sys.stdout.write("\n")
            sys.stdout.flush()
            return buffer.strip()
        elif key == "esc": return ""
        elif key == "ctrl+c": raise KeyboardInterrupt
        else:
            if isinstance(key, str) and key not in ["\x00"]:
                buffer = buffer[:cursor] + key + buffer[cursor:]
                cursor += len(key)


def setup_scrolling_region():
    rows = shutil.get_terminal_size().lines
    sys.stdout.write(f"\033[2J\033[1;{rows - 2}r\033[{rows - 2};1H\n")
    sys.stdout.flush()


def reset_scrolling_region():
    sys.stdout.write("\033[r\033[2J\033[1;1H")
    sys.stdout.flush()


def print_to_scroll_area(text: str):
    rows = shutil.get_terminal_size().lines
    sys.stdout.write(f"\033[s\033[{rows - 2};1H\n{text}\033[u")
    sys.stdout.flush()


def interactive_menu(title: str, options: list, current_index: int = 0) -> int:
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()
    max_len = max(len(opt) for opt in options)
    try:
        while True:
            sys.stdout.write("\033[2J\033[1;1H")
            sys.stdout.flush()
            menu_output = f"{C_PURPLE}─── {title} ───{C_RESET}\n"
            for i, opt in enumerate(options):
                padded_opt = opt.ljust(max_len)
                if i == current_index:
                    menu_output += f"  {C_LIGHT_PURPLE}{i + 1}. {padded_opt} <{C_RESET}\n"
                else:
                    menu_output += f"  {C_GRAY}{i + 1}. {opt}{C_RESET}\n"
            menu_output += f"\n{C_GRAY}↑/↓ navigate   Enter select   Esc cancel{C_RESET}"
            sys.stdout.write(menu_output)
            sys.stdout.flush()
            key = get_key()
            if key == "up": current_index = (current_index - 1) % len(options)
            elif key == "down": current_index = (current_index + 1) % len(options)
            elif key in ["esc", "escape"]: return -1
            elif key == "enter": break
        return current_index
    finally:
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()


def draw_box(title: str, text: str, width: int = 0):
    if not width:
        width = min(shutil.get_terminal_size((80, 20)).columns - 4, 90)
    inner_width = width - 2
    lines = []
    for raw_line in text.split("\n"):
        if not raw_line.strip() and not raw_line:
            lines.append("")
            continue
        while len(raw_line) > inner_width:
            lines.append(raw_line[:inner_width])
            raw_line = raw_line[inner_width:]
        lines.append(raw_line)
    
    title_stuff = f"┤ {title} ├" if title else "─"
    top_line = f"{C_PURPLE}┌─{title_stuff}" + "─" * (width - len(title_stuff) - 3) + f"┐{C_RESET}"
    
    box_content = "\n" + top_line + "\n"
    for line in lines:
        padded = line + " " * (inner_width - len(line))
        box_content += f"{C_PURPLE}│{C_RESET} {padded} {C_PURPLE}│{C_RESET}\n"
    box_content += f"{C_PURPLE}└" + "─" * inner_width + f"┘{C_RESET}\n"
    
    print_to_scroll_area(box_content)


def show_setup_box() -> None:
    draw_box("SETUP", f"provider: {session['provider']}\nmodel: {session['model']}\nlanguage: {get_language_label()}", width=42)


def build_settings_options() -> list:
    return [
        f"Ask before reading files: {'ON' if session['ask_read_file'] else 'OFF'}",
        f"Ask before writing files: {'ON' if session['ask_write_file'] else 'OFF'}",
        f"Ask before executing commands: {'ON' if session['ask_execute_command'] else 'OFF'}",
        "Back",
    ]


def open_settings_menu() -> bool:
    options = build_settings_options()
    current_index = 0
    while True:
        chosen_idx = interactive_menu("SETTINGS", options, current_index)
        if chosen_idx == -1: return False
        if chosen_idx == len(options) - 1:
            save_config()
            show_setup_box()
            return True
        if chosen_idx == 0: session["ask_read_file"] = not session["ask_read_file"]
        elif chosen_idx == 1: session["ask_write_file"] = not session["ask_write_file"]
        else: session["ask_execute_command"] = not session["ask_execute_command"]
        save_config()
        options = build_settings_options()
        current_index = chosen_idx


def print_help():
    print_to_scroll_area(f"""
{C_PURPLE}[─] {get_text('LetCode CLI Commands', 'Команды LetCode CLI')}:{C_RESET}
  {C_LIGHT_PURPLE}/key{C_RESET}              - {get_text('Interactive API key setup for the active provider', 'Интерактивная настройка API-ключа для активного провайдера')}
  {C_LIGHT_PURPLE}/model <name>{C_RESET}     - {get_text('Change and save the model', 'Изменить и сохранить модель')}
  {C_LIGHT_PURPLE}/provider{C_RESET}         - {get_text('Interactive provider selection', 'Интерактивный выбор провайдера')}
  {C_LIGHT_PURPLE}/effort <val>{C_RESET}     - {get_text('Reasoning effort', 'Уровень рассуждений')}
  {C_LIGHT_PURPLE}/language{C_RESET}         - {get_text('Switch interface language', 'Сменить язык интерфейса')}
  {C_LIGHT_PURPLE}/reset{C_RESET}            - {get_text('Reset current chat history', 'Сбросить историю текущего чата')}
  {C_LIGHT_PURPLE}/settings{C_RESET}         - {get_text('Configure read/write/execute prompts', 'Настроить запросы на чтение/запись/выполнение')}
  {C_LIGHT_PURPLE}/help{C_RESET}             - {get_text('Show this help message', 'Показать это сообщение помощи')}
  {C_LIGHT_PURPLE}/exit{C_RESET}             - {get_text('Exit LetCode', 'Выйти из LetCode')}
    """)