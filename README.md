# LetCode CLI Agent

**LetCode** is an interactive console AI agent designed for software development directly within your terminal. It supports a wide range of popular LLM providers and allows the AI to interact with your project's file system through integrated tools for reading, writing, and executing commands

## Key Features

* **Multi-Model Support:** Native support for many providers, including OpenRouter, Gemini, Anthropic, DeepSeek, OpenAI, Mistral, Qwen, Hugging Face, Groq, NVIDIA, MiniMax, Xiaomi, and xAI
* **Autonomous Agent:** The AI can read files, create/edit code, and execute shell commands within your project context
* **Interactive Interface:** User-friendly terminal interface with menu navigation and real-time visualization of the AI's "thought" process
* **Security:** Configurable confirmation prompts before performing critical operations (file read/write, command execution)
* **Flexibility:** Multilingual interface support, configurable reasoning effort, and seamless switching between models

## CLI Commands

The following commands are available during a session:

| Command | Description |
| :--- | :--- |
| `/key` | Interactive API key setup for the active provider|
| `/model <name>` | Change and save the model |
| `/provider` | Interactive provider selection |
| `/effort <val>` | Configure reasoning effort (low, medium, high) |
| `/language` | Switch interface language |
| `/reset` | Reset current chat history|
| `/settings` | Configure confirmation settings for tools |
| `/help` | Show list of available commands |
| `/exit` | Exit the program |

## Technical Details

* **Configuration:** Settings and API keys are stored in json file
* **Security:** The `execute_command`, `read_file`, and `write_file` tools are scoped to the working directory (defaults to `~/Desktop` or the current directory)
* **Synchronization:** The agent supports interactive command execution with user-interrupt capabilities
## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
