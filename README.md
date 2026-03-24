# 🗄️ AI SQL Query Generator (Text-to-SQL)
> Ask questions in plain English → AI writes SQL → See results instantly. Fully local, no API key needed.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red?style=flat-square&logo=streamlit)
![Ollama](https://img.shields.io/badge/Ollama-phi3-green?style=flat-square)
![SQLite](https://img.shields.io/badge/Database-SQLite-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-purple?style=flat-square)

---

## 🚀 Features

- 💬 Type questions in plain English — no SQL knowledge needed
- 🤖 phi3 LLM generates accurate SQL queries locally
- ⚡ Auto-fix — if SQL has an error, AI fixes it automatically
- 📊 Results shown as interactive table + auto bar chart
- ⬇️ Download results as CSV
- 📜 Query history panel
- 🔒 100% local — your data never leaves your machine

---

## 🖥️ Demo

```
You type:  "Show top 5 customers by total purchases"
AI writes: SELECT c.FirstName, c.LastName, SUM(i.Total) AS TotalPurchases
           FROM Customer c JOIN Invoice i ON c.CustomerId = i.CustomerId
           GROUP BY c.CustomerId ORDER BY TotalPurchases DESC LIMIT 5;
Result:    📊 Table + 📈 Bar Chart shown instantly
```

---

## 🛠️ Tech Stack

| Component | Tool |
|---|---|
| LLM | `phi3` via Ollama (local) |
| Database | SQLite (Chinook sample DB) |
| SQL Execution | Python `sqlite3` |
| Orchestration | LangChain |
| UI | Streamlit |

---

## ⚙️ Setup Instructions

### Step 1 — Install Ollama

```bash
# Linux / Mac
curl -fsSL https://ollama.ai/install.sh | sh

# Windows — download from:
https://ollama.ai
```

### Step 2 — Pull phi3 Model

```bash
ollama pull phi3
```

> ⚠️ On Windows, Ollama auto-starts after install.
> Confirm it's running: http://localhost:11434

### Step 3 — Clone This Repo

```bash
git clone https://github.com/YOUR_USERNAME/ai-sql-generator.git
cd ai-sql-generator
```

### Step 4 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 5 — Run the App

```bash
streamlit run app.py
```

The **Chinook database** downloads automatically on first run (~1MB). Open: **http://localhost:8501** 🎉

---

## 📁 Project Structure

```
ai-sql-generator/
├── app.py              # Streamlit UI
├── sql_engine.py       # Core AI pipeline (phi3 + SQLite)
├── requirements.txt    # Python dependencies
├── chinook.db          # Auto-downloaded on first run
└── README.md           # This file
```

---

## 🧠 How It Works

```
User Question (plain English)
        │
        ▼
Schema Extraction (sqlite3)
        │
        ▼
SQL Generation (phi3 via Ollama)
        │
        ▼
SQL Execution (SQLite)
        │
   ┌────┴────┐
Success?   Error?
   │           │
   │     Auto-Fix SQL (phi3)
   │           │
   └─────┬─────┘
         ▼
  AI Explanation (phi3)
         │
         ▼
  Table + Chart + CSV
```

---

## 💡 Sample Questions You Can Ask

- *"Show top 5 customers by total purchases"*
- *"Which genre has the most tracks?"*
- *"List all albums by artist AC/DC"*
- *"Show total sales by country"*
- *"Find employees who are managers"*
- *"Top 5 best selling tracks"*
- *"Count customers per country"*

---

## 🖥️ System Requirements

| Component | Minimum |
|---|---|
| RAM | 8GB |
| Storage | 3GB free (for phi3 model) |
| Python | 3.10+ |
| OS | Windows / Mac / Linux |

---

## 📦 Dependencies

```
streamlit==1.35.0
langchain==0.2.6
langchain-community==0.2.6
pandas==2.2.2
ollama==0.2.1
```

---

## 👨‍💻 Author

**Pratik Pandey**
- GitHub: [@pratik4573](https://github.com/pratik4573)
- LinkedIn: [pratikpandey45](https://linkedin.com/in/pratikpandey45)
- Portfolio: [pratikportfoli.netlify.app](https://pratikportfoli.netlify.app)

---

## ⭐ If this helped you, give it a star!
