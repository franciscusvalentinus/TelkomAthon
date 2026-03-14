# Task 9.2 Implementation: Organization Profile Upload Page

## Overview
Implemented the organization profile upload page with file upload widget, submit button handler, processing status display, and error handling with Indonesian messages.

## Implementation Details

### 1. Created `src/ui/pages.py` Module

This new module contains the UI page components for the Streamlit application:

#### `render_upload_page(orchestrator: WorkflowOrchestrator)`
- Displays header and instructions in Indonesian
- Shows supported file formats (PDF, DOCX, TXT) and size limit (10 MB)
- Provides file upload widget with type restrictions
- Displays file information when uploaded (name, size, type)
- Validates file size (rejects files > 10 MB)
- Provides "Proses Dokumen" button to submit
- Calls `process_uploaded_document()` when button is clicked

#### `process_uploaded_document(orchestrator, uploaded_file)`
- Shows processing spinner with Indonesian message "Memproses dokumen..."
- Reads file content and extracts file extension
- Calls `orchestrator.process_organization_profile()` to process the document
- Updates session state with organization profile and advances to SUMMARY step
- Shows success message and balloons animation
- Displays preview of generated summary in expandable section
- Provides button to continue to next step
- Handles errors with Indonesian messages:
  - `UnsupportedFormatError`: "Format file tidak didukung..."
  - `EmptyFileError`: "File kosong atau tidak dapat dibaca..."
  - General exceptions: "Terjadi kesalahan saat memproses dokumen..."

### 2. Updated `app.py`

Modified the main application to integrate the upload page:

- Added imports for `DatabaseService`, `AIService`, `WorkflowOrchestrator`, and `render_upload_page`
- Updated `main()` function to initialize services:
  - Creates `DatabaseService` instance
  - Creates `AIService` instance
  - Creates `WorkflowOrchestrator` instance
  - Handles initialization errors with Indonesian messages
- Updated `render_main_content()` to accept `orchestrator` parameter
- Replaced placeholder for UPLOAD step with actual `render_upload_page()` call

### 3. Created Unit Tests

Created `tests/unit/test_upload_page.py` with comprehensive test coverage:

#### Test Classes:
1. **TestUploadPageRendering**
   - Tests UI element rendering (header, file uploader, info messages)
   - Tests file info display when file is uploaded
   - Tests button creation

2. **TestDocumentProcessing**
   - Tests successful document processing flow
   - Tests session state updates
   - Tests error handling for unsupported formats
   - Tests error handling for empty files
   - Tests general error handling

3. **TestFileSizeValidation**
   - Tests rejection of files exceeding 10 MB limit

4. **TestIndonesianErrorMessages**
   - Verifies all error messages are in Indonesian

### 4. Error Handling

Implemented comprehensive error handling with Indonesian messages:

| Error Type | Indonesian Message | Additional Info |
|------------|-------------------|-----------------|
| Unsupported Format | "Format file tidak didukung. Silakan unggah file PDF, DOCX, atau TXT." | Shows list of supported formats |
| Empty File | "File kosong atau tidak dapat dibaca. Silakan unggah file yang valid..." | Provides tips for valid files |
| File Too Large | "Ukuran file terlalu besar (X MB). Maksimum 10 MB." | Shows actual file size |
| General Error | "Terjadi kesalahan saat memproses dokumen: {error}" | Shows exception details |

## Requirements Validation

### Requirement 1.1 ✅
**WHEN a user uploads an organization profile document, THE System SHALL accept common document formats (PDF, DOCX, TXT)**
- Implemented: File uploader accepts only PDF, DOCX, TXT formats
- Validation: Type restrictions in `st.file_uploader(type=["pdf", "docx", "txt"])`

### Requirement 1.4 ✅
**IF document upload fails or format is unsupported, THEN THE System SHALL display an error message and allow re-upload**
- Implemented: Error handling for `UnsupportedFormatError` and `EmptyFileError`
- User can upload a new file after error without page refresh

### Requirement 13.6 ✅
**WHEN an error occurs, THE System SHALL display user-friendly error messages in Indonesian**
- Implemented: All error messages are in Indonesian
- Messages are user-friendly and provide actionable guidance

## Integration Points

### With Workflow Orchestrator
- Calls `orchestrator.process_organization_profile(file_content, file_type, file_name)`
- Receives `OrganizationProfile` entity with generated summary
- Handles all exceptions raised by orchestrator

