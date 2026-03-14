# Requirements Document: AI-Powered Syllabus Generation System

## Introduction

Sistem Generasi Silabus Berbasis AI adalah aplikasi web yang memungkinkan pengguna untuk membuat silabus kursus secara otomatis menggunakan AI. Sistem ini menggunakan profil organisasi sebagai konteks, kemudian memandu pengguna melalui proses multi-langkah untuk menghasilkan Terminal Learning Objectives (TLO), Performance objectives, dan Enabling Learning Objectives (ELO), yang akhirnya dikompilasi menjadi dokumen silabus lengkap.

## Glossary

- **System**: The AI-powered syllabus generation application
- **User**: The person using the system to generate syllabi
- **Organization_Profile**: A document containing context and overview about an organization
- **TLO**: Terminal Learning Objective - high-level learning outcomes for a course
- **Performance**: Performance-based objectives derived from TLOs
- **ELO**: Enabling Learning Objective - specific learning objectives that support performances
- **Course_Type**: Category of course (B2B, innovation, tech, etc.)
- **Syllabus_Document**: Final generated document containing all learning objectives
- **AI_Service**: Microsoft Azure OpenAI GPT-4o service
- **Database**: PostgreSQL database for storing application data
- **Streamlit_Interface**: The web-based user interface built with Streamlit

## Requirements

### Requirement 1: Organization Profile Upload and Processing

**User Story:** Sebagai pengguna, saya ingin mengunggah dokumen profil organisasi, sehingga sistem dapat memahami konteks organisasi saya untuk menghasilkan silabus yang relevan.

#### Acceptance Criteria

1. WHEN a user uploads an organization profile document, THE System SHALL accept common document formats (PDF, DOCX, TXT)
2. WHEN a user clicks the submit button, THE System SHALL process the uploaded document and extract text content
3. WHEN document processing is complete, THE System SHALL use the AI_Service to analyze and understand the organization context
4. IF document upload fails or format is unsupported, THEN THE System SHALL display an error message and allow re-upload
5. WHEN processing is successful, THE System SHALL store the organization profile in the Database

### Requirement 2: Organization Context Summarization

**User Story:** Sebagai pengguna, saya ingin melihat ringkasan profil organisasi saya, sehingga saya dapat memverifikasi bahwa sistem memahami konteks dengan benar.

#### Acceptance Criteria

1. WHEN organization profile processing is complete, THE System SHALL generate a summary using the AI_Service
2. THE System SHALL display the organization profile summary on the Streamlit_Interface
3. THE System SHALL display the organization context overview on the Streamlit_Interface
4. WHEN displaying results, THE System SHALL present information in Indonesian language
5. THE System SHALL store the generated summary in the Database

### Requirement 3: Course Type Selection

**User Story:** Sebagai pengguna, saya ingin memilih jenis kursus, sehingga sistem dapat menghasilkan TLO yang sesuai dengan kategori kursus saya.

#### Acceptance Criteria

1. WHEN organization profile is processed, THE System SHALL display available course types (B2B, innovation, tech, etc.)
2. THE System SHALL allow the user to select one course type
3. WHEN a course type is selected, THE System SHALL store the selection in the Database
4. THE System SHALL use the selected course type as context for TLO generation

### Requirement 4: TLO Generation

**User Story:** Sebagai pengguna, saya ingin sistem menghasilkan beberapa Terminal Learning Objectives, sehingga saya dapat memilih yang paling sesuai dengan kebutuhan kursus saya.

#### Acceptance Criteria

1. WHEN a course type is selected, THE System SHALL generate multiple TLOs using the AI_Service
2. THE System SHALL use organization context and course type as input for TLO generation
3. THE System SHALL display all generated TLOs on the Streamlit_Interface
4. THE System SHALL generate at least 3 TLO options for user selection
5. THE System SHALL store all generated TLOs in the Database

### Requirement 5: TLO Selection

**User Story:** Sebagai pengguna, saya ingin memilih satu atau lebih TLO yang dihasilkan, sehingga saya dapat melanjutkan ke tahap pembuatan performance objectives.

#### Acceptance Criteria

1. WHEN TLOs are displayed, THE System SHALL allow the user to select one or more TLOs
2. THE System SHALL provide a clear selection interface (checkboxes or similar)
3. WHEN TLOs are selected, THE System SHALL display the selected TLOs separately
4. THE System SHALL store user selections in the Database
5. THE System SHALL enable progression to performance generation only after at least one TLO is selected

### Requirement 6: Performance Generation

**User Story:** Sebagai pengguna, saya ingin sistem menghasilkan performance objectives berdasarkan TLO yang dipilih, sehingga saya dapat memilih performance yang paling relevan.

#### Acceptance Criteria

1. WHEN TLOs are selected, THE System SHALL display an instruction option "create performance based on TLO results"
2. WHEN the user triggers performance generation, THE System SHALL generate multiple performance objectives using the AI_Service
3. THE System SHALL use selected TLOs as context for performance generation
4. THE System SHALL display all generated performance objectives on the Streamlit_Interface
5. THE System SHALL store all generated performances in the Database

### Requirement 7: Performance Selection

**User Story:** Sebagai pengguna, saya ingin memilih satu atau lebih performance objectives, sehingga saya dapat melanjutkan ke tahap pembuatan ELO.

#### Acceptance Criteria

