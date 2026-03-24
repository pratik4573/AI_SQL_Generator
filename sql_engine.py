"""
sql_engine.py — Core Text-to-SQL Logic
Uses: Ollama (phi3) + MySQL OR SQLite
Optimized for 8GB RAM
"""

import sqlite3
import os
import re
import urllib.request

from langchain_community.llms import Ollama

# ─── Config ───────────────────────────────────────────────────────────────────
LLM_MODEL = "phi3"
OLLAMA_BASE_URL = "http://localhost:11434"
DB_PATH = "chinook.db"
CHINOOK_URL = "https://github.com/lerocha/chinook-database/raw/master/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite"


def get_llm():
    return Ollama(
        model=LLM_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0,
        num_ctx=2048,
        num_thread=4,
    )


# ─── SQLite Setup ─────────────────────────────────────────────────────────────
def init_db() -> str:
    """Download Chinook DB if not present, return path."""
    if not os.path.exists(DB_PATH):
        print("Downloading Chinook sample database...")
        urllib.request.urlretrieve(CHINOOK_URL, DB_PATH)
        print("Database ready!")
    return DB_PATH


# ─── MySQL Connection ─────────────────────────────────────────────────────────
def get_mysql_connection(host: str, port: int, user: str, password: str, database: str):
    """Create and return a MySQL connection."""
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connection_timeout=10
        )
        return conn, None
    except Exception as e:
        return None, str(e)


def test_mysql_connection(host: str, port: int, user: str, password: str, database: str) -> tuple:
    """Test MySQL connection. Returns (success, message)."""
    conn, error = get_mysql_connection(host, port, user, password, database)
    if conn:
        conn.close()
        return True, "✅ Connected successfully!"
    return False, f"❌ Connection failed: {error}"


# ─── Schema Extraction ────────────────────────────────────────────────────────
def get_schema_info_sqlite(db_path: str) -> str:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [row[0] for row in cursor.fetchall()]
    schema_lines = []
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()
        cols_str = ", ".join([f"{col[1]} ({col[2]})" for col in columns])
        schema_lines.append(f"📋 {table}:\n   {cols_str}")
    conn.close()
    return "\n\n".join(schema_lines)


def get_schema_info_mysql(host, port, user, password, database) -> str:
    conn, error = get_mysql_connection(host, port, user, password, database)
    if not conn:
        return f"Error: {error}"
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES;")
    tables = [row[0] for row in cursor.fetchall()]
    schema_lines = []
    for table in tables:
        cursor.execute(f"DESCRIBE `{table}`;")
        columns = cursor.fetchall()
        cols_str = ", ".join([f"{col[0]} ({col[1]})" for col in columns])
        schema_lines.append(f"📋 {table}:\n   {cols_str}")
    conn.close()
    return "\n\n".join(schema_lines)


def get_schema_compact_sqlite(db_path: str) -> str:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [row[0] for row in cursor.fetchall()]
    lines = []
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()
        col_names = [col[1] for col in columns]
        lines.append(f"{table}({', '.join(col_names)})")
    conn.close()
    return "\n".join(lines)


def get_schema_compact_mysql(host, port, user, password, database) -> str:
    conn, error = get_mysql_connection(host, port, user, password, database)
    if not conn:
        return f"Error: {error}"
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES;")
    tables = [row[0] for row in cursor.fetchall()]
    lines = []
    for table in tables:
        cursor.execute(f"DESCRIBE `{table}`;")
        columns = cursor.fetchall()
        col_names = [col[0] for col in columns]
        lines.append(f"{table}({', '.join(col_names)})")
    conn.close()
    return "\n".join(lines)


# ─── Unified Schema Functions ─────────────────────────────────────────────────
def get_schema_info(db_config: dict) -> str:
    if db_config["type"] == "sqlite":
        return get_schema_info_sqlite(db_config["path"])
    else:
        return get_schema_info_mysql(
            db_config["host"], db_config["port"],
            db_config["user"], db_config["password"],
            db_config["database"]
        )


def get_schema_compact(db_config: dict) -> str:
    if db_config["type"] == "sqlite":
        return get_schema_compact_sqlite(db_config["path"])
    else:
        return get_schema_compact_mysql(
            db_config["host"], db_config["port"],
            db_config["user"], db_config["password"],
            db_config["database"]
        )


