import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import json
import hashlib
import os
import sys
import traceback
from io import BytesIO

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PIL import Image

logo_icon = Image.open("assets/logo.png")

st.set_page_config(
    page_title="Resumind",
    page_icon=logo_icon,
    layout="wide"
)

# --- Splash screen (shows once per session) ---
if "splash_shown" not in st.session_state:
    st.session_state.splash_shown = False

if not st.session_state.splash_shown:
    splash = st.empty()
    with splash.container():
        col_a, col_b, col_c = st.columns([1, 1, 1])
        with col_b:
            st.markdown("<div style='margin-top:150px;'></div>", unsafe_allow_html=True)
            st.image("assets/logo.png", use_container_width=True)
            st.markdown(
                "<p style='text-align:center; color:#888; margin-top:10px;'>Loading Resumind...</p>",
                unsafe_allow_html=True
            )
    time.sleep(1.5)
    splash.empty()
    st.session_state.splash_shown = True
# --- Try importing real backend modules; fall back to dummy mode if missing ---
BACKEND_READY = True
BACKEND_ERROR = ""
try:
    from src.pdf_parser import extract_text as extract_pdf_text
    from src.jd_parser import extract_skills as extract_jd_skills
    from src.jd_resume_matcher import evaluate_candidate
except Exception:
    BACKEND_READY = False
    BACKEND_ERROR = traceback.format_exc()

