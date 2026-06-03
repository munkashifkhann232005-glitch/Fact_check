"""
app.py
------
Fact-Check Agent — Main Streamlit Application
Allows users to upload a PDF and automatically fact-check all claims.
"""

import streamlit as st
import pandas as pd
import time

from pdf_extractor import extract_text_from_pdf, get_pdf_metadata
from claim_extractor import extract_claims_from_text
from verifier import verify_claims
from report_generator import (
    generate_csv_report,
    compute_summary_stats,
    get_status_emoji,
    get_status_color,
)

# ─────────────────────────────────────────────────────────────────────────────
#  Page configuration
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Fact-Check Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
#  Custom CSS — professional dark-accent theme
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Global ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #ffffff; }

    /* Main content area */
    .main .block-container {
        background-color: #ffffff;
    }

    /* ── Header banner ── */
    .hero-header {
        background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
        border-radius: 16px;
        padding: 2.5rem 2rem;
        margin-bottom: 2rem;
        border: 1px solid #bfdbfe;
        text-align: center;
    }
    .hero-header h1 { color: #ffffff; font-size: 2.4rem; font-weight: 700; margin: 0; }
    .hero-header p  { color: #dbeafe; font-size: 1.05rem; margin: 0.5rem 0 0; }

    /* ── Section cards ── */
    .section-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #e5e7eb;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* ── Status badges ── */
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .badge-verified     { background:#dcfce7; color:#166534; }
    .badge-inaccurate   { background:#ffedd5; color:#9a3412; }
    .badge-false        { background:#fee2e2; color:#991b1b; }
    .badge-unverifiable { background:#f1f5f9; color:#475569; }

    /* ── Metric cards ── */
    .metric-grid { display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:1.5rem; }
    .metric-card {
        flex:1; min-width:110px;
        background:#f8fafc;
        border-radius:10px;
        padding:1rem;
        text-align:center;
        border:1px solid #e2e8f0;
    }
    .metric-value { font-size:2rem; font-weight:700; line-height:1; color: #1e293b; }
    .metric-label { font-size:0.78rem; color:#64748b; margin-top:4px; }

    /* ── Claim row cards ── */
    .claim-card {
        background:#ffffff;
        border-radius:10px;
        padding:1rem 1.2rem;
        margin-bottom:0.75rem;
        border-left: 4px solid #3b82f6;
        border-top: 1px solid #e5e7eb;
        border-right: 1px solid #e5e7eb;
        border-bottom: 1px solid #e5e7eb;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .claim-text  { font-size:0.92rem; color:#1e293b; font-weight:500; margin-bottom:0.4rem; }
    .claim-meta  { font-size:0.82rem; color:#64748b; }
    .claim-source a { color:#2563eb; text-decoration:none; }
    .claim-source a:hover { text-decoration:underline; }

    /* ── Progress ── */
    .stProgress > div > div > div { background-color: #2563eb !important; }

    /* ── Upload area ── */
    .upload-hint { font-size:0.85rem; color:#6c757d; margin-top:0.5rem; }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] { 
        background: #f8f9fa; 
        border-right: 1px solid #e5e7eb;
    }

    /* Sidebar text */
    section[data-testid="stSidebar"] .stMarkdown {
        color: #1e293b;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg,#2563eb,#1d4ed8);
        color:#fff;
        border:none;
        border-radius:8px;
        font-weight:600;
        padding:0.5rem 1.5rem;
    }
    .stButton > button:hover { opacity:0.9; background: #1d4ed8; }

    div[data-testid="stDownloadButton"] > button {
        background: linear-gradient(135deg,#059669,#047857) !important;
    }

    /* Headers text color */
    h1, h2, h3, h4, .stMarkdown {
        color: #1e293b;
    }

    /* File uploader */
    .stFileUploader {
        background-color: #f8fafc;
        border: 1px dashed #cbd5e1;
        border-radius: 12px;
        padding: 1rem;
    }
</style>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Load API keys from Streamlit secrets (hidden from users)
# ─────────────────────────────────────────────────────────────────────────────
gemini_api_key = st.secrets["GEMINI_API_KEY"]
tavily_api_key = st.secrets["TAVILY_API_KEY"]


# ─────────────────────────────────────────────────────────────────────────────
#  Sidebar — Instructions only (no API key inputs)
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📋 How it works")
    st.markdown("""
1. 📤 Upload a PDF document
2. 📝 AI extracts factual claims
3. 🔎 Web evidence is gathered
4. ✅ Each claim is classified
5. 📊 Download the full report
    """)

    st.markdown("---")
    st.markdown("### 🏷️ Status Legend")
    st.markdown("""
- ✅ **Verified** — Claim confirmed  
- ⚠️ **Inaccurate** — Partially wrong  
- ❌ **False** — Claim contradicted  
- ❓ **Unverifiable** — Insufficient data  
    """)

    st.markdown("---")
    st.caption("Built with Gemini · Tavily · Streamlit")


# ─────────────────────────────────────────────────────────────────────────────
#  Hero header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-header">
    <h1>🔍 Fact-Check Agent</h1>
    <p>Upload any PDF and automatically verify every factual claim using AI + live web search.</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Helper: validate API keys
# ─────────────────────────────────────────────────────────────────────────────
def validate_keys() -> bool:
    if not gemini_api_key or gemini_api_key == "":
        st.error("🔑 Gemini API key not found. Please check your Streamlit secrets.")
        return False
    if not tavily_api_key or tavily_api_key == "":
        st.error("🔑 Tavily API key not found. Please check your Streamlit secrets.")
        return False
    return True


# ─────────────────────────────────────────────────────────────────────────────
#  Step 1 — PDF Upload
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📤 Step 1 — Upload PDF Document</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Drop your PDF here or click to browse",
    type=["pdf"],
    label_visibility="collapsed",
)
st.markdown('<p class="upload-hint">Supported format: PDF · Max recommended size: 10 MB</p>', unsafe_allow_html=True)

if uploaded_file:
    metadata = get_pdf_metadata(uploaded_file)
    uploaded_file.seek(0)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📄 Pages",    metadata["page_count"])
    with col2:
        st.metric("💾 File Size", f"{metadata['file_size_kb']} KB")
    with col3:
        st.metric("📝 Title",    metadata["title"][:20] + "…" if len(metadata["title"]) > 20 else metadata["title"])
    with col4:
        st.metric("✍️ Author",   metadata["author"][:20] + "…" if len(metadata["author"]) > 20 else metadata["author"])

    st.markdown("---")

    # ─── Run Analysis button ─────────────────────────────────────────────────
    run_btn = st.button("🚀 Start Fact-Check Analysis", use_container_width=True)

    if run_btn:
        if not validate_keys():
            st.stop()

        # ── Step 2: Extract PDF text ────────────────────────────────────────
        with st.status("📖 Extracting text from PDF…", expanded=True) as status_box:
            try:
                pdf_text = extract_text_from_pdf(uploaded_file)
                st.write(f"✅ Extracted {len(pdf_text):,} characters from {metadata['page_count']} page(s).")
                status_box.update(label="Text extracted!", state="complete")
            except ValueError as e:
                st.error(f"❌ PDF Error: {e}")
                st.stop()
                # ── Step 3: Extract claims ───────────────────────────────────────────
        with st.status("🧠 Identifying factual claims with Gemini…", expanded=True) as status_box:
           try:
               claims = extract_claims_from_text(pdf_text, gemini_api_key)
               st.write(f"✅ Found **{len(claims)}** verifiable claim(s).")
        MAX_CLAIMS = 5
        if len(claims) > MAX_CLAIMS:
            st.warning(f"⚠️ Found {len(claims)} claims. Due to API rate limits (20 requests/day), only the first {MAX_CLAIMS} will be verified.")
            claims = claims[:MAX_CLAIMS]
            st.info(f"💡 To verify more claims, wait for daily quota reset at Pacific Time midnight or upgrade to a paid tier.")
        
        status_box.update(label=f"{len(claims)} claims identified!", state="complete")
    except ValueError as e:
        st.error(f"❌ Claim Extraction Error: {e}")
        st.stop()

        # Preview extracted claims
        with st.expander(f"📋 View {len(claims)} Extracted Claims", expanded=False):
            for i, claim in enumerate(claims, 1):
                st.markdown(f"**{i}.** {claim}")

        # ── Step 4 & 5: Verify each claim ───────────────────────────────────
        st.markdown("### 🔎 Verifying Claims…")
        progress_bar   = st.progress(0)
        progress_label = st.empty()
        verdicts       = []

        def update_progress(current, total, claim_text):
            pct = int((current / total) * 100) if total else 0
            progress_bar.progress(pct)
            if current < total:
                short = claim_text[:70] + "…" if len(claim_text) > 70 else claim_text
                progress_label.markdown(f"🔍 Checking claim {current + 1}/{total}: *{short}*")
            else:
                progress_label.markdown("✅ All claims verified!")

        try:
            verdicts = verify_claims(
                claims,
                gemini_api_key,
                tavily_api_key,
                progress_callback=update_progress,
            )
        except Exception as e:
            st.error(f"❌ Verification error: {e}")
            st.stop()

        # Save to session state
        st.session_state["verdicts"]       = verdicts
        st.session_state["document_name"]  = uploaded_file.name

        st.success(f"🎉 Fact-check complete! {len(verdicts)} claim(s) analysed.")
        time.sleep(0.5)
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
#  Step 6 — Display results (persisted in session state)
# ─────────────────────────────────────────────────────────────────────────────
if "verdicts" in st.session_state and st.session_state["verdicts"]:
    verdicts      = st.session_state["verdicts"]
    document_name = st.session_state.get("document_name", "document.pdf")

    st.markdown("---")
    st.markdown("## 📊 Fact-Check Results")

    # ── Summary metrics ──────────────────────────────────────────────────────
    stats   = compute_summary_stats(verdicts)
    total   = len(verdicts)
    counts  = {
        "Verified":     sum(1 for v in verdicts if v["status"] == "Verified"),
        "Inaccurate":   sum(1 for v in verdicts if v["status"] == "Inaccurate"),
        "False":        sum(1 for v in verdicts if v["status"] == "False"),
        "Unverifiable": sum(1 for v in verdicts if v["status"] == "Unverifiable"),
    }

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value" style="color:#60a5fa">{total}</div>
            <div class="metric-label">Total Claims</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value" style="color:#22c55e">{counts['Verified']}</div>
            <div class="metric-label">✅ Verified</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value" style="color:#f97316">{counts['Inaccurate']}</div>
            <div class="metric-label">⚠️ Inaccurate</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value" style="color:#ef4444">{counts['False']}</div>
            <div class="metric-label">❌ False</div>
        </div>""", unsafe_allow_html=True)
    with col5:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value" style="color:#94a3b8">{counts['Unverifiable']}</div>
            <div class="metric-label">❓ Unverifiable</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Filter controls ───────────────────────────────────────────────────────
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        filter_status = st.multiselect(
            "Filter by Status",
            options=["Verified", "Inaccurate", "False", "Unverifiable"],
            default=["Verified", "Inaccurate", "False", "Unverifiable"],
        )
    with col_f2:
        view_mode = st.radio("View Mode", ["Cards", "Table"], horizontal=True)

    filtered = [v for v in verdicts if v["status"] in filter_status]
    st.caption(f"Showing {len(filtered)} of {total} claims")

    # ── Results display ───────────────────────────────────────────────────────
    if view_mode == "Cards":
        for v in filtered:
            status  = v["status"]
            emoji   = get_status_emoji(status)
            color   = get_status_color(status)
            source  = v.get("source", "N/A")
            src_html = (
                f'<a href="{source}" target="_blank">{source[:70]}…</a>'
                if source and source != "N/A" and source.startswith("http")
                else source
            )
            badge_class = f"badge-{status.lower()}"
            st.markdown(f"""
<div class="claim-card" style="border-left-color:{color};">
    <div class="claim-text">📌 {v['claim']}</div>
    <div style="margin:0.4rem 0;">
        <span class="badge {badge_class}">{emoji} {status}</span>
    </div>
    <div class="claim-meta">💬 {v['explanation']}</div>
    <div class="claim-meta claim-source" style="margin-top:4px;">🔗 {src_html}</div>
</div>""", unsafe_allow_html=True)

    else:  # Table view
        df = pd.DataFrame(filtered)[["claim", "status", "explanation", "source"]]
        df.columns = ["Claim", "Status", "Explanation", "Source"]

        def color_status(val):
            colors = {
                "Verified":     "background-color:#dcfce7;color:#166534",
                "Inaccurate":   "background-color:#ffedd5;color:#9a3412",
                "False":        "background-color:#fee2e2;color:#991b1b",
                "Unverifiable": "background-color:#e2e8f0;color:#475569",
            }
            return colors.get(val, "")

        styled = df.style.map(color_status, subset=["Status"])
        st.dataframe(styled, use_container_width=True, hide_index=True)
    # ── Download report ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📥 Download Report")
    csv_bytes = generate_csv_report(verdicts, document_name)

    st.download_button(
        label="⬇️ Download Full Report (CSV)",
        data=csv_bytes,
        file_name=f"fact_check_report_{document_name.replace('.pdf','')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

else:
    # ── Empty state ───────────────────────────────────────────────────────────
    if not uploaded_file:
        st.markdown("""
<div style="text-align:center;padding:3rem;color:#475569;">
    <div style="font-size:4rem;margin-bottom:1rem;">📄</div>
    <h3 style="color:#64748b;">No document uploaded yet</h3>
    <p>Upload a PDF above to get started. The agent will automatically<br>
    extract and verify every factual claim in your document.</p>
</div>
""", unsafe_allow_html=True)
