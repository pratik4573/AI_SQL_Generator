import streamlit as st
import pandas as pd
from sql_engine import (
    generate_and_run_query, get_schema_info,
    get_sample_questions, init_db,
    test_mysql_connection
)

st.set_page_config(
    page_title="AI SQL Query Generator",
    page_icon="🗄️",
    layout="wide"
)

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=DM+Sans:wght@300;400;500;600;700&display=swap');

* { font-family: 'DM Sans', sans-serif; }
code, pre { font-family: 'Fira Code', monospace !important; }
.stApp { background: #0f1117; color: #e2e8f0; }

h1 {
    font-size: 2.5rem !important; font-weight: 700 !important;
    background: linear-gradient(135deg, #00d2ff, #7c3aed);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.subtitle { font-family: 'Fira Code', monospace; color: #4a5568; font-size: 0.85rem; margin-bottom: 1.5rem; }

.sql-box {
    background: #1a1f2e; border: 1px solid #2d3748;
    border-left: 4px solid #00d2ff; border-radius: 8px;
    padding: 1rem 1.2rem; font-family: 'Fira Code', monospace;
    font-size: 0.9rem; color: #68d391; white-space: pre-wrap; margin: 0.8rem 0;
}
.explanation-box {
    background: #141920; border: 1px solid #2d3748;
    border-left: 4px solid #7c3aed; border-radius: 8px;
    padding: 1rem 1.2rem; color: #a0aec0; font-size: 0.92rem;
    line-height: 1.7; margin: 0.8rem 0;
}
.schema-box {
    background: #141920; border: 1px solid #2d3748; border-radius: 8px;
    padding: 1rem; font-family: 'Fira Code', monospace;
    font-size: 0.78rem; color: #68d391; max-height: 280px; overflow-y: auto;
}
.metric-card {
    background: #141920; border: 1px solid #2d3748;
    border-radius: 10px; padding: 1rem; text-align: center;
}
.metric-value { font-size: 1.8rem; font-weight: 700; color: #00d2ff; font-family: 'Fira Code', monospace; }
.metric-label { font-size: 0.8rem; color: #4a5568; margin-top: 4px; }
.divider { height: 1px; background: linear-gradient(90deg, transparent, #2d374888, transparent); margin: 1.5rem 0; }
.error-box {
    background: #1f1215; border: 1px solid #e53e3e44;
    border-left: 4px solid #e53e3e; border-radius: 8px;
    padding: 1rem; color: #fc8181; font-family: 'Fira Code', monospace; font-size: 0.85rem;
}
.success-box {
    background: #0f1f15; border: 1px solid #38a16944;
    border-left: 4px solid #38a169; border-radius: 8px;
    padding: 1rem; color: #68d391; font-size: 0.9rem;
}
.db-toggle {
    background: #141920; border: 1px solid #2d3748;
    border-radius: 10px; padding: 1rem; margin-bottom: 1rem;
}
.history-item {
    background: #141920; border: 1px solid #1e2535;
    border-radius: 8px; padding: 0.7rem 1rem; margin-bottom: 0.4rem;
}
.history-q { color: #e2e8f0; font-size: 0.85rem; font-weight: 500; }
.history-sql { color: #4a9eff; font-family: 'Fira Code', monospace; font-size: 0.72rem; margin-top: 3px; }

.stButton > button {
    background: linear-gradient(135deg, #00d2ff, #7c3aed) !important;
    color: white !important; border: none !important;
    border-radius: 8px !important; font-weight: 600 !important;
}
.stTextInput input { background: #1a1f2e !important; border-color: #2d3748 !important; color: #e2e8f0 !important; }
section[data-testid="stSidebar"] { background: #0b0e16 !important; border-right: 1px solid #1e2535; }
</style>
""", unsafe_allow_html=True)

# ─── Session State ────────────────────────────────────────────────────────────
if "query_history" not in st.session_state:
    st.session_state["query_history"] = []
if "current_question" not in st.session_state:
    st.session_state["current_question"] = ""
if "db_config" not in st.session_state:
    sqlite_path = init_db()
    st.session_state["db_config"] = {"type": "sqlite", "path": sqlite_path}
if "mysql_connected" not in st.session_state:
    st.session_state["mysql_connected"] = False

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("<h1>🗄️ AI SQL Query Generator</h1>", unsafe_allow_html=True)
st.markdown('<p class="subtitle">// text-to-sql · phi3 · works with SQLite & MySQL · 100% local</p>', unsafe_allow_html=True)
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔌 Database Connection")

    db_choice = st.radio(
        "Choose database:",
        ["🗂 SQLite (Sample Data)", "🐬 MySQL (Your Database)"], index=1,
        label_visibility="collapsed"
    )

    # ── SQLite Mode ──
    if "SQLite" in db_choice:
        sqlite_path = init_db()
        st.session_state["db_config"] = {"type": "sqlite", "path": sqlite_path}
        st.session_state["mysql_connected"] = False
        st.markdown("""
        <div class="success-box">
        ✅ <b>SQLite Connected</b><br>
        Using Chinook sample database<br>
        <small>(music store data — customers, tracks, invoices)</small>
        </div>
        """, unsafe_allow_html=True)

    # ── MySQL Mode ──
    else:
        st.markdown("#### MySQL Credentials")
        mysql_host = st.text_input("Host", value="localhost", placeholder="localhost")
        mysql_port = st.number_input("Port", value=3306, min_value=1, max_value=65535)
        mysql_user = st.text_input("Username", value="root", placeholder="root")
        mysql_password = st.text_input("Password", value="Admin", type="password", placeholder="your password")
        mysql_database = st.text_input("Database Name", value="uber", placeholder="your_database_name")

        if st.button("🔗 Connect to MySQL", use_container_width=True):
            if not mysql_database.strip():
                st.error("⚠️ Please enter a database name!")
            else:
                with st.spinner("Connecting..."):
                    success, message = test_mysql_connection(
                        mysql_host, int(mysql_port),
                        mysql_user, mysql_password, mysql_database
                    )
                if success:
                    st.session_state["db_config"] = {
                        "type": "mysql",
                        "host": mysql_host,
                        "port": int(mysql_port),
                        "user": mysql_user,
                        "password": mysql_password,
                        "database": mysql_database
                    }
                    st.session_state["mysql_connected"] = True
                    st.success(message)
                else:
                    st.error(message)
                    st.session_state["mysql_connected"] = False

        if st.session_state["mysql_connected"]:
            st.markdown(f"""
            <div class="success-box">
            ✅ <b>MySQL Connected</b><br>
            Host: {mysql_host}:{mysql_port}<br>
            Database: <b>{mysql_database}</b>
            </div>
            """, unsafe_allow_html=True)

    # ── Schema Display ──
    st.markdown("---")
    st.markdown("### 📊 Database Schema")
    db_config = st.session_state["db_config"]
    if db_config["type"] == "sqlite" or st.session_state["mysql_connected"]:
        try:
            schema = get_schema_info(db_config)
            st.markdown(f'<div class="schema-box">{schema}</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Schema error: {e}")

    # ── Query History ──
    st.markdown("---")
    st.markdown("### 📜 Query History")
    if st.session_state["query_history"]:
        for h in reversed(st.session_state["query_history"][-6:]):
            icon = "✅" if h["success"] else "❌"
            st.markdown(f"""
            <div class="history-item">
                <div class="history-q">{icon} {h['question'][:45]}...</div>
                <div class="history-sql">{h['sql'][:55]}...</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:#4a5568;font-size:0.85rem">No queries yet...</p>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🛠 Setup")
    st.markdown("""
```bash
ollama pull phi3
pip install -r requirements.txt
streamlit run app.py
```
    """)

# ─── Sample Questions ─────────────────────────────────────────────────────────
db_config = st.session_state["db_config"]
db_type = db_config["type"]

st.markdown("### 💡 Try a Sample Question")
samples = get_sample_questions(db_type)
cols = st.columns(3)
for i, sample in enumerate(samples):
    with cols[i % 3]:
        if st.button(f"📝 {sample}", key=f"sample_{i}", use_container_width=True):
            st.session_state["current_question"] = sample
            st.rerun()

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ─── Main Input ───────────────────────────────────────────────────────────────
st.markdown("### 🔍 Ask in Plain English")

# Check if MySQL is selected but not connected
if db_type == "mysql" and not st.session_state["mysql_connected"]:
    st.warning("⚠️ Please connect to your MySQL database first using the sidebar!")
else:
    question = st.text_input(
        label="question",
        value=st.session_state["current_question"],
        placeholder="e.g. Show me top 5 customers by total purchases",
        label_visibility="collapsed"
    )

    col_btn, col_clear, col_info = st.columns([1, 1, 4])
    with col_btn:
        run_btn = st.button("⚡ Generate SQL", use_container_width=True)
    with col_clear:
        if st.button("🗑 Clear", use_container_width=True):
            st.session_state["query_history"] = []
            st.session_state["current_question"] = ""
            st.rerun()
    with col_info:
        db_label = "SQLite (Chinook)" if db_type == "sqlite" else f"MySQL → {db_config.get('database', '')}"
        st.markdown(f'<p style="color:#4a5568;font-size:0.85rem;padding-top:0.6rem">🔌 Connected: <b style="color:#00d2ff">{db_label}</b></p>', unsafe_allow_html=True)

    # ─── Run Query ────────────────────────────────────────────────────────────
    if run_btn and question.strip():
        with st.spinner("🤖 phi3 is thinking... generating SQL..."):
            result = generate_and_run_query(question, db_config)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("## 📤 Results")

        # Metrics
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{result.get("row_count", 0)}</div><div class="metric-label">Rows Returned</div></div>', unsafe_allow_html=True)
        with m2:
            status = "✅ Success" if result.get("success") else "❌ Error"
            color = "#68d391" if result.get("success") else "#fc8181"
            st.markdown(f'<div class="metric-card"><div class="metric-value" style="font-size:1.2rem;color:{color}">{status}</div><div class="metric-label">Query Status</div></div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{result.get("col_count", 0)}</div><div class="metric-label">Columns</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col_sql, col_exp = st.columns([1, 1], gap="large")
        with col_sql:
            st.markdown("#### 🟢 Generated SQL")
            st.markdown(f'<div class="sql-box">{result["sql"]}</div>', unsafe_allow_html=True)
        with col_exp:
            st.markdown("#### 💬 AI Explanation")
            st.markdown(f'<div class="explanation-box">{result["explanation"]}</div>', unsafe_allow_html=True)

        if result.get("success") and result.get("data") is not None:
            st.markdown("#### 📊 Query Results")
            df = pd.DataFrame(result["data"], columns=result["columns"])
            st.dataframe(df, use_container_width=True, height=350)

            numeric_cols = df.select_dtypes(include='number').columns.tolist()
            if len(numeric_cols) > 0 and len(df) > 1:
                st.markdown("#### 📈 Quick Chart")
                label_cols = [c for c in df.columns if c not in numeric_cols]
                if label_cols:
                    st.bar_chart(df.set_index(label_cols[0])[numeric_cols[0]])

            csv = df.to_csv(index=False)
            st.download_button("⬇️ Download Results as CSV", csv, "results.csv", "text/csv")

        elif not result.get("success"):
            st.markdown(f'<div class="error-box">❌ SQL Error: {result.get("error", "Unknown error")}</div>', unsafe_allow_html=True)

        st.session_state["query_history"].append({
            "question": question,
            "sql": result["sql"],
            "success": result.get("success", False)
        })
        st.session_state["current_question"] = ""

    elif run_btn:
        st.warning("⚠️ Please enter a question first.")
