"""
Example usage of DocumentGenerator

This example demonstrates how to use the DocumentGenerator class
to create a formatted syllabus document.
"""

from src.processors.document_generator import DocumentGenerator
from src.models.entities import SyllabusMaterials, TLO, Performance, ELO


def main():
    """Example of generating a syllabus document"""
    
    # Create sample learning objectives
    tlo1 = TLO(
        id="tlo-1",
        org_id="org-1",
        course_type="Innovation",
        text="Peserta mampu memahami prinsip-prinsip inovasi dalam bisnis",
        is_selected=True
    )
    
    tlo2 = TLO(
        id="tlo-2",
        org_id="org-1",
        course_type="Innovation",
        text="Peserta mampu menerapkan metodologi design thinking",
        is_selected=True
    )
    
    # Create sample performance objectives
    perf1 = Performance(
        id="perf-1",
        tlo_ids=["tlo-1"],
        text="Mengidentifikasi peluang inovasi dalam organisasi",
        is_selected=True
    )
    
    perf2 = Performance(
        id="perf-2",
        tlo_ids=["tlo-2"],
        text="Memfasilitasi sesi brainstorming dengan tim",
        is_selected=True
    )
    
    # Create sample enabling learning objectives
    elo1 = ELO(
        id="elo-1",
        performance_ids=["perf-1"],
        text="Menjelaskan berbagai jenis inovasi (produk, proses, model bisnis)",
        is_selected=True
    )
    
    elo2 = ELO(
        id="elo-2",
        performance_ids=["perf-1"],
        text="Menganalisis tren pasar untuk mengidentifikasi peluang",
        is_selected=True
    )
    
    elo3 = ELO(
        id="elo-3",
        performance_ids=["perf-2"],
        text="Menerapkan teknik brainstorming yang efektif",
        is_selected=True
    )
    
    # Create syllabus materials
    materials = SyllabusMaterials(
        organization_summary="PT Inovasi Teknologi adalah perusahaan startup yang fokus pada pengembangan solusi digital inovatif untuk industri retail.",
        organization_context="Dengan tim yang terdiri dari para ahli teknologi dan bisnis, perusahaan ini berkomitmen untuk menghadirkan transformasi digital bagi klien-kliennya.",
        selected_tlos=[tlo1, tlo2],
        selected_performances=[perf1, perf2],
        selected_elos=[elo1, elo2, elo3],
        course_type="Innovation"
    )
    
    # Create document generator
    generator = DocumentGenerator()
    
    # Generate the syllabus document
    print("Generating syllabus document...")
    doc_bytes = generator.create_syllabus_document(materials)
    
    # Save to file
    output_file = "example_syllabus.docx"
    with open(output_file, 'wb') as f:
        f.write(doc_bytes)
    
    print(f"✓ Syllabus document generated successfully!")
    print(f"✓ Saved to: {output_file}")
    print(f"✓ File size: {len(doc_bytes)} bytes")


if __name__ == "__main__":
    main()
