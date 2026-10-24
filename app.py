import os
import uuid
import datetime
import platform
import requests
import streamlit as st
from smolagents import CodeAgent, LiteLLMModel, tool

# -----------------------------------------------------------------------------
# Configuration & Layout
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AURA | Local AI Workspace",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# Helper Function: Text & Linebreak Sanitization
# -----------------------------------------------------------------------------
def format_agent_output(text: str) -> str:
    """Ensures raw code escaped characters render as proper multi-line text."""
    if not isinstance(text, str):
        text = str(text)
    if "\\n" in text and "\n" not in text:
        text = text.replace("\\n", "\n")
    return text.strip()

# -----------------------------------------------------------------------------
# Animated Penguin Mascot Component (Pure Offline SVG + CSS, No Indentation)
# -----------------------------------------------------------------------------
PENGUIN_THINKING_HTML = """<div class="penguin-card">
<div class="penguin-mascot-container">
<svg class="penguin-svg" viewBox="0 0 100 100" width="76" height="76" fill="none" xmlns="http://www.w3.org/2000/svg">
<ellipse class="penguin-shadow" cx="50" cy="94" rx="28" ry="4" fill="rgba(0,0,0,0.35)"/>
<g class="penguin-character">
<path d="M22 56 C 14 58, 12 72, 24 76 C 26 71, 26 62, 22 56 Z" fill="#181D2A"/>
<path d="M78 56 C 86 58, 88 72, 76 76 C 74 71, 74 62, 78 56 Z" fill="#181D2A"/>
<ellipse cx="38" cy="91" rx="8" ry="4" fill="#F59E0B"/>
<ellipse cx="62" cy="91" rx="8" ry="4" fill="#F59E0B"/>
<path d="M50 18 C30 18 24 38 24 64 C24 84 32 90 50 90 C68 90 76 84 76 64 C76 38 70 18 50 18 Z" fill="#181D2A"/>
<path d="M50 28 C38 28 34 44 34 65 C34 82 40 86 50 86 C60 86 66 82 66 65 C66 44 62 28 50 28 Z" fill="#F8FAFC"/>
<path d="M22 40 C 22 18, 78 18, 78 40" stroke="#8B5CF6" stroke-width="4.5" stroke-linecap="round" fill="none"/>
<circle cx="23" cy="40" r="7" fill="#7C3AED"/>
<circle cx="77" cy="40" r="7" fill="#7C3AED"/>
<circle cx="23" cy="40" r="4.5" fill="#A78BFA"/>
<circle cx="77" cy="40" r="4.5" fill="#A78BFA"/>
<ellipse cx="37" cy="53" rx="4" ry="2.5" fill="#F472B6" opacity="0.65"/>
<ellipse cx="63" cy="53" rx="4" ry="2.5" fill="#F472B6" opacity="0.65"/>
<g class="penguin-eye-group">
<ellipse class="penguin-eye" cx="42" cy="46" rx="3.5" ry="4.5" fill="#0F172A"/>
<circle cx="43.5" cy="44.5" r="1.5" fill="#FFFFFF"/>
</g>
<g class="penguin-eye-group">
<ellipse class="penguin-eye" cx="58" cy="46" rx="3.5" ry="4.5" fill="#0F172A"/>
<circle cx="59.5" cy="44.5" r="1.5" fill="#FFFFFF"/>
</g>
<path d="M47 50 Q 50 54 53 50 Q 50 57 47 50 Z" fill="#F59E0B"/>
</g>
</svg>
</div>
<div class="penguin-info">
<div class="penguin-title">Hmm, let me think<span class="p-dot dot-1">.</span><span class="p-dot dot-2">.</span><span class="p-dot dot-3">.</span></div>
<div class="penguin-status">Working on your question...</div>
</div>
</div>"""

