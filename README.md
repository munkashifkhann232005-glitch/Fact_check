# 🔍 Fact-Check Agent

> **AI-powered PDF fact-checking using Google Gemini + Tavily Web Search + Streamlit**

Automatically upload any PDF document and verify every factual claim — statistics, dates, financial figures, market sizes, and more — against live web data.

---

## 📸 Screenshots

> _Add screenshots here after deployment_

| Upload & Extract | Verification Results | Download Report |
|---|---|---|
| `screenshot-upload.png` | `screenshot-results.png` | `screenshot-report.png` |

---

## ✨ Features

- 📤 **PDF Upload** — Drag-and-drop PDF ingestion with metadata preview
- 🧠 **AI Claim Extraction** — Gemini identifies all verifiable factual claims
- 🔎 **Live Web Search** — Tavily fetches real-time evidence for each claim
- ✅ **Smart Classification** — Each claim labelled as Verified / Inaccurate / False / Unverifiable
- 💬 **Reasoning** — Full explanation for every classification decision
- 📊 **Visual Dashboard** — Summary metrics, card view, and table view with colour coding
- 📥 **CSV Export** — Download the complete report as a structured CSV file
- 🎨 **Professional UI** — Dark theme, responsive layout, real-time progress tracking

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit |
| **LLM** | Google Gemini 1.5 Flash |
| **Web Search** | Tavily Search API |
| **PDF Processing** | PyMuPDF (fitz) |
| **Data** | Pandas |
| **Language** | Python 3.11+ |

---

## 🚀 Installation & Running Locally

### Prerequisites

- Python 3.11 or higher
- A [Google Gemini API key](https://aistudio.google.com/) (free tier available)
- A [Tavily API key](https://tavily.com/) (free tier available)

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/fact-check-agent.git
cd fact-check-agent
```

### 2. Create and activate a virtual environment

```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API keys

Create the secrets file:

```bash
# The file already exists as a template — just fill in your keys:
nano .streamlit/secrets.toml
```

```toml
GEMINI_API_KEY = "AIza..."
TAVILY_API_KEY = "tvly-..."
```

> **Tip:** You can also enter your keys directly in the sidebar when the app runs — no file needed.

### 5. Run the app

```bash
streamlit run app.py
```

Open your browser at **http://localhost:8501**

---

## ☁️ Deployment on Streamlit Community Cloud

Follow these steps to deploy for free on [share.streamlit.io](https://share.streamlit.io):

### Step 1 — Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/fact-check-agent.git
git push -u origin main
```

> ⚠️ Make sure `.gitignore` is present — it prevents `secrets.toml` from being committed.

### Step 2 — Create a Streamlit Cloud account

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account

### Step 3 — Deploy the app

1. Click **"New app"**
2. Select your repository: `YOUR_USERNAME/fact-check-agent`
3. Set **Branch** to `main`
4. Set **Main file path** to `app.py`
5. Click **"Deploy"**

### Step 4 — Add API keys as Secrets

1. In your deployed app dashboard, click **"Settings"**
2. Go to the **"Secrets"** tab
3. Paste the following:

```toml
GEMINI_API_KEY = "AIza..."
TAVILY_API_KEY = "tvly-..."
```

4. Click **"Save"** — the app will automatically restart.

### Step 5 — Share your app

Your app is now live at:
```
https://YOUR_USERNAME-fact-check-agent-app-XXXX.streamlit.app
```

---

## 📁 Project Structure

```
fact-check-agent/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── .gitignore                # Excludes secrets and cache
├── utils/
│   ├── __init__.py
│   ├── pdf_extractor.py      # PDF text extraction (PyMuPDF)
│   ├── claim_extractor.py    # Claim identification (Gemini)
│   ├── verifier.py           # Web search + classification (Tavily + Gemini)
│   └── report_generator.py  # CSV report generation
├── .streamlit/
│   ├── config.toml           # Theme and server configuration
│   └── secrets.toml          # API keys (local only, gitignored)
└── assets/                   # Static assets (optional)
```

---

## 🔄 Application Flow

```
PDF Upload
    │
    ▼
Text Extraction (PyMuPDF)
    │
    ▼
Claim Identification (Gemini)
    │
    ▼
Web Evidence Search (Tavily) ──► per claim
    │
    ▼
Claim Classification (Gemini) ──► Verified / Inaccurate / False / Unverifiable
    │
    ▼
Results Dashboard + CSV Download
```

---

## ⚙️ Configuration

| Setting | Default | Description |
|---|---|---|
| Max PDF text | 30,000 chars | Truncates very large documents |
| Search results per claim | 5 | Tavily results used as evidence |
| API rate-limit delay | 0.5s | Pause between claims |
| Max file upload size | 50 MB | Set in `.streamlit/config.toml` |

---

## ❗ Error Handling

| Scenario | Behaviour |
|---|---|
| Empty or scanned PDF | Clear error with guidance |
| No claims found | User-friendly message |
| Tavily API failure | Falls back to "Unverifiable" with error note |
| Gemini API failure | Falls back to "Unverifiable" with error note |
| Invalid API key | Streamlit error notification |

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 🤝 Contributing

Pull requests are welcome! Please open an issue first to discuss what you'd like to change.

---

_Built with ❤️ using Google Gemini, Tavily, and Streamlit_
