"""Example usage of AI Service with Azure OpenAI"""

import sys
import os

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import AzureOpenAIConfig
from src.services.ai_service import AIService, AIServiceError


def main():
    """Demonstrate AI service usage"""
    
    # Create configuration
    try:
        config = AzureOpenAIConfig.from_env()
        print("✓ Configuration loaded successfully")
        print(f"  Endpoint: {config.endpoint}")
        print(f"  API Version: {config.api_version}")
        print(f"  Deployment: {config.deployment_name}")
        print()
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        print("\nPlease ensure your .env file contains:")
        print("  - AZURE_OPENAI_ENDPOINT")
        print("  - AZURE_OPENAI_API_KEY")
        print("  - AZURE_OPENAI_API_VERSION")
        print("  - AZURE_OPENAI_DEPLOYMENT_NAME")
        print("  - AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
        return
    
    # Initialize AI service
    service = AIService(config)
    print("✓ AI Service initialized")
    print()
    
    # Example 1: Summarize organization profile
    print("Example 1: Organization Profile Summary")
    print("-" * 50)
    org_text = """PT Teknologi Edukasi Indonesia adalah perusahaan yang bergerak di bidang 
    teknologi pendidikan. Kami fokus pada pengembangan platform pembelajaran digital 
    untuk meningkatkan kualitas pendidikan di Indonesia. Visi kami adalah menjadi 
    pemimpin dalam transformasi digital pendidikan di Asia Tenggara."""
    
    try:
        summary = service.summarize_organization_profile(org_text)
        print(f"Original text length: {len(org_text)} characters")
        print(f"Summary length: {len(summary)} characters")
        print(f"\nSummary:\n{summary}")
        print()
    except AIServiceError as e:
        print(f"✗ Error: {e}")
        print()
    
    # Example 2: Generate TLOs
    print("Example 2: Generate Terminal Learning Objectives")
    print("-" * 50)
    org_context = "Perusahaan teknologi pendidikan yang fokus pada inovasi digital"
    course_type = "B2B"
    
    try:
        tlos = service.generate_tlos(org_context, course_type, count=3)
        print(f"Generated {len(tlos)} TLOs for course type: {course_type}")
        for i, tlo in enumerate(tlos, 1):
            print(f"{i}. {tlo}")
        print()
    except AIServiceError as e:
        print(f"✗ Error: {e}")
        print()
    
    # Example 3: Generate Performance Objectives
    print("Example 3: Generate Performance Objectives")
    print("-" * 50)
    sample_tlos = [
        "Peserta mampu menganalisis kebutuhan bisnis klien",
        "Peserta mampu merancang solusi teknologi yang tepat"
    ]
    
    try:
        performances = service.generate_performances(sample_tlos, count=3)
        print(f"Generated {len(performances)} performance objectives")
        for i, perf in enumerate(performances, 1):
            print(f"{i}. {perf}")
        print()
    except AIServiceError as e:
        print(f"✗ Error: {e}")
        print()
    
    # Example 4: Generate ELOs
    print("Example 4: Generate Enabling Learning Objectives")
    print("-" * 50)
    sample_performances = [
        "Mengidentifikasi stakeholder utama dalam proyek B2B"
    ]
    
    try:
        elos = service.generate_elos(sample_performances, count=3)
        print(f"Generated {len(elos)} ELOs")
        for i, elo in enumerate(elos, 1):
            print(f"{i}. {elo}")
        print()
    except AIServiceError as e:
        print(f"✗ Error: {e}")
        print()
    
    print("✓ All examples completed")


if __name__ == "__main__":
    main()
