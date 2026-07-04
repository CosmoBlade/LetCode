import os
import select
import subprocess
import sys
import time

try:
    from .constants import C_DARK_PURPLE, C_LIGHT_PURPLE
    from .ui import print_to_scroll_area
except ImportError:
    from constants import C_DARK_PURPLE, C_LIGHT_PURPLE
    from ui import print_to_scroll_area

WORKSPACE_ROOT = os.path.expanduser("~/Desktop")
if not os.path.exists(WORKSPACE_ROOT):
    WORKSPACE_ROOT = os.getcwd()


def resolve_path(path: str) -> str:
    if not path:
        return WORKSPACE_ROOT
    expanded = os.path.expanduser(path)
    if os.path.isabs(expanded):
        return expanded
    return os.path.abspath(os.path.join(WORKSPACE_ROOT, expanded))


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "Runs a Bash command in the current project terminal and returns the result.",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string", "description": "Command to execute"}},
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads the contents of the specified file and returns its text.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Path to the file"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Creates a new file or fully overwrites an existing one with the provided content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"},
                    "content": {"type": "string", "description": "Full text to write"},
                },
                "required": ["path", "content"],
            },
        },
    },
]


def read_file(path: str) -> str:
    resolved_path = resolve_path(path)
    print_to_scroll_area(f"{C_LIGHT_PURPLE}[READ] LetCode reads file: {resolved_path}{C_DARK_PURPLE}")
    try:
        with open(resolved_path, "r", encoding="utf-8") as f:
            content = f.read()
        return f"─── FILE CONTENT OF {resolved_path} ───\n{content}\n─── END OF FILE ───"
    except Exception as e:
        return f"ERROR reading file: {str(e)}"


def write_file(path: str, content: str) -> str:
    resolved_path = resolve_path(path)
    print_to_scroll_area(f"{C_LIGHT_PURPLE}[WRITE] LetCode writes to file: {resolved_path}{C_DARK_PURPLE}")
    try:
        os.makedirs(os.path.dirname(resolved_path), exist_ok=True)
        with open(resolved_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"SUCCESS: File {resolved_path} has been written successfully."
    except Exception as e:
        return f"ERROR writing file: {str(e)}"


def execute_command(command: str) -> str:
    print_to_scroll_area(f"{C_LIGHT_PURPLE}[RUN] LetCode executes: {command}{C_DARK_PURPLE}")
    try:
        if not sys.stdin.isatty():
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60, cwd=WORKSPACE_ROOT)
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += result.stderr
            if not output.strip():
                return "Command executed successfully, but output was empty."
            return output

        proc = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=WORKSPACE_ROOT,
        )
        output_chunks = []

        while True:
            if proc.stdout:
                try:
                    ready, _, _ = select.select([proc.stdout], [], [], 0.1)
                    if ready:
                        chunk = proc.stdout.read(1)
                        if chunk:
                            output_chunks.append(chunk)
                            continue
                except Exception:
                    pass

            if proc.poll() is not None:
                break

            try:
                ready, _, _ = select.select([sys.stdin], [], [], 0.1)
                if ready:
                    pressed = sys.stdin.read(1)
                    if pressed in ["\n", "\r"]:
                        proc.terminate()
                        try:
                            proc.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            proc.kill()
                        return "Command execution was interrupted by the user."
            except Exception:
                pass

            time.sleep(0.05)

        output = "".join(output_chunks)
        if proc.returncode == 0:
            if not output.strip():
                return "Command executed successfully, but output was empty."
            return output
        return f"ERROR executing command: exit code {proc.returncode}\n{output}"
    except Exception as e:
        return f"ERROR executing command: {str(e)}"
