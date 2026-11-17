import streamlit as st
from forensic_engine import analyze_uploaded_file
from ai_detector import screen_image_with_ai, screen_video_with_ai
from report_generator import build_json_report, build_html_report, build_pdf_report
from datetime import datetime
import json

st.set_page_config(page_title="TraceLens Forensics", page_icon="🔎", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.4rem; max-width: 1180px;}
.hero {padding: 1.3rem 1.5rem; border: 1px solid rgba(128,128,128,.25); border-radius: 16px; background: linear-gradient(120deg, rgba(31,111,235,.10), rgba(16,185,129,.07));}
.muted {color: #777; font-size: .92rem;}
div[data-testid="stMetric"] {border: 1px solid rgba(128,128,128,.22); padding: 12px; border-radius: 12px;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>🔎 TraceLens Forensics</h1><p>Digital media examination for images and videos</p><span class="muted">Evidence-led triage • Metadata inspection • AI screening • Downloadable reports</span></div>', unsafe_allow_html=True)
st.write("")
st.warning("Forensic triage only. Automated indicators are not proof of authenticity, manipulation, or deception. Preserve original evidence and use validated forensic procedures for consequential decisions.")

with st.sidebar:
    st.header("Examination settings")
    run_ai = st.toggle("Run optional AI screening", value=False, help="Uses Hugging Face models when configured. The first run may download model files and take time.")
    run_video_ai = st.toggle("Run optional video deepfake screening", value=False, disabled=not run_ai)
    st.caption("AI screening is experimental and may be unavailable on some deployments.")

uploaded = st.file_uploader("Upload an image or video", type=["jpg","jpeg","png","webp","bmp","tif","tiff","mp4","mov","avi","mkv","webm"])
if uploaded:
    st.write(f"**Evidence file:** {uploaded.name}  ·  **Size:** {uploaded.size:,} bytes")
    if uploaded.type.startswith("image/"):
        st.image(uploaded, caption="Uploaded evidence", use_container_width=True)
    else:
        st.video(uploaded)

    if st.button("Run forensic examination", type="primary", use_container_width=True):
        with st.spinner("Examining evidence and calculating file hash…"):
            result = analyze_uploaded_file(uploaded.getvalue(), uploaded.name)
            result["analysis_timestamp"] = datetime.now().astimezone().isoformat()
            if run_ai and result.get("media_type") == "image":
                result["ai_screening"] = screen_image_with_ai(uploaded.getvalue())
            elif run_ai and result.get("media_type") == "video" and run_video_ai:
                result["ai_screening"] = screen_video_with_ai(uploaded.getvalue(), uploaded.name)
            st.session_state["last_result"] = result
            st.session_state["last_filename"] = uploaded.name

if "last_result" in st.session_state:
    result = st.session_state["last_result"]
    st.divider()
    st.subheader("Examination result")
    st.success("Examination completed. Review the findings below; do not interpret indicators as a definitive verdict.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Media type", result.get("media_type", "Unknown").title())
    c2.metric("SHA-256", (result.get("file_facts", {}).get("sha256", "N/A"))[:16] + "…")
    c3.metric("File size", f'{result.get("file_facts", {}).get("size_bytes", 0):,} bytes')

    st.markdown("#### Summary")
    st.write(result.get("summary", "No summary available."))
    if result.get("findings"):
        st.markdown("#### Forensic findings")
        for item in result["findings"]:
            st.write(f"• {item}")
    if result.get("metadata"):
        with st.expander("Metadata and technical details", expanded=False):
            st.json(result["metadata"])
    if result.get("ai_screening"):
        with st.expander("Optional AI screening", expanded=True):
            st.json(result["ai_screening"])
    if result.get("limitations"):
        with st.expander("Limitations and interpretation"):
            for item in result["limitations"]:
                st.write(f"• {item}")

    st.divider()
    st.subheader("Download examination report")
    json_bytes = build_json_report(result)
    html_bytes = build_html_report(result)
    pdf_bytes = build_pdf_report(result)
    d1, d2, d3 = st.columns(3)
    stem = st.session_state.get("last_filename", "evidence").rsplit(".", 1)[0]
    d1.download_button("Download JSON", json_bytes, file_name=f"{stem}_forensic_report.json", mime="application/json", use_container_width=True)
    d2.download_button("Download HTML", html_bytes, file_name=f"{stem}_forensic_report.html", mime="text/html", use_container_width=True)
    d3.download_button("Download PDF", pdf_bytes, file_name=f"{stem}_forensic_report.pdf", mime="application/pdf", use_container_width=True)

st.divider()
st.caption("TraceLens Forensics • Treat original files as evidence. Work on copies, document chain of custody, and corroborate automated findings with qualified examination.")
