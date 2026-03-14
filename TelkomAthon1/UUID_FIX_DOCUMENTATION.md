# Perbaikan Error UUID Type Casting

## Masalah
Ketika memilih TLO (Terminal Learning Objectives) di aplikasi, muncul error:
```
❌ Gagal menyimpan pilihan: Operasi database gagal: operator does not exist: uuid = text
LINE 4: WHERE id = ANY(ARRAY['6a2479b2-129a-4505...
HINT: No operator matches the given name and argument types. You might need to add explicit type casts.
```

## Penyebab
PostgreSQL tidak bisa secara otomatis mengkonversi array Python string ke array UUID. Query SQL seperti:
```sql
WHERE id = ANY(%s)
```
dengan parameter berupa list string Python akan gagal karena kolom `id` bertipe UUID.

## Solusi
Menambahkan explicit type cast `::uuid[]` pada semua query yang menggunakan `ANY(%s)` dengan UUID:
```sql
WHERE id = ANY(%s::uuid[])
```

## File yang Diperbaiki
`src/database/service.py` - 8 fungsi diperbaiki:

1. `update_tlo_selections()` - Update multiple TLO selections
2. `update_performance_selections()` - Update multiple Performance selections  
3. `update_elo_selections()` - Update multiple ELO selections
4. `get_performances_by_tlos()` - Retrieve performances by TLO IDs
5. `get_performances_by_ids()` - Retrieve performances by IDs
6. `get_selected_performances()` - Get selected performances
7. `get_elos_by_performances()` - Retrieve ELOs by performance IDs
8. `get_selected_elos()` - Get selected ELOs

## Testing
Jalankan test untuk memverifikasi perbaikan:
```bash
python test_uuid_fix.py
```

## Dampak
- ✅ User sekarang bisa memilih TLO tanpa error
- ✅ User bisa memilih Performance objectives tanpa error
- ✅ User bisa memilih ELO tanpa error
- ✅ Semua operasi database yang melibatkan array UUID sekarang bekerja dengan benar
