"""Pytest configuration and shared fixtures"""

import pytest
import os
from dotenv import load_dotenv


@pytest.fixture(scope="session", autouse=True)
def load_test_env():
    """Load test environment variables"""
    # Load test environment if exists, otherwise use regular .env
    test_env_path = ".env.test"
    if os.path.exists(test_env_path):
        load_dotenv(test_env_path, override=True)
    else:
        load_dotenv()


@pytest.fixture
def sample_organization_text():
    """Sample organization profile text for testing"""
    return """
    PT Teknologi Cerdas Indonesia adalah perusahaan teknologi yang berfokus pada 
    pengembangan solusi AI untuk pendidikan. Kami memiliki misi untuk meningkatkan 
    kualitas pendidikan di Indonesia melalui teknologi inovatif.
    
    Visi kami adalah menjadi pemimpin dalam transformasi digital pendidikan di Asia Tenggara.
    Kami menyediakan platform pembelajaran adaptif yang menggunakan AI untuk personalisasi
    pengalaman belajar setiap siswa.
    """


@pytest.fixture
def sample_course_types():
    """Sample course types for testing"""
    return ["B2B", "Innovation", "Technology", "Leadership", "Digital Transformation"]