# ─── Sample Questions ─────────────────────────────────────────────────────────
def get_sample_questions(db_type: str = "sqlite") -> list:
    if db_type == "mysql":
        return [
            "Show all tables in the database",
            "Show first 10 rows of any table",
            "Count total rows in each table",
            "Find duplicate records in any table",
            "Show all columns of first table",
        ]
    return [
        "Show top 5 customers by total purchases",
        "List all albums by artist AC/DC",
        "Which genre has the most tracks?",
        "Show total sales by country",
        "Find employees who are managers",
        "Top 5 best selling tracks",
        "Show all invoices above $10",
        "Count customers per country",
        "List all rock genre tracks",
    ]


# ─── SQL Extraction ───────────────────────────────────────────────────────────
def extract_sql(text: str) -> str:
    match = re.search(r'```sql\s*([\s\S]*?)```', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(r'```([\s\S]*?)```', text)
    if match:
        return match.group(1).strip()
    match = re.search(r'(SELECT[\s\S]+?)(;|$)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip() + ";"
    return text.strip()


# ─── SQL Generation ───────────────────────────────────────────────────────────
def generate_sql(llm, question: str, schema: str, db_type: str = "sqlite") -> str:
    syntax = "MySQL" if db_type == "mysql" else "SQLite"
    prompt = f"""You are an expert SQL developer. Generate a {syntax} SQL query for the question below.

DATABASE SCHEMA:
{schema}

RULES:
- Write only the SQL query, nothing else
- Use proper {syntax} syntax
- Always use LIMIT 100 to avoid large results
- Use backticks for table/column names in MySQL
- Wrap the SQL in ```sql``` code block

QUESTION: {question}

SQL:"""
    response = llm.invoke(prompt)
    return extract_sql(response)


# ─── SQL Explanation ──────────────────────────────────────────────────────────
def explain_sql(llm, sql: str, question: str) -> str:
    prompt = f"""Explain this SQL query in 2-3 simple sentences for a non-technical person.

ORIGINAL QUESTION: {question}
SQL QUERY: {sql}

Give a clear, simple explanation. No technical jargon."""
    return llm.invoke(prompt).strip()


# ─── SQL Execution ────────────────────────────────────────────────────────────
def run_sql_sqlite(db_path: str, sql: str) -> dict:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        conn.close()
        return {"success": True, "columns": columns, "data": rows,
                "row_count": len(rows), "col_count": len(columns), "error": None}
    except Exception as e:
        return {"success": False, "columns": [], "data": None,
                "row_count": 0, "col_count": 0, "error": str(e)}


def run_sql_mysql(host, port, user, password, database, sql: str) -> dict:
    try:
        conn, error = get_mysql_connection(host, port, user, password, database)
        if not conn:
            return {"success": False, "columns": [], "data": None,
                    "row_count": 0, "col_count": 0, "error": error}
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        conn.close()
        return {"success": True, "columns": columns, "data": rows,
                "row_count": len(rows), "col_count": len(columns), "error": None}
    except Exception as e:
        return {"success": False, "columns": [], "data": None,
                "row_count": 0, "col_count": 0, "error": str(e)}


def run_sql(db_config: dict, sql: str) -> dict:
    if db_config["type"] == "sqlite":
        return run_sql_sqlite(db_config["path"], sql)
    else:
        return run_sql_mysql(
            db_config["host"], db_config["port"],
            db_config["user"], db_config["password"],
            db_config["database"], sql
        )


# ─── Auto-fix SQL ─────────────────────────────────────────────────────────────
def fix_sql(llm, sql: str, error: str, schema: str, db_type: str = "sqlite") -> str:
    syntax = "MySQL" if db_type == "mysql" else "SQLite"
    prompt = f"""Fix this {syntax} SQL query that has an error.

SCHEMA:
{schema}

BROKEN SQL:
{sql}

ERROR:
{error}

Return only the fixed SQL wrapped in ```sql``` block."""
    response = llm.invoke(prompt)
    return extract_sql(response)


# ─── Main Pipeline ────────────────────────────────────────────────────────────
def generate_and_run_query(question: str, db_config: dict) -> dict:
    llm = get_llm()
    db_type = db_config["type"]
    schema = get_schema_compact(db_config)

    sql = generate_sql(llm, question, schema, db_type)
    result = run_sql(db_config, sql)

    if not result["success"]:
        fixed_sql = fix_sql(llm, sql, result["error"], schema, db_type)
        result = run_sql(db_config, fixed_sql)
        sql = fixed_sql

    explanation = explain_sql(llm, sql, question)

    return {
        **result,
        "sql": sql,
        "explanation": explanation,
        "question": question
    }
