import json
import shutil
import sys
import threading
import time

try:
    from .config import (
        get_active_key,
        get_default_model_for_provider,
        get_provider_display_name,
        get_provider_key_field,
        get_text,
        load_config,
        save_config,
        session,
    )
    from .constants import C_DARK_PURPLE, C_LIGHT_PURPLE, C_PURPLE, C_RESET
    from .providers import dispatch_provider, reset_chat
    from .tools import execute_command, read_file, write_file
    from .ui import (
        draw_box,
        interactive_menu,
        open_settings_menu,
        print_help,
        print_to_scroll_area,
        read_input_line,
        reset_scrolling_region,
        setup_scrolling_region,
        show_setup_box,
    )
except ImportError:
    from config import (
        get_active_key,
        get_default_model_for_provider,
        get_provider_display_name,
        get_provider_key_field,
        get_text,
        load_config,
        save_config,
        session,
    )
    from constants import C_DARK_PURPLE, C_LIGHT_PURPLE, C_PURPLE, C_RESET
    from providers import dispatch_provider, reset_chat
    from tools import execute_command, read_file, write_file
    from ui import (
        draw_box,
        interactive_menu,
        open_settings_menu,
        print_help,
        print_to_scroll_area,
        read_input_line,
        reset_scrolling_region,
        setup_scrolling_region,
        show_setup_box,
    )


def handle_command(user_input: str) -> bool:
    parts = user_input.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd == "/exit":
        reset_scrolling_region()
        print(f"{C_LIGHT_PURPLE}Exiting. Happy coding!{C_RESET}")
        sys.exit(0)
    if cmd == "/help":
        print_help()
        return True
    if cmd == "/reset":
        reset_chat()
        return True
    if cmd == "/provider":
        providers = [
            "openrouter", "gemini_api_studio", "anthropic", "deepseek", "openai",
            "mistral", "qwen", "huggingface", "groq", "nvidia", "minimax",
            "xiaomi", "xai", "proxyapi", "exit",
        ]
        current_idx = providers.index(session["provider"]) if session["provider"] in providers else 0
        chosen_idx = interactive_menu("SELECT PROVIDER", providers, current_idx)
        if chosen_idx == -1:
            print_to_scroll_area(f"{C_LIGHT_PURPLE}[i] Provider selection cancelled.{C_RESET}")
            return True
        chosen_provider = providers[chosen_idx]
        if chosen_provider == "exit":
            print_to_scroll_area(f"{C_LIGHT_PURPLE}[i] Returning to the main menu.{C_RESET}")
            return True

        key_field = get_provider_key_field(chosen_provider)
        has_saved_key = bool(session[key_field])
        session["provider"] = chosen_provider
        if has_saved_key:
            print_to_scroll_area(f"{C_LIGHT_PURPLE}[i] Saved key found for {get_provider_display_name(chosen_provider)}. Using it.{C_RESET}")
        else:
            rows = shutil.get_terminal_size().lines
            sys.stdout.write(f"\033[{rows - 2};1H\n")
            key_val = input(f"Enter {get_provider_display_name(chosen_provider)} API Key: ").strip()
            if key_val:
                session[key_field] = key_val
                save_config()
                print_to_scroll_area(f"{C_LIGHT_PURPLE}[OK] Key saved for {get_provider_display_name(chosen_provider)}.{C_RESET}")
            else:
                print_to_scroll_area(f"{C_DARK_PURPLE}[!] Key skipped for {get_provider_display_name(chosen_provider)}.{C_RESET}")

        if not session["model"] or not has_saved_key:
            session["model"] = get_default_model_for_provider(chosen_provider)
        save_config()
        show_setup_box()
        return True
    if cmd == "/key":
        rows = shutil.get_terminal_size().lines
        sys.stdout.write(f"\033[{rows - 2};1H\n")
        keys = {
            "openrouter": "openrouter_api_key",
            "anthropic": "anthropic_api_key",
            "deepseek": "deepseek_api_key",
            "openai": "openai_api_key",
            "mistral": "mistral_api_key",
            "qwen": "qwen_api_key",
            "huggingface": "hf_api_key",
            "groq": "groq_api_key",
            "nvidia": "nvidia_api_key",
            "minimax": "minimax_api_key",
            "xiaomi": "xiaomi_api_key",
            "proxyapi": "proxyapi_api_key",
            "xai": "xai_api_key"
        }
        key_name = keys.get(session["provider"], "gemini_api_key")
        key_val = input(f"Enter {session['provider']} API Key: ").strip()
        session[key_name] = key_val
        save_config()
        print_to_scroll_area(f"{C_LIGHT_PURPLE}[OK] Key updated and saved successfully!{C_RESET}")
        return True
    if cmd == "/settings":
        open_settings_menu()
        return True
    if cmd == "/language":
        language_options = ["English", "Russian", "Back"]
        current_idx = 0 if session.get("language") != "ru" else 1
        chosen_idx = interactive_menu("SELECT LANGUAGE", language_options, current_idx)
        if chosen_idx == -1:
            print_to_scroll_area(f"{C_LIGHT_PURPLE}[i] Language selection cancelled.{C_RESET}")
            return True
        if chosen_idx == len(language_options) - 1:
            return True
        session["language"] = "en" if chosen_idx == 0 else "ru"
        save_config()
        show_setup_box()
        return True
    if cmd == "/model":
        if arg:
            session["model"] = arg
            save_config()
            print_to_scroll_area(f"{C_LIGHT_PURPLE}[i] Model changed to: {session['model']}{C_RESET}")
        else:
            print_to_scroll_area(f"Current model: {session['model']}")
        return True
    if cmd == "/effort":
        if arg:
            if arg.lower() in ["low", "medium", "high"]:
                session["effort"] = arg.lower()
                save_config()
                print_to_scroll_area(f"{C_LIGHT_PURPLE}[i] Reasoning effort set to: {session['effort']}{C_RESET}")
            return True
        effort_options = ["low", "medium", "high", "Back"]
        current_idx = effort_options.index(session.get("effort", "medium")) if session.get("effort", "medium") in effort_options else 0
        chosen_idx = interactive_menu("SELECT EFFORT", effort_options, current_idx)
        if chosen_idx != -1 and chosen_idx < 3:
            session["effort"] = effort_options[chosen_idx]
            save_config()
            show_setup_box()
        return True
    return False


