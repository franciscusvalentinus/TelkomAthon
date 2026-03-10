"""AI Service for Azure OpenAI integration"""

import time
from typing import List, Optional
from openai import AzureOpenAI, RateLimitError, APITimeoutError, APIConnectionError
from openai.types.chat import ChatCompletion

from src.config import AzureOpenAIConfig


class AIServiceError(Exception):
    """Base exception for AI service errors"""
    pass


class AIService:
    """Service for interacting with Azure OpenAI API"""

    def __init__(self, config: AzureOpenAIConfig):
        """
        Initialize AI service with Azure OpenAI configuration
        
        Args:
            config: Azure OpenAI configuration with endpoint, API key, etc.
        """
        self.config = config
        self.client = self._initialize_client()

    def _initialize_client(self) -> AzureOpenAI:
        """
        Initialize Azure OpenAI client with configuration
        
        Returns:
            Configured AzureOpenAI client instance
        """
        return AzureOpenAI(
            api_key=self.config.api_key,
            api_version=self.config.api_version,
            azure_endpoint=self.config.endpoint
        )

    def _call_api_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        base_delay: float = 1.0,
        temperature: float = 0.7
    ) -> str:
        """
        Call Azure OpenAI API with exponential backoff retry logic
        
        Args:
            prompt: The prompt to send to the API
            max_retries: Maximum number of retry attempts (default: 3)
            base_delay: Base delay in seconds for exponential backoff (default: 1.0)
            temperature: Temperature parameter for generation (default: 0.7)
            
        Returns:
            Generated text response from the API
            
        Raises:
            AIServiceError: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                response: ChatCompletion = self.client.chat.completions.create(
                    model=self.config.deployment_name,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature
                )
                
                return response.choices[0].message.content or ""
                
            except RateLimitError as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
                else:
                    raise AIServiceError(
                        "Layanan AI sedang sibuk. Silakan coba lagi nanti."
                    ) from e
                    
            except APITimeoutError as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
                else:
                    raise AIServiceError(
                        "Koneksi timeout. Silakan periksa koneksi internet Anda."
                    ) from e
                    
            except APIConnectionError as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
                else:
                    raise AIServiceError(
                        "Tidak dapat terhubung ke layanan AI. Silakan coba lagi."
                    ) from e
                    
            except Exception as e:
                # For unexpected errors, don't retry
                raise AIServiceError(
                    f"Terjadi kesalahan saat memanggil layanan AI: {str(e)}"
                ) from e
        
        # This should not be reached, but just in case
        raise AIServiceError(
            "Gagal memanggil layanan AI setelah beberapa percobaan."
        ) from last_exception

    def summarize_organization_profile(self, text: str) -> str:
        """
        Generate organization profile summary using AI
        
        Args:
            text: Original organization profile text
            
        Returns:
            Generated summary in Indonesian
            
        Raises:
            AIServiceError: If API call fails
        """
        prompt = f"""Anda adalah asisten AI yang membantu merangkum profil organisasi.

Berdasarkan teks profil organisasi berikut, buatlah ringkasan yang mencakup:
1. Nama dan jenis organisasi
2. Visi dan misi utama
3. Bidang kegiatan atau industri
4. Karakteristik unik organisasi

Teks profil organisasi:
{text}

Berikan ringkasan dalam bahasa Indonesia yang jelas dan ringkas (maksimal 300 kata)."""

        return self._call_api_with_retry(prompt, temperature=0.5)

    def generate_tlos(
        self,
        org_context: str,
        course_type: str,
        count: int = 5,
        min_count: int = 3,
        max_retries: int = 2
    ) -> List[str]:
        """
        Generate Terminal Learning Objectives based on organization context
        
        Args:
            org_context: Organization profile summary
            course_type: Type of course (B2B, innovation, tech, etc.)
            count: Number of TLOs to generate (default: 5)
            min_count: Minimum number of TLOs required (default: 3)
            max_retries: Maximum number of retry attempts if insufficient (default: 2)
            
        Returns:
            List of generated TLO texts
            
        Raises:
            AIServiceError: If API call fails or insufficient TLOs generated after retries
        """
        for attempt in range(max_retries + 1):
            prompt = f"""Anda adalah ahli desain kurikulum yang membantu membuat Terminal Learning Objectives (TLO).

Konteks Organisasi:
{org_context}

Jenis Kursus: {course_type}

Buatlah {count} Terminal Learning Objectives (TLO) yang:
1. Sesuai dengan konteks organisasi
2. Relevan dengan jenis kursus {course_type}
3. Menggunakan kata kerja aksi yang terukur
4. Fokus pada hasil pembelajaran tingkat tinggi
5. Ditulis dalam bahasa Indonesia

Format: Berikan setiap TLO dalam baris terpisah, dimulai dengan nomor (1., 2., dst.)."""

            response = self._call_api_with_retry(prompt, temperature=0.8)
            
            # Parse response into list of TLOs
            tlos = []
            for line in response.strip().split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    # Remove numbering/bullets
                    tlo_text = line.lstrip('0123456789.-) ').strip()
                    if tlo_text:
                        tlos.append(tlo_text)
            
            # Check if we have minimum count
            if len(tlos) >= min_count:
                return tlos[:count]  # Ensure we don't return more than requested
            
            # If this is not the last attempt, retry
            if attempt < max_retries:
                continue
        
        # If we reach here, we failed to generate minimum count
        raise AIServiceError(
            f"Gagal menghasilkan jumlah TLO minimum ({min_count}). "
            f"Hanya {len(tlos)} yang dihasilkan setelah {max_retries + 1} percobaan."
        )

    def generate_performances(
        self,
        tlo_texts: List[str],
        count: int = 5
    ) -> List[str]:
        """
        Generate performance objectives from selected TLOs
        
        Args:
            tlo_texts: List of selected TLO texts
            count: Number of performance objectives to generate (default: 5)
            
        Returns:
            List of generated performance objective texts
            
        Raises:
            AIServiceError: If API call fails
        """
        tlos_formatted = '\n'.join([f"{i+1}. {tlo}" for i, tlo in enumerate(tlo_texts)])
        
        prompt = f"""Anda adalah ahli desain kurikulum yang membantu membuat Performance Objectives.

