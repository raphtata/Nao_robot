# -*- coding: utf-8 -*-

"""
Application Streamlit pour piloter le robot NAO
Interface web remplacant le fichier .bat
"""

import streamlit as st
import subprocess
import json
import threading
import time
import queue
import os

# Configuration de la page
st.set_page_config(
    page_title="NAO Robot Controller",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalise
st.markdown("""
<style>
    /* Style general */
    .main .block-container {
        padding-top: 1rem;
        max-width: 1200px;
    }
    
    /* Header */
    .nao-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        text-align: center;
        color: white;
    }
    .nao-header h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }
    .nao-header p {
        margin: 0.3rem 0 0 0;
        opacity: 0.8;
        font-size: 0.95rem;
    }
    
    /* Status badge */
    .status-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    .status-connected {
        background: #00c853;
        color: white;
    }
    .status-disconnected {
        background: #ff5252;
        color: white;
    }
    .status-listening {
        background: #2979ff;
        color: white;
    }
    .status-thinking {
        background: #ff9100;
        color: white;
    }
    .status-speaking {
        background: #7c4dff;
        color: white;
    }
    
    /* Chat messages */
    .chat-container {
        max-height: 500px;
        overflow-y: auto;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
    }
    
    .chat-message {
        display: flex;
        margin-bottom: 1rem;
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .chat-message.user {
        flex-direction: row-reverse;
    }
    
    .chat-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        flex-shrink: 0;
    }
    
    .chat-avatar.robot {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
    }
    
    .chat-avatar.human {
        background: linear-gradient(135deg, #f093fb, #f5576c);
        color: white;
    }
    
    .chat-bubble {
        max-width: 75%;
        padding: 0.8rem 1.2rem;
        border-radius: 16px;
        margin: 0 0.8rem;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    
    .chat-bubble.robot {
        background: white;
        border: 1px solid #e0e0e0;
        border-bottom-left-radius: 4px;
    }
    
    .chat-bubble.human {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border-bottom-right-radius: 4px;
    }
    
    .chat-sender {
        font-size: 0.75rem;
        font-weight: 600;
        margin-bottom: 0.2rem;
        opacity: 0.7;
    }
    
    /* Terminal */
    .terminal-output {
        background: #1e1e1e;
        color: #d4d4d4;
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 0.8rem;
        padding: 1rem;
        border-radius: 8px;
        max-height: 600px;
        overflow-y: auto;
        line-height: 1.6;
    }
    
    .terminal-output .log-ok {
        color: #4ec9b0;
    }
    .terminal-output .log-error {
        color: #f44747;
    }
    .terminal-output .log-info {
        color: #569cd6;
    }
    .terminal-output .log-action {
        color: #dcdcaa;
    }
    
    /* Connection card */
    .connection-card {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        text-align: center;
    }
    
    /* Boutons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #1a1a2e;
    }
    [data-testid="stSidebar"] .stMarkdown {
        color: #d4d4d4;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# Session State Initialization
# ============================================================

if "bridge_process" not in st.session_state:
    st.session_state.bridge_process = None
if "connected" not in st.session_state:
    st.session_state.connected = False
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "terminal_logs" not in st.session_state:
    st.session_state.terminal_logs = []
if "robot_status" not in st.session_state:
    st.session_state.robot_status = "disconnected"
if "response_queue" not in st.session_state:
    st.session_state.response_queue = queue.Queue()
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False
if "exchange_count" not in st.session_state:
    st.session_state.exchange_count = 0
if "nao_ip" not in st.session_state:
    st.session_state.nao_ip = "169.254.201.219"
if "nao_port" not in st.session_state:
    st.session_state.nao_port = 9559
if "language" not in st.session_state:
    st.session_state.language = "fr"


# ============================================================
# Bridge Communication
# ============================================================

PYTHON27_PATH = r"C:\Python27\python.exe"
CHOREGRAPHE_BIN = r"C:\Program Files (x86)\Softbank Robotics\Choregraphe Suite 2.5\bin"
BRIDGE_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nao_bridge_py27.py")


def add_log(message):
    """Ajouter un log au terminal"""
    timestamp = time.strftime("%H:%M:%S")
    st.session_state.terminal_logs.append(f"[{timestamp}] {message}")
    # Garder les 200 derniers logs
    if len(st.session_state.terminal_logs) > 200:
        st.session_state.terminal_logs = st.session_state.terminal_logs[-200:]


def format_log_html(log):
    """Formater un log en HTML avec couleurs"""
    if "OK " in log or "succes" in log.lower():
        return f'<span class="log-ok">{log}</span>'
    elif "X " in log or "Erreur" in log or "erreur" in log:
        return f'<span class="log-error">{log}</span>'
    elif ">>>" in log:
        return f'<span class="log-action">{log}</span>'
    elif "===" in log or "---" in log:
        return f'<span class="log-info">{log}</span>'
    return log


def start_bridge():
    """Demarrer le processus bridge Python 2.7"""
    env = os.environ.copy()
    env["PATH"] = CHOREGRAPHE_BIN + ";" + env.get("PATH", "")
    
    process = subprocess.Popen(
        [PYTHON27_PATH, BRIDGE_SCRIPT],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    return process


def send_command(action, params=None):
    """Envoyer une commande au bridge et attendre la reponse"""
    process = st.session_state.bridge_process
    if not process or process.poll() is not None:
        add_log("X Bridge non disponible")
        return None
    
    command = json.dumps({"action": action, "params": params or {}}) + "\n"
    
    try:
        process.stdin.write(command.encode("utf-8"))
        process.stdin.flush()
    except Exception as e:
        add_log(f"X Erreur envoi commande: {e}")
        return None
    
    # Lire les reponses (logs + reponse finale)
    responses = []
    while True:
        try:
            line = process.stdout.readline()
            if not line:
                break
            
            line = line.decode("utf-8", errors="ignore").strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
                responses.append(data)
                
                # Ajouter les logs
                for log_msg in data.get("logs", []):
                    add_log(log_msg)
                
                # Si c'est la reponse finale (pas un log)
                if data.get("action") != "log":
                    return data
                    
            except json.JSONDecodeError:
                add_log(line)
                
        except Exception as e:
            add_log(f"X Erreur lecture: {e}")
            break
    
    return None


def stop_bridge():
    """Arreter le processus bridge"""
    process = st.session_state.bridge_process
    if process and process.poll() is None:
        try:
            command = json.dumps({"action": "quit", "params": {}}) + "\n"
            process.stdin.write(command.encode("utf-8"))
            process.stdin.flush()
            process.wait(timeout=5)
        except:
            process.kill()
    st.session_state.bridge_process = None


# ============================================================
# UI Components
# ============================================================

def render_header():
    """Afficher le header"""
    status_class = f"status-{st.session_state.robot_status}"
    status_labels = {
        "disconnected": "Deconnecte",
        "connected": "Connecte",
        "listening": "Ecoute...",
        "thinking": "Reflexion...",
        "speaking": "Parle..."
    }
    status_label = status_labels.get(st.session_state.robot_status, "Inconnu")
    
    st.markdown(f"""
    <div class="nao-header">
        <h1>🤖 NAO Robot Controller</h1>
        <p>Interface de conversation vocale avec le robot NAO</p>
        <div class="status-badge {status_class}">{status_label}</div>
    </div>
    """, unsafe_allow_html=True)


def render_chat():
    """Afficher le chat avec les composants natifs Streamlit"""
    chat_container = st.container(height=450)
    
    with chat_container:
        if not st.session_state.chat_messages:
            st.markdown(
                "<p style='text-align:center; color:#999; padding:2rem;'>"
                "Connectez-vous au robot pour commencer la conversation</p>",
                unsafe_allow_html=True
            )
        
        for msg in st.session_state.chat_messages:
            role = msg["role"]
            text = msg["content"]
            
            if role == "robot":
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(text)
            elif role == "human":
                with st.chat_message("user", avatar="👤"):
                    st.markdown(text)
            elif role == "system":
                st.caption(f"_{text}_")


def render_terminal():
    """Afficher le terminal dans la sidebar"""
    logs_html = '<div class="terminal-output">'
    logs_html += '<div style="color:#569cd6; margin-bottom:0.5rem; font-weight:bold;">$ NAO Bridge Terminal</div>'
    
    for log in st.session_state.terminal_logs[-50:]:
        formatted = format_log_html(log)
        logs_html += f'{formatted}<br>'
    
    if not st.session_state.terminal_logs:
        logs_html += '<span style="color:#666;">En attente de connexion...</span>'
    
    logs_html += '</div>'
    st.markdown(logs_html, unsafe_allow_html=True)


# ============================================================
# Actions
# ============================================================

def do_connect():
    """Connecter au robot"""
    add_log("=" * 50)
    add_log("CONNEXION AU ROBOT NAO")
    add_log("=" * 50)
    
    # Demarrer le bridge
    try:
        st.session_state.bridge_process = start_bridge()
        add_log("OK Bridge Python 2.7 demarre")
    except Exception as e:
        add_log(f"X Erreur demarrage bridge: {e}")
        return
    
    # Attendre le message "ready"
    try:
        line = st.session_state.bridge_process.stdout.readline()
        data = json.loads(line.decode("utf-8", errors="ignore").strip())
        if data.get("action") == "ready":
            add_log("OK Bridge pret")
    except Exception as e:
        add_log(f"X Erreur initialisation bridge: {e}")
        return
    
    # Envoyer la commande de connexion
    result = send_command("connect", {
        "nao_ip": st.session_state.nao_ip,
        "nao_port": st.session_state.nao_port,
        "language": st.session_state.language
    })
    
    if result and result.get("success"):
        st.session_state.connected = True
        st.session_state.robot_status = "connected"
        add_log("OK Robot connecte avec succes!")
        
        # Message d'accueil
        st.session_state.robot_status = "speaking"
        result = send_command("say_greeting", {"language": st.session_state.language})
        if result and result.get("success"):
            greeting = result.get("data", {}).get("text", "Bonjour!")
            st.session_state.chat_messages.append({
                "role": "robot",
                "content": greeting
            })
        st.session_state.robot_status = "connected"
    else:
        error = result.get("data", {}).get("error", "Erreur inconnue") if result else "Bridge non disponible"
        add_log(f"X Connexion echouee: {error}")


def do_disconnect():
    """Deconnecter du robot"""
    add_log(">>> Deconnexion...")
    send_command("disconnect")
    stop_bridge()
    st.session_state.connected = False
    st.session_state.robot_status = "disconnected"
    st.session_state.chat_messages.append({
        "role": "system",
        "content": "Deconnecte du robot"
    })
    add_log("OK Deconnecte")


def do_listen_and_respond():
    """Ecouter, reflechir et repondre"""
    if not st.session_state.connected:
        return
    
    st.session_state.is_processing = True
    st.session_state.exchange_count += 1
    
    add_log(f"--- Echange {st.session_state.exchange_count} ---")
    
    # Synchroniser la langue avec le bridge
    send_command("set_language", {"language": st.session_state.language})
    
    # 1. Ecouter
    st.session_state.robot_status = "listening"
    st.session_state.chat_messages.append({
        "role": "system",
        "content": "🎤 Ecoute en cours..."
    })
    
    result = send_command("listen", {"max_duration": 10})
    
    # Retirer le message "ecoute en cours"
    st.session_state.chat_messages = [
        m for m in st.session_state.chat_messages 
        if m.get("content") != "🎤 Ecoute en cours..."
    ]
    
    if not result or not result.get("success"):
        transcription = None
    else:
        transcription = result.get("data", {}).get("transcription", "")
    
    if not transcription:
        st.session_state.robot_status = "speaking"
        not_understood = "Je n'ai pas compris. Pouvez-vous repeter?" if st.session_state.language == "fr" else "I didn't understand. Can you repeat?"
        send_command("speak", {"text": not_understood})
        st.session_state.chat_messages.append({
            "role": "robot",
            "content": not_understood
        })
        st.session_state.robot_status = "connected"
        st.session_state.is_processing = False
        return
    
    # Ajouter le message humain
    st.session_state.chat_messages.append({
        "role": "human",
        "content": transcription
    })
    
    # 2. Reflexion
    st.session_state.robot_status = "thinking"
    send_command("think")
    
    # 3. Obtenir la reponse LLM
    result = send_command("get_response", {"text": transcription})
    
    if result and result.get("success"):
        response_text = result.get("data", {}).get("response", "Desole, une erreur s'est produite.")
    else:
        error_detail = result.get("data", {}).get("error", "unknown") if result else "no response"
        add_log(f"X get_response failed: {error_detail}")
        response_text = "Sorry, I couldn't process your request." if st.session_state.language == "en" else "Desole, je n'ai pas pu traiter votre demande."
    
    # 4. Parler
    st.session_state.robot_status = "speaking"
    send_command("speak", {"text": response_text})
    
    st.session_state.chat_messages.append({
        "role": "robot",
        "content": response_text
    })
    
    st.session_state.robot_status = "connected"
    st.session_state.is_processing = False


def do_send_text(text):
    """Envoyer un texte manuellement (mode texte)"""
    if not st.session_state.connected or not text:
        return
    
    st.session_state.is_processing = True
    st.session_state.exchange_count += 1
    
    # Synchroniser la langue avec le bridge
    send_command("set_language", {"language": st.session_state.language})
    
    # Ajouter le message humain
    st.session_state.chat_messages.append({
        "role": "human",
        "content": text
    })
    
    # Reflexion
    st.session_state.robot_status = "thinking"
    send_command("think")
    
    # Obtenir la reponse LLM
    result = send_command("get_response", {"text": text})
    
    if result and result.get("success"):
        response_text = result.get("data", {}).get("response", "Desole, une erreur s'est produite.")
    else:
        error_detail = result.get("data", {}).get("error", "unknown") if result else "no response"
        add_log(f"X get_response failed: {error_detail}")
        response_text = "Sorry, I couldn't process your request." if st.session_state.language == "en" else "Desole, je n'ai pas pu traiter votre demande."
    
    # Parler
    st.session_state.robot_status = "speaking"
    send_command("speak", {"text": response_text})
    
    st.session_state.chat_messages.append({
        "role": "robot",
        "content": response_text
    })
    
    st.session_state.robot_status = "connected"
    st.session_state.is_processing = False


# ============================================================
# Main Layout
# ============================================================

render_header()

# Sidebar - Terminal Output
with st.sidebar:
    st.markdown("### 📟 Terminal Output")
    render_terminal()
    
    st.markdown("---")
    st.markdown("### ⚙️ Configuration")
    st.session_state.nao_ip = st.text_input("IP du robot NAO", value=st.session_state.nao_ip)
    st.session_state.nao_port = st.number_input("Port", value=st.session_state.nao_port, min_value=1, max_value=65535)
    
    st.markdown("---")
    st.markdown("### 🌐 Langue / Language")
    lang_options = {"Francais 🇫🇷": "fr", "English 🇬🇧": "en"}
    selected_lang = st.radio(
        "Choisir la langue",
        options=list(lang_options.keys()),
        index=0 if st.session_state.language == "fr" else 1,
        label_visibility="collapsed"
    )
    st.session_state.language = lang_options[selected_lang]
    
    if st.session_state.connected:
        st.markdown("---")
        st.markdown("### 📊 Statistiques")
        st.metric("Echanges", st.session_state.exchange_count)
        st.metric("Messages", len(st.session_state.chat_messages))

# Main content
if not st.session_state.connected:
    # Page de connexion
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="connection-card">
            <h2 style="color:#666; margin-bottom:1.5rem;">🔌 Connexion au Robot</h2>
            <p style="color:#666; margin-bottom:1.5rem;">
                Connectez-vous au robot NAO pour demarrer la conversation vocale.
                Assurez-vous que le robot est allume et accessible sur le reseau.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("")
        
        col_a, col_b, col_c = st.columns([1, 2, 1])
        with col_b:
            if st.button("🤖 Connecter au Robot NAO", use_container_width=True, type="primary"):
                with st.spinner("Connexion en cours..."):
                    do_connect()
                st.rerun()
        
        st.markdown("")
        st.info(f"📡 Robot cible: **{st.session_state.nao_ip}:{st.session_state.nao_port}**\n\nModifiez l'IP dans la barre laterale si necessaire.")

else:
    # Page de conversation
    # Zone de chat
    st.markdown("### 💬 Conversation")
    render_chat()
    
    st.markdown("")
    
    # Controles
    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
    
    with col1:
        text_input = st.text_input(
            "Message texte (optionnel)",
            placeholder="Tapez un message ou utilisez le micro...",
            key="text_input",
            label_visibility="collapsed"
        )
    
    with col2:
        send_text_btn = st.button(
            "📝 Envoyer texte",
            use_container_width=True,
            disabled=st.session_state.is_processing
        )
    
    with col3:
        listen_btn = st.button(
            "🎤 Ecouter (micro NAO)",
            use_container_width=True,
            type="primary",
            disabled=st.session_state.is_processing
        )
    
    with col4:
        disconnect_btn = st.button(
            "🔌",
            use_container_width=True,
            help="Deconnecter"
        )
    
    # Actions
    if listen_btn:
        with st.spinner("🎤 Ecoute en cours... Parlez au robot!"):
            do_listen_and_respond()
        st.rerun()
    
    if send_text_btn and text_input:
        with st.spinner("💭 Traitement en cours..."):
            do_send_text(text_input)
        st.rerun()
    
    if disconnect_btn:
        do_disconnect()
        st.rerun()
