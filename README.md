# 🌌 Jedi Archive Terminal (Ollama Project)

A sophisticated, themed Streamlit interface for interacting with local LLMs via Ollama. Built specifically for high-performance usage on Apple Silicon (M2).

## 🚀 Overview
The **Jedi Archive Terminal** is a local AI workbench designed for the "Jedi" workflow. It provides a rich, immersive terminal experience with real-time date/time awareness, persistent chat history, and dynamic UI themes.

## ✨ Features Implemented (Latest Update: April 21, 2026)

### 1. Interface & Aesthetics
- **Space-Themed UI:** Custom CSS implementation featuring a "Space Jedi" dark mode with neon accents.
- **Dynamic Backgrounds:** Two fixed "Lightsaber" glowing pillars that react to the chosen theme.
- **Theme Engine:** Four switchable themes available via the "Command Center":
    - **Jedi Archive:** Original deep space blue.
    - **Universal:** High-contrast emerald/slate.
    - **Sun-Surface:** Intense solar orange and magma red.
    - **Galactic Nebula:** Deep purple/magenta nebula aesthetic.
- **Optimized Chat Layout:** User messages are aligned to the **right**, Assistant messages to the **left**, with high-contrast bubbles for maximum readability.

### 2. Core Functionality
- **Ollama Integration:** Seamless connection to the local Ollama API.
- **Model Auto-Discovery:** Automatically detects and lists all models currently installed on the system (e.g., `llama3.1:8b`, `gemma4:e4b`).
- **Context Awareness:** Automatically injects the current Bangkok (UTC+7) time and date into the System Prompt to ensure the LLM has real-time context.
- **Persistence (Holocron Archive):**
    - **Auto-Save:** All conversations are automatically saved to `.json` files in the `/chats` directory.
    - **Session Recovery:** Re-opening the app automatically restores the most recent active session.
    - **Mission Management:** "Start New Mission" button to archive current chats and begin fresh.

### 3. Configuration
- **Persistent Settings:** `config.json` stores your preferred model and default system prompts.
- **In-App Config Editor:** Edit the JSON configuration directly from the sidebar without leaving the browser.

## 🛠️ Tech Stack
- **Frontend:** Streamlit (Python)
- **Engine:** Ollama (Running locally)
- **Models:** Optimized for `llama3.1:8b` and `gemma4:e4b`
- **Environment:** macOS (M2 Silicon optimized)

## 🏁 Getting Started

### Prerequisites
1.  **Ollama:** Must be running in the background. [Download here](https://ollama.com/).
2.  **Python 3.9+**

### Installation
```bash
# Clone the repository and install dependencies
pip install streamlit ollama pytz
```

### Running the App
```bash
streamlit run app.py
```

## 📋 Hand-over Notes for NCG Engineer
- **Next Milestone:** Integrate the **OpenClaw agent** framework to enable autonomous task execution using the local Ollama models.
- **Customization:** The CSS is injected dynamically in `app.py` based on the `THEMES` dictionary. Any new themes should follow the existing schema in that dictionary.
- **Chat Storage:** Files in `/chats` are named by timestamp. To implement a "Delete" feature, you will need to add file system deletion logic to the Sidebar Archive.

---
**Status:** ✅ Environment Verified (MacBook Air M2 16GB) | ✅ Ollama Models Active | ✅ Persistence Layer Functional