def run_with_thinking_status(provider_call):
    start_time = time.monotonic()
    result_holder = {}
    error_holder = {}

    def worker():
        try:
            result_holder["value"] = provider_call()
        except Exception as exc:
            error_holder["error"] = exc

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    status_row = shutil.get_terminal_size().lines - 2

    while thread.is_alive():
        elapsed = int(time.monotonic() - start_time)
        est_tokens = max(80, elapsed * 120)
        # Обновление строки без перехода на новую
        sys.stdout.write(f"\033[{status_row};1H\033[K{C_DARK_PURPLE}[THINKING] LetCode is thinking...{C_RESET} Elapsed: {elapsed}s | Est. tokens: {est_tokens}")
        sys.stdout.flush()
        time.sleep(0.5)

    # Очистка строки статуса после ответа
    sys.stdout.write(f"\033[{status_row};1H\033[K")
    sys.stdout.flush()

    if "error" in error_holder:
        raise error_holder["error"]

    return result_holder.get("value"), int(time.monotonic() - start_time), max(80, int(time.monotonic() - start_time) * 120)


def main():
    load_config()
    setup_scrolling_region()
    show_setup_box()

    active_key = get_active_key()
    if not active_key:
        print_to_scroll_area(f"{C_DARK_PURPLE}[!] Warning: API key not found. Use /key{C_RESET}")
    else:
        masked = active_key[:6] + "..." + active_key[-4:] if len(active_key) > 10 else "***"
        print_to_scroll_area(f"{C_LIGHT_PURPLE}[API] Active key ({session['provider']}): {masked}{C_RESET}")

    reset_chat()
    history = []

    while True:
        try:
            model_short = session["model"].split("/")[-1]
            prompt = f"LetCode ({model_short}) > "
            user_input = read_input_line(prompt, history)
            if not user_input:
                continue

            history.append(user_input)
            
            if user_input.startswith("/"):
                if handle_command(user_input):
                    continue

            draw_box("YOU", user_input)
            session["messages"].append({"role": "user", "content": user_input})

            processing = True
            while processing:
                response_json, elapsed_seconds, est_tokens = run_with_thinking_status(lambda: dispatch_provider(session["messages"]))
                choice = response_json["choices"][0]
                message = choice["message"]
                session["messages"].append(message)

                if message.get("content"):
                    res = message["content"] + f"\n\n[elapsed: {elapsed_seconds}s | est. tokens: {est_tokens}]"
                    draw_box("LETCODE AI", res)

                if message.get("tool_calls"):
                    for tool_call in message["tool_calls"]:
                        tool_name = tool_call["function"]["name"]
                        args = json.loads(tool_call["function"]["arguments"])
                        
                        confirm = True
                        if session.get(f"ask_{tool_name}", True):
                            print_to_scroll_area(f"\n{C_DARK_PURPLE}[?] Execute {tool_name}: {args.get('command') or args.get('path')}{C_RESET}")
                            confirm = input(f"{C_PURPLE}Allow? (y/N): {C_RESET}").lower() in ["y", "yes"]
                        
                        cmd_result = "Denied"
                        if confirm:
                            cmd_result = execute_command(args["command"]) if tool_name == "execute_command" else (read_file(args["path"]) if tool_name == "read_file" else write_file(args["path"], args["content"]))
                        
                        session["messages"].append({"role": "tool", "tool_call_id": tool_call["id"], "name": tool_name, "content": str(cmd_result)})
                else:
                    processing = False
        except KeyboardInterrupt:
            reset_scrolling_region()
            print(f"\n{C_LIGHT_PURPLE}Exiting...{C_RESET}")
            break
        except Exception as e:
            print_to_scroll_area(f"\n{C_DARK_PURPLE}[ERROR] {e}{C_RESET}")


if __name__ == "__main__":
    try:
        main()
    finally:
        sys.stdout.write("\033[r")
        sys.stdout.flush()