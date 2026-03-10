# Manual Testing Guide - AI-Powered Syllabus Generation System

## Overview

This document provides a comprehensive manual testing checklist for the AI-Powered Syllabus Generation System. Follow these steps to verify that all functionality works correctly.

## Prerequisites

Before starting manual testing:

1. ✅ Database is running and migrated
2. ✅ Environment variables are configured in `.env`
3. ✅ Application is running: `streamlit run app.py`
4. ✅ Test documents are prepared (PDF, DOCX, TXT)

## Test Scenarios

### Test 1: Organization Profile Upload

**Objective**: Verify that users can upload organization profile documents in supported formats.

#### Test Steps:

1. **Navigate to Upload Page**
   - [ ] Application opens to the upload page
   - [ ] Page title is in Indonesian: "📚 Sistem Generasi Silabus Berbasis AI"
   - [ ] Upload instructions are displayed in Indonesian

2. **Test PDF Upload**
   - [ ] Click "Browse files" button
   - [ ] Select a PDF file containing organization profile
   - [ ] Click "Proses Dokumen" (Process Document) button
   - [ ] Verify processing indicator appears
   - [ ] Verify success message appears in Indonesian
   - [ ] Verify application advances to Summary page

3. **Test DOCX Upload**
   - [ ] Reset application (click "Mulai Ulang" in sidebar)
   - [ ] Upload a DOCX file
   - [ ] Verify successful processing
   - [ ] Verify advancement to Summary page

4. **Test TXT Upload**
   - [ ] Reset application
   - [ ] Upload a TXT file
   - [ ] Verify successful processing
   - [ ] Verify advancement to Summary page

5. **Test Unsupported Format**
   - [ ] Reset application
   - [ ] Try to upload an unsupported file (e.g., .jpg, .png, .exe)
   - [ ] Verify error message appears in Indonesian
   - [ ] Verify message lists supported formats (PDF, DOCX, TXT)
   - [ ] Verify user remains on upload page

6. **Test Empty File**
   - [ ] Reset application
   - [ ] Try to upload an empty file
   - [ ] Verify appropriate error message in Indonesian
   - [ ] Verify user can retry upload

**Expected Results**:
- ✅ All supported formats (PDF, DOCX, TXT) are accepted
- ✅ Unsupported formats are rejected with clear error messages
- ✅ All messages are in Indonesian
- ✅ Successful uploads advance to Summary page

---

### Test 2: Organization Summary Display

**Objective**: Verify that organization profile summary is displayed correctly.

#### Test Steps:

1. **Upload Organization Profile**
   - [ ] Upload a valid organization profile document
   - [ ] Wait for processing to complete

2. **Verify Summary Display**
   - [ ] Verify page title: "Ringkasan Profil Organisasi" or similar
   - [ ] Verify organization summary is displayed
   - [ ] Verify context overview is displayed
   - [ ] Verify all text is in Indonesian
   - [ ] Verify summary is readable and makes sense

3. **Verify Navigation**
   - [ ] Verify "Lanjutkan" (Continue) button is present
   - [ ] Click continue button
   - [ ] Verify application advances to Course Type selection page

4. **Verify Sidebar Progress**
   - [ ] Verify sidebar shows "✅" for Upload step
   - [ ] Verify sidebar shows "▶️" for Summary step
   - [ ] Verify sidebar shows "⭕" for future steps

**Expected Results**:
- ✅ Summary is generated and displayed in Indonesian
- ✅ Context overview is displayed
- ✅ Navigation works correctly
- ✅ Sidebar reflects current progress

---

### Test 3: Course Type Selection

**Objective**: Verify that users can select a course type.

#### Test Steps:

1. **Navigate to Course Type Page**
   - [ ] Complete upload and summary steps
   - [ ] Verify course type selection page is displayed

2. **Verify Course Type Options**
   - [ ] Verify multiple course type options are displayed
   - [ ] Verify options include: B2B, Innovation, Tech, etc.
   - [ ] Verify labels are in Indonesian
   - [ ] Verify selection interface is clear (radio buttons or dropdown)