# --- Custom CSS ---
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #0E1117 0%, #1a1f2e 100%);
        padding: 28px 32px;
        border-radius: 12px;
        margin-bottom: 25px;
    }
    .main-header h1 { color: white; margin-bottom: 5px; }
    .main-header p { color: #A0A0A0; font-size: 16px; margin: 0; }

    div[data-testid="stMetric"] {
        background-color: #F8F9FB;
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #E8E8E8;
    }

    section[data-testid="stSidebar"] button {
        background-color: #1E2530;
        color: white !important;
        border: 1px solid #2E3744;
        border-radius: 8px;
    }
    section[data-testid="stSidebar"] button:hover {
        background-color: #2A3340;
        border-color: #3E4A5C;
    }

    .candidate-card {
        background-color: #FFFFFF;
        border: 1px solid #E8E8E8;
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 12px;
    }
    .rank-badge {
        display: inline-block;
        background-color: #0E1117;
        color: white;
        border-radius: 50%;
        width: 28px;
        height: 28px;
        text-align: center;
        line-height: 28px;
        font-weight: bold;
        margin-right: 10px;
    }
    .skill-tag-match {
        background-color: #E6F4EA;
        color: #1E7E34;
        padding: 4px 10px;
        border-radius: 14px;
        font-size: 13px;
        margin: 3px;
        display: inline-block;
    }
    .skill-tag-missing {
        background-color: #FBE9E7;
        color: #C62828;
        padding: 4px 10px;
        border-radius: 14px;
        font-size: 13px;
        margin: 3px;
        display: inline-block;
    }
    </style>
""", unsafe_allow_html=True)

# =================== AUTH ===================
USERS_FILE = "data/users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    os.makedirs("data", exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def auth_screen():
    if st.session_state.get("authenticated"):
        return True

    col_a, col_b, col_c = st.columns([0.7, 1, 0.7])
    with col_b:
        st.image("assets/logo.png", use_container_width=True)
    st.markdown("""
        <div style="text-align:center; margin-top:-10px;">
            <p style="color:#888;">Recruiter Dashboard — Restricted Access</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        users = load_users()

        with tab1:
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Login", use_container_width=True):
                if username in users and users[username] == hash_password(password):
                    st.session_state["authenticated"] = True
                    st.session_state["current_user"] = username
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

        with tab2:
            new_username = st.text_input("Choose a username", key="signup_user")
            new_password = st.text_input("Choose a password", type="password", key="signup_pass")
            confirm_password = st.text_input("Confirm password", type="password", key="signup_confirm")
            if st.button("Create Account", use_container_width=True):
                if not new_username or not new_password:
                    st.error("Username and password cannot be empty.")
                elif new_username in users:
                    st.error("Username already exists. Please log in instead.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    users[new_username] = hash_password(new_password)
                    save_users(users)
                    st.success("Account created! Please log in using the Login tab.")

    return False

if not auth_screen():
    st.stop()

# =================== SESSION STATE ===================
if "resumes" not in st.session_state:
    st.session_state.resumes = []
if "jd_file" not in st.session_state:
    st.session_state.jd_file = None
if "jd_text" not in st.session_state:
    st.session_state.jd_text = None
if "jd_skills" not in st.session_state:
    st.session_state.jd_skills = []
if "analyzed" not in st.session_state:
    st.session_state.analyzed = False
if "results" not in st.session_state:
    st.session_state.results = []

# =================== BACKEND HELPERS ===================
def get_dummy_results(resumes):
    sample = [
        {"Candidate": "John Doe", "Score": 94, "Matched": ["Python", "SQL", "Git", "Machine Learning"], "Missing": ["AWS"]},
        {"Candidate": "Alice Smith", "Score": 88, "Matched": ["Python", "SQL"], "Missing": ["AWS", "Git"]},
        {"Candidate": "Bob Lee", "Score": 76, "Matched": ["Python"], "Missing": ["SQL", "AWS", "Git"]},
        {"Candidate": "Charlie Kim", "Score": 65, "Matched": ["SQL"], "Missing": ["Python", "AWS"]},
    ]
    results = []
    for i, f in enumerate(resumes):
        base = sample[i % len(sample)]
        results.append({"Candidate": f.name, "Score": base["Score"], "Matched": base["Matched"], "Missing": base["Missing"]})
    return sorted(results, key=lambda x: x["Score"], reverse=True)

def save_uploaded_file(uploaded_file, folder):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, uploaded_file.name)
    uploaded_file.seek(0)
    with open(path, "wb") as out:
        out.write(uploaded_file.read())
    return path

def extract_text_any(uploaded_file, save_folder):
    """Extract text from an uploaded PDF or TXT file."""
    if uploaded_file.name.lower().endswith(".pdf"):
        path = save_uploaded_file(uploaded_file, save_folder)
        return extract_pdf_text(path)
    else:
        uploaded_file.seek(0)
        raw_bytes = uploaded_file.read()
        try:
            return raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return raw_bytes.decode("latin-1", errors="ignore")


def get_real_results(resumes, jd_text):
    jd_skills = extract_jd_skills(jd_text)
    st.session_state.jd_skills = jd_skills

    candidates = []
    for f in resumes:
        resume_text = extract_text_any(f, "data/resumes")

        if not resume_text or not resume_text.strip():
            candidates.append({
                "Candidate": f.name,
                "Score": 0,
                "Matched": [],
                "Missing": jd_skills,
            })
            continue

        match_result = evaluate_candidate(jd_text, jd_skills, resume_text)

        candidates.append({
            "Candidate": f.name,
            "Score": match_result["score"],
            "Matched": match_result["matched"],
            "Missing": match_result["missing"],
        })

    return sorted(candidates, key=lambda x: x["Score"], reverse=True)

def recommendation(score):
    if score >= 85:
        return "Highly Recommended", "success"
    elif score >= 70:
        return "Recommended", "info"
    else:
        return "Needs Review", "warning"

# =================== SIDEBAR ===================
with st.sidebar:
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image("assets/logo.png", width=45)
    with col2:
        st.markdown("### Resumind")
    st.caption(f"Logged in as **{st.session_state.get('current_user', 'Guest')}**")
    if st.button("Logout"):
        st.session_state["authenticated"] = False
        st.rerun()
    st.divider()
    page = st.radio("Navigate", ["Dashboard", "Upload", "Results", "Compare"], label_visibility="collapsed")
    st.divider()
    if not BACKEND_READY:
        st.warning("Backend modules not fully wired — using demo data.")
        with st.expander("Show error details"):
            st.code(BACKEND_ERROR)
    st.caption("Hackathon Build · Python Track")

# =================== HEADER ===================
st.markdown("""
    <div class="main-header">
        <h1>📄 Intelligent Resume Screening Platform</h1>
        <p>Upload resumes and a job description to automatically extract skills,
        match candidates, and rank them with explainable scores.</p>
    </div>
""", unsafe_allow_html=True)

results = st.session_state.results if st.session_state.analyzed else []

# =================== DASHBOARD ===================
if page == "Dashboard":
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Resumes Processed", len(st.session_state.resumes))
    col2.metric("Avg Match Score", f"{int(sum(r['Score'] for r in results)/len(results))}%" if results else "0%")
    col3.metric("Top Candidate", results[0]["Candidate"] if results else "—")
    col4.metric("JD Loaded", "Yes" if st.session_state.jd_file else "No")

    st.divider()

    if results:
        c1, c2 = st.columns([2, 1])
        with c1:
            df = pd.DataFrame(results)
            fig = px.bar(df, x="Candidate", y="Score", color="Score",
                         color_continuous_scale="Tealgrn", title="Candidate Match Scores")
            fig.update_layout(showlegend=False, height=380)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig2 = go.Figure(go.Pie(
                labels=["Highly Recommended", "Recommended", "Needs Review"],
                values=[
                    sum(1 for r in results if r["Score"] >= 85),
                    sum(1 for r in results if 70 <= r["Score"] < 85),
                    sum(1 for r in results if r["Score"] < 70),
                ],
                hole=0.5,
                marker_colors=["#1E7E34", "#0288D1", "#F9A825"]
            ))
            fig2.update_layout(title="Recommendation Split", height=380, showlegend=True)
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Go to **Upload** to add resumes and a job description, then run analysis.")

# =================== UPLOAD ===================
elif page == "Upload":
    st.header("Upload Files")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Candidate Resumes")
        resumes = st.file_uploader(
            "Upload one or more resumes (PDF)",
            type=["pdf"],
            accept_multiple_files=True
        )
        if resumes:
            st.session_state.resumes = resumes
            st.success(f"{len(resumes)} resume(s) uploaded")

    with col2:
        st.subheader("Job Description")
        jd = st.file_uploader("Upload the job description (PDF or TXT)", type=["pdf", "txt"])
        if jd:
            st.session_state.jd_file = jd
            try:
                if BACKEND_READY:
                    jd_text = extract_text_any(jd, "data/job_descriptions")
                else:
                    jd.seek(0)
                    raw_bytes = jd.read()
                    try:
                        jd_text = raw_bytes.decode("utf-8")
                    except UnicodeDecodeError:
                        jd_text = raw_bytes.decode("latin-1", errors="ignore")
                st.session_state.jd_text = jd_text
                st.success("Job description uploaded")
            except Exception as e:
                st.session_state.jd_text = None
                st.warning(f"Job description uploaded, but text extraction failed: {e}")

    st.divider()

    if st.button("🚀 Analyze Candidates", type="primary", use_container_width=True):
        if not st.session_state.resumes or not st.session_state.jd_file:
            st.error("Please upload at least one resume and a job description first.")
        else:
            progress = st.progress(0, text="Analyzing resumes...")
            for i in range(60):
                time.sleep(0.01)
                progress.progress(i + 1, text="Analyzing resumes...")

            try:
                if BACKEND_READY and st.session_state.jd_text:
                    progress.progress(70, text="Extracting skills and computing scores...")
                    results = get_real_results(st.session_state.resumes, st.session_state.jd_text)
                else:
                    results = get_dummy_results(st.session_state.resumes)
            except Exception as e:
                st.warning(f"Real analysis failed ({e}). Showing demo data instead.")
                results = get_dummy_results(st.session_state.resumes)

            progress.progress(100, text="Done")
            st.session_state.results = results
            st.session_state.analyzed = True
            st.success("Analysis complete! Go to the Results tab.")

# =================== RESULTS ===================
elif page == "Results":
    st.header("Candidate Rankings")

    if not results:
        st.warning("No analysis yet. Upload files and click Analyze first.")
    else:
        for i, r in enumerate(results, 1):
            label, kind = recommendation(r["Score"])
            st.markdown(f"""
                <div class="candidate-card">
                    <span class="rank-badge">{i}</span>
                    <strong style="font-size:17px;">{r['Candidate']}</strong>
                    <span style="float:right; font-weight:bold; color:#0E1117;">{r['Score']}%</span>
                </div>
            """, unsafe_allow_html=True)

            with st.expander(f"View details — {r['Candidate']}"):
                cA, cB = st.columns(2)
                with cA:
                    st.markdown("**Matched Skills**")
                    st.markdown("".join(f'<span class="skill-tag-match">✔ {s}</span>' for s in r["Matched"]) or "None", unsafe_allow_html=True)
                with cB:
                    st.markdown("**Missing Skills**")
                    st.markdown("".join(f'<span class="skill-tag-missing">✘ {s}</span>' for s in r["Missing"]) or "None", unsafe_allow_html=True)
                getattr(st, kind)(f"Recommendation: {label}")

        st.divider()
        st.subheader("Shortlist & Export")

        min_score = st.slider("Minimum match score to shortlist", 0, 100, 70)
        shortlisted = [r for r in results if r["Score"] >= min_score]
        st.caption(f"{len(shortlisted)} of {len(results)} candidates meet this threshold.")

        if shortlisted:
            export_rows = []
            for r in shortlisted:
                label, _ = recommendation(r["Score"])
                export_rows.append({
                    "Candidate": r["Candidate"],
                    "Match Score (%)": r["Score"],
                    "Matched Skills": ", ".join(r["Matched"]),
                    "Missing Skills": ", ".join(r["Missing"]) or "None",
                    "Recommendation": label,
                })
            df_export = pd.DataFrame(export_rows)

            colA, colB = st.columns(2)
            with colA:
                st.download_button(
                    "⬇ Download CSV",
                    df_export.to_csv(index=False),
                    "shortlisted_candidates.csv",
                    "text/csv",
                    use_container_width=True
                )
            with colB:
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    df_export.to_excel(writer, index=False, sheet_name="Shortlist")
                    worksheet = writer.sheets["Shortlist"]
                    for i, col in enumerate(df_export.columns):
                        max_len = max(df_export[col].astype(str).map(len).max(), len(col)) + 4
                        worksheet.column_dimensions[chr(65 + i)].width = max_len
                st.download_button(
                    "⬇ Download Excel (.xlsx)",
                    buffer.getvalue(),
                    "shortlisted_candidates.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        else:
            st.info("No candidates meet this score threshold yet.")

# =================== COMPARE ===================
elif page == "Compare":
    st.header("Compare Candidates")

    if len(results) < 2:
        st.warning("Need at least 2 analyzed candidates to compare.")
    else:
        names = [r["Candidate"] for r in results]
        col1, col2 = st.columns(2)
        with col1:
            c1 = st.selectbox("Candidate A", names, index=0)
        with col2:
            c2 = st.selectbox("Candidate B", names, index=1)

        rA = next(r for r in results if r["Candidate"] == c1)
        rB = next(r for r in results if r["Candidate"] == c2)

        colA, colB = st.columns(2)
        for col, r in [(colA, rA), (colB, rB)]:
            with col:
                st.markdown(f"### {r['Candidate']}")
                st.metric("Match Score", f"{r['Score']}%")
                st.markdown("**Matched Skills**")
                st.markdown("".join(f'<span class="skill-tag-match">✔ {s}</span>' for s in r["Matched"]) or "None", unsafe_allow_html=True)
                st.markdown("**Missing Skills**")
                st.markdown("".join(f'<span class="skill-tag-missing">✘ {s}</span>' for s in r["Missing"]) or "None", unsafe_allow_html=True)
                label, kind = recommendation(r["Score"])
                getattr(st, kind)(label)

        st.divider()
        fig = go.Figure()
        fig.add_trace(go.Bar(name=rA["Candidate"], x=["Match Score"], y=[rA["Score"]]))
        fig.add_trace(go.Bar(name=rB["Candidate"], x=["Match Score"], y=[rB["Score"]]))
        fig.update_layout(barmode="group", height=350, title="Score Comparison")
        st.plotly_chart(fig, use_container_width=True)