import json
import platform
import time

import requests

try:
    from .config import get_default_model_for_provider, get_provider_key_field, get_text, save_config, session
    from .constants import C_DARK_PURPLE, C_LIGHT_PURPLE, C_RESET
    from .tools import TOOLS
    from .ui import print_to_scroll_area
except ImportError:
    from config import get_default_model_for_provider, get_provider_key_field, get_text, save_config, session
    from constants import C_DARK_PURPLE, C_LIGHT_PURPLE, C_RESET
    from tools import TOOLS
    from ui import print_to_scroll_area


def reset_chat():
    current_os = f"{platform.system()} {platform.release()} ({platform.machine()})"
    session["messages"] = [
        {
            "role": "system",
            "content": (
                get_text(
                    "You are an autonomous AI developer for LetCode.\n"
                    f"The user is running: {current_os}.\n"
                    "You have access to the tools: `execute_command`, `read_file`, `write_file`.\n"
                    "For reading and creating/editing files, always use the dedicated `read_file` and `write_file` functions instead of shell utilities.\n"
                    "Formatting requirements:\n"
                    "1. If you present folder structure or a report, use plain Markdown lists or code blocks.\n"
                    "2. Put commands, logs, and file structure in code fences with the `text` language.\n"
                    "3. Answer briefly, concisely, and in the same language as the user.",
                )
            ),
        }
    ]
    print_to_scroll_area(f"{C_LIGHT_PURPLE}[v] Chat context reset! Target OS set to: {platform.system()}{C_RESET}")


def normalize_response(response_json):
    if isinstance(response_json, dict):
        if "choices" in response_json and response_json["choices"]:
            return response_json
        if "message" in response_json:
            return {"choices": [{"message": response_json["message"]}]}
        if "content" in response_json:
            return {"choices": [{"message": {"role": "assistant", "content": response_json["content"]}}]}
        if "error" in response_json:
            err = response_json.get("error", {})
            message = err.get("message") if isinstance(err, dict) else str(err)
            return {"choices": [{"message": {"role": "assistant", "content": f"[Provider error] {message}"}}]}
    return {"choices": [{"message": {"role": "assistant", "content": ""}}]}


def send_to_openai_compatible(messages, api_key, url, provider_name):
    if not api_key:
        raise Exception(f"{provider_name} API key is not set. Use command: /key")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": session["model"], "messages": messages, "tools": TOOLS, "tool_choice": "auto"}
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"{provider_name} Error ({response.status_code}): {response.text}")
    return normalize_response(response.json())


def send_to_proxyapi(messages):
    return send_to_openai_compatible(messages, session.get("proxyapi_api_key"), "https://openai.api.proxyapi.ru/v1/chat/completions", "ProxyAPI")


def send_to_anthropic(messages):
    if not session["anthropic_api_key"]:
        raise Exception("Anthropic API key is not set. Use command: /key")
    system_instruction = ""
    anthropic_messages = []
    for msg in messages:
        if msg["role"] == "system":
            system_instruction = msg.get("content", "")
            continue
        if msg["role"] == "user":
            anthropic_messages.append({"role": "user", "content": msg.get("content") or ""})
        elif msg["role"] == "assistant":
            content = []
            if msg.get("content"):
                content.append({"type": "text", "text": msg["content"]})
            if msg.get("tool_calls"):
                for tc in msg["tool_calls"]:
                    content.append({
                        "type": "tool_use",
                        "id": tc["id"],
                        "name": tc["function"]["name"],
                        "input": json.loads(tc["function"]["arguments"]),
                    })
            anthropic_messages.append({"role": "assistant", "content": content})
        elif msg["role"] == "tool":
            anthropic_messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": msg.get("tool_call_id", "tool_result"),
                    "content": msg.get("content") or "",
                }],
            })

    payload = {
        "model": session["model"],
        "max_tokens": 2048,
        "messages": anthropic_messages,
        "tools": [{
            "name": t["function"]["name"],
            "description": t["function"]["description"],
            "input_schema": {
                "type": "object",
                "properties": {k: {"type": v["type"], "description": v.get("description", "")} for k, v in t["function"]["parameters"]["properties"].items()},
                "required": t["function"]["parameters"].get("required", []),
            },
        } for t in TOOLS],
        "tool_choice": {"type": "auto"},
    }
    if system_instruction:
        payload["system"] = system_instruction

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": session["anthropic_api_key"],
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        },
        json=payload,
        timeout=30,
    )
    if response.status_code != 200:
        raise Exception(f"Anthropic Error ({response.status_code}): {response.text}")

    res_json = response.json()
    text_parts = []
    tool_calls = []
    for block in res_json.get("content", []):
        if block.get("type") == "text":
            text_parts.append(block.get("text", ""))
        elif block.get("type") == "tool_use":
            tool_calls.append({
                "id": block.get("id", "anthropic_tool"),
                "type": "function",
                "function": {"name": block.get("name", ""), "arguments": json.dumps(block.get("input", {}))},
            })
    openai_msg = {"role": "assistant"}
    if text_parts:
        openai_msg["content"] = "".join(text_parts)
    if tool_calls:
        openai_msg["tool_calls"] = tool_calls
    return {"choices": [{"message": openai_msg}]}


