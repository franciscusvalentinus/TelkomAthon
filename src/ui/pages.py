"""UI page components for Streamlit application"""

import streamlit as st
from typing import Optional
from src.ui.utils import show_error, show_success, show_info, with_spinner
from src.workflow.orchestrator import WorkflowOrchestrator
from src.processors.document_processor import UnsupportedFormatError, EmptyFileError
from src.models.entities import WorkflowStep, OrganizationProfile


def render_upload_page(orchestrator: WorkflowOrchestrator) -> None:
    """
    Render organization profile upload interface.
    
    Provides file upload widget, submit button, processing status display,
    and error handling with Indonesian messages.
    
    Args:
        orchestrator: Workflow orchestrator for processing uploads
    """
    st.header("📤 Unggah Profil Organisasi")
    st.write(
        "Unggah dokumen profil organisasi Anda untuk memulai proses "
        "generasi silabus. Sistem akan menganalisis dokumen dan "
        "menghasilkan ringkasan konteks organisasi."
    )
    
    st.markdown("---")
    
    # Display supported formats
    st.info(
        "**Format yang didukung:** PDF (.pdf), Word (.docx), Text (.txt)\n\n"
        "**Ukuran maksimum:** 10 MB"
    )
    
    # File upload widget
    uploaded_file = st.file_uploader(
        "Pilih file profil organisasi",
        type=["pdf", "docx", "txt"],
        help="Unggah dokumen yang berisi informasi tentang organisasi Anda",
        key="org_profile_upload"
    )
    
    # Show file info if uploaded
    if uploaded_file is not None:
        st.success(f"✅ File dipilih: **{uploaded_file.name}**")
        st.write(f"Ukuran: {uploaded_file.size / 1024:.2f} KB")
        st.write(f"Tipe: {uploaded_file.type}")
        
        # Check file size (10 MB limit)
        max_size = 10 * 1024 * 1024  # 10 MB in bytes
        if uploaded_file.size > max_size:
            show_error(
                f"Ukuran file terlalu besar ({uploaded_file.size / 1024 / 1024:.2f} MB). "
                f"Maksimum 10 MB."
            )
            return
        
        st.markdown("---")
        
        # Submit button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submit_button = st.button(
                "🚀 Proses Dokumen",
                type="primary",
                use_container_width=True,
                help="Klik untuk memproses dokumen dan menghasilkan ringkasan"
            )
        
        # Process document when submit is clicked
        if submit_button:
            process_uploaded_document(orchestrator, uploaded_file)
    
    else:
        st.info("👆 Silakan pilih file untuk diunggah")


def process_uploaded_document(
    orchestrator: WorkflowOrchestrator,
    uploaded_file
) -> None:
    """
    Process uploaded organization profile document.
    
    Handles document processing, displays progress, and manages errors
    with Indonesian messages.
    
    Args:
        orchestrator: Workflow orchestrator for processing
        uploaded_file: Streamlit UploadedFile object
    """
    try:
        # Show processing status
        with with_spinner("Memproses dokumen..."):
            # Read file content
            file_content = uploaded_file.read()
            
            # Get file extension
            file_name = uploaded_file.name
            file_extension = "." + file_name.split(".")[-1].lower()
            
            # Process document through orchestrator
            org_profile = orchestrator.process_organization_profile(
                file_content=file_content,
                file_type=file_extension,
                file_name=file_name
            )
            
            # Store in session state
            st.session_state.organization = org_profile
            st.session_state.current_step = WorkflowStep.SUMMARY
        
        # Show success message
        show_success("Dokumen berhasil diproses!")
        st.balloons()
        
        # Show preview of summary
        st.markdown("---")
        st.subheader("📋 Ringkasan Profil Organisasi")
        with st.expander("Lihat ringkasan", expanded=True):
            st.write(org_profile.summary)
        
        # Button to continue to next step
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "➡️ Lanjut ke Ringkasan Lengkap",
                type="primary",
                use_container_width=True
            ):
                st.rerun()
    
    except UnsupportedFormatError as e:
        show_error(
            "Format file tidak didukung. Silakan unggah file PDF, DOCX, atau TXT."
        )
        st.info(
            "**Format yang didukung:**\n"
            "- PDF (.pdf)\n"
            "- Microsoft Word (.docx)\n"
            "- Text (.txt)"
        )
    
    except EmptyFileError as e:
        show_error(
            "File kosong atau tidak dapat dibaca. Silakan unggah file yang valid "
            "dengan konten teks yang dapat diekstrak."
        )
        st.info(
            "**Tips:**\n"
            "- Pastikan file tidak kosong\n"
            "- Untuk PDF, pastikan teks dapat dipilih (bukan gambar scan)\n"
            "- Untuk DOCX, pastikan dokumen berisi teks"
        )
    
    except Exception as e:
        # Import the new error classes
        from src.processors.document_processor import FileCorruptedError, FileSizeError
        
        if isinstance(e, FileCorruptedError):
            show_error(
                "File rusak atau tidak dapat dibaca. Silakan periksa file Anda dan coba lagi."
            )
            st.info(
                "**Kemungkinan penyebab:**\n"
                "- File rusak atau terenkripsi\n"
                "- Format file tidak sesuai dengan ekstensi\n"
                "- File memerlukan password untuk dibuka"
            )
        elif isinstance(e, FileSizeError):
            show_error(str(e))
        else:
            show_error(f"Terjadi kesalahan saat memproses dokumen: {str(e)}")
            st.info(
                "Silakan coba lagi atau hubungi administrator jika masalah berlanjut."
            )
            # Log error for debugging
            st.exception(e)


