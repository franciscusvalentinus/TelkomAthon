import streamlit as st
import requests
import pandas as pd
import io

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="LDD AI Assistant — Telkom", page_icon="🎓", layout="wide")


# ── Helpers ───────────────────────────────────────────────────────────────────

def api_request(method: str, endpoint: str, token: str = None, **kwargs):
    """Make HTTP request to FastAPI with optional Bearer token."""
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = "Bearer " + token
    clean_endpoint = endpoint.strip().lstrip("/")
    url = API_BASE + "/" + clean_endpoint
    try:
        resp = getattr(requests, method)(url, headers=headers, allow_redirects=False, **kwargs)
        return resp
    except requests.exceptions.ConnectionError:
        st.error("Tidak dapat terhubung ke server. Pastikan FastAPI sudah berjalan di port 8000.")
        return None


def df_to_csv_download(df: pd.DataFrame, filename: str):
    """Return a download button for a DataFrame as CSV."""
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label="⬇️ Download CSV", data=csv, file_name=filename, mime="text/csv")


# ── Session State Init ────────────────────────────────────────────────────────

for key, default in [("token", None), ("user_email", ""), ("logged_in", False)]:
    if key not in st.session_state:
        st.session_state[key] = default


# ── Auth Gate ─────────────────────────────────────────────────────────────────

def page_auth():
    st.title("🎓 AI Learning Assistant — Telkom")
    st.caption("Powered by Azure OpenAI GPT-4o")
    st.divider()

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", use_container_width=True):
            resp = api_request("post", "/auth/login", data={"username": email, "password": password})
            if resp and resp.status_code == 200:
                data = resp.json()
                st.session_state["token"] = data["access_token"]
                st.session_state["user_email"] = email
                st.session_state["logged_in"] = True
                st.rerun()
            elif resp:
                st.error(resp.json().get("detail", "Login gagal"))

    with tab_register:
        full_name = st.text_input("Nama Lengkap", key="reg_name")
        reg_email = st.text_input("Email", key="reg_email")
        reg_pass = st.text_input("Password", type="password", key="reg_pass")
        reg_pass2 = st.text_input("Konfirmasi Password", type="password", key="reg_pass2")
        if st.button("Daftar", use_container_width=True):
            if reg_pass != reg_pass2:
                st.error("Password tidak cocok")
            else:
                resp = api_request("post", "/auth/register", json={
                    "email": reg_email, "password": reg_pass, "full_name": full_name
                })
                if resp and resp.status_code == 201:
                    # Auto-login
                    login_resp = api_request("post", "/auth/login", data={"username": reg_email, "password": reg_pass})
                    if login_resp and login_resp.status_code == 200:
                        st.session_state["token"] = login_resp.json()["access_token"]
                        st.session_state["user_email"] = reg_email
                        st.session_state["logged_in"] = True
                        st.rerun()
                elif resp:
                    st.error(resp.json().get("detail", "Registrasi gagal"))


# ── Pages ─────────────────────────────────────────────────────────────────────

def page_upload():
    st.title("📁 Upload Dokumen Referensi")
    token = st.session_state["token"]

    uploaded = st.file_uploader(
        "Pilih file (PDF, PPTX, DOCX, XLSX)", type=["pdf", "pptx", "docx", "xlsx"],
        accept_multiple_files=True
    )
    if st.button("Upload & Proses", disabled=not uploaded):
        with st.spinner("Memproses dan membuat embedding..."):
            files = [("files", (f.name, f.getvalue(), f.type)) for f in uploaded]
            resp = api_request("post", "/upload", token=token, files=files)
        if resp and resp.status_code == 200:
            st.success(f"Berhasil mengupload {len(resp.json()['uploaded'])} file.")
        elif resp:
            st.error(resp.json().get("detail", "Upload gagal"))

    st.divider()
    st.subheader("Dokumen Tersimpan")
    resp = api_request("get", "/documents", token=token)
    if resp and resp.status_code == 200:
        docs = resp.json()
        if docs:
            st.dataframe(pd.DataFrame(docs), use_container_width=True)
        else:
            st.info("Belum ada dokumen. Upload dokumen terlebih dahulu.")


def page_syllabus():
    st.title("📋 Generate Draft Silabus")
    token = st.session_state["token"]

    # Get document list
    resp = api_request("get", "/documents", token=token)
    docs = resp.json() if resp and resp.status_code == 200 else []
    doc_options = {d["filename"]: d["document_id"] for d in docs}

    topic = st.text_input("Topik Pelatihan", placeholder="contoh: Workflow Optimization")
    level = st.selectbox("Target Level", ["All Levels", "Beginner", "Intermediate", "Advanced", "Mastery"])
    selected_docs = st.multiselect("Dokumen Referensi (opsional)", list(doc_options.keys()))
    doc_ids = [doc_options[d] for d in selected_docs]

    if st.button("Generate Silabus", disabled=not topic):
        with st.spinner("AI sedang menyusun silabus..."):
            resp = api_request("post", "/syllabus/generate", token=token, json={
                "topic": topic, "level": level, "document_ids": doc_ids
            })
        if resp and resp.status_code == 200:
            result = resp.json()["result"]
            df = pd.DataFrame(result)
            st.success(f"Silabus berhasil dibuat — {len(df)} level")
            st.dataframe(df, use_container_width=True)
            df_to_csv_download(df, f"silabus_{topic.replace(' ', '_')}.csv")
        elif resp:
            st.error(resp.json().get("detail", "Gagal generate silabus"))


