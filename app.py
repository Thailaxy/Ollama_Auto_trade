import json
import os
import re
from pathlib import Path
import streamlit as st
import ollama
from datetime import datetime
import pytz

st.set_page_config(page_title="Jedi Terminal (K2)", page_icon="📡", layout="wide")

CHATS_DIR = Path("chats")
CHATS_DIR.mkdir(exist_ok=True)
CONFIG_PATH = Path("config.json")
DEFAULT_CONFIG = {"model": "hermes3", "system_prompt": ""}

def load_config():
    if CONFIG_PATH.exists():
        try: return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except: return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_config(config_data):
    CONFIG_PATH.write_text(json.dumps(config_data, indent=2, ensure_ascii=False), encoding="utf-8")

def save_chat(chat_id, messages):
    if chat_id and messages:
        file_path = CHATS_DIR / f"{chat_id}.json"
        file_path.write_text(json.dumps(messages, indent=2, ensure_ascii=False), encoding="utf-8")

def get_all_chats():
    files = sorted(CHATS_DIR.glob("*.json"), key=os.path.getmtime, reverse=True)
    return [f.stem for f in files]

config = load_config()

class SkillRegistry:
    @staticmethod
    def get_date(offset_days=0):
        from datetime import datetime, timedelta
        try:
            val = re.sub(r"[^0-9-]", "", str(offset_days))
            offset = int(val) if val else 0
            target = datetime.now() + timedelta(days=offset)
            return f"RESULT: {target.strftime('%A, %B %d, %Y')}"
        except: return f"RESULT: {datetime.now().strftime('%A, %B %d, %Y')}"

    @staticmethod
    def calculate(expression):
        try:
            expr = str(expression).replace("expr", "").replace("(", "").replace(")", "").strip()
            if not expr or not any(c in "0123456789" for c in expr): return "ERROR: Provide math."
            return f"RESULT: {eval(expr)}"
        except: return "ERROR: Math failed."

    @staticmethod
    def fetch_price(symbol):
        import yfinance as yf
        try:
            sym = symbol.strip().strip("'\"").upper()
            mappings = {"BTC": "BTC-USD", "ETH": "ETH-USD"}
            sym = mappings.get(sym, sym)
            if len(sym) < 1: return "ERROR: Provide ticker."
            ticker = yf.Ticker(sym)
            data = ticker.history(period="1d")
            if data.empty: return f"ERROR: No data for {sym}."
            price = data['Close'].iloc[-1]
            currency = "THB" if sym.endswith(".BK") else "USD"
            return f"RESULT: {sym} is {price:,.2f} {currency}."
        except: return f"ERROR: Fetch failed."

    @staticmethod
    def fetch_weather(location):
        try:
            import requests
            url = f"https://wttr.in/{location.strip()}?format=3"
            res = requests.get(url).text
            if "Unknown" in res: return "ERROR: Unknown loc."
            return f"RESULT: {res}"
        except: return "ERROR: Offline."

# Main UI
st.title("🌌 Jedi Terminal (K2)")

tab_chat, tab_monitor = st.tabs(["💬 Mission Control", "📊 Market Archives"])

with tab_monitor:
    st.header("📈 Historical Logs & Performance")
    log_path = Path("price_alert_bot/trade_history.csv")
    if log_path.exists() and os.path.getsize(log_path) > 0:
        import pandas as pd
        df = pd.read_csv(log_path)
        
        # --- PERFORMANCE SUMMARY ---
        resolved_df = df[df['status'] != 'PENDING']
        total_alerts = len(df)
        wins = len(df[df['status'] == 'WIN'])
        losses = len(df[df['status'] == 'LOSS'])
        winrate = (wins / len(resolved_df) * 100) if not resolved_df.empty else 0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Alerts", total_alerts)
        c2.metric("Wins", wins)
        c3.metric("Losses", losses)
        c4.metric("Winrate", f"{winrate:.1f}%")
        
        st.markdown("---")
        
        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("Asset Performance")
            if not resolved_df.empty:
                status_counts = resolved_df.groupby(['symbol', 'status']).size().unstack(fill_value=0)
                st.bar_chart(status_counts)
            else: st.info("Waiting for resolved data to show chart.")
            
        with col_right:
            st.subheader("Leaderboard")
            if not resolved_df.empty:
                best = resolved_df[resolved_df['status'] == 'WIN']['symbol'].mode()
                worst = resolved_df[resolved_df['status'] == 'LOSS']['symbol'].mode()
                st.write(f"🏆 **Best Performer:** {best[0] if not best.empty else 'N/A'}")
                st.write(f"💀 **Worst Performer:** {worst[0] if not worst.empty else 'N/A'}")
            else: st.write("No resolved data yet.")

        st.markdown("---")
        st.subheader("Raw Archive")
        st.dataframe(df, use_container_width=True)
    else: st.info("No archives found.")

