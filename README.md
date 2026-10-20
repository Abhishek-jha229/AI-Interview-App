# 🤖 AI Interview Simulator

**AI Interview Simulator** is a full-stack, production-grade Streamlit application powered by Groq LLMs (`openai/gpt-oss-120b`) and SQLite. It provides realistic technical interview simulations, instantaneous multi-dimensional scoring, performance analytics, and report management tailored to your specific software engineering role and target difficulty.

---

## 🌟 Key Features

- **🎤 Interactive AI Interviewer**: Generates calibrated technical questions based on candidate role and difficulty level (Easy, Medium, Hard).
- **📊 Multi-Dimensional Scoring**: Evaluates answers across **Accuracy**, **Technical Depth**, and **Communication**, returning actionable missing points and constructive feedback.
- **📈 Analytics Dashboard**: Built with Plotly to track score progression over time, performance trends (last 5 vs. previous 5), and score breakdowns by role and difficulty.
- **📜 History & Reports**: Comprehensive history log with search, filters, pagination, cascade record deletion, and single/batch CSV report downloads.
- **⚙️ Customization**: Configure default roles, add custom job roles, select Groq LLM models, test API connectivity, and toggle optional per-question timers.
- **🛡️ Production Hardened**: Zero raw tracebacks in UI, exponential backoff retries, session caching, and safe SQLite schema migrations.

---

## 🛠️ Tech Stack

- **Frontend / Framework**: [Streamlit](https://streamlit.io/)
- **AI Inference Engine**: [Groq API](https://groq.com/) (using `openai/gpt-oss-120b` / `openai/gpt-oss-20b`)
- **Database Layer**: SQLite3 with PRAGMA foreign keys and auto-migrations
- **Data Analytics & Charts**: Plotly Express & Pandas
- **Environment Management**: `python-dotenv`

---

## 📸 Screenshots

*(Add screenshots of Landing Page, Live Interview, Analytics Dashboard, and History here)*

---

## 🚀 Quick Start & Setup Instructions

### 1. Clone or Download Repository
```bash
cd AI_Interview
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and insert your Groq API key:
```bash
cp .env.example .env
```
Edit `.env`:
```env
GROQ_API_KEY=gsk_your_actual_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b
```

### 5. Launch the Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 📂 Project Structure

```
AI_Interview/
├── app.py                      # Main landing page & application entrypoint
├── core/
│   ├── __init__.py
│   ├── ai.py                   # Groq API client, retries, caching, question generation
│   ├── database.py             # SQLite connection, safe schema migrations, analytics queries
│   ├── evaluator.py            # Answer evaluation & score normalization logic
│   ├── prompts.py              # Role & difficulty calibrated prompt templates
│   ├── settings.py             # Local settings.json management helper
│   └── utils.py                # Formatting & utility functions
├── pages/
│   ├── 1_Interview.py          # Interactive interview & live status session
│   ├── 2_History.py            # History log, filters, details expander & CSV export
│   ├── 3_Dashboard.py          # Plotly analytics dashboard & metrics trends
│   └── 4_Settings.py           # API connection test, model preferences & data reset
├── database/
│   └── interview.db            # Local SQLite database (created on first run)
├── .env.example                # Environment variables template
├── .gitignore                  # Git exclusions
├── requirements.txt            # Pinned project dependencies
└── README.md                   # Project documentation
```

---

## 🧠 How It Works

1. **Question Generation**: When an interview starts, `core/ai.py` sends a structured JSON request to Groq LLM containing the candidate's role and difficulty. Responses are cached in memory for identical setups.
2. **Evaluation Pipeline**: Submitting an answer invokes `core/evaluator.py`, which prompts Groq to evaluate the response against accuracy, technical depth, and communication standards.
3. **Persistence & Migration**: Completed or early-ended interview sessions are stored in SQLite using `core/database.py` with automatic schema migration.
4. **Analytics**: The Dashboard uses SQL aggregation and Plotly to render score trends, progression timelines, and aspect breakdowns.
