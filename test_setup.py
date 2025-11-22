"""
Simple test script to verify project setup and configuration.
Run this to ensure the basic structure is working correctly.
"""

import os
import sys


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        import config
        print("✓ config module imported")
        
        import app
        print("✓ app module imported")
        
        # Test agent imports
        import agents
        print("✓ agents package imported")
        
        # Test model imports
        import models
        print("✓ models package imported")
        
        # Test utils imports
        import utils
        print("✓ utils package imported")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_directory_structure():
    """Test that all required directories exist."""
    print("\nTesting directory structure...")
    required_dirs = [
        "agents",
        "models",
        "api",
        "utils",
    ]
    
    all_exist = True
    for dir_name in required_dirs:
        if os.path.isdir(dir_name):
            print(f"✓ {dir_name}/ exists")
        else:
            print(f"✗ {dir_name}/ missing")
            all_exist = False
    
    return all_exist


def test_required_files():
    """Test that all required files exist."""
    print("\nTesting required files...")
    required_files = [
        "config.py",
        "app.py",
        "requirements.txt",
        ".env.example",
        ".gitignore",
        "README.md",
    ]
    
    all_exist = True
    for file_name in required_files:
        if os.path.isfile(file_name):
            print(f"✓ {file_name} exists")
        else:
            print(f"✗ {file_name} missing")
            all_exist = False
    
    return all_exist


def test_config_validation():
    """Test configuration validation (without loading from env)."""
    print("\nTesting configuration validation...")
    try:
        from config import Config
        
        # Test that validation works for invalid API key
        try:
            Config(huggingface_api_key="invalid_key")
            print("✗ Config validation failed - should reject invalid API key")
            return False
        except ValueError as e:
            if "must start with 'hf_'" in str(e):
                print("✓ Config correctly validates API key format")
            else:
                print(f"✗ Unexpected validation error: {e}")
                return False
        
        # Test that empty API key is rejected
        try:
            Config(huggingface_api_key="")
            print("✗ Config validation failed - should reject empty API key")
            return False
        except ValueError:
            print("✓ Config correctly rejects empty API key")
        
        return True
    except Exception as e:
        print(f"✗ Config validation test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Project Setup Verification")
    print("=" * 60)
    
    results = []
    
    results.append(("Directory Structure", test_directory_structure()))
    results.append(("Required Files", test_required_files()))
    results.append(("Module Imports", test_imports()))
    results.append(("Config Validation", test_config_validation()))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        symbol = "✓" if passed else "✗"
        print(f"{symbol} {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All tests passed! Project setup is complete.")
        print("\nNext steps:")
        print("1. Copy .env.example to .env")
        print("2. Add your Hugging Face API key to .env")
        print("3. Create data directories: mkdir -p data/reports data/logs data/faiss_index")
        print("4. Install dependencies: pip install -r requirements.txt")
        return 0
    else:
        print("\n✗ Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