### With Session State
- Updates `st.session_state.organization` with processed profile
- Updates `st.session_state.current_step` to `WorkflowStep.SUMMARY`
- Triggers page rerun to show next step

### With UI Utils
- Uses `show_error()` for error messages
- Uses `show_success()` for success messages
- Uses `show_info()` for informational messages
- Uses `with_spinner()` for processing status

## User Experience Flow

1. User sees upload page with instructions in Indonesian
2. User sees supported formats and size limit
3. User selects file using file uploader
4. System displays file information (name, size, type)
5. System validates file size (rejects if > 10 MB)
6. User clicks "Proses Dokumen" button
7. System shows spinner "Memproses dokumen..."
8. System processes document through orchestrator:
   - Extracts text from document
   - Generates AI summary
   - Stores in database
9. System shows success message and balloons
10. System displays preview of summary
11. User clicks "Lanjut ke Ringkasan Lengkap" to continue
12. System advances to SUMMARY step

## Testing Strategy

### Unit Tests
- Mock all Streamlit functions to test logic
- Test UI element rendering
- Test document processing flow
- Test error handling for all error types
- Test Indonesian language messages

### Manual Testing
Created `test_upload_page_manual.py` for manual verification:
- Tests upload page rendering
- Tests successful document processing
- Tests error handling
- Tests Indonesian messages

## Files Modified/Created

### Created:
- `src/ui/pages.py` - Upload page UI components
- `tests/unit/test_upload_page.py` - Unit tests
- `test_upload_page_manual.py` - Manual test script
- `TASK_9_2_IMPLEMENTATION.md` - This document

### Modified:
- `app.py` - Integrated upload page and services

## Code Quality

### Indonesian Language
All user-facing text is in Indonesian:
- UI labels and instructions
- Error messages
- Success messages
- Button text
- Help text

### Error Handling
Comprehensive error handling for:
- Unsupported file formats
- Empty files
- File size limits
- Document processing errors
- Service initialization errors

### Code Organization
- Separated UI components into `src/ui/pages.py`
- Reused utility functions from `src/ui/utils.py`
- Followed existing code patterns and conventions

## Next Steps

Task 9.2 is complete. The next task (9.3) will implement the organization summary display page, which will:
- Display the full organization profile summary
- Display the context overview
- Provide a button to continue to course type selection

## Verification

To verify the implementation:

1. **Check file structure:**
   ```bash
   ls src/ui/pages.py
   ls tests/unit/test_upload_page.py
   ```

2. **Check for syntax errors:**
   ```bash
   python -m py_compile src/ui/pages.py
   python -m py_compile app.py
   ```

3. **Run unit tests:**
   ```bash
   pytest tests/unit/test_upload_page.py -v
   ```

4. **Run manual tests:**
   ```bash
   python test_upload_page_manual.py
   ```

5. **Start the application:**
   ```bash
   streamlit run app.py
   ```

## Screenshots (Conceptual)

### Upload Page - Initial State
```
📚 Sistem Generasi Silabus Berbasis AI
Buat silabus kursus secara otomatis dengan bantuan AI
---

📤 Unggah Profil Organisasi
Unggah dokumen profil organisasi Anda untuk memulai proses...

ℹ️ Format yang didukung: PDF (.pdf), Word (.docx), Text (.txt)
   Ukuran maksimum: 10 MB

[File Upload Widget]

👆 Silakan pilih file untuk diunggah
```

### Upload Page - File Selected
```
✅ File dipilih: company_profile.pdf
Ukuran: 245.67 KB
Tipe: application/pdf

---

[     🚀 Proses Dokumen     ]
```

### Upload Page - Processing
```
⏳ Memproses dokumen...
```

### Upload Page - Success
```
✅ Dokumen berhasil diproses!
🎈🎈🎈

---

📋 Ringkasan Profil Organisasi
▼ Lihat ringkasan
   [Summary text displayed here...]

---

[  ➡️ Lanjut ke Ringkasan Lengkap  ]
```

### Upload Page - Error
```
❌ Format file tidak didukung. Silakan unggah file PDF, DOCX, atau TXT.

ℹ️ Format yang didukung:
   - PDF (.pdf)
   - Microsoft Word (.docx)
   - Text (.txt)
```