# -----------------------------------------------------------------------------
# Custom Styling: Modern Studio Dark Theme + Mascot Keyframes
# -----------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Base Canvas */
    .stApp {
        background-color: #090B10;
        color: #E2E8F0;
    }

    /* Sidebar Background */
    section[data-testid="stSidebar"] {
        background-color: #0F1219;
        border-right: 1px solid rgba(255, 255, 255, 0.07);
    }

    header[data-testid="stHeader"] {
        background-color: rgba(9, 11, 16, 0.85);
        backdrop-filter: blur(12px);
    }

    /* Topbar Header */
    .topbar-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.75rem 1.25rem;
        background: #121622;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }

    .topbar-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #F8FAFC;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Status Badges */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 9999px;
    }

    .status-online {
        background: rgba(16, 185, 129, 0.15);
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    .status-offline {
        background: rgba(239, 68, 68, 0.15);
        color: #EF4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }

    /* Welcome Hero */
    .hero-container {
        text-align: center;
        padding: 3rem 1rem 2rem 1rem;
        max-width: 720px;
        margin: 0 auto;
    }

    .hero-title {
        font-size: 2.25rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #FFFFFF 0%, #A5B4FC 50%, #06B6D4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }

    .hero-subtitle {
        color: #94A3B8;
        font-size: 0.95rem;
        line-height: 1.6;
        margin-bottom: 2rem;
    }

    /* Suggestion Cards */
    .stButton > button[kind="secondary"] {
        background-color: #131722 !important;
        color: #E2E8F0 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        padding: 0.85rem 1.1rem !important;
        text-align: left !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        width: 100%;
    }

    .stButton > button[kind="secondary"]:hover {
        background-color: #1A202E !important;
        border-color: #8B5CF6 !important;
        transform: translateY(-2px);
        box-shadow: 0 8px 15px -3px rgba(139, 92, 246, 0.15);
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #7C3AED 0%, #6366F1 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s ease;
    }

    .stButton > button[kind="primary"]:hover {
        opacity: 0.92;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(124, 58, 237, 0.35);
    }

    /* Message Bubbles */
    div[data-testid="stChatMessage"] {
        background: #11141E;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 1rem;
    }

    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
        background: #161A26;
        border-left: 3px solid #8B5CF6;
    }

    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-assistant"]) {
        background: #0E121B;
        border-left: 3px solid #06B6D4;
    }

    /* Chat Input */
    div[data-testid="stChatInput"] {
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.12);
        background-color: #121622;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }

    div[data-testid="stChatInput"]:focus-within {
        border-color: #8B5CF6 !important;
    }

    .composer-footer {
        text-align: center;
        font-size: 0.75rem;
        color: #64748B;
        margin-top: 0.5rem;
    }

    /* Expander Details */
    div[data-testid="stExpander"] {
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
        background: #0A0D14 !important;
        margin-bottom: 0.75rem !important;
    }

    /* ---------------------------------------------------- */
    /* Penguin Mascot Thinking Card & Keyframe Animations  */
    /* ---------------------------------------------------- */
    .penguin-card {
        display: inline-flex;
        align-items: center;
        gap: 1.25rem;
        background: #121624;
        border: 1px solid rgba(139, 92, 246, 0.35);
        box-shadow: 0 0 24px -4px rgba(139, 92, 246, 0.22), 0 8px 16px -2px rgba(0, 0, 0, 0.35);
        border-radius: 16px;
        padding: 0.9rem 1.4rem;
        margin: 0.4rem 0 0.8rem 0;
        animation: cardFadeIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }

    @keyframes cardFadeIn {
        from { opacity: 0; transform: translateY(6px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .penguin-mascot-container {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 76px;
        height: 76px;
    }

    /* Floating & Head Tilt Motion */
    .penguin-character {
        transform-origin: 50% 88%;
        animation: penguinFloat 2.6s ease-in-out infinite, penguinTilt 5.2s ease-in-out infinite;
    }

    @keyframes penguinFloat {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-5px); }
    }

    @keyframes penguinTilt {
        0%, 100% { transform: rotate(0deg); }
        25% { transform: rotate(-3.5deg); }
        75% { transform: rotate(3.5deg); }
    }

    /* Soft Breathing Shadow Scale */
    .penguin-shadow {
        transform-origin: 50% 94%;
        animation: shadowBreath 2.6s ease-in-out infinite;
    }

    @keyframes shadowBreath {
        0%, 100% { transform: scale(1); opacity: 0.35; }
        50% { transform: scale(0.85); opacity: 0.18; }
    }

    /* Blinking Animation */
    .penguin-eye {
        transform-origin: 50% 46%;
        animation: penguinBlink 4s ease-in-out infinite;
    }

    @keyframes penguinBlink {
        0%, 46%, 50%, 100% { transform: scaleY(1); }
        48% { transform: scaleY(0.1); }
    }

    /* Typography & Pulsing Dots */
    .penguin-info {
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 3px;
    }

    .penguin-title {
        font-size: 0.98rem;
        font-weight: 600;
        color: #F8FAFC;
        letter-spacing: -0.01em;
        display: flex;
        align-items: center;
    }

    .penguin-status {
        font-size: 0.78rem;
        color: #A5B4FC;
        letter-spacing: 0.01em;
    }

    .p-dot {
        display: inline-block;
        font-weight: 700;
        color: #8B5CF6;
        animation: dotPulse 1.4s infinite ease-in-out;
    }

    .dot-1 { animation-delay: 0.0s; }
    .dot-2 { animation-delay: 0.25s; }
    .dot-3 { animation-delay: 0.5s; }

    @keyframes dotPulse {
        0%, 80%, 100% { opacity: 0.2; transform: translateY(0); }
        40% { opacity: 1; transform: translateY(-2px); }
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Ollama Dynamic Model Inspection & Status Check
# -----------------------------------------------------------------------------
OLLAMA_API_BASE = "http://localhost:11434"

@st.cache_data(ttl=15)
def check_ollama_health() -> tuple[bool, list[str]]:
    """Checks whether the local Ollama instance is active and fetches installed models."""
    try:
        response = requests.get(f"{OLLAMA_API_BASE}/api/tags", timeout=2.0)
        if response.status_code == 200:
            data = response.json()
            models = [m.get("name") for m in data.get("models", [])]
            return True, models if models else ["qwen2.5:7b"]
    except Exception:
        pass
    return False, ["qwen2.5:7b"]

is_online, available_models = check_ollama_health()

# -----------------------------------------------------------------------------
# Backend Agent Factory
# -----------------------------------------------------------------------------
@st.cache_resource
def build_agent(model_name: str):
    """Instantiates a CodeAgent bound to the selected offline local model."""
    model = LiteLLMModel(
        model_id=f"ollama_chat/{model_name}",
        api_base=OLLAMA_API_BASE
    )

    @tool
    def list_directory(path: str = ".") -> str:
        """Lists files and folders inside a given local path.
        Args:
            path: Directory path to inspect. Defaults to current directory.
        """
        try:
            items = os.listdir(path)
            return "\n".join(items) if items else "Directory is empty."
        except Exception as e:
            return f"Error reading directory: {e}"

    @tool
    def get_system_info() -> str:
        """Returns local OS, CPU architecture, and machine hardware details."""
        try:
            uname = platform.uname()
            return f"OS: {uname.system} {uname.release} | Machine: {uname.machine} | Node: {uname.node}"
        except Exception as e:
            return f"Error inspecting system: {e}"

    @tool
    def read_local_file(filepath: str) -> str:
        """Safely inspects up to the first 2000 characters of a local text file.
        Args:
            filepath: The full or relative file path.
        """
        try:
            if not os.path.exists(filepath):
                return f"File '{filepath}' not found."
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(2000)
        except Exception as e:
            return f"Error reading file: {e}"

    return CodeAgent(
        tools=[list_directory, get_system_info, read_local_file],
        model=model,
        add_base_tools=False
    )

# -----------------------------------------------------------------------------
# Session & Conversation State Management
# -----------------------------------------------------------------------------
if "conversations" not in st.session_state:
    initial_id = str(uuid.uuid4())
    st.session_state.conversations = {
        initial_id: {
            "title": "Initial Session",
            "created_at": datetime.datetime.now().strftime("%b %d, %H:%M"),
            "messages": []
        }
    }
    st.session_state.active_chat_id = initial_id

if "active_chat_id" not in st.session_state or st.session_state.active_chat_id not in st.session_state.conversations:
    st.session_state.active_chat_id = list(st.session_state.conversations.keys())[0]

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

# -----------------------------------------------------------------------------
# Left Sidebar: Navigation, Model Config & Local Status
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 1.25rem;">
            <div style="background: linear-gradient(135deg, #8B5CF6, #06B6D4); width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white;">✦</div>
            <div>
                <div style="font-weight: 700; font-size: 1.1rem; letter-spacing: -0.02em; color: #F8FAFC;">AURA</div>
                <div style="font-size: 0.72rem; color: #94A3B8;">Local Intelligence Studio</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("＋ New Chat", key="btn_new_chat", use_container_width=True, type="primary"):
        new_id = str(uuid.uuid4())
        st.session_state.conversations[new_id] = {
            "title": "Untitled Chat",
            "created_at": datetime.datetime.now().strftime("%b %d, %H:%M"),
            "messages": []
        }
        st.session_state.active_chat_id = new_id
        st.rerun()

    st.write("")
    st.markdown("<p style='font-size: 0.78rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; margin-bottom: 4px;'>Local Model Engine</p>", unsafe_allow_html=True)
    selected_model = st.selectbox(
        "Model Selector",
        options=available_models,
        index=0,
        label_visibility="collapsed"
    )

    st.write("")
    st.markdown("<p style='font-size: 0.78rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; margin-bottom: 4px;'>Conversations</p>", unsafe_allow_html=True)
    search_query = st.text_input("Search chats", placeholder="Filter history...", label_visibility="collapsed")

    history_box = st.container()
    with history_box:
        for chat_id, chat_data in list(st.session_state.conversations.items()):
            if search_query and search_query.lower() not in chat_data["title"].lower():
                continue
            
            is_selected = (chat_id == st.session_state.active_chat_id)
            btn_style = "primary" if is_selected else "secondary"
            
            col_chat, col_del = st.columns([0.82, 0.18])
            with col_chat:
                label = f"💬 {chat_data['title'][:20]}"
                if st.button(label, key=f"sel_{chat_id}", use_container_width=True, type=btn_style):
                    st.session_state.active_chat_id = chat_id
                    st.rerun()
            with col_del:
                if len(st.session_state.conversations) > 1:
                    if st.button("×", key=f"del_{chat_id}", help="Delete chat"):
                        del st.session_state.conversations[chat_id]
                        st.session_state.active_chat_id = list(st.session_state.conversations.keys())[0]
                        st.rerun()

    st.write("")
    with st.expander("⚙ Settings & Hardware", expanded=False):
        st.caption("Agent Runtime Parameters")
        temperature = st.slider("Temperature", 0.0, 1.0, 0.3, 0.05)
        allow_file_io = st.checkbox("Enable File System Access", value=True)
        st.caption(f"Host: `{platform.node()}`")

    st.markdown("---")
    if is_online:
        st.markdown('<div class="status-badge status-online">● Ollama Engine Connected</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-badge status-offline">● Ollama Disconnected (Port 11434)</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div style="font-size: 0.72rem; color: #64748B; margin-top: 10px; line-height: 1.4;">
            <strong>AURA v2.4 Local</strong><br>
            Zero external telemetry. All model weights and memory cached on this PC.
        </div>
        """,
        unsafe_allow_html=True
    )

# -----------------------------------------------------------------------------
# Active Chat Data & Agent Setup
# -----------------------------------------------------------------------------
current_chat = st.session_state.conversations[st.session_state.active_chat_id]
messages = current_chat["messages"]
active_agent = build_agent(selected_model)

# -----------------------------------------------------------------------------
# Main Header Bar
# -----------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="topbar-container">
        <div class="topbar-title">
            <span>✦</span>
            <span>{current_chat['title']}</span>
        </div>
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 0.8rem; background: #1C2230; padding: 4px 10px; border-radius: 6px; color: #A5B4FC; border: 1px solid rgba(255,255,255,0.08);">
                {selected_model}
            </span>
            <span class="status-badge {'status-online' if is_online else 'status-offline'}">
                {'● Local Connected' if is_online else '● Offline'}
            </span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------------------------------------------------------
# Main Conversation Area
# -----------------------------------------------------------------------------
if not messages:
    st.markdown(
        """
        <div class="hero-container">
            <h1 class="hero-title">Your AI. Your machine.</h1>
            <p class="hero-subtitle">
                A high-performance offline workspace executing tasks, analyzing files, and inspecting system state directly through your local hardware.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("💡 Explain a programming concept\n\nWalk through how Python manages memory and garbage collection.", key="sug_1", use_container_width=True):
            st.session_state.pending_prompt = "Explain how Python manages memory and how garbage collection operates in simple steps."
            st.rerun()

        if st.button("🔍 Help me debug code\n\nAnalyze common logic errors and provide practical fixes.", key="sug_2", use_container_width=True):
            st.session_state.pending_prompt = "Give me a practical checklist for debugging intermittent memory leaks in Python."
            st.rerun()

    with c2:
        if st.button("📄 Summarize a document or inspect files\n\nRun the list_directory tool to check files in this workspace.", key="sug_3", use_container_width=True):
            st.session_state.pending_prompt = "Please list the files in the current workspace directory and tell me what you find."
            st.rerun()

        if st.button("🚀 Brainstorm a project idea\n\nDesign an offline local workflow using open-source models.", key="sug_4", use_container_width=True):
            st.session_state.pending_prompt = "Brainstorm three innovative tools I can build with local LLMs and offline Python tools."
            st.rerun()

else:
    for msg in messages:
        with st.chat_message(msg["role"]):
            if msg.get("steps"):
                with st.expander("🔍 Thought & Execution Details", expanded=False):
                    for step in msg["steps"]:
                        st.markdown(f"**Step {step.get('step', 1)}**")
                        if step.get("thought"):
                            st.info(step["thought"])
                        if step.get("code"):
                            st.code(step["code"], language="python")
                        if step.get("observation"):
                            st.caption(f"System Observation: {step['observation']}")
            
            st.markdown(format_agent_output(msg["content"]))

# -----------------------------------------------------------------------------
# Input Handling & Execution Loop
# -----------------------------------------------------------------------------
user_input = st.chat_input("Ask AURA to inspect files, execute Python tools, or analyze logic...")

effective_prompt = None
if st.session_state.pending_prompt:
    effective_prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None
elif user_input:
    effective_prompt = user_input

if effective_prompt:
    if not messages:
        first_line = effective_prompt.split("\n")[0][:28]
        current_chat["title"] = first_line

    # 1. Render User Query Bubble
    current_chat["messages"].append({"role": "user", "content": effective_prompt})
    with st.chat_message("user"):
        st.markdown(effective_prompt)

    # 2. Assistant Response Container
    with st.chat_message("assistant"):
        if not is_online:
            err = "Cannot reach Ollama daemon. Start Ollama using `ollama serve` or open the Ollama desktop app."
            st.error(err)
            current_chat["messages"].append({"role": "assistant", "content": err})
        else:
            final_text = ""
            captured_steps = []

            # Dynamic placeholder: renders animated thinking mascot while active_agent.run() executes
            mascot_slot = st.empty()
            mascot_slot.markdown(PENGUIN_THINKING_HTML, unsafe_allow_html=True)

            try:
                # Real LLM / agent tool execution
                result = active_agent.run(effective_prompt)
                final_text = format_agent_output(str(result))

                # Extract reasoning memory
                if hasattr(active_agent, "memory") and hasattr(active_agent.memory, "steps"):
                    for idx, s in enumerate(active_agent.memory.steps, 1):
                        step_record = {"step": idx}
                        if hasattr(s, "model_output") and s.model_output:
                            step_record["thought"] = str(s.model_output)
                        if hasattr(s, "action_output") and s.action_output:
                            step_record["observation"] = str(s.action_output)
                        captured_steps.append(step_record)

            except Exception as ex:
                final_text = f"Error during execution: {ex}"
            finally:
                # Cleanly clear the mascot card when response or error arrives
                mascot_slot.empty()

            # Render collapsible reasoning trace if any steps were executed
            if captured_steps:
                with st.expander("🔍 Thought & Execution Details", expanded=False):
                    for step in captured_steps:
                        st.markdown(f"**Step {step.get('step', 1)}**")
                        if step.get("thought"):
                            st.info(step["thought"])
                        if step.get("observation"):
                            st.caption(f"System Observation: {step['observation']}")

            # Render the final text answer directly
            if final_text:
                if final_text.startswith("Error during execution:"):
                    st.error(final_text)
                else:
                    st.markdown(final_text)

                current_chat["messages"].append({
                    "role": "assistant",
                    "content": final_text,
                    "steps": captured_steps
                })

# -----------------------------------------------------------------------------
# Bottom Indicator
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="composer-footer">
        Runs locally • Your conversations stay on your machine, subject to your configuration.
    </div>
    """,
    unsafe_allow_html=True
)