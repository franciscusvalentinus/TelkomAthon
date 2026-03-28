import streamlit as st
import requests
import pandas as pd
import io
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from export_utils import (to_csv, to_xlsx, to_docx, to_pdf,
                          syllabus_to_text, syllabus_to_docx, syllabus_to_pdf,
                          decompose_to_text, decompose_to_docx, decompose_to_pdf,
                          recommend_to_text, recommend_to_docx, recommend_to_pdf,
                          combined_to_docx, combined_to_pdf, combined_to_text,
                          build_timeline, timeline_to_df,
                          decompose_manual_to_docx, decompose_manual_to_pdf,
                          decompose_manual_to_text)

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
    """Display DataFrame with 1-based 'nomor' index column."""
    display = df.copy().reset_index(drop=True)
    display.index = display.index + 1
    display.index.name = "nomor"
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
                           file_name=f"{basename}.pdf", mime="application/pdf")


def decompose_download_buttons(modules: list, basename: str, source_name: str = ""):
    """Download buttons untuk dekomposisi modul — plain text (TXT, DOCX, PDF)."""
    cols = st.columns(3)
    with cols[0]:
        st.download_button("⬇️ TXT", data=decompose_to_text(modules, source_name).encode("utf-8"),
                           file_name=f"{basename}.txt", mime="text/plain")
    with cols[1]:
        st.download_button("⬇️ DOCX", data=decompose_to_docx(modules, source_name),
                           file_name=f"{basename}.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    with cols[2]:
        st.download_button("⬇️ PDF", data=decompose_to_pdf(modules, source_name),
                           file_name=f"{basename}.pdf", mime="application/pdf")


def recommend_download_buttons(recs: list, basename: str, participant: str = "", gap: str = ""):
    """Download buttons untuk rekomendasi — plain text (TXT, DOCX, PDF)."""
    cols = st.columns(3)
    with cols[0]:
        st.download_button("⬇️ TXT", data=recommend_to_text(recs, participant, gap).encode("utf-8"),
                           file_name=f"{basename}.txt", mime="text/plain")
    with cols[1]:
        st.download_button("⬇️ DOCX", data=recommend_to_docx(recs, participant, gap),
                           file_name=f"{basename}.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    with cols[2]:
        st.download_button("⬇️ PDF", data=recommend_to_pdf(recs, participant, gap),
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
        "syl_start_level": 1,
        "syl_current_condition": "",
        "syl_desired_condition": "",
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
        st.subheader("Langkah 1 — Profil Perusahaan")

        input_mode = st.radio(
            "Sumber profil perusahaan",
            ["📄 Upload dokumen profil", "✏️ Tidak ada profil perusahaan?"],
            horizontal=True,
        )

        if input_mode == "📄 Upload dokumen profil":
            resp = api_request("get", "/documents", token=token)
            docs = resp.json() if resp and resp.status_code == 200 else []
            doc_options = {d["filename"]: d["document_id"] for d in docs}

            if not doc_options:
                st.warning("Belum ada dokumen. Upload dokumen terlebih dahulu di menu Upload Dokumen.")
                return

            selected = st.selectbox("Pilih dokumen profil perusahaan", list(doc_options.keys()))
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

        else:  # Manual input
            st.info("Masukkan nama dan industri perusahaan. AI akan membantu melengkapi profil secara otomatis.")
            company_name = st.text_input("Nama Perusahaan", placeholder="contoh: PT Cahaya Langit")
            industry = st.text_input("Industri / Sektor", placeholder="contoh: Teknologi Informasi, Perbankan, Manufaktur")

            can_submit = bool(company_name.strip() and industry.strip())
            if st.button("Generate Silabus →", disabled=not can_submit, type="primary"):
                with st.spinner("AI sedang menyusun profil perusahaan..."):
                    resp = api_request("post", "/syllabus/analyze-org-manual", token=token,
                                       json={"company_name": company_name.strip(),
                                             "industry": industry.strip()})
                if resp and resp.status_code == 200:
                    st.session_state["syl_org_profile"] = resp.json()["org_profile"]
                    st.session_state["syl_doc_ids"] = []
                    st.session_state["syl_step"] = 2
                    st.rerun()
                elif resp:
                    st.error(resp.json().get("detail", "Gagal menyusun profil perusahaan"))

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

        level_labels = {
            1: "Level 1 — Intro",
            2: "Level 2 — Beginner",
            3: "Level 3 — Intermediate",
            4: "Level 4 — Advanced",
            5: "Level 5 — Mastery",
        }
        start_level = st.selectbox(
            "Level Awal Peserta",
            options=list(level_labels.keys()),
            format_func=lambda x: level_labels[x],
            help="Silabus akan mencakup dari level yang dipilih hingga Level 5 — Mastery"
        )
        active_levels = list(range(start_level, 6))
        st.caption(f"Silabus akan mencakup: {', '.join(level_labels[l] for l in active_levels)}")

        with st.expander("📝 Konteks Pelatihan (opsional)", expanded=False):
            current_condition = st.text_area(
                "Kondisi Saat Ini",
                placeholder="contoh: Tim sales belum memahami teknik consultative selling, konversi deal masih rendah, dan kurang percaya diri saat presentasi ke klien enterprise.",
                help="Deskripsikan kendala atau masalah yang sedang dihadapi peserta / perusahaan saat ini"
            )
            desired_condition = st.text_area(
                "Kondisi yang Diinginkan",
                placeholder="contoh: Tim sales mampu melakukan discovery call yang efektif, membangun rapport dengan klien, dan menutup deal dengan win rate minimal 30%.",
                help="Deskripsikan target atau hasil yang ingin dicapai setelah pelatihan"
            )

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
                        "start_level": start_level,
                        "current_condition": current_condition.strip(),
                        "desired_condition": desired_condition.strip(),
                    })
                if resp and resp.status_code == 200:
                    st.session_state["syl_course_type"] = final_course_type
                    st.session_state["syl_start_level"] = start_level
                    st.session_state["syl_current_condition"] = current_condition.strip()
                    st.session_state["syl_desired_condition"] = desired_condition.strip()
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
                        "start_level": st.session_state["syl_start_level"],
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
                        "start_level": st.session_state["syl_start_level"],
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
                        "start_level": st.session_state["syl_start_level"],
                        "current_condition": st.session_state["syl_current_condition"],
                        "desired_condition": st.session_state["syl_desired_condition"],
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

        level_labels = {1: "Intro", 2: "Beginner", 3: "Intermediate", 4: "Advanced", 5: "Mastery"}
        start_level = final.get("start_level", 1)
        active_levels = [f"Level {l} — {level_labels[l]}" for l in range(start_level, 6)]
        st.caption(f"Level: {' → '.join(active_levels)}")

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

        if final.get("current_condition") or final.get("desired_condition"):
            with st.expander("📋 Konteks Pelatihan", expanded=False):
                if final.get("current_condition"):
                    st.markdown(f"**Kondisi Saat Ini:** {final['current_condition']}")
                if final.get("desired_condition"):
                    st.markdown(f"**Kondisi yang Diinginkan:** {final['desired_condition']}")

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


def _render_decompose_result(modules: list, guide_id: str, syllabus_data: dict | None, safe_name: str, manual_meta: dict | None = None):
    """Render hasil dekomposisi modul dan tombol export."""
    total_dur = sum(m.get("duration_minutes", 0) for m in modules)

    # Tampilkan ringkasan profil untuk mode tanpa silabus
    if manual_meta:
        profile = manual_meta.get("org_profile", {})
        course_type_disp = manual_meta.get("course_type", safe_name)
        levels_disp = manual_meta.get("levels_covered", [])
        with st.expander("📊 Profil Perusahaan & Course", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Perusahaan:** {profile.get('organization_name', '-')}")
                st.markdown(f"**Industri:** {profile.get('industry', '-')}")
                st.markdown(f"**Visi:** {profile.get('vision', '-')}")
                st.markdown(f"**Misi:** {profile.get('mission', '-')}")
            with col2:
                st.markdown(f"**Tipe Course:** {course_type_disp}")
                st.markdown(f"**Level:** {' → '.join(levels_disp) if levels_disp else '-'}")
                if profile.get("strategic_priorities"):
                    st.markdown("**Prioritas Strategis:**")
                    for p in profile["strategic_priorities"]:
                        st.markdown(f"- {p}")
            if profile.get("learning_context"):
                st.info(profile["learning_context"])

    col1, col2 = st.columns(2)
    col1.metric("Total Modul Mikro", len(modules))
    col2.metric("Total Durasi", f"{total_dur} menit")
    st.divider()

    for m in modules:
        st.markdown(f"**Modul {m.get('module_number', '')}. {m.get('title', '')}**")
        st.caption(
            f"Format: {m.get('delivery_format', '')}  |  Durasi: {m.get('duration_minutes', '')} menit"
            + (f"  |  Berdasarkan: {m.get('related_elo', '')}" if m.get("related_elo") else "")
        )
        st.markdown(f"**Tujuan:** {m.get('specific_objective', '')}")
        st.markdown(f"**Ringkasan:** {m.get('content_summary', '')}")
        st.divider()

    st.subheader("📅 Timeline Penyelesaian Modul")
    timeline = build_timeline(modules)

    tab_short, tab_long = st.tabs(["⚡ Versi Singkat (2 Modul/Minggu)", "🗓️ Versi Lama (1 Modul/Minggu)"])
    with tab_short:
        df_short = timeline_to_df(timeline["short"])
        show_table(df_short)
    with tab_long:
        df_long = timeline_to_df(timeline["long"])
        show_table(df_long)

    st.subheader("Export")
    safe = safe_name.replace(" ", "_").replace("/", "-")

    if syllabus_data:
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.download_button("⬇️ DOCX (Silabus + Modul)",
                               data=combined_to_docx(syllabus_data, modules),
                               file_name=f"silabus_modul_{safe}.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        with col_b:
            st.download_button("⬇️ PDF (Silabus + Modul)",
                               data=combined_to_pdf(syllabus_data, modules),
                               file_name=f"silabus_modul_{safe}.pdf",
                               mime="application/pdf")
        with col_c:
            st.download_button("⬇️ TXT (Silabus + Modul)",
                               data=combined_to_text(syllabus_data, modules).encode("utf-8"),
                               file_name=f"silabus_modul_{safe}.txt",
                               mime="text/plain")
    else:
        if manual_meta:
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.download_button("⬇️ DOCX (Profil + Modul)",
                                   data=decompose_manual_to_docx(modules, manual_meta),
                                   file_name=f"modul_mikro_{safe}.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            with col_b:
                st.download_button("⬇️ PDF (Profil + Modul)",
                                   data=decompose_manual_to_pdf(modules, manual_meta),
                                   file_name=f"modul_mikro_{safe}.pdf",
                                   mime="application/pdf")
            with col_c:
                st.download_button("⬇️ TXT (Profil + Modul)",
                                   data=decompose_manual_to_text(modules, manual_meta).encode("utf-8"),
                                   file_name=f"modul_mikro_{safe}.txt",
                                   mime="text/plain")
        else:
            decompose_download_buttons(modules, f"modul_mikro_{safe}", source_name=safe_name)

def page_decompose():
    st.title("🔬 Dekomposisi Modul Mikro")
    token = st.session_state.get("token")
    if not token:
        st.error("Sesi tidak valid. Silakan logout dan login ulang.")
        return

    # ── Panduan microlearning (wajib, shared untuk kedua mode) ───────────────
    resp_docs = api_request("get", "/documents", token=token)
    docs = resp_docs.json() if resp_docs and resp_docs.status_code == 200 else []
    doc_options = {d["filename"]: d["document_id"] for d in docs}

    col_guide, col_template = st.columns([3, 1])
    with col_guide:
        guide_doc = st.selectbox(
            "Panduan Microlearning",
            ["— Pilih panduan —"] + list(doc_options.keys()),
            help="Upload dan pilih dokumen panduan microlearning sebagai acuan format modul"
        )
    with col_template:
        st.markdown("<br>", unsafe_allow_html=True)
        template_path = os.path.join(os.path.dirname(__file__), "template_microlearning.docx")
        if os.path.exists(template_path):
            with open(template_path, "rb") as f:
                st.download_button(
                    "📥 Download Template",
                    data=f.read(),
                    file_name="template_microlearning.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )

    guide_id = doc_options.get(guide_doc) if guide_doc != "— Pilih panduan —" else None
    guide_selected = guide_id is not None
    if not guide_selected:
        st.caption("⚠️ Pilih dokumen panduan microlearning, atau download template di atas, isi, lalu upload di menu Upload Dokumen.")

    st.divider()

    input_mode = st.radio(
        "Sumber materi",
        ["📋 Dari Silabus yang sudah dibuat", "📁 Tanpa Silabus (dari dokumen profil perusahaan)"],
        horizontal=True,
    )

    st.divider()

    # ── MODE 1: Dari Silabus ──────────────────────────────────────────────────
    if input_mode == "📋 Dari Silabus yang sudah dibuat":
        resp_syl = api_request("get", "/syllabi", token=token)
        syllabi = resp_syl.json() if resp_syl and resp_syl.status_code == 200 else []

        if not syllabi:
            st.warning("Belum ada silabus. Generate silabus terlebih dahulu di menu Generate Silabus.")
            return

        syl_options = {f"{s['topic']} ({s['created_at'][:10]})": s for s in syllabi}
        selected_label = st.selectbox("Pilih Silabus", list(syl_options.keys()))
        selected_syl = syl_options[selected_label]

        output = selected_syl.get("output_json", {})
        profile = output.get("org_profile", {})
        with st.expander("📋 Ringkasan Silabus", expanded=False):
            st.caption(
                f"Perusahaan: {profile.get('organization_name', '-')}  |  "
                f"Course: {output.get('course_type', '-')}  |  "
                f"Level: {' → '.join(output.get('levels_covered', []))}"
            )
            st.markdown(f"**TLO:** {len(output.get('tlos', []))} objektif")
            st.markdown(f"**PO:** {len(output.get('performance_objectives', []))} objektif")
            st.markdown(f"**ELO:** {len(output.get('elos', []))} objektif")
            total_syl = sum(e.get("duration_minutes", 0) for e in output.get("elos", []))
            st.markdown(f"**Total Estimasi Durasi Silabus:** {total_syl} menit")

        if st.button("Decompose", type="primary", disabled=not guide_selected, key="btn_decompose_syl"):
            with st.spinner("AI sedang memecah silabus menjadi modul mikro..."):
                resp = api_request("post", "/decompose-from-syllabus", token=token, json={
                    "syllabus_id": selected_syl["id"],
                    "guide_document_id": guide_id,
                })

            if resp and resp.status_code == 200:
                data = resp.json()
                modules = data["modules"]
                syllabus_data = data["syllabus"]
                _render_decompose_result(modules, guide_id, syllabus_data=syllabus_data,
                                         safe_name=output.get("course_type", "modul"))
            elif resp:
                st.error(f"Error {resp.status_code}: {resp.text}")

    # ── MODE 2: Tanpa Silabus ─────────────────────────────────────────────────
    else:
        if not doc_options:
            st.warning("Belum ada dokumen. Upload dokumen profil perusahaan terlebih dahulu.")
            return

        profile_doc = st.selectbox("Pilih Dokumen Profil Perusahaan", list(doc_options.keys()))
        profile_doc_id = doc_options[profile_doc]

        level_labels = {
            1: "Level 1 — Intro",
            2: "Level 2 — Beginner",
            3: "Level 3 — Intermediate",
            4: "Level 4 — Advanced",
            5: "Level 5 — Mastery",
        }
        start_level = st.selectbox(
            "Level Peserta",
            options=list(level_labels.keys()),
            format_func=lambda x: level_labels[x],
        )

        all_types = ["B2B Sales", "Innovation", "Technology", "Leadership", "Operations",
                     "Customer Experience", "Finance", "HR & People", "Digital Marketing", "Other"]
        course_type_sel = st.selectbox("Tipe Course", all_types)
        if course_type_sel == "Other":
            course_type_custom = st.text_input("Ketik tipe course kustom", placeholder="contoh: AI Engineering")
            course_type = course_type_custom.strip() if course_type_custom.strip() else course_type_sel
        else:
            course_type = course_type_sel

        can_submit = guide_selected and bool(course_type)
        if st.button("Decompose", type="primary", disabled=not can_submit, key="btn_decompose_manual"):
            with st.spinner("AI sedang menyusun modul mikro dari profil perusahaan..."):
                resp = api_request("post", "/decompose-without-syllabus", token=token, json={
                    "profile_document_id": profile_doc_id,
                    "guide_document_id": guide_id,
                    "course_type": course_type,
                    "start_level": start_level,
                })

            if resp and resp.status_code == 200:
                data = resp.json()
                modules = data["modules"]
                manual_meta = {
                    "org_profile": data.get("org_profile", {}),
                    "course_type": data.get("course_type", course_type),
                    "levels_covered": data.get("levels_covered", []),
                }
                _render_decompose_result(modules, guide_id, syllabus_data=None,
                                         safe_name=course_type, manual_meta=manual_meta)
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
            total_dur = sum(r.get("estimated_duration_minutes", 0) for r in recs)
            st.success(f"Rekomendasi untuk {participant}")
            st.metric("Estimasi Total Durasi", f"{total_dur} menit")
            st.divider()
            priority_icon = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
            for r in recs:
                icon = priority_icon.get(r.get("priority", ""), "⚪")
                st.markdown(f"**#{r.get('rank', '')}. {r.get('module_title', '')}** {icon} {r.get('priority', '')}")
                st.markdown(f"**Alasan Relevansi:** {r.get('relevance_reason', '')}")
                st.caption(f"Estimasi Durasi: {r.get('estimated_duration_minutes', '')} menit")
                st.divider()
            safe = participant.replace(" ", "_")
            recommend_download_buttons(recs, f"rekomendasi_{safe}", participant=participant, gap=gap)
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
                        levels_covered = output.get("levels_covered", [])
                        levels_str = " → ".join(levels_covered) if levels_covered else "-"
                        st.caption(f"Perusahaan: {profile.get('organization_name', '-')} | Course: {output.get('course_type', '-')} | Level: {levels_str}")

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
                    modules = g["modules"]
                    total_dur = sum(m.get("duration_minutes", 0) for m in modules)
                    col1, col2 = st.columns(2)
                    col1.metric("Total Modul Mikro", len(modules))
                    col2.metric("Total Durasi", f"{total_dur} menit")
                    st.divider()
                    for m in modules:
                        st.markdown(f"**Modul {m.get('module_number', m.get('id', '')[:4] if 'id' in m else '')}. {m.get('title', '')}**")
                        st.caption(f"Format: {m.get('delivery_format', '')}  |  Durasi: {m.get('duration_minutes', '')} menit")
                        st.markdown(f"**Tujuan:** {m.get('objective', m.get('specific_objective', ''))}")
                        st.markdown(f"**Ringkasan:** {m.get('summary', m.get('content_summary', ''))}")
                        st.divider()
                    safe_name = g["source_filename"].replace(" ", "_")[:40]
                    # Normalize field names for export
                    export_modules = [{
                        "module_number": i + 1,
                        "title": m.get("title", ""),
                        "specific_objective": m.get("objective", m.get("specific_objective", "")),
                        "content_summary": m.get("summary", m.get("content_summary", "")),
                        "delivery_format": m.get("delivery_format", ""),
                        "duration_minutes": m.get("duration_minutes", 0),
                    } for i, m in enumerate(modules)]
                    decompose_download_buttons(export_modules, f"modul_mikro_{safe_name}_{g['date']}", source_name=g["source_filename"])
        else:
            st.info("Belum ada modul mikro yang dibuat.")

    with tab3:
        recs = data.get("recommendations", [])
        if recs:
            priority_icon = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
            for r in recs:
                with st.expander(f"{r['participant_name']} ({r['created_at'][:10]})"):
                    st.caption(f"Gap: {r['gap_input']}")
                    items = r["recommended_modules"]
                    total_dur = sum(i.get("estimated_duration_minutes", 0) for i in items)
                    st.metric("Estimasi Total Durasi", f"{total_dur} menit")
                    st.divider()
                    for item in items:
                        icon = priority_icon.get(item.get("priority", ""), "⚪")
                        st.markdown(f"**#{item.get('rank', '')}. {item.get('module_title', '')}** {icon} {item.get('priority', '')}")
                        st.markdown(f"**Alasan Relevansi:** {item.get('relevance_reason', '')}")
                        st.caption(f"Estimasi Durasi: {item.get('estimated_duration_minutes', '')} menit")
                        st.divider()
                    safe = r["participant_name"].replace(" ", "_")
                    recommend_download_buttons(items, f"rekomendasi_{r['id'][:8]}",
                                               participant=r["participant_name"], gap=r["gap_input"])
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