def send_to_openrouter(messages):
    if not session["openrouter_api_key"]:
        raise Exception("OpenRouter API key is not set. Use command: /key")
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {session['openrouter_api_key']}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/letcode-cli",
        "X-Title": "LetCode CLI Agent",
    }
    payload = {"model": session["model"], "messages": messages, "tools": TOOLS, "tool_choice": "auto"}
    if any(model in session["model"] for model in ["o1", "o3", "r1"]):
        payload["reasoning"] = {"effort": session["effort"]}
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"OpenRouter Error ({response.status_code}): {response.text}")
    return response.json()


def send_to_deepseek(messages):
    return send_to_openai_compatible(messages, session["deepseek_api_key"], "https://api.deepseek.com/v1/chat/completions", "DeepSeek")


def send_to_openai(messages):
    return send_to_openai_compatible(messages, session["openai_api_key"], "https://api.openai.com/v1/chat/completions", "OpenAI")


def send_to_mistral(messages):
    return send_to_openai_compatible(messages, session["mistral_api_key"], "https://api.mistral.ai/v1/chat/completions", "Mistral")


def send_to_qwen(messages):
    return send_to_openai_compatible(messages, session["qwen_api_key"], "https://dashscope.aliyuncs.com/compatible/openai/v1/chat/completions", "Qwen")


def send_to_groq(messages):
    if not session["groq_api_key"]:
        raise Exception("Groq API key is not set. Use command: /key")
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {session['groq_api_key']}", "Content-Type": "application/json"},
        json={"model": session["model"], "messages": messages, "tools": TOOLS, "tool_choice": "auto"},
        timeout=30,
    )
    if response.status_code != 200:
        raise Exception(f"Groq Error ({response.status_code}): {response.text}")
    return response.json()


def send_to_nvidia(messages):
    if not session["nvidia_api_key"]:
        raise Exception("NVIDIA API key is not set. Use command: /key")
    response = requests.post(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {session['nvidia_api_key']}", "Content-Type": "application/json"},
        json={"model": session["model"], "messages": messages, "tools": TOOLS, "tool_choice": "auto"},
        timeout=30,
    )
    if response.status_code != 200:
        raise Exception(f"NVIDIA Error ({response.status_code}): {response.text}")
    return response.json()


def send_to_minimax(messages):
    return send_to_openai_compatible(messages, session["minimax_api_key"], "https://api.minimax.io/v1/chat/completions", "MiniMax")


def send_to_xiaomi(messages):
    return send_to_openai_compatible(messages, session["xiaomi_api_key"], "https://api.mimobeta.com/v1/chat/completions", "Xiaomi MiMo")


def send_to_xai(messages):
    return send_to_openai_compatible(messages, session["xai_api_key"], "https://api.x.ai/v1/chat/completions", "xAI")


