"""
Test untuk memverifikasi perbaikan UUID type casting
"""
import os
from dotenv import load_dotenv
from src.database.service import DatabaseService
from src.models.entities import TLO
from datetime import datetime

# Load environment variables
load_dotenv()

def test_tlo_selection():
    """Test update_tlo_selections dengan multiple UUIDs"""
    db = DatabaseService(os.getenv('DATABASE_URL'))
    
    try:
        # Buat beberapa TLO untuk testing
        test_tlos = [
            TLO(
                id=None,
                org_id="00000000-0000-0000-0000-000000000001",
                course_type="Test Course",
                text=f"Test TLO {i}",
                generated_at=datetime.now(),
                is_selected=False
            )
            for i in range(3)
        ]
        
        # Simpan TLOs
        tlo_ids = db.save_tlos(test_tlos, "00000000-0000-0000-0000-000000000001", "Test Course")
        print(f"✅ Berhasil menyimpan {len(tlo_ids)} TLOs")
        print(f"   TLO IDs: {tlo_ids}")
        
        # Update selections - ini yang sebelumnya error
        db.update_tlo_selections(tlo_ids, True)
        print(f"✅ Berhasil update selections untuk {len(tlo_ids)} TLOs")
        
        # Verifikasi update berhasil
        selected_tlos = db.get_selected_tlos("00000000-0000-0000-0000-000000000001")
        print(f"✅ Berhasil retrieve {len(selected_tlos)} selected TLOs")
        
        # Cleanup
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM tlos WHERE org_id = %s", ("00000000-0000-0000-0000-000000000001",))
        
        print("\n🎉 Semua test berhasil! UUID type casting sudah diperbaiki.")
        
    except Exception as e:
        print(f"\n❌ Test gagal: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    test_tlo_selection()
