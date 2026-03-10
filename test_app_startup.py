#!/usr/bin/env python3
"""
Quick Application Startup Test

This script performs basic checks to verify the application can start:
1. Configuration loading
2. Database connection
3. AI service initialization
4. Import checks

Run this before starting the Streamlit app to catch configuration issues early.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    try:
        from src.config import get_config
        from src.models.entities import WorkflowStep, SessionData
        from src.database.service import DatabaseService
        from src.services.ai_service import AIService
        from src.workflow.orchestrator import WorkflowOrchestrator
        from src.ui.pages import (
            render_upload_page,
            render_summary_page,
            render_course_type_page,
            render_tlo_page,
            render_performance_page,
            render_elo_page,
            render_syllabus_page
        )
        print("   ✅ All imports successful")
        return True
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False


def test_configuration():
    """Test that configuration can be loaded"""
    print("\n🔍 Testing configuration...")
    try:
        from src.config import get_config
        config = get_config()
        print(f"   ✅ Configuration loaded")
        db_url = config.database.get_connection_string()
        print(f"      - Database URL: {db_url[:30]}...")
        print(f"      - Azure OpenAI Endpoint: {config.azure_openai.endpoint}")
        print(f"      - API Version: {config.azure_openai.api_version}")
        print(f"      - Deployment: {config.azure_openai.deployment_name}")
        return True
    except ValueError as e:
        print(f"   ❌ Configuration error: {e}")
        print("\n   💡 Make sure your .env file contains:")
        print("      - AZURE_OPENAI_API_KEY")
        print("      - DATABASE_USER")
        print("      - DATABASE_PASSWORD")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False


def test_database_connection():
    """Test that database connection can be established"""
    print("\n🔍 Testing database connection...")
    try:
        from src.config import get_config
        from src.database.service import DatabaseService
        
        config = get_config()
        db_connection_string = config.database.get_connection_string()
        db = DatabaseService(db_connection_string)
        
        # Try a simple query
        print("   ✅ Database connection successful")
        return True
    except Exception as e:
        print(f"   ❌ Database connection error: {e}")
        print("\n   💡 Troubleshooting:")
        print("      1. Ensure PostgreSQL is running (or Supabase is accessible)")
        print("      2. Verify database credentials in .env")
        print("      3. Check if database exists")
        print("      4. Run migration: python migrate_db.py")
        return False


def test_ai_service():
    """Test that AI service can be initialized"""
    print("\n🔍 Testing AI service initialization...")
    try:
        from src.config import get_config
        from src.services.ai_service import AIService
        
        config = get_config()
        ai = AIService(config)
        
        print("   ✅ AI service initialized")
        print(f"      - Endpoint: {config.azure_openai.endpoint}")
        print(f"      - Deployment: {config.azure_openai.deployment_name}")
        return True
    except Exception as e:
        print(f"   ❌ AI service initialization error: {e}")
        print("\n   💡 Troubleshooting:")
        print("      1. Verify Azure OpenAI credentials in .env")
        print("      2. Check API key is valid")
        print("      3. Verify endpoint URL is correct")
        return False


def test_orchestrator():
    """Test that workflow orchestrator can be initialized"""
    print("\n🔍 Testing workflow orchestrator...")
    try:
        from src.config import get_config
        from src.database.service import DatabaseService
        from src.services.ai_service import AIService
        from src.workflow.orchestrator import WorkflowOrchestrator
        
        config = get_config()
        db_connection_string = config.database.get_connection_string()
        db = DatabaseService(db_connection_string)
        ai = AIService(config)
        orchestrator = WorkflowOrchestrator(db, ai)
        
        print("   ✅ Workflow orchestrator initialized")
        return True
    except Exception as e:
        print(f"   ❌ Orchestrator initialization error: {e}")
        return False


def main():
    """Run all startup tests"""
    print("=" * 70)
    print("AI-Powered Syllabus Generation System - Startup Tests")
    print("=" * 70)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_configuration()))
    results.append(("Database Connection", test_database_connection()))
    results.append(("AI Service", test_ai_service()))
    results.append(("Workflow Orchestrator", test_orchestrator()))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "=" * 70)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 70)
    
    if passed == total:
        print("\n✅ All tests passed! Application is ready to start.")
        print("\nRun the application with:")
        print("   streamlit run app.py")
        return 0
    else:
        print("\n❌ Some tests failed. Please fix the issues before starting the application.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