with tab_chat:
    if "chat_id" not in st.session_state: st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    if "messages" not in st.session_state: st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    if st.button("New Mission"):
        st.session_state.chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.messages = []; st.rerun()
    st.markdown("---")
    history = get_all_chats()
    if history:
        sel = st.selectbox("Previous Logs", ["Select..."] + history)
        if sel != "Select...":
            st.session_state.messages = json.loads((CHATS_DIR / f"{sel}.json").read_text(encoding="utf-8"))
            st.session_state.chat_id = sel; st.rerun()
    st.markdown("---")
    try:
        models = [m.get('model', m.get('name')) for m in ollama.list().get('models', [])] or ["llama3.1:8b"]
    except: models = ["llama3.1:8b"]
    default_model = config.get("model", models[0])
    model = st.selectbox("Droid Model", models, index=models.index(default_model) if default_model in models else 0)

for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("Input command..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        now = datetime.now(pytz.timezone('Asia/Bangkok'))
        ctx_str = f"Date: {now.strftime('%A, %B %d, %Y')}. Time: {now.strftime('%H:%M')}."
        
        system_prompt = (
            "You are K2, a tactical droid assistant.\n\n"
            "IDENTITY: Blunt, dry, sarcastic. Never warm. Never chatty.\n\n"
            "RESPONSE FORMAT — strictly follow this order:\n"
            "1. Call the required tool(s)\n"
            "2. Read the RESULT\n"
            "3. Output the data in one line: \"SYMBOL: VALUE.\"\n"
            "4. Add ONE sarcastic sentence maximum\n"
            "5. Output DONE. Stop immediately. No more text.\n\n"
            "TOOLS YOU HAVE (use ONLY these, no others):\n"
            "- <call:fetch_price symbol=\"SYMBOL\" /> — gets stock or crypto price\n"
            "- <call:fetch_weather city=\"CITY\" /> — gets weather\n"
            "- <call:get_date offset=\"N\" /> — gets date (offset=0 for today)\n\n"
            "STRICT RULES:\n"
            "- Never call a tool that is not in the list above\n"
            "- Never guess or fabricate data\n"
            "- Never give financial advice\n"
            "- Never explain what you cannot do — just answer what you can\n"
            "- DONE ends every response, no exceptions"
        )

        current_history = st.session_state.messages[:-1].copy()
        
        for i in range(3):
            chat_messages = [{"role": "system", "content": system_prompt}] + current_history + [{"role": "user", "content": prompt if i == 0 else "System tool execution finished. Review the result above and give your final answer."}]
            
            turn_response = ""
            for chunk in ollama.chat(model=model, messages=chat_messages, stream=True):
                content = chunk['message']['content']
                turn_response += content
                message_placeholder.markdown(full_response + turn_response + "▌")
                if "<call:" in turn_response.lower() and "/>" in turn_response.lower():
                    break
            
            # Extract Call
            call_match = re.search(r"<call:(\w+)\s+(.*?)\s*/>", turn_response.lower())
            if call_match:
                tag_end = turn_response.lower().find("/>") + 2
                clean_thought = turn_response[:tag_end]
                
                tool_name, args_raw = call_match.groups()
                # Simple arg extractor
                arg_val = re.search(r'="?([^"]*)"?', args_raw)
                val = arg_val.group(1) if arg_val else ""
                
                with st.spinner(f"Executing {tool_name}..."):
                    res = "ERROR"
                    if tool_name == "fetch_price": res = SkillRegistry.fetch_price(val)
                    elif tool_name == "get_date": res = SkillRegistry.get_date(val)
                    elif tool_name == "calculate": res = SkillRegistry.calculate(val)
                    elif tool_name == "fetch_weather": res = SkillRegistry.fetch_weather(val)
                
                current_history.append({"role": "assistant", "content": clean_thought})
                current_history.append({"role": "user", "content": f"[SYSTEM: {res}]"})
                full_response += clean_thought + f"\n\n> 🤖 **Sensor:** {res}\n\n"
            else:
                full_response += turn_response; break

        message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        save_chat(st.session_state.chat_id, st.session_state.messages)