3. **Select Course Type**
   - [ ] Select "B2B" course type
   - [ ] Click "Lanjutkan" or similar button
   - [ ] Verify selection is saved
   - [ ] Verify application advances to TLO generation page

4. **Verify Selection Persistence**
   - [ ] Note the selected course type
   - [ ] Verify it's displayed somewhere on subsequent pages

**Expected Results**:
- ✅ Course type options are displayed clearly
- ✅ User can select one course type
- ✅ Selection is saved and persists
- ✅ Application advances to TLO generation

---

### Test 4: TLO Generation and Selection

**Objective**: Verify that TLOs are generated and users can select them.

#### Test Steps:

1. **Navigate to TLO Page**
   - [ ] Complete previous steps (upload, summary, course type)
   - [ ] Verify TLO generation page is displayed

2. **Verify TLO Generation**
   - [ ] Click "Generate TLO" or similar button
   - [ ] Verify loading indicator appears
   - [ ] Verify at least 3 TLOs are generated
   - [ ] Verify TLOs are displayed in Indonesian
   - [ ] Verify TLOs are relevant to organization and course type

3. **Verify TLO Selection Interface**
   - [ ] Verify each TLO has a checkbox or selection control
   - [ ] Verify TLOs are clearly formatted and readable
   - [ ] Verify selection instructions are in Indonesian

4. **Select TLOs**
   - [ ] Select at least 2 TLOs using checkboxes
   - [ ] Verify selected TLOs are highlighted or marked
   - [ ] Verify "Lanjutkan" button becomes enabled
   - [ ] Click continue button
   - [ ] Verify application advances to Performance generation

5. **Test Minimum Selection Requirement**
   - [ ] Reset to TLO page
   - [ ] Try to continue without selecting any TLOs
   - [ ] Verify error message appears in Indonesian
   - [ ] Verify message states "at least one TLO must be selected"

**Expected Results**:
- ✅ At least 3 TLOs are generated
- ✅ TLOs are in Indonesian and contextually relevant
- ✅ Selection interface is clear and functional
- ✅ At least one TLO must be selected to continue
- ✅ Selected TLOs are saved

---

### Test 5: Performance Generation and Selection

**Objective**: Verify that performance objectives are generated from selected TLOs.

#### Test Steps:

1. **Navigate to Performance Page**
   - [ ] Complete previous steps including TLO selection
   - [ ] Verify Performance generation page is displayed

2. **Verify Performance Generation**
   - [ ] Click "Generate Performance" or similar button
   - [ ] Verify loading indicator appears
   - [ ] Verify multiple performance objectives are generated
   - [ ] Verify performances are in Indonesian
   - [ ] Verify performances are related to selected TLOs

3. **Verify Performance Selection Interface**
   - [ ] Verify each performance has a checkbox
   - [ ] Verify performances are clearly formatted
   - [ ] Verify selection instructions are in Indonesian

4. **Select Performances**
   - [ ] Select at least 2 performances
   - [ ] Verify selected performances are highlighted
   - [ ] Click continue button
   - [ ] Verify application advances to ELO generation

5. **Test Minimum Selection Requirement**
   - [ ] Reset to Performance page
   - [ ] Try to continue without selecting any performances
   - [ ] Verify error message appears in Indonesian

**Expected Results**:
- ✅ Multiple performances are generated
- ✅ Performances are in Indonesian and relevant to TLOs
- ✅ Selection interface works correctly
- ✅ At least one performance must be selected
- ✅ Selected performances are saved

---

### Test 6: ELO Generation and Selection

**Objective**: Verify that ELOs are generated from selected performances.

#### Test Steps:

1. **Navigate to ELO Page**
   - [ ] Complete previous steps including performance selection
   - [ ] Verify ELO generation page is displayed

