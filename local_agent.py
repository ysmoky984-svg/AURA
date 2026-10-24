import os
import platform
import subprocess
from smolagents import CodeAgent, LiteLLMModel, tool

# 1. Connect directly to your local Ollama instance (no internet required)
model = LiteLLMModel(
    model_id="ollama_chat/qwen2.5:7b",
    api_base="http://localhost:11434"
)

# 2. Define custom local tools
@tool
def list_directory(path: str = ".") -> str:
    """Lists files and folders inside a given local path.
    Args:
        path: The directory path to inspect. Defaults to the current directory.
    """
    try:
        items = os.listdir(path)
        return "\n".join(items) if items else "Directory is empty."
    except Exception as e:
        return f"Error reading directory: {e}"

@tool
def get_system_info() -> str:
    """Returns basic local OS and hardware platform details."""
    try:
        uname = platform.uname()
        return f"System: {uname.system} {uname.release} | Machine: {uname.machine} | Node: {uname.node}"
    except Exception as e:
        return f"Error getting system info: {e}"

@tool
def read_local_file(filepath: str) -> str:
    """Reads the text contents of a local file safely.
    Args:
        filepath: Full or relative path to the file.
    """
    try:
        if not os.path.exists(filepath):
            return f"File '{filepath}' not found."
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(2000)  # Read up to 2,000 characters to prevent memory overflow
    except Exception as e:
        return f"Error reading file: {e}"

# 3. Instantiate the agent with the defined tools
agent = CodeAgent(
    tools=[list_directory, get_system_info, read_local_file],
    model=model,
    add_base_tools=False
)

# 4. Interactive Command-Line Loop
if __name__ == "__main__":
    print("=" * 50)
    print("Offline Local AI Agent Ready (Type 'exit' to quit)")
    print("=" * 50 + "\n")

    while True:
        try:
            prompt = input("Agent > ")
            if prompt.strip().lower() in ["exit", "quit", "q"]:
                print("Exiting...")
                break
            if not prompt.strip():
                continue

            response = agent.run(prompt)
            print(f"\n[Agent Response]:\n{response}\n")
        except KeyboardInterrupt:
            print("\nSession interrupted.")
            break