def send_to_huggingface(messages):
    if not session["hf_api_key"]:
        raise Exception("Hugging Face API key is not set. Use command: /key")
    formatted_messages = []
    for m in messages:
        clean_msg = {"role": m["role"], "content": m.get("content") or ""}
        if "tool_calls" in m:
            clean_msg["tool_calls"] = m["tool_calls"]
        if "tool_call_id" in m:
            clean_msg["tool_call_id"] = m["tool_call_id"]
        if "name" in m:
            clean_msg["name"] = m["name"]
        formatted_messages.append(clean_msg)
    response = requests.post(
        "https://api-inference.huggingface.co/v1/chat/completions",
        headers={"Authorization": f"Bearer {session['hf_api_key']}", "Content-Type": "application/json"},
        json={"model": session["model"], "messages": formatted_messages, "tools": TOOLS, "tool_choice": "auto"},
        timeout=30,
    )
    if response.status_code != 200:
        raise Exception(f"Hugging Face Error ({response.status_code}): {response.text}")
    return response.json()


def send_to_gemini(messages):
    if not session["gemini_api_key"]:
        raise Exception("Gemini API key is not set. Use command: /key")
    gemini_contents = []
    system_instruction = ""
    for msg in messages:
        if msg["role"] == "system":
            system_instruction = msg["content"]
            continue
        role = "user" if msg["role"] in ["user", "tool"] else "model"
        parts = []
        if msg.get("content"):
            parts.append({"text": msg["content"]})
        if msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                parts.append({"function_call": {"name": tc["function"]["name"], "args": json.loads(tc["function"]["arguments"])}})
        if msg["role"] == "tool":
            parts = [{"function_call_response": {"name": msg["name"], "response": {"output": msg["content"]}}}]
        gemini_contents.append({"role": role, "parts": parts})

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{session['model']}:generateContent?key={session['gemini_api_key']}"
    gemini_tools = []
    for t in TOOLS:
        f = t["function"]
        gemini_tools.append({
            "name": f["name"],
            "description": f["description"],
            "parameters": {
                "type": f["parameters"]["type"].upper(),
                "properties": {k: {"type": v["type"].upper(), "description": v.get("description", "")} for k, v in f["parameters"]["properties"].items()},
                "required": f["parameters"].get("required", []),
            },
        })

    payload = {"contents": gemini_contents, "tools": [{"function_declarations": gemini_tools}]}
    if system_instruction:
        payload["system_instruction"] = {"parts": [{"text": system_instruction}]}
    response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=30)
    if response.status_code != 200:
        raise Exception(f"Gemini API Error ({response.status_code}): {response.text}")
    res_json = response.json()
    part = res_json["candidates"][0]["content"]["parts"][0]
    openai_msg = {"role": "assistant"}
    if "text" in part:
        openai_msg["content"] = part["text"]
    if "functionCall" in part:
        fc = part["functionCall"]
        openai_msg["tool_calls"] = [{
            "id": "gemini_tc_" + fc["name"],
            "type": "function",
            "function": {"name": fc["name"], "arguments": json.dumps(fc.get("args", {}))},
        }]
    return {"choices": [{"message": openai_msg}]}


def dispatch_provider(messages):
    if session["provider"] == "gemini_api_studio":
        return normalize_response(send_to_gemini(messages))
    if session["provider"] == "anthropic":
        return normalize_response(send_to_anthropic(messages))
    if session["provider"] == "deepseek":
        return normalize_response(send_to_deepseek(messages))
    if session["provider"] == "openai":
        return normalize_response(send_to_openai(messages))
    if session["provider"] == "proxyapi":
        return normalize_response(send_to_proxyapi(messages))
    if session["provider"] == "mistral":
        return normalize_response(send_to_mistral(messages))
    if session["provider"] == "qwen":
        return normalize_response(send_to_qwen(messages))
    if session["provider"] == "huggingface":
        return normalize_response(send_to_huggingface(messages))
    if session["provider"] == "groq":
        return normalize_response(send_to_groq(messages))
    if session["provider"] == "nvidia":
        return normalize_response(send_to_nvidia(messages))
    if session["provider"] == "minimax":
        return normalize_response(send_to_minimax(messages))
    if session["provider"] == "xiaomi":
        return normalize_response(send_to_xiaomi(messages))
    if session["provider"] == "xai":
        return normalize_response(send_to_xai(messages))
    return normalize_response(send_to_openrouter(messages))