2. **Verify ELO Generation**
   - [ ] Click "Generate ELO" or similar button
   - [ ] Verify loading indicator appears
   - [ ] Verify at least 3 ELOs are generated per selected performance
   - [ ] Verify ELOs are in Indonesian
   - [ ] Verify ELOs support the selected performances

3. **Verify ELO Selection Interface**
   - [ ] Verify each ELO has a checkbox
   - [ ] Verify ELOs are grouped by performance (if applicable)
   - [ ] Verify selection instructions are in Indonesian

4. **Select ELOs**
   - [ ] Select multiple ELOs (at least 3)
   - [ ] Verify selected ELOs are highlighted
   - [ ] Click continue button
   - [ ] Verify application advances to Syllabus generation

5. **Test Minimum Selection Requirement**
   - [ ] Reset to ELO page
   - [ ] Try to continue without selecting any ELOs
   - [ ] Verify error message appears in Indonesian

**Expected Results**:
- ✅ At least 3 ELOs generated per performance
- ✅ ELOs are in Indonesian and support performances
- ✅ Selection interface works correctly
- ✅ At least one ELO must be selected
- ✅ Selected ELOs are saved

---

### Test 7: Syllabus Document Generation and Download

**Objective**: Verify that complete syllabus document can be generated and downloaded.

#### Test Steps:

1. **Navigate to Syllabus Page**
   - [ ] Complete all previous steps
   - [ ] Verify Syllabus generation page is displayed

2. **Verify Syllabus Generation Interface**
   - [ ] Verify page shows summary of selections
   - [ ] Verify "Buat Silabus" (Create Syllabus) button is present
   - [ ] Verify instructions are in Indonesian

3. **Generate Syllabus**
   - [ ] Click "Buat Silabus" button
   - [ ] Verify loading indicator appears
   - [ ] Verify success message appears when complete
   - [ ] Verify download button appears

4. **Download Syllabus**
   - [ ] Click download button
   - [ ] Verify DOCX file is downloaded
   - [ ] Verify filename is meaningful (e.g., "silabus_[date].docx")

5. **Verify Document Content**
   - [ ] Open downloaded DOCX file
   - [ ] Verify document contains organization profile section
   - [ ] Verify document contains selected TLOs
   - [ ] Verify document contains selected performances
   - [ ] Verify document contains selected ELOs
   - [ ] Verify document is properly formatted
   - [ ] Verify all content is in Indonesian
   - [ ] Verify document is readable and professional

**Expected Results**:
- ✅ Syllabus document is generated successfully
- ✅ Document can be downloaded as DOCX
- ✅ Document contains all selected materials
- ✅ Document is properly formatted and in Indonesian
- ✅ Document is ready for professional use

---

### Test 8: Indonesian Language Verification

**Objective**: Verify that all UI elements and generated content are in Indonesian.

#### Test Steps:

1. **UI Elements**
   - [ ] Verify page titles are in Indonesian
   - [ ] Verify button labels are in Indonesian
   - [ ] Verify instructions are in Indonesian
   - [ ] Verify error messages are in Indonesian
   - [ ] Verify success messages are in Indonesian
   - [ ] Verify sidebar labels are in Indonesian

2. **Generated Content**
   - [ ] Verify organization summary is in Indonesian
   - [ ] Verify TLOs are in Indonesian
   - [ ] Verify performances are in Indonesian
   - [ ] Verify ELOs are in Indonesian
   - [ ] Verify syllabus document content is in Indonesian

3. **Grammar and Terminology**
   - [ ] Verify Indonesian grammar is correct
   - [ ] Verify educational terminology is appropriate
   - [ ] Verify no English text appears (except technical terms if necessary)

**Expected Results**:
- ✅ All UI elements are in Indonesian
- ✅ All generated content is in Indonesian
- ✅ Grammar and terminology are correct

---

### Test 9: Error Scenarios

**Objective**: Verify that error scenarios are handled gracefully.

#### Test Steps:

