import streamlit as st
import requests
import pandas as pd
import io
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from export_utils import to_csv, to_xlsx, to_docx, to_pdf, syllabus_to_text, syllabus_to_docx, syllabus_to_pdf

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


def download_buttons(df: pd.DataFrame, basename: str, title: str = "Export"):
    """Render a row of download buttons for CSV, XLSX, DOCX, PDF."""
    cols = st.columns(4)
    with cols[0]:
        st.download_button("⬇️ CSV", data=to_csv(df),
                           file_name=f"{basename}.csv", mime="text/csv")
    with cols[1]:
        st.download_button("⬇️ XLSX", data=to_xlsx(df),
                           file_name=f"{basename}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with cols[2]:
        st.download_button("⬇️ DOCX", data=to_docx(df, title),
                           file_name=f"{basename}.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    with cols[3]:
        st.download_button("⬇️ PDF", data=to_pdf(df, title),
                           file_name=f"{basename}.pdf", mime="application/pdf")


def show_table(df: pd.DataFrame):
    """Display DataFrame with 1-based 'Nomor' index column."""
    display = df.copy().reset_index(drop=True)
    display.index = display.index + 1
    display.index.name = "Nomor"
    st.dataframe(display, use_container_width=True)


def syllabus_download_buttons(final: dict, basename: str):
    """Download buttons khusus silabus — plain text (TXT, DOCX, PDF)."""
    title = f"Silabus: {final.get('course_type', '')} — {final.get('org_profile', {}).get('organization_name', '')}"
    cols = st.columns(3)
    with cols[0]:
        st.download_button("⬇️ TXT", data=syllabus_to_text(final).encode("utf-8"),
                           file_name=f"{basename}.txt", mime="text/plain")
    with cols[1]:
        st.download_button("⬇️ DOCX", data=syllabus_to_docx(final, title),
                           file_name=f"{basename}.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    with cols[2]:
        st.download_button("⬇️ PDF", data=syllabus_to_pdf(final, title),
                           file_name=f"{basename}.pdf", mime="application/pdf")# ── Session State Init ────────────────────────────────────────────────────────

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
            show_table(pd.DataFrame(docs))
        else:
            st.info("Belum ada dokumen. Upload dokumen terlebih dahulu.")


def page_syllabus():
    st.title("📋 Generate Draft Silabus")
    token = st.session_state["token"]

    # ── Session state keys untuk wizard ──────────────────────────────────────
    defaults = {
        "syl_step": 1,
        "syl_org_profile": None,
        "syl_doc_ids": [],
        "syl_course_type": "",
        "syl_tlos": [],
        "syl_selected_tlos": [],
        "syl_performances": [],
        "syl_selected_perfs": [],
        "syl_elos": [],
        "syl_selected_elos": [],
        "syl_final": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    step = st.session_state["syl_step"]

    # Progress indicator
    steps_label = ["1 Profil", "2 Tipe Course", "3 TLO", "4 Performance", "5 ELO", "6 Silabus"]
    cols_prog = st.columns(len(steps_label))
    for i, label in enumerate(steps_label, start=1):
        with cols_prog[i - 1]:
            if i < step:
                st.markdown(f"✅ ~~{label}~~")
            elif i == step:
                st.markdown(f"**🔵 {label}**")
            else:
                st.markdown(f"⬜ {label}")
    st.divider()

    # ── STEP 1: Pilih dokumen profil perusahaan ───────────────────────────────
    if step == 1:
        st.subheader("Langkah 1 — Pilih Dokumen Profil Perusahaan")
        resp = api_request("get", "/documents", token=token)
        docs = resp.json() if resp and resp.status_code == 200 else []
        doc_options = {d["filename"]: d["document_id"] for d in docs}

        if not doc_options:
            st.warning("Belum ada dokumen. Upload dokumen terlebih dahulu di menu Upload Dokumen.")
            return

        selected = st.selectbox(
            "Pilih dokumen profil perusahaan",
            list(doc_options.keys())
        )
        doc_ids = [doc_options[selected]] if selected else []

        if st.button("Generate Silabus →", disabled=not selected, type="primary"):
            with st.spinner("AI sedang membaca dan memahami profil perusahaan..."):
                resp = api_request("post", "/syllabus/analyze-org", token=token,
                                   json={"document_ids": doc_ids})
            if resp and resp.status_code == 200:
                st.session_state["syl_org_profile"] = resp.json()["org_profile"]
                st.session_state["syl_doc_ids"] = doc_ids
                st.session_state["syl_step"] = 2
                st.rerun()
            elif resp:
                st.error(resp.json().get("detail", "Gagal menganalisis dokumen"))

    # ── STEP 2: Tampilkan profil org + pilih tipe course ─────────────────────
    elif step == 2:
        profile = st.session_state["syl_org_profile"]
        st.subheader("Langkah 2 — Profil Perusahaan & Tipe Course")

        with st.expander("📊 Ringkasan Profil Perusahaan", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Perusahaan:** {profile.get('organization_name', '-')}")
                st.markdown(f"**Industri:** {profile.get('industry', '-')}")
                st.markdown(f"**Visi:** {profile.get('vision', '-')}")
                st.markdown(f"**Misi:** {profile.get('mission', '-')}")
            with col2:
                st.markdown("**Prioritas Strategis:**")
                for p in profile.get("strategic_priorities", []):
                    st.markdown(f"- {p}")
                st.markdown("**Kompetensi Inti:**")
                for c in profile.get("core_competencies", []):
                    st.markdown(f"- {c}")
            st.info(f"💡 {profile.get('learning_context', '')}")

        st.subheader("Pilih Jenis Course")
        recommended = profile.get("recommended_course_types", [])
        all_types = ["B2B Sales", "Innovation", "Technology", "Leadership", "Operations",
                     "Customer Experience", "Finance", "HR & People", "Digital Marketing", "Other"]
        # Merge recommended first
        ordered = recommended + [t for t in all_types if t not in recommended]

        course_type = st.selectbox("Tipe Course", ordered)
        if course_type == "Other":
            custom = st.text_input("Ketik tipe course kustom", placeholder="contoh: Agile Project Management")
            final_course_type = custom.strip() if custom.strip() else course_type
        else:
            final_course_type = course_type

        col_back, col_next = st.columns([1, 3])
        with col_back:
            if st.button("← Kembali"):
                st.session_state["syl_step"] = 1
                st.rerun()
        with col_next:
            if st.button("Generate TLO →", type="primary"):
                with st.spinner("AI sedang membuat Terminal Learning Objectives..."):
                    resp = api_request("post", "/syllabus/generate-tlo", token=token, json={
                        "course_type": final_course_type,
                        "org_profile": profile,
                        "document_ids": st.session_state["syl_doc_ids"],
                    })
                if resp and resp.status_code == 200:
                    st.session_state["syl_course_type"] = final_course_type
                    st.session_state["syl_tlos"] = resp.json()["tlos"]
                    st.session_state["syl_step"] = 3
                    st.rerun()
                elif resp:
                    st.error(resp.json().get("detail", "Gagal generate TLO"))

    # ── STEP 3: Pilih TLO ────────────────────────────────────────────────────
    elif step == 3:
        st.subheader("Langkah 3 — Pilih Terminal Learning Objectives (TLO)")
        st.caption(f"Course: **{st.session_state['syl_course_type']}** | Pilih 1 atau lebih TLO yang paling sesuai")

        tlos = st.session_state["syl_tlos"]
        selected_indices = []
        for i, tlo in enumerate(tlos):
            checked = st.checkbox(
                f"**TLO {tlo['tlo_number']}** — {tlo['tlo']}",
                key=f"tlo_check_{i}",
                value=True
            )
            if checked:
                selected_indices.append(i)
            with st.container():
                st.caption(f"📌 Rationale: {tlo['rationale']}")

        col_back, col_next = st.columns([1, 3])
        with col_back:
            if st.button("← Kembali"):
                st.session_state["syl_step"] = 2
                st.rerun()
        with col_next:
            if st.button("Generate Performance Objectives →", disabled=not selected_indices, type="primary"):
                selected_tlos = [tlos[i] for i in selected_indices]
                with st.spinner("AI sedang membuat Performance Objectives..."):
                    resp = api_request("post", "/syllabus/generate-performance", token=token, json={
                        "selected_tlos": selected_tlos,
                        "org_profile": st.session_state["syl_org_profile"],
                        "document_ids": st.session_state["syl_doc_ids"],
                    })
                if resp and resp.status_code == 200:
                    st.session_state["syl_selected_tlos"] = selected_tlos
                    st.session_state["syl_performances"] = resp.json()["performance_objectives"]
                    st.session_state["syl_step"] = 4
                    st.rerun()
                elif resp:
                    st.error(resp.json().get("detail", "Gagal generate Performance Objectives"))

    # ── STEP 4: Pilih Performance Objectives ─────────────────────────────────
    elif step == 4:
        st.subheader("Langkah 4 — Pilih Performance Objectives")
        st.caption("Pilih performance objectives yang paling sesuai / mendekati kebutuhan")

        perfs = st.session_state["syl_performances"]
        selected_indices = []
        for i, p in enumerate(perfs):
            checked = st.checkbox(
                f"**PO {p['perf_number']}** [{p['related_tlo']}] — {p['performance_objective']}",
                key=f"perf_check_{i}",
                value=True
            )
            if checked:
                selected_indices.append(i)
            with st.container():
                st.caption(f"Kondisi: {p['condition']} | Standar: {p['standard']}")

        col_back, col_next = st.columns([1, 3])
        with col_back:
            if st.button("← Kembali"):
                st.session_state["syl_step"] = 3
                st.rerun()
        with col_next:
            if st.button("Generate ELO →", disabled=not selected_indices, type="primary"):
                selected_perfs = [perfs[i] for i in selected_indices]
                with st.spinner("AI sedang membuat Enabling Learning Objectives..."):
                    resp = api_request("post", "/syllabus/generate-elo", token=token, json={
                        "selected_tlos": st.session_state["syl_selected_tlos"],
                        "selected_performances": selected_perfs,
                        "org_profile": st.session_state["syl_org_profile"],
                        "document_ids": st.session_state["syl_doc_ids"],
                    })
                if resp and resp.status_code == 200:
                    st.session_state["syl_selected_perfs"] = selected_perfs
                    st.session_state["syl_elos"] = resp.json()["elos"]
                    st.session_state["syl_step"] = 5
                    st.rerun()
                elif resp:
                    st.error(resp.json().get("detail", "Gagal generate ELO"))

    # ── STEP 5: Pilih ELO ────────────────────────────────────────────────────
    elif step == 5:
        st.subheader("Langkah 5 — Pilih Enabling Learning Objectives (ELO)")
        st.caption("Pilih ELO yang mendukung pencapaian performance objectives")

        elos = st.session_state["syl_elos"]
        selected_indices = []
        for i, e in enumerate(elos):
            checked = st.checkbox(
                f"**ELO {e['elo_number']}** [{e['related_performance']}] — {e['elo']}",
                key=f"elo_check_{i}",
                value=True
            )
            if checked:
                selected_indices.append(i)
            with st.container():
                st.caption(f"Bloom: {e['bloom_level']} | Format: {e['delivery_method']} | Durasi: {e['duration_minutes']} menit")

        col_back, col_next = st.columns([1, 3])
        with col_back:
            if st.button("← Kembali"):
                st.session_state["syl_step"] = 4
                st.rerun()
        with col_next:
            if st.button("Finalisasi Silabus →", disabled=not selected_indices, type="primary"):
                selected_elos = [elos[i] for i in selected_indices]
                with st.spinner("AI sedang merangkum dan menyusun dokumen silabus..."):
                    resp = api_request("post", "/syllabus/finalize", token=token, json={
                        "course_type": st.session_state["syl_course_type"],
                        "org_profile": st.session_state["syl_org_profile"],
                        "selected_tlos": st.session_state["syl_selected_tlos"],
                        "selected_performances": st.session_state["syl_selected_perfs"],
                        "selected_elos": selected_elos,
                    })
                if resp and resp.status_code == 200:
                    st.session_state["syl_selected_elos"] = selected_elos
                    st.session_state["syl_final"] = resp.json()["result"]
                    st.session_state["syl_step"] = 6
                    st.rerun()
                elif resp:
                    st.error(resp.json().get("detail", "Gagal finalisasi silabus"))

    # ── STEP 6: Tampilkan & export silabus final ──────────────────────────────
    elif step == 6:
        final = st.session_state["syl_final"]
        profile = final["org_profile"]
        course_type = final["course_type"]

        st.success(f"Silabus berhasil dibuat — {course_type}")

        with st.expander("📊 Profil Perusahaan", expanded=False):
            st.markdown(f"**{profile.get('organization_name')}** | {profile.get('industry')}")
            st.markdown(f"**Visi:** {profile.get('vision', '-')}")
            st.markdown(f"**Misi:** {profile.get('mission', '-')}")
            st.markdown("**Prioritas Strategis:**")
            for p in profile.get("strategic_priorities", []):
                st.markdown(f"- {p}")
            st.markdown("**Kompetensi Inti:**")
            for c in profile.get("core_competencies", []):
                st.markdown(f"- {c}")
            st.info(profile.get("learning_context", ""))

        st.subheader("Terminal Learning Objectives (TLO)")
        for t in final.get("tlos", []):
            st.markdown(f"**TLO {t.get('tlo_number', '')}.**  {t.get('tlo', '')}")
            st.caption(f"Rationale: {t.get('rationale', '')}")

        st.divider()
        st.subheader("Performance Objectives")
        for po in final.get("performance_objectives", []):
            st.markdown(f"**PO {po.get('perf_number', '')}.** [{po.get('related_tlo', '')}]  {po.get('performance_objective', '')}")
            st.caption(f"Kondisi: {po.get('condition', '')}  |  Standar: {po.get('standard', '')}")

        st.divider()
        st.subheader("Enabling Learning Objectives (ELO)")
        total_dur = sum(e.get("duration_minutes", 0) for e in final.get("elos", []))
        st.metric("Estimasi Total Durasi", f"{total_dur} menit")
        for e in final.get("elos", []):
            st.markdown(f"**ELO {e.get('elo_number', '')}.** [{e.get('related_performance', '')}]  {e.get('elo', '')}")
            st.caption(f"Bloom: {e.get('bloom_level', '')}  |  Metode: {e.get('delivery_method', '')}  |  Durasi: {e.get('duration_minutes', '')} menit")

        st.divider()
        st.subheader("Export Silabus")
        safe_name = course_type.replace(" ", "_").replace("/", "-")
        syllabus_download_buttons(final, f"silabus_{safe_name}")

        st.divider()
        if st.button("🔄 Buat Silabus Baru", type="secondary"):
            for k in defaults:
                st.session_state[k] = defaults[k]
            st.rerun()


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
            show_table(df)
            download_buttons(df, f"modul_mikro_{selected_doc.replace(' ', '_')}", title=f"Modul Mikro: {selected_doc}")
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
            show_table(df)
            download_buttons(df, f"rekomendasi_{participant.replace(' ', '_')}", title=f"Rekomendasi: {participant}")
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
                    output = s["output_json"]
                    if isinstance(output, dict) and "tlos" in output:
                        profile = output.get("org_profile", {})
                        st.caption(f"Perusahaan: {profile.get('organization_name', '-')} | Course: {output.get('course_type', '-')}")

                        st.markdown("**Terminal Learning Objectives (TLO)**")
                        for t in output.get("tlos", []):
                            st.markdown(f"**TLO {t.get('tlo_number', '')}.**  {t.get('tlo', '')}")
                            st.caption(f"Rationale: {t.get('rationale', '')}")

                        st.markdown("**Performance Objectives**")
                        for po in output.get("performance_objectives", []):
                            st.markdown(f"**PO {po.get('perf_number', '')}.** [{po.get('related_tlo', '')}]  {po.get('performance_objective', '')}")
                            st.caption(f"Kondisi: {po.get('condition', '')}  |  Standar: {po.get('standard', '')}")

                        st.markdown("**Enabling Learning Objectives (ELO)**")
                        for e in output.get("elos", []):
                            st.markdown(f"**ELO {e.get('elo_number', '')}.** [{e.get('related_performance', '')}]  {e.get('elo', '')}")
                            st.caption(f"Bloom: {e.get('bloom_level', '')}  |  Metode: {e.get('delivery_method', '')}  |  Durasi: {e.get('duration_minutes', '')} menit")

                        syllabus_download_buttons(output, f"silabus_{s['id'][:8]}")
                    else:
                        # Legacy flat format
                        df = pd.DataFrame(output) if isinstance(output, list) else pd.DataFrame([output])
                        show_table(df)
                        download_buttons(df, f"silabus_{s['id'][:8]}", title=f"Silabus: {s['topic']}")
        else:
            st.info("Belum ada silabus yang dibuat.")

    with tab2:
        groups = data.get("micro_module_groups", [])
        if groups:
            for g in groups:
                label = f"{g['source_filename']} ({g['date']})"
                with st.expander(label):
                    df = pd.DataFrame(g["modules"])
                    total_dur = df["duration_minutes"].sum() if "duration_minutes" in df.columns else 0
                    col1, col2 = st.columns(2)
                    col1.metric("Total Modul Mikro", len(df))
                    col2.metric("Total Durasi", f"{total_dur} menit")
                    show_table(df)
                    safe_name = g["source_filename"].replace(" ", "_")[:40]
                    download_buttons(df, f"modul_mikro_{safe_name}_{g['date']}", title=f"Modul Mikro: {g['source_filename']}")
        else:
            st.info("Belum ada modul mikro yang dibuat.")

    with tab3:
        recs = data.get("recommendations", [])
        if recs:
            for r in recs:
                with st.expander(f"{r['participant_name']} ({r['created_at'][:10]})"):
                    st.caption(f"Gap: {r['gap_input']}")
                    df = pd.DataFrame(r["recommended_modules"])
                    show_table(df)
                    download_buttons(df, f"rekomendasi_{r['id'][:8]}", title=f"Rekomendasi: {r['participant_name']}")
        else:
            st.info("Belum ada rekomendasi yang dibuat.")


# ── Main Router ───────────────────────────────────────────────────────────────

if not st.session_state["logged_in"]:
    page_auth()
else:
    with st.sidebar:
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
