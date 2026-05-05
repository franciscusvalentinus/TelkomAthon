import streamlit as st
import pandas as pd
import io
import sys
import os

# Ensure streamlit_app is importable as a package
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from streamlit_app.export_utils import (
    to_csv, to_xlsx, to_docx, to_pdf,
    syllabus_to_text, syllabus_to_docx, syllabus_to_pdf,
    decompose_to_text, decompose_to_docx, decompose_to_pdf,
    recommend_to_text, recommend_to_docx, recommend_to_pdf,
    combined_to_docx, combined_to_pdf, combined_to_text,
    build_timeline, timeline_to_df,
    decompose_manual_to_docx, decompose_manual_to_pdf, decompose_manual_to_text,
    roadmap_to_text, roadmap_to_docx, roadmap_to_pdf,
    bulk_recommend_to_xlsx, bulk_recommend_to_docx, bulk_recommend_to_pdf,
    quiz_to_docx, quiz_to_pdf, quiz_to_xlsx,
)
from streamlit_app.db.database import get_db_session
from streamlit_app.auth import register_user, login_user, decode_token
import streamlit_app.backend as backend

st.set_page_config(page_title="LDD AI Assistant — Telkom", page_icon="🎓", layout="wide")


# ── DB session helper ─────────────────────────────────────────────────────────

def get_db():
    return get_db_session()


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_user_id() -> str:
    return st.session_state.get("user_id", "")