Terminal Learning Objectives (TLO) yang dipilih:
{tlos_formatted}

Buatlah {count} Performance Objectives yang:
1. Mendukung pencapaian TLO di atas
2. Lebih spesifik dan terukur dari TLO
3. Menggambarkan kinerja yang dapat diamati
4. Menggunakan kata kerja aksi yang jelas
5. Ditulis dalam bahasa Indonesia

Format: Berikan setiap performance objective dalam baris terpisah, dimulai dengan nomor (1., 2., dst.)."""

        response = self._call_api_with_retry(prompt, temperature=0.8)
        
        # Parse response into list of performances
        performances = []
        for line in response.strip().split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # Remove numbering/bullets
                perf_text = line.lstrip('0123456789.-) ').strip()
                if perf_text:
                    performances.append(perf_text)
        
        return performances[:count]

    def generate_elos(
        self,
        performance_texts: List[str],
        count: int = 3,
        min_count: int = 3,
        max_retries: int = 2
    ) -> List[str]:
        """
        Generate Enabling Learning Objectives from selected performances
        
        Args:
            performance_texts: List of selected performance objective texts
            count: Number of ELOs to generate per performance (default: 3)
            min_count: Minimum number of ELOs required (default: 3)
            max_retries: Maximum number of retry attempts if insufficient (default: 2)
            
        Returns:
            List of generated ELO texts
            
        Raises:
            AIServiceError: If API call fails or insufficient ELOs generated after retries
        """
        perfs_formatted = '\n'.join([f"{i+1}. {perf}" for i, perf in enumerate(performance_texts)])
        
        for attempt in range(max_retries + 1):
            prompt = f"""Anda adalah ahli desain kurikulum yang membantu membuat Enabling Learning Objectives (ELO).

Performance Objectives yang dipilih:
{perfs_formatted}

Buatlah {count} Enabling Learning Objectives (ELO) untuk setiap performance objective yang:
1. Mendukung pencapaian performance objective
2. Sangat spesifik dan detail
3. Menggambarkan langkah-langkah pembelajaran konkret
4. Menggunakan kata kerja aksi yang dapat diukur
5. Ditulis dalam bahasa Indonesia

Format: Berikan setiap ELO dalam baris terpisah, dimulai dengan nomor (1., 2., dst.)."""

            response = self._call_api_with_retry(prompt, temperature=0.8)
            
            # Parse response into list of ELOs
            elos = []
            for line in response.strip().split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    # Remove numbering/bullets
                    elo_text = line.lstrip('0123456789.-) ').strip()
                    if elo_text:
                        elos.append(elo_text)
            
            # Check if we have minimum count
            if len(elos) >= min_count:
                return elos
            
            # If this is not the last attempt, retry
            if attempt < max_retries:
                continue
        
        # If we reach here, we failed to generate minimum count
        raise AIServiceError(
            f"Gagal menghasilkan jumlah ELO minimum ({min_count}). "
            f"Hanya {len(elos)} yang dihasilkan setelah {max_retries + 1} percobaan."
        )

    def format_syllabus_content(
        self,
        org_summary: str,
        tlos: List[str],
        performances: List[str],
        elos: List[str]
    ) -> str:
        """
        Format all selected materials into structured syllabus content
        
        Args:
            org_summary: Organization profile summary
            tlos: Selected TLO texts
            performances: Selected performance objective texts
            elos: Selected ELO texts
            
        Returns:
            Formatted syllabus content in Indonesian
            
        Raises:
            AIServiceError: If API call fails
        """
        tlos_formatted = '\n'.join([f"- {tlo}" for tlo in tlos])
        perfs_formatted = '\n'.join([f"- {perf}" for perf in performances])
        elos_formatted = '\n'.join([f"- {elo}" for elo in elos])
        
        prompt = f"""Anda adalah ahli desain kurikulum yang membantu menyusun dokumen silabus.

Buatlah dokumen silabus yang terstruktur dengan baik berdasarkan komponen berikut:

PROFIL ORGANISASI:
{org_summary}

TERMINAL LEARNING OBJECTIVES (TLO):
{tlos_formatted}

PERFORMANCE OBJECTIVES:
{perfs_formatted}

ENABLING LEARNING OBJECTIVES (ELO):
{elos_formatted}

Susunlah dokumen silabus yang:
1. Memiliki struktur yang jelas dan profesional
2. Menjelaskan hubungan antara TLO, Performance, dan ELO
3. Mencakup semua komponen di atas
4. Ditulis dalam bahasa Indonesia yang formal dan akademis
5. Siap untuk digunakan sebagai dokumen resmi

Format dokumen dengan heading dan sub-heading yang sesuai."""

        return self._call_api_with_retry(prompt, temperature=0.5)
