import json
import os

CONFIG_PATH = os.path.expanduser("~/.letcode.json")

session = {
    "provider": "openrouter",
    "model": "anthropic/claude-3.5-sonnet",
    "effort": "medium",
    "language": "en",
    "openrouter_api_key": os.environ.get("OPENROUTER_API_KEY", ""),
    "gemini_api_key": os.environ.get("GEMINI_API_KEY", ""),
    "anthropic_api_key": os.environ.get("ANTHROPIC_API_KEY", ""),
    "deepseek_api_key": os.environ.get("DEEPSEEK_API_KEY", ""),
    "openai_api_key": os.environ.get("OPENAI_API_KEY", ""),
    "mistral_api_key": os.environ.get("MISTRAL_API_KEY", ""),
    "qwen_api_key": os.environ.get("QWEN_API_KEY", ""),
    "hf_api_key": os.environ.get("HF_API_KEY", ""),
    "groq_api_key": os.environ.get("GROQ_API_KEY", ""),
    "nvidia_api_key": os.environ.get("NVIDIA_API_KEY", ""),
    "minimax_api_key": os.environ.get("MINIMAX_API_KEY", ""),
    "xiaomi_api_key": os.environ.get("XIAOMI_API_KEY", ""),
    "xai_api_key": os.environ.get("XAI_API_KEY", ""),
    "ask_read_file": True,
    "ask_write_file": True,
    "ask_execute_command": True,
    "messages": [],
}


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config_data = json.load(f)
            for key in [
                "provider",
                "model",
                "effort",
                "language",
                "openrouter_api_key",
                "gemini_api_key",
                "anthropic_api_key",
                "deepseek_api_key",
                "openai_api_key",
                "mistral_api_key",
                "qwen_api_key",
                "hf_api_key",
                "groq_api_key",
                "nvidia_api_key",
                "minimax_api_key",
                "xiaomi_api_key",
                "xai_api_key",
                "ask_read_file",
                "ask_write_file",
                "ask_execute_command",
            ]:
                if key in config_data:
                    session[key] = config_data[key]
    except Exception:
        pass


def save_config():
    try:
        config_data = {
            "provider": session["provider"],
            "model": session["model"],
            "effort": session["effort"],
            "language": session["language"],
            "openrouter_api_key": session["openrouter_api_key"],
            "gemini_api_key": session["gemini_api_key"],
            "anthropic_api_key": session["anthropic_api_key"],
            "deepseek_api_key": session["deepseek_api_key"],
            "openai_api_key": session["openai_api_key"],
            "mistral_api_key": session["mistral_api_key"],
            "qwen_api_key": session["qwen_api_key"],
            "hf_api_key": session["hf_api_key"],
            "groq_api_key": session["groq_api_key"],
            "nvidia_api_key": session["nvidia_api_key"],
            "minimax_api_key": session["minimax_api_key"],
            "xiaomi_api_key": session["xiaomi_api_key"],
            "xai_api_key": session["xai_api_key"],
            "ask_read_file": session["ask_read_file"],
            "ask_write_file": session["ask_write_file"],
            "ask_execute_command": session["ask_execute_command"],
        }
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


def get_text(en: str, ru: str | None = None) -> str:
    if session.get("language") == "ru":
        return ru if ru is not None else en
    return en


def get_language_label() -> str:
    return "English" if session.get("language") != "ru" else "Русский"


def get_provider_display_name(provider: str) -> str:
    return {
        "openrouter": "OpenRouter",
        "gemini_api_studio": "Gemini",
        "anthropic": "Anthropic",
        "deepseek": "DeepSeek",
        "openai": "OpenAI",
        "mistral": "Mistral",
        "qwen": "Qwen",
        "huggingface": "Hugging Face",
        "groq": "Groq",
        "nvidia": "NVIDIA",
        "minimax": "MiniMax",
        "xiaomi": "Xiaomi MiMo",
        "xai": "xAI",
    }.get(provider, provider)


def get_provider_key_field(provider: str) -> str:
    return {
        "openrouter": "openrouter_api_key",
        "gemini_api_studio": "gemini_api_key",
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
        "xai": "xai_api_key",
    }.get(provider, "openrouter_api_key")


def get_default_model_for_provider(provider: str) -> str:
    defaults = {
        "gemini_api_studio": "gemini-2.5-flash",
        "anthropic": "claude-3-5-sonnet-latest",
        "deepseek": "deepseek-chat",
        "openai": "gpt-4o-mini",
        "mistral": "mistral-small-latest",
        "qwen": "qwen-max",
        "huggingface": "Qwen/Qwen2.5-Coder-32B-Instruct",
        "groq": "llama-3.3-70b-versatile",
        "nvidia": "meta/llama-3.3-70b-instruct",
        "minimax": "abab6.5s-chat",
        "xiaomi": "MiMo-7B-RL",
        "xai": "grok-3-mini-fast-beta",
        "openrouter": "google/gemini-2.5-flash:free",
    }
    return defaults.get(provider, session["model"])


def get_active_key(provider: str | None = None) -> str:
    provider_name = provider or session["provider"]
    if provider_name == "openrouter":
        return session["openrouter_api_key"]
    if provider_name == "anthropic":
        return session["anthropic_api_key"]
    if provider_name == "deepseek":
        return session["deepseek_api_key"]
    if provider_name == "openai":
        return session["openai_api_key"]
    if provider_name == "mistral":
        return session["mistral_api_key"]
    if provider_name == "qwen":
        return session["qwen_api_key"]
    if provider_name == "huggingface":
        return session["hf_api_key"]
    if provider_name == "groq":
        return session["groq_api_key"]
    if provider_name == "nvidia":
        return session["nvidia_api_key"]
    if provider_name == "minimax":
        return session["minimax_api_key"]
    if provider_name == "xiaomi":
        return session["xiaomi_api_key"]
    if provider_name == "xai":
        return session["xai_api_key"]
    return session["gemini_api_key"]