def download_buttons(df: pd.DataFrame, basename: str, title: str = "Export"):
    cols = st.columns(4)
    with cols[0]:
        st.download_button("⬇️ CSV", data=to_csv(df), file_name=f"{basename}.csv", mime="text/csv")
    with cols[1]:
        st.download_button("⬇️ XLSX", data=to_xlsx(df), file_name=f"{basename}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with cols[2]:
        st.download_button("⬇️ DOCX", data=to_docx(df, title), file_name=f"{basename}.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    with cols[3]:
        st.download_button("⬇️ PDF", data=to_pdf(df, title), file_name=f"{basename}.pdf", mime="application/pdf")


def show_table(df: pd.DataFrame):
    display = df.copy().reset_index(drop=True)
    display.index = display.index + 1
    display.index.name = "nomor"
    st.dataframe(display, use_container_width=True)


def syllabus_download_buttons(final: dict, basename: str):
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
                           file_name=f"{basename}.pdf", mime="application/pdf")


def _upload_file(file, user_id: str) -> str | None:
    """Upload a Streamlit UploadedFile and return document_id or None."""
    db = get_db()
    try:
        result = backend.upload_document(db, user_id, file.getvalue(), file.name)
        return result["document_id"]
    except Exception as e:
        st.error(f"Gagal mengupload {file.name}: {e}")
        return None
    finally:
        db.close()


# ── Session State Init ────────────────────────────────────────────────────────

for key, default in [("token", None), ("user_email", ""), ("logged_in", False), ("user_id", "")]:
    if key not in st.session_state:
        st.session_state[key] = default


# ── Auth Gate ─────────────────────────────────────────────────────────────────

def page_auth():
    st.title("🎓 Prima : Personalized Responsive Intelligent Micro-Learning Assistant")
    st.caption("Created by Group 5")
    st.divider()

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", use_container_width=True):
            db = get_db()
            try:
                token, err = login_user(db, email, password)
                if err:
                    st.error(err)
                else:
                    user_id = decode_token(token)
                    st.session_state["token"] = token
                    st.session_state["user_email"] = email
                    st.session_state["user_id"] = user_id
                    st.session_state["logged_in"] = True
                    st.rerun()
            finally:
                db.close()

    with tab_register:
        full_name = st.text_input("Nama Lengkap", key="reg_name")
        reg_email = st.text_input("Email", key="reg_email")
        reg_pass = st.text_input("Password", type="password", key="reg_pass")
        reg_pass2 = st.text_input("Konfirmasi Password", type="password", key="reg_pass2")
        if st.button("Daftar", use_container_width=True):
            if reg_pass != reg_pass2:
                st.error("Password tidak cocok")
            else:
                db = get_db()
                try:
                    user, err = register_user(db, reg_email, reg_pass, full_name)
                    if err:
                        st.error(err)
                    else:
                        token, _ = login_user(db, reg_email, reg_pass)
                        user_id = decode_token(token)
                        st.session_state["token"] = token
                        st.session_state["user_email"] = reg_email
                        st.session_state["user_id"] = user_id
                        st.session_state["logged_in"] = True
                        st.rerun()
                finally:
                    db.close()


# ── Pages ─────────────────────────────────────────────────────────────────────

def page_syllabus():
    st.title("📋 Generate Draft Silabus")
    st.caption("Buat silabus pelatihan secara otomatis mulai dari profil organisasi hingga Enabling Learning Objectives (ELO).")
    user_id = get_user_id()

    defaults = {
        "syl_step": 1, "syl_org_profile": None, "syl_doc_ids": [],
        "syl_course_type": "", "syl_start_level": 1,
        "syl_current_condition": "", "syl_desired_condition": "",
        "syl_tlos": [], "syl_selected_tlos": [],
        "syl_performances": [], "syl_selected_perfs": [],
        "syl_elos": [], "syl_selected_elos": [], "syl_final": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    step = st.session_state["syl_step"]

    steps_label = ["1 Profil", "2 Tipe Course", "3 TLO", "4 PCS", "5 ELO", "6 Silabus"]
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

    # ── STEP 1 ────────────────────────────────────────────────────────────────
    if step == 1:
        st.subheader("Langkah 1 — Profil Perusahaan")
        input_mode = st.radio(
            "Sumber profil perusahaan",
            ["📄 Upload dokumen profil", "✏️ Tidak ada profil perusahaan?"],
            horizontal=True,
        )

        if input_mode == "📄 Upload dokumen profil":
            uploaded_profile = st.file_uploader(
                "Upload dokumen profil perusahaan",
                type=["pdf", "pptx", "docx", "xlsx"],
                key="syl_profile_upload",
            )
            if st.button("Generate Silabus →", disabled=not uploaded_profile, type="primary"):
                with st.spinner("Mengupload dan menganalisis dokumen profil perusahaan..."):
                    doc_id = _upload_file(uploaded_profile, user_id)
                if not doc_id:
                    st.error("Gagal mengupload dokumen. Coba lagi.")
                else:
                    with st.spinner("AI sedang membaca dan memahami profil perusahaan..."):
                        db = get_db()
                        try:
                            org_profile = backend.analyze_org_from_docs(db, user_id, [doc_id])
                            st.session_state["syl_org_profile"] = org_profile
                            st.session_state["syl_doc_ids"] = [doc_id]
                            st.session_state["syl_step"] = 2
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))
                        finally:
                            db.close()
        else:
            st.info("Masukkan nama dan industri perusahaan. AI akan membantu melengkapi profil secara otomatis.")
            company_name = st.text_input("Nama Perusahaan", placeholder="contoh: PT Cahaya Langit")
            industry = st.text_input("Industri / Sektor", placeholder="contoh: Teknologi Informasi")
            can_submit = bool(company_name.strip() and industry.strip())
            if st.button("Generate Silabus →", disabled=not can_submit, type="primary"):
                with st.spinner("AI sedang menyusun profil perusahaan..."):
                    try:
                        org_profile = backend.analyze_org_manual(company_name.strip(), industry.strip())
                        st.session_state["syl_org_profile"] = org_profile
                        st.session_state["syl_doc_ids"] = []
                        st.session_state["syl_step"] = 2
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    # ── STEP 2 ────────────────────────────────────────────────────────────────
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
        ordered = recommended + [t for t in all_types if t not in recommended]
        course_type = st.selectbox("Tipe Course", ordered)
        if course_type == "Other":
            custom = st.text_input("Ketik tipe course kustom")
            final_course_type = custom.strip() if custom.strip() else course_type
        else:
            final_course_type = course_type

        level_labels = {1: "Level 1 — Intro", 2: "Level 2 — Beginner", 3: "Level 3 — Intermediate",
                        4: "Level 4 — Advanced", 5: "Level 5 — Mastery"}
        start_level = st.selectbox("Level Awal Peserta", options=list(level_labels.keys()),
                                   format_func=lambda x: level_labels[x])
        active_levels = list(range(start_level, 6))
        st.caption(f"Silabus akan mencakup: {', '.join(level_labels[l] for l in active_levels)}")

        with st.expander("📝 Konteks Pelatihan (opsional)", expanded=False):
            current_condition = st.text_area("Kondisi Saat Ini")
            desired_condition = st.text_area("Kondisi yang Diinginkan")

        col_back, col_next = st.columns([1, 3])
        with col_back:
            if st.button("← Kembali"):
                st.session_state["syl_step"] = 1
                st.rerun()
        with col_next:
            if st.button("Generate TLO →", type="primary"):
                with st.spinner("AI sedang membuat Terminal Learning Objectives..."):
                    db = get_db()
                    try:
                        tlos = backend.generate_tlo(
                            db, user_id, final_course_type, profile,
                            st.session_state["syl_doc_ids"], start_level,
                            current_condition.strip(), desired_condition.strip()
                        )
                        st.session_state["syl_course_type"] = final_course_type
                        st.session_state["syl_start_level"] = start_level
                        st.session_state["syl_current_condition"] = current_condition.strip()
                        st.session_state["syl_desired_condition"] = desired_condition.strip()
                        st.session_state["syl_tlos"] = tlos
                        st.session_state["syl_step"] = 3
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
                    finally:
                        db.close()

    # ── STEP 3 ────────────────────────────────────────────────────────────────
    elif step == 3:
        st.subheader("Langkah 3 — Pilih Terminal Learning Objectives (TLO)")
        st.caption(f"Course: **{st.session_state['syl_course_type']}** | Pilih 1 atau lebih TLO yang paling sesuai")
        tlos = st.session_state["syl_tlos"]
        selected_indices = []
        for i, tlo in enumerate(tlos):
            checked = st.checkbox(f"**TLO {tlo['tlo_number']}** — {tlo['tlo']}", key=f"tlo_check_{i}", value=True)
            if checked:
                selected_indices.append(i)
            st.caption(f"📌 Rationale: {tlo['rationale']}")

        col_back, col_next = st.columns([1, 3])
        with col_back:
            if st.button("← Kembali"):
                st.session_state["syl_step"] = 2
                st.rerun()
        with col_next:
            if st.button("Generate PCS →", disabled=not selected_indices, type="primary"):
                selected_tlos = [tlos[i] for i in selected_indices]
                with st.spinner("AI sedang membuat PCS..."):
                    db = get_db()
                    try:
                        perfs = backend.generate_performance(
                            db, user_id, selected_tlos,
                            st.session_state["syl_org_profile"],
                            st.session_state["syl_doc_ids"],
                            st.session_state["syl_start_level"],
                        )
                        st.session_state["syl_selected_tlos"] = selected_tlos
                        st.session_state["syl_performances"] = perfs
                        st.session_state["syl_step"] = 4
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
                    finally:
                        db.close()

    # ── STEP 4 ────────────────────────────────────────────────────────────────
    elif step == 4:
        st.subheader("Langkah 4 — Pilih PCS")
        perfs = st.session_state["syl_performances"]
        selected_indices = []
        for i, p in enumerate(perfs):
            checked = st.checkbox(f"**PCS {p['perf_number']}** [{p['related_tlo']}]", key=f"perf_check_{i}", value=True)
            if checked:
                selected_indices.append(i)
            st.markdown(f"Performance : {p.get('performance_objective', '')}")
            st.markdown(f"Condition : {p.get('condition', '')}")
            st.markdown(f"Standard : {p.get('standard', '')}")

        col_back, col_next = st.columns([1, 3])
        with col_back:
            if st.button("← Kembali"):
                st.session_state["syl_step"] = 3
                st.rerun()
        with col_next:
            if st.button("Generate ELO →", disabled=not selected_indices, type="primary"):
                selected_perfs = [perfs[i] for i in selected_indices]
                with st.spinner("AI sedang membuat Enabling Learning Objectives..."):
                    db = get_db()
                    try:
                        elos = backend.generate_elo(
                            db, user_id,
                            st.session_state["syl_selected_tlos"], selected_perfs,
                            st.session_state["syl_org_profile"],
                            st.session_state["syl_doc_ids"],
                            st.session_state["syl_start_level"],
                        )
                        st.session_state["syl_selected_perfs"] = selected_perfs
                        st.session_state["syl_elos"] = elos
                        st.session_state["syl_step"] = 5
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
                    finally:
                        db.close()

    # ── STEP 5 ────────────────────────────────────────────────────────────────
    elif step == 5:
        st.subheader("Langkah 5 — Pilih Enabling Learning Objectives (ELO)")
        elos = st.session_state["syl_elos"]
        selected_indices = []
        for i, e in enumerate(elos):
            checked = st.checkbox(
                f"**ELO {e['elo_number']}** [{e['related_performance'].replace('PO ', 'PCS ')}] — {e['elo']}",
                key=f"elo_check_{i}", value=True
            )
            if checked:
                selected_indices.append(i)
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
                    db = get_db()
                    try:
                        result = backend.finalize_syllabus(
                            db, user_id,
                            st.session_state["syl_course_type"],
                            st.session_state["syl_org_profile"],
                            st.session_state["syl_selected_tlos"],
                            st.session_state["syl_selected_perfs"],
                            selected_elos,
                            st.session_state["syl_start_level"],
                            st.session_state["syl_current_condition"],
                            st.session_state["syl_desired_condition"],
                        )
                        st.session_state["syl_selected_elos"] = selected_elos
                        st.session_state["syl_final"] = result["result"]
                        st.session_state["syl_step"] = 6
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
                    finally:
                        db.close()

    # ── STEP 6 ────────────────────────────────────────────────────────────────
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
            for p in profile.get("strategic_priorities", []):
                st.markdown(f"- {p}")
            st.info(profile.get("learning_context", ""))

        st.subheader("Terminal Learning Objectives (TLO)")
        for t in final.get("tlos", []):
            st.markdown(f"**TLO {t.get('tlo_number', '')}.**  {t.get('tlo', '')}")
            st.caption(f"Rationale: {t.get('rationale', '')}")

        st.divider()
        st.subheader("PCS")
        for po in final.get("performance_objectives", []):
            st.markdown(f"**PCS {po.get('perf_number', '')}.** [{po.get('related_tlo', '')}]")
            st.markdown(f"Performance : {po.get('performance_objective', '')}")
            st.markdown(f"Condition : {po.get('condition', '')}")
            st.markdown(f"Standard : {po.get('standard', '')}")

        st.divider()
        st.subheader("Enabling Learning Objectives (ELO)")
        total_dur = sum(e.get("duration_minutes", 0) for e in final.get("elos", []))
        st.metric("Estimasi Total Durasi", f"{total_dur} menit")
        for e in final.get("elos", []):
            st.markdown(f"**ELO {e.get('elo_number', '')}.** [{e.get('related_performance', '').replace('PO ', 'PCS ')}]  {e.get('elo', '')}")
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