1. WHEN performances are displayed, THE System SHALL allow the user to select one or more performances
2. THE System SHALL provide a clear selection interface for performances
3. WHEN performances are selected, THE System SHALL display the selected performances separately
4. THE System SHALL store performance selections in the Database
5. THE System SHALL enable progression to ELO generation only after at least one performance is selected

### Requirement 8: ELO Generation

**User Story:** Sebagai pengguna, saya ingin sistem menghasilkan Enabling Learning Objectives berdasarkan performance yang dipilih, sehingga saya dapat memilih ELO yang paling sesuai.

#### Acceptance Criteria

1. WHEN performances are selected, THE System SHALL generate multiple ELOs using the AI_Service
2. THE System SHALL use selected performances as context for ELO generation
3. THE System SHALL display all generated ELOs on the Streamlit_Interface
4. THE System SHALL generate at least 3 ELO options per selected performance
5. THE System SHALL store all generated ELOs in the Database

### Requirement 9: ELO Selection

**User Story:** Sebagai pengguna, saya ingin memilih beberapa ELO yang dihasilkan, sehingga saya dapat melanjutkan ke tahap pembuatan dokumen silabus.

#### Acceptance Criteria

1. WHEN ELOs are displayed, THE System SHALL allow the user to select multiple ELOs
2. THE System SHALL provide a clear selection interface for ELOs
3. WHEN ELOs are selected, THE System SHALL display the selected ELOs
4. THE System SHALL store ELO selections in the Database
5. THE System SHALL enable syllabus document creation only after at least one ELO is selected

### Requirement 10: Syllabus Document Generation

**User Story:** Sebagai pengguna, saya ingin membuat dokumen silabus berdasarkan semua material yang telah dipilih, sehingga saya memiliki silabus lengkap yang siap digunakan.

#### Acceptance Criteria

1. WHEN the user types command "create syllabus document based on these materials", THE System SHALL compile all selected materials
2. THE System SHALL generate a formatted syllabus document using the AI_Service
3. THE System SHALL include organization profile, selected TLOs, performances, and ELOs in the document
4. THE System SHALL create the syllabus in document format (DOCX or similar)
5. THE System SHALL store the generated syllabus in the Database
6. THE System SHALL provide a download link for the syllabus document

### Requirement 11: Azure OpenAI Integration

**User Story:** Sebagai sistem, saya perlu terhubung dengan Azure OpenAI, sehingga saya dapat menghasilkan konten AI untuk semua tahap generasi silabus.

#### Acceptance Criteria

1. THE System SHALL connect to Azure OpenAI endpoint at https://openaitcuc.openai.azure.com/
2. THE System SHALL use API version 2024-10-01-preview for all requests
3. THE System SHALL use deployment name "corpu-text-gpt-4o" for text generation
4. THE System SHALL use deployment name "corpu-text-embedding-3-large" for embeddings
5. THE System SHALL handle API authentication securely using environment variables
6. IF API connection fails, THEN THE System SHALL display an error message and retry with exponential backoff

### Requirement 12: Database Persistence

**User Story:** Sebagai sistem, saya perlu menyimpan semua data pengguna dan hasil generasi, sehingga pengguna dapat mengakses kembali pekerjaan mereka di masa mendatang.

#### Acceptance Criteria

1. THE System SHALL store organization profiles in the Database
2. THE System SHALL store all generated TLOs, performances, and ELOs in the Database
3. THE System SHALL store user selections for each generation step in the Database
4. THE System SHALL store generated syllabus documents in the Database
5. THE System SHALL maintain referential integrity between related entities
6. WHEN storing data, THE System SHALL use PostgreSQL as the database engine

### Requirement 13: User Interface and Workflow

**User Story:** Sebagai pengguna, saya ingin antarmuka yang jelas dan intuitif, sehingga saya dapat dengan mudah menavigasi proses generasi silabus multi-langkah.

#### Acceptance Criteria

1. THE System SHALL use Streamlit for the web interface
2. THE System SHALL display workflow steps in sequential order
3. THE System SHALL prevent users from skipping required steps
4. THE System SHALL provide clear visual feedback for each completed step
5. THE System SHALL display all content in Indonesian language
6. WHEN an error occurs, THE System SHALL display user-friendly error messages in Indonesian

### Requirement 14: Document Format Support

**User Story:** Sebagai pengguna, saya ingin mengunggah berbagai format dokumen, sehingga saya tidak perlu mengonversi file saya sebelum mengunggah.

#### Acceptance Criteria

1. THE System SHALL accept PDF files for organization profile upload
2. THE System SHALL accept DOCX files for organization profile upload
3. THE System SHALL accept TXT files for organization profile upload
4. WHEN an unsupported format is uploaded, THE System SHALL reject the file and display supported formats
5. THE System SHALL extract text content from all supported formats accurately

### Requirement 15: AI Content Generation Quality

**User Story:** Sebagai pengguna, saya ingin konten yang dihasilkan AI berkualitas tinggi dan relevan, sehingga silabus yang dihasilkan memenuhi standar pendidikan.

#### Acceptance Criteria

1. WHEN generating TLOs, THE System SHALL provide diverse and relevant options
2. WHEN generating performances, THE System SHALL ensure alignment with selected TLOs
3. WHEN generating ELOs, THE System SHALL ensure they support the selected performances
4. THE System SHALL use organization context consistently across all generation steps
5. THE System SHALL generate content in proper Indonesian language with correct grammar and terminology