def render_summary_page(orchestrator: WorkflowOrchestrator) -> None:
    """
    Display organization profile summary and context overview.
    
    Shows the AI-generated summary and context of the organization profile,
    allowing users to review before proceeding to course type selection.
    
    Args:
        orchestrator: Workflow orchestrator (not used but kept for consistency)
    
    Requirements: 2.2, 2.3, 13.4
    """
    st.header("📋 Ringkasan Profil Organisasi")
    st.write(
        "Berikut adalah ringkasan profil organisasi Anda yang telah dianalisis "
        "oleh sistem AI. Silakan tinjau informasi ini sebelum melanjutkan ke "
        "langkah berikutnya."
    )
    
    st.markdown("---")
    
    # Get organization profile from session state
    org_profile = st.session_state.organization
    
    if org_profile is None:
        show_error(
            "Profil organisasi tidak ditemukan. Silakan unggah dokumen terlebih dahulu."
        )
        # Button to go back to upload
        if st.button("⬅️ Kembali ke Unggah", type="primary"):
            st.session_state.current_step = WorkflowStep.UPLOAD
            st.rerun()
        return
    
    # Display file information
    st.subheader("📄 Informasi File")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Nama File", org_profile.file_name)
    with col2:
        st.metric("Tipe File", org_profile.file_type.upper().replace(".", ""))
    with col3:
        if org_profile.uploaded_at:
            st.metric("Waktu Unggah", org_profile.uploaded_at.strftime("%d/%m/%Y %H:%M"))
    
    st.markdown("---")
    
    # Display organization profile summary
    st.subheader("📝 Ringkasan Profil Organisasi")
    st.markdown(
        """
        <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; 
                    border-left: 5px solid #1f77b4;">
        {}
        </div>
        """.format(org_profile.summary.replace("\n", "<br>")),
        unsafe_allow_html=True
    )
    
    st.markdown("---")
    
    # Display context overview
    st.subheader("🔍 Konteks Organisasi")
    st.markdown(
        """
        <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; 
                    border-left: 5px solid #2ca02c;">
        {}
        </div>
        """.format(org_profile.context_overview.replace("\n", "<br>")),
        unsafe_allow_html=True
    )
    
    st.markdown("---")
    
    # Optional: Show original text in expander
    with st.expander("📖 Lihat Teks Asli Dokumen"):
        st.text_area(
            "Teks yang diekstrak dari dokumen:",
            value=org_profile.original_text,
            height=300,
            disabled=True,
            key="original_text_display"
        )
    
    st.markdown("---")
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button(
            "⬅️ Kembali",
            use_container_width=True,
            help="Kembali ke halaman unggah dokumen"
        ):
            st.session_state.current_step = WorkflowStep.UPLOAD
            st.rerun()
    
    with col3:
        if st.button(
            "Lanjutkan ➡️",
            type="primary",
            use_container_width=True,
            help="Lanjut ke pemilihan jenis kursus"
        ):
            # Advance to course type selection
            st.session_state.current_step = WorkflowStep.COURSE_TYPE
            st.rerun()
    
    # Info message
    st.info(
        "💡 **Tips:** Pastikan ringkasan dan konteks organisasi sudah sesuai "
        "sebelum melanjutkan. Informasi ini akan digunakan untuk menghasilkan "
        "learning objectives yang relevan dengan organisasi Anda."
    )