def _render_decompose_result(modules: list, syllabus_data: dict | None, safe_name: str,
                              manual_meta: dict | None = None, quiz_data: dict | None = None):
    total_dur = sum(m.get("duration_minutes", 0) for m in modules)

    if manual_meta:
        profile = manual_meta.get("org_profile", {})
        course_type_disp = manual_meta.get("course_type", safe_name)
        levels_disp = manual_meta.get("levels_covered", [])
        with st.expander("📊 Profil Perusahaan & Course", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Perusahaan:** {profile.get('organization_name', '-')}")
                st.markdown(f"**Industri:** {profile.get('industry', '-')}")
            with col2:
                st.markdown(f"**Tipe Course:** {course_type_disp}")
                st.markdown(f"**Level:** {' → '.join(levels_disp) if levels_disp else '-'}")

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
        show_table(timeline_to_df(timeline["short"]))
    with tab_long:
        show_table(timeline_to_df(timeline["long"]))

    if quiz_data is not None:
        st.divider()
        st.subheader("📝 Soal Quiz")
        if not quiz_data.get("has_quiz_elos"):
            st.info("Tidak ada ELO yang metodenya Quiz pada silabus ini.")
        else:
            mode = quiz_data.get("mode", "single")

            def _render_questions(questions: list, section: str):
                st.markdown(f"**{section}** — {len(questions)} soal")
                for q in questions:
                    with st.expander(f"Soal {q.get('nomor', '')}. {q.get('pertanyaan', '')[:80]}..."):
                        st.caption(f"ELO: {q.get('elo_reference', '')}")
                        st.markdown(q.get("pertanyaan", ""))
                        for k, v in q.get("pilihan", {}).items():
                            benar = k == q.get("jawaban_benar", "")
                            st.markdown(f"{'✅' if benar else '◻️'} **{k}.** {v}")
                        st.caption(f"Penjelasan: {q.get('penjelasan', '')}")

            if mode == "prepost":
                tab_pre, tab_post = st.tabs(["📋 Pre-test", "📋 Post-test"])
                with tab_pre:
                    _render_questions(quiz_data.get("pre_test", []), "Pre-test")
                with tab_post:
                    _render_questions(quiz_data.get("post_test", []), "Post-test")
            else:
                _render_questions(quiz_data.get("quiz", []), "Quiz")

    st.subheader("Export")
    safe = safe_name.replace(" ", "_").replace("/", "-")

    if syllabus_data:
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.download_button("⬇️ DOCX (Silabus + Modul)",
                               data=combined_to_docx(syllabus_data, modules, quiz_data),
                               file_name=f"silabus_modul_{safe}.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        with col_b:
            st.download_button("⬇️ PDF (Silabus + Modul)",
                               data=combined_to_pdf(syllabus_data, modules, quiz_data),
                               file_name=f"silabus_modul_{safe}.pdf", mime="application/pdf")
        with col_c:
            st.download_button("⬇️ TXT (Silabus + Modul)",
                               data=combined_to_text(syllabus_data, modules, quiz_data).encode("utf-8"),
                               file_name=f"silabus_modul_{safe}.txt", mime="text/plain")
    elif manual_meta:
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.download_button("⬇️ DOCX", data=decompose_manual_to_docx(modules, manual_meta),
                               file_name=f"modul_mikro_{safe}.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        with col_b:
            st.download_button("⬇️ PDF", data=decompose_manual_to_pdf(modules, manual_meta),
                               file_name=f"modul_mikro_{safe}.pdf", mime="application/pdf")
        with col_c:
            st.download_button("⬇️ TXT", data=decompose_manual_to_text(modules, manual_meta).encode("utf-8"),
                               file_name=f"modul_mikro_{safe}.txt", mime="text/plain")
    else:
        decompose_download_buttons(modules, f"modul_mikro_{safe}", source_name=safe_name)


def page_decompose():
    st.title("🔬 Dekomposisi Modul Mikro")
    st.caption("Pecah materi pelatihan besar menjadi modul-modul mikro yang mandiri dan dapat diselesaikan dalam 5–15 menit.")
    user_id = get_user_id()

    guide_file = st.file_uploader(
        "Panduan Microlearning",
        type=["pdf", "pptx", "docx", "xlsx"],
        key="decompose_guide_upload",
    )
    template_path = os.path.join(os.path.dirname(__file__), "template_microlearning.docx")
    if os.path.exists(template_path):
        with open(template_path, "rb") as f:
            st.download_button("📥 Download Template", data=f.read(),
                               file_name="template_microlearning.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    guide_id = None
    if guide_file:
        if st.session_state.get("decompose_guide_filename") != guide_file.name:
            with st.spinner("Mengupload panduan microlearning..."):
                guide_id = _upload_file(guide_file, user_id)
            if guide_id:
                st.session_state["decompose_guide_id"] = guide_id
                st.session_state["decompose_guide_filename"] = guide_file.name
            else:
                st.error("Gagal mengupload panduan. Coba lagi.")
        else:
            guide_id = st.session_state.get("decompose_guide_id")

    if not guide_id:
        st.caption("⚠️ Upload dokumen panduan microlearning, atau download template di atas, isi, lalu upload.")

    st.divider()

    db = get_db()
    try:
        syllabi = backend.list_syllabi(db, user_id)
    finally:
        db.close()

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
        st.markdown(f"**ELO:** {len(output.get('elos', []))} objektif")
        total_syl = sum(e.get("duration_minutes", 0) for e in output.get("elos", []))
        st.markdown(f"**Total Estimasi Durasi Silabus:** {total_syl} menit")

    st.divider()
    gen_quiz = st.checkbox("📝 Generate Soal Quiz?")
    quiz_mode = None
    jumlah_soal = 10
    if gen_quiz:
        quiz_mode = st.radio("Tipe Quiz",
                             ["Generate Pre-test & Post-test saja", "Generate Quiz jadi 1 saja"],
                             horizontal=True)
        jumlah_soal = st.number_input("Jumlah soal", min_value=1, max_value=50, value=10, step=1)
        if quiz_mode == "Generate Pre-test & Post-test saja":
            st.caption(f"Akan digenerate Pre-test & Post-test masing-masing sebanyak **{jumlah_soal} soal**.")
        else:
            st.caption(f"Akan digenerate Quiz sebanyak **{jumlah_soal} soal**.")
    st.divider()

    if st.button("Submit", type="primary", disabled=not guide_id, key="btn_decompose_syl"):
        with st.spinner("AI sedang memecah silabus menjadi modul mikro..."):
            db = get_db()
            try:
                data = backend.decompose_from_syllabus(db, user_id, selected_syl["id"], guide_id)
                modules = data["modules"]
                syllabus_data = data["syllabus"]

                quiz_data = None
                if gen_quiz:
                    mode_key = "prepost" if quiz_mode == "Generate Pre-test & Post-test saja" else "single"
                    with st.spinner("AI sedang membuat soal quiz..."):
                        try:
                            quiz_data = backend.generate_quiz(db, user_id, selected_syl["id"], mode_key, jumlah_soal)
                        except Exception as qe:
                            st.warning(f"Gagal generate quiz: {qe}")

                _render_decompose_result(modules, syllabus_data=syllabus_data,
                                         safe_name=output.get("course_type", "modul"),
                                         quiz_data=quiz_data)
            except Exception as e:
                st.error(str(e))
            finally:
                db.close()


def page_recommend():
    st.title("🎯 Personalisasi User")
    st.caption("Generate rekomendasi learning path yang dipersonalisasi berdasarkan gap kompetensi satu peserta.")
    user_id = get_user_id()

    db = get_db()
    try:
        syllabi = backend.list_syllabi(db, user_id)
    finally:
        db.close()

    syl_options = {"— Tanpa konteks silabus —": None}
    syl_options.update({f"{s['topic']} ({s['created_at'][:10]})": s["id"] for s in syllabi})

    participant = st.text_input("Nama Peserta")
    gap = st.text_area("Deskripsi Gap Kompetensi",
                       placeholder="contoh: Belum memahami prinsip lean management")

    with st.expander("📋 Informasi Profil Tambahan (opsional)", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            jabatan = st.text_input("Jabatan")
            lama_bekerja = st.text_input("Lama Bekerja")
            departemen = st.text_input("Departemen")
        with col2:
            pendidikan_terakhir = st.text_input("Pendidikan Terakhir")
            preferensi_belajar = st.text_input("Preferensi Belajar")
            waktu_belajar = st.text_input("Waktu Belajar per Minggu")

    top_k = st.slider("Jumlah Rekomendasi", 3, 10, 5)
    selected_syl_label = st.selectbox("Konteks Silabus (opsional)", list(syl_options.keys()))
    syllabus_id = syl_options[selected_syl_label]

    if st.button("Submit", type="primary", disabled=not (participant and gap)):
        with st.spinner("AI sedang menganalisis gap kompetensi..."):
            db = get_db()
            try:
                result = backend.recommend(
                    db, user_id, participant, gap, top_k, syllabus_id,
                    jabatan, lama_bekerja, departemen,
                    pendidikan_terakhir, preferensi_belajar, waktu_belajar
                )
                recs = result["recommendations"]
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
            except Exception as e:
                st.error(str(e))
            finally:
                db.close()


def page_career_roadmap():
    st.title("🗺️ Roadmap Karir")
    st.caption("Susun roadmap pengembangan karir bertahap dari posisi saat ini menuju target posisi yang diinginkan.")
    user_id = get_user_id()

    db = get_db()
    try:
        syllabi = backend.list_syllabi(db, user_id)
    finally:
        db.close()

    syl_options = {"— Tanpa konteks silabus —": None}
    syl_options.update({f"{s['topic']} ({s['created_at'][:10]})": s["id"] for s in syllabi})

    participant = st.text_input("Nama Peserta")
    col1, col2 = st.columns(2)
    with col1:
        current_pos = st.text_input("Posisi Saat Ini", placeholder="contoh: Junior Data Analyst")
    with col2:
        target_pos = st.text_input("Target Posisi", placeholder="contoh: Senior AI Engineer")

    timeline = st.select_slider("Timeline Target", options=[3, 6, 9, 12, 18, 24], value=12,
                                format_func=lambda x: f"{x} bulan")
    additional = st.text_area("Konteks Tambahan (opsional)")
    selected_syl_label = st.selectbox("Konteks Silabus (opsional)", list(syl_options.keys()))
    syllabus_id = syl_options[selected_syl_label]

    if st.button("Submit", disabled=not (participant and current_pos and target_pos), type="primary"):
        with st.spinner("AI sedang menyusun career roadmap..."):
            db = get_db()
            try:
                data = backend.generate_career_roadmap(
                    db, user_id, participant, current_pos, target_pos,
                    timeline, additional.strip(), syllabus_id
                )
                phases = data["phases"]
                summary = data["summary"]
                total_dur = data["total_duration_minutes"]

                st.success(f"Roadmap Karir untuk {participant}")
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Total Phase", len(phases))
                col_b.metric("Total Durasi", f"{total_dur} menit")
                col_c.metric("Timeline", f"{timeline} bulan")
                st.divider()

                urgency_icon = {"Critical": "🔴", "Important": "🟡", "Nice-to-have": "🟢"}
                for phase in phases:
                    st.subheader(
                        f"Phase {phase.get('phase_number', '')} — {phase.get('phase_name', '')} "
                        f"({phase.get('month_range', '')})"
                    )
                    st.caption(f"Fokus: {phase.get('focus', '')}")
                    for m in phase.get("modules", []):
                        urgency = m.get("urgency", "")
                        icon = urgency_icon.get(urgency, "⚪")
                        st.markdown(f"**{icon} {m.get('module_title', '')}** — {urgency}")
                        st.markdown(f"{m.get('description', '')}")
                        st.caption(f"Metode: {m.get('delivery_method', '')}  |  Durasi: {m.get('duration_minutes', '')} menit")
                    st.divider()

                st.subheader("Export Roadmap")
                safe = f"{current_pos}_to_{target_pos}".replace(" ", "_").replace("/", "-")[:50]
                col_x, col_y, col_z = st.columns(3)
                with col_x:
                    st.download_button("⬇️ TXT", data=roadmap_to_text(summary, phases).encode("utf-8"),
                                       file_name=f"roadmap_{safe}.txt", mime="text/plain")
                with col_y:
                    st.download_button("⬇️ DOCX", data=roadmap_to_docx(summary, phases),
                                       file_name=f"roadmap_{safe}.docx",
                                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                with col_z:
                    st.download_button("⬇️ PDF", data=roadmap_to_pdf(summary, phases),
                                       file_name=f"roadmap_{safe}.pdf", mime="application/pdf")
            except Exception as e:
                st.error(str(e))
            finally:
                db.close()


def page_bulk_recommend():
    st.title("👥 Personalisasi Multi User")
    st.caption("Generate rekomendasi learning path untuk banyak peserta sekaligus via upload Excel.")
    user_id = get_user_id()

    template_df = pd.DataFrame([
        {"nama": "Budi Santoso", "jabatan": "Staff IT", "lama_bekerja": "2 tahun",
         "departemen": "Teknologi Informasi", "gap_kompetensi": "Belum memahami cloud computing dan DevOps",
         "pendidikan_terakhir": "S1 Teknik Informatika", "preferensi_belajar": "Video & hands-on",
         "waktu_belajar_per_minggu": "5 jam"},
        {"nama": "Sari Dewi", "jabatan": "Supervisor Operasional", "lama_bekerja": "5 tahun",
         "departemen": "Operasional", "gap_kompetensi": "Kurang memahami lean management",
         "pendidikan_terakhir": "S1 Manajemen", "preferensi_belajar": "Case study & diskusi",
         "waktu_belajar_per_minggu": "4 jam"},
    ])

    excel_file = st.file_uploader("Upload File Excel Peserta (.xlsx)", type=["xlsx"])
    st.download_button("📥 Download Template Excel", data=to_xlsx(template_df),
                       file_name="template_bulk_peserta.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    df_peserta = None
    if excel_file:
        try:
            df_peserta = pd.read_excel(excel_file)
            df_peserta.columns = [c.strip().lower().replace(" ", "_") for c in df_peserta.columns]
            required_cols = {"nama", "gap_kompetensi"}
            missing = required_cols - set(df_peserta.columns)
            if missing:
                st.error(f"Kolom wajib tidak ditemukan: {', '.join(missing)}")
                df_peserta = None
            else:
                df_peserta = df_peserta.dropna(subset=["nama", "gap_kompetensi"])
                df_peserta = df_peserta[
                    df_peserta["nama"].astype(str).str.strip().ne("") &
                    df_peserta["gap_kompetensi"].astype(str).str.strip().ne("")
                ]
                st.success(f"✅ {len(df_peserta)} peserta valid ditemukan")
                show_table(df_peserta)
        except Exception as e:
            st.error(f"Gagal membaca file Excel: {e}")

    db = get_db()
    try:
        syllabi = backend.list_syllabi(db, user_id)
    finally:
        db.close()

    syl_options = {"— Tanpa konteks silabus —": None}
    syl_options.update({f"{s['topic']} ({s['created_at'][:10]})": s["id"] for s in syllabi})
    selected_syl_label = st.selectbox("Konteks Silabus (opsional)", list(syl_options.keys()))
    syllabus_id = syl_options[selected_syl_label]
    top_k = st.slider("Jumlah Rekomendasi per Peserta", 3, 10, 5)

    can_generate = df_peserta is not None and len(df_peserta) > 0
    if st.button("Submit", disabled=not can_generate, type="primary"):
        optional_cols = ["jabatan", "lama_bekerja", "departemen",
                         "pendidikan_terakhir", "preferensi_belajar", "waktu_belajar_per_minggu"]
        participants = []
        for _, row in df_peserta.iterrows():
            p = {"nama": str(row["nama"]).strip(), "gap_kompetensi": str(row["gap_kompetensi"]).strip()}
            for col in optional_cols:
                val = row.get(col)
                if pd.notna(val) and str(val).strip():
                    p[col] = str(val).strip()
            participants.append(p)

        with st.spinner(f"AI sedang memproses {len(participants)} peserta... Harap tunggu."):
            db = get_db()
            try:
                data = backend.bulk_recommend(db, user_id, participants, top_k, syllabus_id)
                results = data.get("results", [])
                errors = data.get("errors", [])
                st.success(f"✅ Berhasil: {data['total_processed']} peserta | ❌ Gagal: {data['total_errors']} peserta")

                if errors:
                    with st.expander(f"⚠️ {len(errors)} peserta gagal diproses"):
                        for e in errors:
                            st.error(f"**{e['nama']}**: {e['error']}")

                if results:
                    st.session_state["bulk_results"] = results
            except Exception as e:
                st.error(str(e))
            finally:
                db.close()

    if "bulk_results" in st.session_state and st.session_state["bulk_results"]:
        results = st.session_state["bulk_results"]
        st.divider()
        st.subheader(f"Hasil Rekomendasi — {len(results)} Peserta")
        priority_icon = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
        level_colors = {1: "🔵", 2: "🟢", 3: "🟡", 4: "🟠", 5: "🔴"}

        for r in results:
            recs = r.get("recommendations", [])
            total_dur = sum(x.get("estimated_duration_minutes", 0) for x in recs)
            label = r.get("nama", "")
            if r.get("jabatan"):
                label += f" — {r['jabatan']}"
            with st.expander(f"👤 {label}  |  {len(recs)} modul  |  {total_dur} menit"):
                lvl = r.get("recommended_level")
                lvl_label = r.get("level_label", "")
                if lvl:
                    icon = level_colors.get(lvl, "⚪")
                    st.info(f"{icon} **Recommended Level: {lvl} — {lvl_label}**")
                st.divider()
                for rec in recs:
                    icon = priority_icon.get(rec.get("priority", ""), "⚪")
                    st.markdown(f"**#{rec.get('rank', '')}. {rec.get('module_title', '')}** {icon} {rec.get('priority', '')}")
                    st.markdown(f"**Alasan Relevansi:** {rec.get('relevance_reason', '')}")
                    st.caption(f"Estimasi Durasi: {rec.get('estimated_duration_minutes', '')} menit")
                    st.divider()

        st.subheader("Export Semua Hasil")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button("⬇️ XLSX", data=bulk_recommend_to_xlsx(results),
                               file_name="bulk_rekomendasi.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with col2:
            st.download_button("⬇️ DOCX", data=bulk_recommend_to_docx(results),
                               file_name="bulk_rekomendasi.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        with col3:
            st.download_button("⬇️ PDF", data=bulk_recommend_to_pdf(results),
                               file_name="bulk_rekomendasi.pdf", mime="application/pdf")


def page_history():
    st.title("📥 Riwayat & Export")
    st.caption("Lihat dan unduh semua hasil yang pernah di-generate.")
    user_id = get_user_id()

    db = get_db()
    try:
        data = backend.get_history(db, user_id)
    except Exception as e:
        st.error(f"Gagal memuat riwayat: {e}")
        return
    finally:
        db.close()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Silabus", "🔬 Modul Mikro", "🎯 Personalisasi User",
        "👥 Personalisasi Multi User", "🗺️ Roadmap Karir"
    ])

    with tab1:
        syllabi = data.get("syllabi", [])
        if syllabi:
            for s in syllabi:
                with st.expander(f"{s['topic']} — {s['level']} ({s['created_at'][:10]})"):
                    output = s["output_json"]
                    if isinstance(output, dict) and "tlos" in output:
                        profile = output.get("org_profile", {})
                        levels_covered = output.get("levels_covered", [])
                        st.caption(f"Perusahaan: {profile.get('organization_name', '-')} | Course: {output.get('course_type', '-')} | Level: {' → '.join(levels_covered)}")
                        st.markdown("**TLO**")
                        for t in output.get("tlos", []):
                            st.markdown(f"**TLO {t.get('tlo_number', '')}.**  {t.get('tlo', '')}")
                            st.caption(f"Rationale: {t.get('rationale', '')}")
                        st.markdown("**ELO**")
                        for e in output.get("elos", []):
                            st.markdown(f"**ELO {e.get('elo_number', '')}.**  {e.get('elo', '')}")
                            st.caption(f"Bloom: {e.get('bloom_level', '')}  |  Metode: {e.get('delivery_method', '')}  |  Durasi: {e.get('duration_minutes', '')} menit")
                        syllabus_download_buttons(output, f"silabus_{s['id'][:8]}")
        else:
            st.info("Belum ada silabus yang dibuat.")

    with tab2:
        groups = data.get("micro_module_groups", [])
        if groups:
            for g in groups:
                with st.expander(f"{g['source_filename']} ({g['date']})"):
                    modules = g["modules"]
                    total_dur = sum(m.get("duration_minutes", 0) for m in modules)
                    col1, col2 = st.columns(2)
                    col1.metric("Total Modul Mikro", len(modules))
                    col2.metric("Total Durasi", f"{total_dur} menit")
                    st.divider()
                    for m in modules:
                        st.markdown(f"**{m.get('title', '')}**")
                        st.caption(f"Format: {m.get('delivery_format', '')}  |  Durasi: {m.get('duration_minutes', '')} menit")
                        st.markdown(f"**Tujuan:** {m.get('objective', '')}")
                        st.divider()
                    safe_name = g["source_filename"].replace(" ", "_")[:40]
                    export_modules = [{
                        "module_number": i + 1, "title": m.get("title", ""),
                        "specific_objective": m.get("objective", ""),
                        "content_summary": m.get("summary", ""),
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
                created = r["created_at"]
                created_str = created[:10] if isinstance(created, str) else created.strftime("%Y-%m-%d")
                with st.expander(f"{r['participant_name']} ({created_str})"):
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
                    recommend_download_buttons(items, f"rekomendasi_{r['id'][:8]}",
                                               participant=r["participant_name"], gap=r["gap_input"])
        else:
            st.info("Belum ada rekomendasi yang dibuat.")

    with tab4:
        bulk_groups = data.get("bulk_groups", [])
        if bulk_groups:
            priority_icon = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
            level_colors = {1: "🔵", 2: "🟢", 3: "🟡", 4: "🟠", 5: "🔴"}
            for g in bulk_groups:
                participants = g.get("participants", [])
                with st.expander(f"Batch {g['date']} — {g['total_participants']} peserta"):
                    export_results = []
                    for r in participants:
                        items = r.get("recommended_modules", [])
                        total_dur = sum(i.get("estimated_duration_minutes", 0) for i in items)
                        lvl = r.get("recommended_level")
                        lvl_label = r.get("level_label", "")
                        st.markdown(f"**👤 {r['participant_name']}**")
                        st.caption(f"Gap: {r['gap_input']}")
                        if lvl:
                            icon = level_colors.get(lvl, "⚪")
                            st.caption(f"{icon} Recommended Level: {lvl} — {lvl_label}")
                        st.caption(f"Total Durasi: {total_dur} menit")
                        for item in items:
                            icon = priority_icon.get(item.get("priority", ""), "⚪")
                            st.markdown(f"&nbsp;&nbsp;&nbsp;**#{item.get('rank', '')}. {item.get('module_title', '')}** {icon}")
                            st.caption(f"&nbsp;&nbsp;&nbsp;{item.get('relevance_reason', '')} — {item.get('estimated_duration_minutes', '')} menit")
                        st.divider()
                        export_results.append({
                            "nama": r["participant_name"], "gap_kompetensi": r["gap_input"],
                            "recommended_level": lvl, "level_label": lvl_label,
                            "recommendations": items,
                        })
                    safe_date = g['date'].replace(" ", "_").replace(":", "")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.download_button("⬇️ XLSX", data=bulk_recommend_to_xlsx(export_results),
                                           file_name=f"bulk_{safe_date}.xlsx",
                                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                           key=f"xlsx_{g['bulk_session_id']}")
                    with col2:
                        st.download_button("⬇️ DOCX", data=bulk_recommend_to_docx(export_results),
                                           file_name=f"bulk_{safe_date}.docx",
                                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                           key=f"docx_{g['bulk_session_id']}")
                    with col3:
                        st.download_button("⬇️ PDF", data=bulk_recommend_to_pdf(export_results),
                                           file_name=f"bulk_{safe_date}.pdf", mime="application/pdf",
                                           key=f"pdf_{g['bulk_session_id']}")
        else:
            st.info("Belum ada hasil personalisasi multi user.")

    with tab5:
        roadmaps = data.get("roadmaps", [])
        if roadmaps:
            urgency_icon = {"Critical": "🔴", "Important": "🟡", "Nice-to-have": "🟢"}
            for r in roadmaps:
                created = r["created_at"]
                created_str = created[:10] if isinstance(created, str) else created.strftime("%Y-%m-%d")
                label = f"{r['participant_name']} — {r['gap_input'].replace('Career: ', '')} ({created_str})"
                with st.expander(label):
                    phases = r["recommended_modules"]
                    total_dur = sum(
                        m.get("duration_minutes", 0)
                        for phase in phases
                        for m in (phase.get("modules", []) if isinstance(phase, dict) else [])
                    )
                    col1, col2 = st.columns(2)
                    col1.metric("Total Phase", len(phases))
                    col2.metric("Total Durasi", f"{total_dur} menit")
                    st.divider()
                    for phase in phases:
                        st.markdown(f"**Phase {phase.get('phase_number', '')} — {phase.get('phase_name', '')}** ({phase.get('month_range', '')})")
                        st.caption(f"Fokus: {phase.get('focus', '')}")
                        for m in phase.get("modules", []):
                            urgency = m.get("urgency", "")
                            icon = urgency_icon.get(urgency, "⚪")
                            st.markdown(f"{icon} **{m.get('module_title', '')}** — {urgency}")
                            st.caption(f"Metode: {m.get('delivery_method', '')}  |  Durasi: {m.get('duration_minutes', '')} menit")
                        st.divider()
                    gap = r["gap_input"].replace("Career: ", "")
                    parts = gap.split(" → ")
                    from_pos = parts[0].strip() if len(parts) > 1 else gap
                    to_parts = parts[1].split("(") if len(parts) > 1 else ["", ""]
                    to_pos = to_parts[0].strip()
                    timeline_str = to_parts[1].replace(" bulan)", "").strip() if len(to_parts) > 1 else "12"
                    summary = {
                        "participant": r["participant_name"], "from": from_pos, "to": to_pos,
                        "timeline_months": int(timeline_str) if timeline_str.isdigit() else 12,
                        "num_phases": len(phases),
                    }
                    col_x, col_y, col_z = st.columns(3)
                    with col_x:
                        st.download_button("⬇️ TXT", data=roadmap_to_text(summary, phases).encode("utf-8"),
                                           file_name=f"roadmap_{r['id'][:8]}.txt", mime="text/plain",
                                           key=f"txt_{r['id']}")
                    with col_y:
                        st.download_button("⬇️ DOCX", data=roadmap_to_docx(summary, phases),
                                           file_name=f"roadmap_{r['id'][:8]}.docx",
                                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                           key=f"docx_{r['id']}")
                    with col_z:
                        st.download_button("⬇️ PDF", data=roadmap_to_pdf(summary, phases),
                                           file_name=f"roadmap_{r['id'][:8]}.pdf", mime="application/pdf",
                                           key=f"pdf_{r['id']}")
        else:
            st.info("Belum ada roadmap karir yang dibuat.")


# ── Main Router ───────────────────────────────────────────────────────────────

if not st.session_state["logged_in"]:
    page_auth()
else:
    with st.sidebar:
        st.caption(f"👤 {st.session_state['user_email']}")
        st.divider()
        page = st.radio("Navigasi", [
            "📋 Generate Silabus",
            "🔬 Dekomposisi Modul",
            "🎯 Personalisasi User",
            "👥 Personalisasi Multi User",
            "🗺️ Roadmap Karir",
            "📥 Riwayat & Export",
        ])
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            for key in ["token", "user_email", "logged_in", "user_id"]:
                st.session_state[key] = None if key == "token" else (False if key == "logged_in" else "")
            st.rerun()

    if page == "📋 Generate Silabus":
        page_syllabus()
    elif page == "🔬 Dekomposisi Modul":
        page_decompose()
    elif page == "🎯 Personalisasi User":
        page_recommend()
    elif page == "👥 Personalisasi Multi User":
        page_bulk_recommend()
    elif page == "🗺️ Roadmap Karir":
        page_career_roadmap()
    elif page == "📥 Riwayat & Export":
        page_history()