1. **Test Database Connection Error**
   - [ ] Stop PostgreSQL database
   - [ ] Try to start application
   - [ ] Verify error message appears in Indonesian
   - [ ] Verify error message is user-friendly
   - [ ] Restart database and verify recovery

2. **Test API Connection Error**
   - [ ] Temporarily set invalid Azure OpenAI API key in .env
   - [ ] Try to generate TLOs
   - [ ] Verify error message appears in Indonesian
   - [ ] Verify error message suggests checking configuration
   - [ ] Restore correct API key

3. **Test File Upload Error**
   - [ ] Try to upload a corrupted PDF file
   - [ ] Verify error message appears in Indonesian
   - [ ] Verify user can retry upload

4. **Test Session Recovery**
   - [ ] Complete several workflow steps
   - [ ] Refresh browser page
   - [ ] Verify session state is maintained (if implemented)
   - [ ] OR verify user is returned to start with clear message

**Expected Results**:
- ✅ All errors display user-friendly messages in Indonesian
- ✅ Error messages provide helpful troubleshooting guidance
- ✅ Application doesn't crash on errors
- ✅ Users can recover from errors

---

### Test 10: Workflow Navigation and Progress

**Objective**: Verify that workflow navigation and progress tracking work correctly.

#### Test Steps:

1. **Verify Sequential Workflow**
   - [ ] Verify users cannot skip steps
   - [ ] Verify each step requires completion before advancing
   - [ ] Verify workflow follows correct order:
     1. Upload → 2. Summary → 3. Course Type → 4. TLO → 5. Performance → 6. ELO → 7. Syllabus

2. **Verify Sidebar Progress Indicators**
   - [ ] At each step, verify sidebar shows:
     - ✅ for completed steps
     - ▶️ for current step
     - ⭕ for future steps

3. **Test Reset Functionality**
   - [ ] Complete several workflow steps
   - [ ] Click "Mulai Ulang" (Reset) button in sidebar
   - [ ] Verify confirmation dialog appears (if implemented)
   - [ ] Confirm reset
   - [ ] Verify application returns to upload page
   - [ ] Verify all session data is cleared
   - [ ] Verify new session ID is generated

4. **Test Session ID Display**
   - [ ] Verify session ID is displayed in sidebar
   - [ ] Verify session ID remains consistent throughout workflow
   - [ ] Verify session ID changes after reset

**Expected Results**:
- ✅ Workflow enforces sequential order
- ✅ Progress indicators are accurate
- ✅ Reset functionality works correctly
- ✅ Session management is reliable

---

## Test Summary Checklist

After completing all tests, verify:

- [ ] All supported file formats work (PDF, DOCX, TXT)
- [ ] All workflow steps complete successfully
- [ ] All UI elements are in Indonesian
- [ ] All generated content is in Indonesian and relevant
- [ ] Error scenarios are handled gracefully
- [ ] Syllabus document is generated and downloadable
- [ ] Document contains all required sections
- [ ] Navigation and progress tracking work correctly
- [ ] Application is stable and doesn't crash

## Known Issues / Notes

Document any issues found during testing:

1. Issue: _______________________________________________
   - Steps to reproduce: _________________________________
   - Expected behavior: __________________________________
   - Actual behavior: ____________________________________
   - Severity: [ ] Critical [ ] High [ ] Medium [ ] Low

2. Issue: _______________________________________________
   - Steps to reproduce: _________________________________
   - Expected behavior: __________________________________
   - Actual behavior: ____________________________________
   - Severity: [ ] Critical [ ] High [ ] Medium [ ] Low

## Test Environment

- Date: _______________
- Tester: _______________
- Python Version: _______________
- PostgreSQL Version: _______________
- Browser: _______________
- Operating System: _______________

## Sign-off

- [ ] All critical tests passed
- [ ] All high-priority tests passed
- [ ] Known issues documented
- [ ] Application ready for deployment

Tester Signature: _______________ Date: _______________