def render_course_type_page(orchestrator: WorkflowOrchestrator) -> None:
    """
    Display course type selection interface.
    
    Allows users to select a course type which will be used as context
    for TLO generation.
    
    Args:
        orchestrator: Workflow orchestrator (not used but kept for consistency)
    
    Requirements: 3.1, 3.2
    """
    st.header("📚 Pilih Jenis Kursus")
    st.write(
        "Pilih jenis kursus yang ingin Anda buat. Pilihan ini akan membantu "
        "sistem menghasilkan Terminal Learning Objectives (TLO) yang sesuai "
        "dengan kategori kursus Anda."
    )
    
    st.markdown("---")
    
    # Check if organization profile exists
    if st.session_state.organization is None:
        show_error(
            "Profil organisasi tidak ditemukan. Silakan unggah dokumen terlebih dahulu."
        )
        if st.button("⬅️ Kembali ke Unggah", type="primary"):
            st.session_state.current_step = WorkflowStep.UPLOAD
            st.rerun()
        return
    
    # Define course type options
    course_types = {
        "B2B": {
            "title": "Business to Business (B2B)",
            "description": "Kursus yang dirancang untuk pelatihan antar perusahaan, "
                         "fokus pada keterampilan bisnis dan kolaborasi profesional.",
            "icon": "🏢"
        },
        "Innovation": {
            "title": "Innovation & Creativity",
            "description": "Kursus yang berfokus pada pengembangan inovasi, kreativitas, "
                         "dan pemikiran desain untuk solusi baru.",
            "icon": "💡"
        },
        "Tech": {
            "title": "Technology & IT",
            "description": "Kursus teknologi yang mencakup pengembangan software, "
                         "infrastruktur IT, dan keterampilan teknis.",
            "icon": "💻"
        },
        "Leadership": {
            "title": "Leadership & Management",
            "description": "Kursus kepemimpinan yang mengembangkan keterampilan "
                         "manajemen, kepemimpinan tim, dan pengambilan keputusan.",
            "icon": "👔"
        },
        "Sales": {
            "title": "Sales & Marketing",
            "description": "Kursus penjualan dan pemasaran yang fokus pada strategi "
                         "penjualan, pemasaran digital, dan hubungan pelanggan.",
            "icon": "📈"
        },
        "Operations": {
            "title": "Operations & Process",
            "description": "Kursus operasional yang mencakup manajemen proses, "
                         "efisiensi operasional, dan optimisasi sistem.",
            "icon": "⚙️"
        }
    }
    
    # Display course type options as cards
    st.subheader("Pilih Jenis Kursus:")
    
    # Create a grid layout for course type cards
    cols = st.columns(2)
    
    selected_type = st.session_state.course_type
    
    for idx, (key, info) in enumerate(course_types.items()):
        with cols[idx % 2]:
            # Create a card-like container
            with st.container():
                st.markdown(
                    f"""
                    <div style="padding: 15px; border-radius: 10px; 
                                border: 2px solid {'#1f77b4' if selected_type == key else '#e0e0e0'}; 
                                background-color: {'#e3f2fd' if selected_type == key else '#ffffff'};">
                        <h3>{info['icon']} {info['title']}</h3>
                        <p style="color: #666;">{info['description']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                # Radio button for selection
                if st.button(
                    f"Pilih {key}",
                    key=f"select_{key}",
                    type="primary" if selected_type == key else "secondary",
                    use_container_width=True
                ):
                    st.session_state.course_type = key
                    st.rerun()
                
                st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Show selected course type
    if selected_type:
        st.success(f"✅ Jenis kursus terpilih: **{course_types[selected_type]['title']}**")
        
        st.markdown("---")
        
        # Navigation buttons
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button(
                "⬅️ Kembali",
                use_container_width=True,
                help="Kembali ke halaman ringkasan"
            ):
                st.session_state.current_step = WorkflowStep.SUMMARY
                st.rerun()
        
        with col3:
            if st.button(
                "Lanjutkan ➡️",
                type="primary",
                use_container_width=True,
                help="Lanjut ke generasi TLO"
            ):
                # Advance to TLO generation
                st.session_state.current_step = WorkflowStep.TLO_GENERATION
                st.rerun()
    else:
        st.info("👆 Silakan pilih jenis kursus untuk melanjutkan")
        
        # Back button only
        if st.button(
            "⬅️ Kembali",
            use_container_width=False,
            help="Kembali ke halaman ringkasan"
        ):
            st.session_state.current_step = WorkflowStep.SUMMARY
            st.rerun()



def render_tlo_page(orchestrator: WorkflowOrchestrator) -> None:
    """
    Display TLO generation and selection interface.
    
    Generates Terminal Learning Objectives using AI based on organization
    context and course type, then allows users to select one or more TLOs.
    
    Args:
        orchestrator: Workflow orchestrator for TLO generation
    
    Requirements: 4.3, 5.1, 5.2, 5.3, 6.1
    """
    st.header("🎯 Terminal Learning Objectives (TLO)")
    st.write(
        "Terminal Learning Objectives adalah tujuan pembelajaran tingkat tinggi "
        "untuk kursus Anda. Sistem akan menghasilkan beberapa pilihan TLO "
        "berdasarkan profil organisasi dan jenis kursus yang dipilih."
    )
    
    st.markdown("---")
    
    # Check prerequisites
    if st.session_state.organization is None or st.session_state.course_type is None:
        show_error(
            "Informasi tidak lengkap. Silakan lengkapi langkah sebelumnya terlebih dahulu."
        )
        if st.button("⬅️ Kembali", type="primary"):
            st.session_state.current_step = WorkflowStep.COURSE_TYPE
            st.rerun()
        return
    
    # Display context information
    with st.expander("📋 Konteks Generasi", expanded=False):
        st.write(f"**Jenis Kursus:** {st.session_state.course_type}")
        st.write(f"**Organisasi:** {st.session_state.organization.file_name}")
    
    st.markdown("---")
    
    # Generate TLOs if not already generated
    if not st.session_state.tlos:
        st.subheader("🤖 Generasi TLO")
        st.write("Klik tombol di bawah untuk menghasilkan TLO dengan AI.")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "✨ Hasilkan TLO",
                type="primary",
                use_container_width=True
            ):
                generate_tlos(orchestrator)
    
    # Display generated TLOs with selection
    if st.session_state.tlos:
        st.subheader("📝 TLO yang Dihasilkan")
        st.write("Pilih satu atau lebih TLO yang sesuai dengan kebutuhan kursus Anda:")
        
        st.markdown("---")
        
        # Track selection changes
        selection_changed = False
        new_selections = []
        
        # Display TLOs with checkboxes
        for idx, tlo in enumerate(st.session_state.tlos):
            with st.container():
                col1, col2 = st.columns([0.1, 0.9])
                
                with col1:
                    # Checkbox for selection
                    is_selected = st.checkbox(
                        "",
                        value=tlo.id in st.session_state.selected_tlo_ids,
                        key=f"tlo_checkbox_{tlo.id}",
                        label_visibility="collapsed"
                    )
                    
                    # Track changes
                    if is_selected:
                        new_selections.append(tlo.id)
                        if tlo.id not in st.session_state.selected_tlo_ids:
                            selection_changed = True
                    elif tlo.id in st.session_state.selected_tlo_ids:
                        selection_changed = True
                
                with col2:
                    # Display TLO text
                    st.markdown(
                        f"""
                        <div style="padding: 15px; border-radius: 10px; 
                                    border-left: 5px solid {'#2ca02c' if is_selected else '#cccccc'}; 
                                    background-color: {'#e8f5e9' if is_selected else '#f5f5f5'};">
                            <strong>TLO {idx + 1}:</strong><br>
                            {tlo.text}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                st.markdown("<br>", unsafe_allow_html=True)
        
        # Persist selections to database if changed
        if selection_changed:
            try:
                # Update all TLO selections in database
                all_tlo_ids = [tlo.id for tlo in st.session_state.tlos]
                orchestrator.db.update_tlo_selections(all_tlo_ids, False)  # Deselect all first
                if new_selections:
                    orchestrator.db.update_tlo_selections(new_selections, True)  # Select chosen ones
                st.session_state.selected_tlo_ids = new_selections
            except Exception as e:
                show_error(f"Gagal menyimpan pilihan: {str(e)}")
        
        st.markdown("---")
        
        # Display selected TLOs
        if st.session_state.selected_tlo_ids:
            st.success(f"✅ {len(st.session_state.selected_tlo_ids)} TLO terpilih")
            
            with st.expander("Lihat TLO Terpilih", expanded=False):
                selected_tlos = [
                    tlo for tlo in st.session_state.tlos 
                    if tlo.id in st.session_state.selected_tlo_ids
                ]
                for idx, tlo in enumerate(selected_tlos):
                    st.write(f"**{idx + 1}.** {tlo.text}")
        else:
            st.info("ℹ️ Belum ada TLO yang dipilih. Pilih setidaknya satu TLO untuk melanjutkan.")
        
        st.markdown("---")
        
        # Navigation buttons
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button(
                "⬅️ Kembali",
                use_container_width=True,
                help="Kembali ke pemilihan jenis kursus"
            ):
                st.session_state.current_step = WorkflowStep.COURSE_TYPE
                st.rerun()
        
        with col2:
            # Regenerate button
            if st.button(
                "🔄 Hasilkan Ulang TLO",
                use_container_width=True,
                help="Hasilkan TLO baru"
            ):
                st.session_state.tlos = []
                st.session_state.selected_tlo_ids = []
                st.rerun()
        
        with col3:
            if st.button(
                "Lanjutkan ➡️",
                type="primary",
                use_container_width=True,
                help="Lanjut ke generasi performance",
                disabled=len(st.session_state.selected_tlo_ids) == 0
            ):
                # Advance to performance generation
                st.session_state.current_step = WorkflowStep.PERFORMANCE_GENERATION
                st.rerun()


def generate_tlos(orchestrator: WorkflowOrchestrator) -> None:
    """Generate TLOs using the orchestrator"""
    try:
        with with_spinner("Menghasilkan TLO dengan AI..."):
            tlos = orchestrator.generate_tlos(
                org_id=st.session_state.organization.id,
                course_type=st.session_state.course_type
            )
            st.session_state.tlos = tlos
            st.session_state.selected_tlo_ids = []
        
        show_success(f"Berhasil menghasilkan {len(tlos)} TLO!")
        st.rerun()
    
    except Exception as e:
        show_error(f"Terjadi kesalahan saat menghasilkan TLO: {str(e)}")
        st.info("Silakan coba lagi atau hubungi administrator jika masalah berlanjut.")



def render_performance_page(orchestrator: WorkflowOrchestrator) -> None:
    """
    Display performance generation and selection interface.
    
    Generates performance objectives using AI based on selected TLOs,
    then allows users to select one or more performances.
    
    Args:
        orchestrator: Workflow orchestrator for performance generation
    
    Requirements: 6.4, 7.1, 7.2, 7.3
    """
    st.header("🎪 Performance Objectives")
    st.write(
        "Performance objectives adalah tujuan berbasis kinerja yang diturunkan "
        "dari TLO yang Anda pilih. Sistem akan menghasilkan beberapa pilihan "
        "performance objectives berdasarkan TLO terpilih."
    )
    
    st.markdown("---")
    
    # Check prerequisites
    if not st.session_state.selected_tlo_ids:
        show_error(
            "Belum ada TLO yang dipilih. Silakan pilih TLO terlebih dahulu."
        )
        if st.button("⬅️ Kembali ke TLO", type="primary"):
            st.session_state.current_step = WorkflowStep.TLO_GENERATION
            st.rerun()
        return
    
    # Display context information
    with st.expander("📋 Konteks Generasi", expanded=False):
        st.write(f"**Jumlah TLO Terpilih:** {len(st.session_state.selected_tlo_ids)}")
        selected_tlos = [
            tlo for tlo in st.session_state.tlos 
            if tlo.id in st.session_state.selected_tlo_ids
        ]
        for idx, tlo in enumerate(selected_tlos):
            st.write(f"**TLO {idx + 1}:** {tlo.text}")
    
    st.markdown("---")
    
    # Generate performances if not already generated
    if not st.session_state.performances:
        st.subheader("🤖 Generasi Performance")
        st.write("Klik tombol di bawah untuk menghasilkan performance objectives dengan AI.")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "✨ Hasilkan Performance",
                type="primary",
                use_container_width=True
            ):
                generate_performances(orchestrator)
    
    # Display generated performances with selection
    if st.session_state.performances:
        st.subheader("📝 Performance yang Dihasilkan")
        st.write("Pilih satu atau lebih performance yang sesuai dengan kebutuhan kursus Anda:")
        
        st.markdown("---")
        
        # Track selection changes
        selection_changed = False
        new_selections = []
        
        # Display performances with checkboxes
        for idx, performance in enumerate(st.session_state.performances):
            with st.container():
                col1, col2 = st.columns([0.1, 0.9])
                
                with col1:
                    # Checkbox for selection
                    is_selected = st.checkbox(
                        "",
                        value=performance.id in st.session_state.selected_performance_ids,
                        key=f"perf_checkbox_{performance.id}",
                        label_visibility="collapsed"
                    )
                    
                    # Track changes
                    if is_selected:
                        new_selections.append(performance.id)
                        if performance.id not in st.session_state.selected_performance_ids:
                            selection_changed = True
                    elif performance.id in st.session_state.selected_performance_ids:
                        selection_changed = True
                
                with col2:
                    # Display performance text
                    st.markdown(
                        f"""
                        <div style="padding: 15px; border-radius: 10px; 
                                    border-left: 5px solid {'#ff7f0e' if is_selected else '#cccccc'}; 
                                    background-color: {'#fff3e0' if is_selected else '#f5f5f5'};">
                            <strong>Performance {idx + 1}:</strong><br>
                            {performance.text}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                st.markdown("<br>", unsafe_allow_html=True)
        
        # Persist selections to database if changed
        if selection_changed:
            try:
                # Update all performance selections in database
                all_perf_ids = [perf.id for perf in st.session_state.performances]
                orchestrator.db.update_performance_selections(all_perf_ids, False)  # Deselect all first
                if new_selections:
                    orchestrator.db.update_performance_selections(new_selections, True)  # Select chosen ones
                st.session_state.selected_performance_ids = new_selections
            except Exception as e:
                show_error(f"Gagal menyimpan pilihan: {str(e)}")
        
        st.markdown("---")
        
        # Display selected performances
        if st.session_state.selected_performance_ids:
            st.success(f"✅ {len(st.session_state.selected_performance_ids)} Performance terpilih")
            
            with st.expander("Lihat Performance Terpilih", expanded=False):
                selected_perfs = [
                    perf for perf in st.session_state.performances 
                    if perf.id in st.session_state.selected_performance_ids
                ]
                for idx, perf in enumerate(selected_perfs):
                    st.write(f"**{idx + 1}.** {perf.text}")
        else:
            st.info("ℹ️ Belum ada performance yang dipilih. Pilih setidaknya satu performance untuk melanjutkan.")
        
        st.markdown("---")
        
        # Navigation buttons
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button(
                "⬅️ Kembali",
                use_container_width=True,
                help="Kembali ke pemilihan TLO"
            ):
                st.session_state.current_step = WorkflowStep.TLO_GENERATION
                st.rerun()
        
        with col2:
            # Regenerate button
            if st.button(
                "🔄 Hasilkan Ulang Performance",
                use_container_width=True,
                help="Hasilkan performance baru"
            ):
                st.session_state.performances = []
                st.session_state.selected_performance_ids = []
                st.rerun()
        
        with col3:
            if st.button(
                "Lanjutkan ➡️",
                type="primary",
                use_container_width=True,
                help="Lanjut ke generasi ELO",
                disabled=len(st.session_state.selected_performance_ids) == 0
            ):
                # Advance to ELO generation
                st.session_state.current_step = WorkflowStep.ELO_GENERATION
                st.rerun()


def generate_performances(orchestrator: WorkflowOrchestrator) -> None:
    """Generate performances using the orchestrator"""
    try:
        with with_spinner("Menghasilkan performance objectives dengan AI..."):
            performances = orchestrator.generate_performances(
                selected_tlo_ids=st.session_state.selected_tlo_ids,
                org_id=st.session_state.organization.id
            )
            st.session_state.performances = performances
            st.session_state.selected_performance_ids = []
        
        show_success(f"Berhasil menghasilkan {len(performances)} performance objectives!")
        st.rerun()
    
    except Exception as e:
        show_error(f"Terjadi kesalahan saat menghasilkan performance: {str(e)}")
        st.info("Silakan coba lagi atau hubungi administrator jika masalah berlanjut.")



def render_elo_page(orchestrator: WorkflowOrchestrator) -> None:
    """
    Display ELO generation and selection interface.
    
    Generates Enabling Learning Objectives using AI based on selected performances,
    then allows users to select multiple ELOs.
    
    Args:
        orchestrator: Workflow orchestrator for ELO generation
    
    Requirements: 8.3, 9.1, 9.2, 9.3
    """
    st.header("🎓 Enabling Learning Objectives (ELO)")
    st.write(
        "Enabling Learning Objectives adalah tujuan pembelajaran spesifik yang "
        "mendukung performance objectives. Sistem akan menghasilkan beberapa "
        "pilihan ELO berdasarkan performance yang Anda pilih."
    )
    
    st.markdown("---")
    
    # Check prerequisites
    if not st.session_state.selected_performance_ids:
        show_error(
            "Belum ada performance yang dipilih. Silakan pilih performance terlebih dahulu."
        )
        if st.button("⬅️ Kembali ke Performance", type="primary"):
            st.session_state.current_step = WorkflowStep.PERFORMANCE_GENERATION
            st.rerun()
        return
    
    # Display context information
    with st.expander("📋 Konteks Generasi", expanded=False):
        st.write(f"**Jumlah Performance Terpilih:** {len(st.session_state.selected_performance_ids)}")
        selected_perfs = [
            perf for perf in st.session_state.performances 
            if perf.id in st.session_state.selected_performance_ids
        ]
        for idx, perf in enumerate(selected_perfs):
            st.write(f"**Performance {idx + 1}:** {perf.text}")
    
    st.markdown("---")
    
    # Generate ELOs if not already generated
    if not st.session_state.elos:
        st.subheader("🤖 Generasi ELO")
        st.write("Klik tombol di bawah untuk menghasilkan ELO dengan AI.")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "✨ Hasilkan ELO",
                type="primary",
                use_container_width=True
            ):
                generate_elos(orchestrator)
    
    # Display generated ELOs with selection
    if st.session_state.elos:
        st.subheader("📝 ELO yang Dihasilkan")
        st.write("Pilih beberapa ELO yang sesuai dengan kebutuhan kursus Anda:")
        
        st.markdown("---")
        
        # Track selection changes
        selection_changed = False
        new_selections = []
        
        # Display ELOs with checkboxes
        for idx, elo in enumerate(st.session_state.elos):
            with st.container():
                col1, col2 = st.columns([0.1, 0.9])
                
                with col1:
                    # Checkbox for selection
                    is_selected = st.checkbox(
                        "",
                        value=elo.id in st.session_state.selected_elo_ids,
                        key=f"elo_checkbox_{elo.id}",
                        label_visibility="collapsed"
                    )
                    
                    # Track changes
                    if is_selected:
                        new_selections.append(elo.id)
                        if elo.id not in st.session_state.selected_elo_ids:
                            selection_changed = True
                    elif elo.id in st.session_state.selected_elo_ids:
                        selection_changed = True
                
                with col2:
                    # Display ELO text
                    st.markdown(
                        f"""
                        <div style="padding: 15px; border-radius: 10px; 
                                    border-left: 5px solid {'#9467bd' if is_selected else '#cccccc'}; 
                                    background-color: {'#f3e5f5' if is_selected else '#f5f5f5'};">
                            <strong>ELO {idx + 1}:</strong><br>
                            {elo.text}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                st.markdown("<br>", unsafe_allow_html=True)
        
        # Persist selections to database if changed
        if selection_changed:
            try:
                # Update all ELO selections in database
                all_elo_ids = [elo.id for elo in st.session_state.elos]
                orchestrator.db.update_elo_selections(all_elo_ids, False)  # Deselect all first
                if new_selections:
                    orchestrator.db.update_elo_selections(new_selections, True)  # Select chosen ones
                st.session_state.selected_elo_ids = new_selections
            except Exception as e:
                show_error(f"Gagal menyimpan pilihan: {str(e)}")
        
        st.markdown("---")
        
        # Display selected ELOs
        if st.session_state.selected_elo_ids:
            st.success(f"✅ {len(st.session_state.selected_elo_ids)} ELO terpilih")
            
            with st.expander("Lihat ELO Terpilih", expanded=False):
                selected_elos = [
                    elo for elo in st.session_state.elos 
                    if elo.id in st.session_state.selected_elo_ids
                ]
                for idx, elo in enumerate(selected_elos):
                    st.write(f"**{idx + 1}.** {elo.text}")
        else:
            st.info("ℹ️ Belum ada ELO yang dipilih. Pilih setidaknya satu ELO untuk melanjutkan.")
        
        st.markdown("---")
        
        # Navigation buttons
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button(
                "⬅️ Kembali",
                use_container_width=True,
                help="Kembali ke pemilihan performance"
            ):
                st.session_state.current_step = WorkflowStep.PERFORMANCE_GENERATION
                st.rerun()
        
        with col2:
            # Regenerate button
            if st.button(
                "🔄 Hasilkan Ulang ELO",
                use_container_width=True,
                help="Hasilkan ELO baru"
            ):
                st.session_state.elos = []
                st.session_state.selected_elo_ids = []
                st.rerun()
        
        with col3:
            if st.button(
                "Lanjutkan ➡️",
                type="primary",
                use_container_width=True,
                help="Lanjut ke pembuatan silabus",
                disabled=len(st.session_state.selected_elo_ids) == 0
            ):
                # Advance to syllabus generation
                st.session_state.current_step = WorkflowStep.SYLLABUS_GENERATION
                st.rerun()


def generate_elos(orchestrator: WorkflowOrchestrator) -> None:
    """Generate ELOs using the orchestrator"""
    try:
        with with_spinner("Menghasilkan ELO dengan AI..."):
            elos = orchestrator.generate_elos(
                selected_performance_ids=st.session_state.selected_performance_ids
            )
            st.session_state.elos = elos
            st.session_state.selected_elo_ids = []
        
        show_success(f"Berhasil menghasilkan {len(elos)} ELO!")
        st.rerun()
    
    except Exception as e:
        show_error(f"Terjadi kesalahan saat menghasilkan ELO: {str(e)}")
        st.info("Silakan coba lagi atau hubungi administrator jika masalah berlanjut.")



def render_syllabus_page(orchestrator: WorkflowOrchestrator) -> None:
    """
    Display syllabus generation and download interface.
    
    Compiles all selected materials into a final syllabus document
    and provides download functionality.
    
    Args:
        orchestrator: Workflow orchestrator for syllabus generation
    
    Requirements: 10.6
    """
    st.header("📄 Generasi Dokumen Silabus")
    st.write(
        "Langkah terakhir! Sistem akan mengkompilasi semua material yang telah "
        "Anda pilih menjadi dokumen silabus lengkap dalam format DOCX."
    )
    
    st.markdown("---")
    
    # Check prerequisites
    if not st.session_state.selected_elo_ids:
        show_error(
            "Belum ada ELO yang dipilih. Silakan lengkapi langkah sebelumnya terlebih dahulu."
        )
        if st.button("⬅️ Kembali ke ELO", type="primary"):
            st.session_state.current_step = WorkflowStep.ELO_GENERATION
            st.rerun()
        return
    
    # Display summary of selections
    st.subheader("📊 Ringkasan Material Terpilih")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Jenis Kursus",
            st.session_state.course_type,
            delta=None
        )
    
    with col2:
        st.metric(
            "TLO Terpilih",
            len(st.session_state.selected_tlo_ids),
            delta=None
        )
    
    with col3:
        st.metric(
            "Performance Terpilih",
            len(st.session_state.selected_performance_ids),
            delta=None
        )
    
    with col4:
        st.metric(
            "ELO Terpilih",
            len(st.session_state.selected_elo_ids),
            delta=None
        )
    
    st.markdown("---")
    
    # Show detailed selections in expanders
    with st.expander("📋 Lihat Detail Material Terpilih", expanded=False):
        # TLOs
        st.write("**Terminal Learning Objectives:**")
        selected_tlos = [
            tlo for tlo in st.session_state.tlos 
            if tlo.id in st.session_state.selected_tlo_ids
        ]
        for idx, tlo in enumerate(selected_tlos):
            st.write(f"{idx + 1}. {tlo.text}")
        
        st.markdown("---")
        
        # Performances
        st.write("**Performance Objectives:**")
        selected_perfs = [
            perf for perf in st.session_state.performances 
            if perf.id in st.session_state.selected_performance_ids
        ]
        for idx, perf in enumerate(selected_perfs):
            st.write(f"{idx + 1}. {perf.text}")
        
        st.markdown("---")
        
        # ELOs
        st.write("**Enabling Learning Objectives:**")
        selected_elos = [
            elo for elo in st.session_state.elos 
            if elo.id in st.session_state.selected_elo_ids
        ]
        for idx, elo in enumerate(selected_elos):
            st.write(f"{idx + 1}. {elo.text}")
    
    st.markdown("---")
    
    # Generate syllabus section
    if st.session_state.syllabus is None:
        st.subheader("🚀 Buat Dokumen Silabus")
        st.write(
            "Klik tombol di bawah untuk menghasilkan dokumen silabus lengkap. "
            "Proses ini akan mengkompilasi semua material yang telah Anda pilih "
            "menjadi dokumen DOCX yang siap digunakan."
        )
        
        st.info(
            "💡 **Tips:** Dokumen silabus akan mencakup:\n"
            "- Profil dan konteks organisasi\n"
            "- Terminal Learning Objectives (TLO)\n"
            "- Performance Objectives\n"
            "- Enabling Learning Objectives (ELO)\n"
            "- Format profesional dan terstruktur"
        )
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "📝 Buat Dokumen Silabus",
                type="primary",
                use_container_width=True
            ):
                generate_syllabus(orchestrator)
    
    # Display download section if syllabus is generated
    else:
        st.success("✅ Dokumen silabus berhasil dibuat!")
        
        st.subheader("📥 Unduh Dokumen Silabus")
        st.write("Dokumen silabus Anda sudah siap. Klik tombol di bawah untuk mengunduh.")
        
        # Create download button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.download_button(
                label="⬇️ Unduh Silabus (DOCX)",
                data=st.session_state.syllabus.document_content,
                file_name=f"silabus_{st.session_state.course_type}_{st.session_state.session_id[:8]}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
                use_container_width=True
            )
        
        st.markdown("---")
        
        # Success message and next steps
        st.balloons()
        
        st.markdown(
            """
            <div style="background-color: #e8f5e9; padding: 20px; border-radius: 10px; 
                        border-left: 5px solid #2ca02c;">
                <h3>🎉 Selamat!</h3>
                <p>Dokumen silabus Anda telah berhasil dibuat. Anda dapat:</p>
                <ul>
                    <li>Mengunduh dokumen dan menggunakannya langsung</li>
                    <li>Mengedit dokumen sesuai kebutuhan Anda</li>
                    <li>Membuat silabus baru dengan memulai ulang proses</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("---")
        
        # Option to start over
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "🔄 Buat Silabus Baru",
                use_container_width=True,
                help="Mulai proses baru dari awal"
            ):
                # Clear all session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
    
    # Back button (always available)
    st.markdown("---")
    if st.button(
        "⬅️ Kembali ke ELO",
        use_container_width=False,
        help="Kembali ke pemilihan ELO"
    ):
        st.session_state.current_step = WorkflowStep.ELO_GENERATION
        st.rerun()


def generate_syllabus(orchestrator: WorkflowOrchestrator) -> None:
    """Generate syllabus document using the orchestrator"""
    try:
        with with_spinner("Menghasilkan dokumen silabus..."):
            document_content = orchestrator.create_syllabus_document(
                session_id=st.session_state.session_id,
                org_id=st.session_state.organization.id,
                course_type=st.session_state.course_type,
                selected_tlo_ids=st.session_state.selected_tlo_ids,
                selected_performance_ids=st.session_state.selected_performance_ids,
                selected_elo_ids=st.session_state.selected_elo_ids
            )
            # Create a syllabus object to store in session state
            from src.models.entities import Syllabus
            syllabus = Syllabus(
                session_id=st.session_state.session_id,
                org_id=st.session_state.organization.id,
                course_type=st.session_state.course_type,
                selected_tlo_ids=st.session_state.selected_tlo_ids,
                selected_performance_ids=st.session_state.selected_performance_ids,
                selected_elo_ids=st.session_state.selected_elo_ids,
                document_content=document_content
            )
            st.session_state.syllabus = syllabus
        
        show_success("Dokumen silabus berhasil dibuat!")
        st.rerun()
    
    except Exception as e:
        show_error(f"Terjadi kesalahan saat membuat silabus: {str(e)}")
        st.info("Silakan coba lagi atau hubungi administrator jika masalah berlanjut.")
        st.exception(e)