def page_decompose():
    st.title("🔬 Dekomposisi Modul Mikro")
    token = st.session_state.get("token")
    if not token:
        st.error("Sesi tidak valid. Silakan logout dan login ulang.")
        return

    resp = api_request("get", "/documents", token=token)
    docs = resp.json() if resp and resp.status_code == 200 else []
    doc_options = {d["filename"]: d["document_id"] for d in docs}

    if not doc_options:
        st.warning("Upload dokumen terlebih dahulu.")
        return

    selected_doc = st.selectbox("Pilih Modul Pelatihan", list(doc_options.keys()))
    guide_doc = st.selectbox("Panduan Microlearning (opsional)", ["— Tidak ada —"] + list(doc_options.keys()))
    guide_id = doc_options.get(guide_doc) if guide_doc != "— Tidak ada —" else None

    if st.button("Decompose"):
        with st.spinner("AI sedang memecah materi..."):
            payload = {
                "document_id": doc_options[selected_doc],
                "guide_document_id": guide_id,
            }
            resp = api_request("post", "/decompose", token=token, json=payload)
        if resp and resp.status_code == 200:
            modules = resp.json()["modules"]
            df = pd.DataFrame(modules)
            total_dur = df["duration_minutes"].sum() if "duration_minutes" in df.columns else 0
            col1, col2 = st.columns(2)
            col1.metric("Total Modul Mikro", len(df))
            col2.metric("Total Durasi", f"{total_dur} menit")
            st.dataframe(df, use_container_width=True)
            df_to_csv_download(df, f"modul_mikro_{selected_doc.replace(' ', '_')}.csv")
        elif resp:
            st.error(f"Error {resp.status_code}: {resp.text}")


def page_recommend():
    st.title("🎯 Rekomendasi Learning Path Personal")
    token = st.session_state["token"]

    participant = st.text_input("Nama Peserta")
    gap = st.text_area("Deskripsi Gap Kompetensi", placeholder="contoh: Belum memahami prinsip lean management dan optimasi proses bisnis")
    top_k = st.slider("Jumlah Rekomendasi", 3, 10, 5)

    if st.button("Generate Rekomendasi", disabled=not (participant and gap)):
        with st.spinner("AI sedang menganalisis gap kompetensi..."):
            resp = api_request("post", "/recommend", token=token, json={
                "participant_name": participant,
                "gap_description": gap,
                "top_k": top_k,
            })
        if resp and resp.status_code == 200:
            recs = resp.json()["recommendations"]
            df = pd.DataFrame(recs)
            total_dur = df["estimated_duration_minutes"].sum() if "estimated_duration_minutes" in df.columns else 0
            st.success(f"Rekomendasi untuk {participant}")
            st.metric("Estimasi Total Durasi", f"{total_dur} menit")
            st.dataframe(df, use_container_width=True)
            df_to_csv_download(df, f"rekomendasi_{participant.replace(' ', '_')}.csv")
        elif resp:
            st.error(resp.json().get("detail", "Gagal generate rekomendasi"))


def page_history():
    st.title("📥 Riwayat & Export")
    token = st.session_state["token"]

    resp = api_request("get", "/history", token=token)
    if not resp or resp.status_code != 200:
        st.error("Gagal memuat riwayat")
        return

    data = resp.json()
    tab1, tab2, tab3 = st.tabs(["📋 Silabus", "🔬 Modul Mikro", "🎯 Rekomendasi"])

    with tab1:
        syllabi = data.get("syllabi", [])
        if syllabi:
            for s in syllabi:
                with st.expander(f"{s['topic']} — {s['level']} ({s['created_at'][:10]})"):
                    df = pd.DataFrame(s["output_json"])
                    st.dataframe(df, use_container_width=True)
                    df_to_csv_download(df, f"silabus_{s['id'][:8]}.csv")
        else:
            st.info("Belum ada silabus yang dibuat.")

    with tab2:
        modules = data.get("micro_modules", [])
        if modules:
            df = pd.DataFrame(modules)
            st.dataframe(df, use_container_width=True)
            df_to_csv_download(df, "semua_modul_mikro.csv")
        else:
            st.info("Belum ada modul mikro yang dibuat.")

    with tab3:
        recs = data.get("recommendations", [])
        if recs:
            for r in recs:
                with st.expander(f"{r['participant_name']} ({r['created_at'][:10]})"):
                    st.caption(f"Gap: {r['gap_input']}")
                    df = pd.DataFrame(r["recommended_modules"])
                    st.dataframe(df, use_container_width=True)
                    df_to_csv_download(df, f"rekomendasi_{r['id'][:8]}.csv")
        else:
            st.info("Belum ada rekomendasi yang dibuat.")


# ── Main Router ───────────────────────────────────────────────────────────────

if not st.session_state["logged_in"]:
    page_auth()
else:
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/Telkom_Indonesia_2013.svg/200px-Telkom_Indonesia_2013.svg.png", width=120)
        st.caption(f"👤 {st.session_state['user_email']}")
        st.divider()
        page = st.radio("Navigasi", [
            "📁 Upload Dokumen",
            "📋 Generate Silabus",
            "🔬 Dekomposisi Modul",
            "🎯 Rekomendasi Personal",
            "📥 Riwayat & Export",
        ])
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            for key in ["token", "user_email", "logged_in"]:
                st.session_state[key] = None if key == "token" else (False if key == "logged_in" else "")
            st.rerun()

    if page == "📁 Upload Dokumen":
        page_upload()
    elif page == "📋 Generate Silabus":
        page_syllabus()
    elif page == "🔬 Dekomposisi Modul":
        page_decompose()
    elif page == "🎯 Rekomendasi Personal":
        page_recommend()
    elif page == "📥 Riwayat & Export":
        page_history()
