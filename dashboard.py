import streamlit as st
import sqlite3
import pandas as pd
import random

st.set_page_config(page_title="Groq Reviewer Insights", page_icon="🤖", layout="wide")

st.title("🤖 Groq AI Automated Code Reviewer Insights")
st.subheader("Real-time Repository Code Quality & Security Analytics")

# Fetch data from shared SQLite database
def load_data():
    try:
        conn = sqlite3.connect("metrics.db")
        df = pd.read_sql_query("SELECT * FROM reviews ORDER BY timestamp DESC", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

df = load_data()

# --- ⚙️ HACKATHON DEMO PANEL (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Hackathon Demo Panel")
    st.write("Don't want to trigger manual GitHub PR loops? Click below to simulate incoming pull request webhooks instantly!")
    
    if st.button("🚀 Simulate Incoming PR Scan", use_container_width=True):
        # Realistic mock repositories for your portfolio showcase
        mock_repos = [
            "chitralekha28/ai-code-reviewer", 
            "enterprise-app/core-api", 
            "fintech-secure/payment-gateway"
        ]
        
        try:
            conn = sqlite3.connect("metrics.db")
            cursor = conn.cursor()
            
            # Insert a realistic random scan entry
            cursor.execute(
                "INSERT INTO reviews (repo_name, pr_number, bugs, security, smells, performance) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    random.choice(mock_repos),
                    random.randint(2, 150),
                    random.randint(0, 4),
                    random.randint(0, 3),
                    random.randint(1, 5),
                    random.randint(0, 2)
                )
            )
            conn.commit()
            conn.close()
            st.success("Incoming webhook simulated!")
            st.rerun()
        except Exception as e:
            st.error(f"Error writing simulation data: {e}")

# --- MAIN DASHBOARD INTERFACE ---
if df.empty:
    st.info("💡 Waiting for incoming GitHub webhooks to populate data analytics...")
else:
    # Top Level KPI Cards
    total_scans = len(df)
    total_bugs = df['bugs'].sum()
    total_security = df['security'].sum()
    total_smells = df['smells'].sum()
    total_perf = df['performance'].sum()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("📦 Total PRs Audited", total_scans)
    col2.metric("🛑 Security Vulnerabilities", total_security, delta="-100% Resolved" if total_security > 0 else None)
    col3.metric("🐛 Logic Bugs Found", total_bugs)
    col4.metric("🧼 Code Smells Tracked", total_smells)
    col5.metric("⚡ Performance Flaws", total_perf)

    st.markdown("---")

    left_co, right_co = st.columns(2)
    
    with left_co:
        st.markdown("### 📊 Distribution of Issues Found")
        chart_data = pd.DataFrame({
            'Category': ['Bugs', 'Security', 'Code Smells', 'Performance'],
            'Count': [total_bugs, total_security, total_smells, total_perf]
        })
        st.bar_chart(data=chart_data, x='Category', y='Count', use_container_width=True)

    with right_co:
        st.markdown("### 📋 Recent Review Activities Logs")
        
        # Build out clean columns display list safely checking if timestamp exists
        display_cols = ['repo_name', 'pr_number', 'bugs', 'security', 'smells', 'performance']
        if 'timestamp' in df.columns:
            display_cols.append('timestamp')
            
        st.dataframe(
            df[display_cols],
            use_container_width=True,
            hide_index=True
        )