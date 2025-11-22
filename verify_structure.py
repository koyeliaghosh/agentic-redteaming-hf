"""
Verify project structure without requiring dependencies.
This can be run immediately after setup.
"""

import os


def verify_structure():
    """Verify all directories and files are in place."""
    print("Verifying project structure...")
    print("=" * 60)
    
    # Check directories
    directories = {
        "agents": ["__init__.py", "coordinator.py", "attack_planner.py", 
                   "retriever.py", "executor.py", "evaluator.py"],
        "models": ["__init__.py", "data_models.py", "api_models.py"],
        "api": ["__init__.py"],
        "utils": ["__init__.py", "hf_client.py", "logger.py"],
    }
    
    root_files = [
        "config.py",
        "app.py",
        "requirements.txt",
        ".env.example",
        ".gitignore",
        "README.md",
    ]
    
    all_good = True
    
    # Check root files
    print("\nRoot files:")
    for file in root_files:
        exists = os.path.isfile(file)
        status = "✓" if exists else "✗"
        print(f"  {status} {file}")
        if not exists:
            all_good = False
    
    # Check directories and their contents
    for dir_name, files in directories.items():
        print(f"\n{dir_name}/:")
        dir_exists = os.path.isdir(dir_name)
        if not dir_exists:
            print(f"  ✗ Directory missing!")
            all_good = False
            continue
        
        for file in files:
            file_path = os.path.join(dir_name, file)
            exists = os.path.isfile(file_path)
            status = "✓" if exists else "✗"
            print(f"  {status} {file}")
            if not exists:
                all_good = False
    
    print("\n" + "=" * 60)
    if all_good:
        print("✓ Project structure is complete!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Copy .env.example to .env and configure")
        print("3. Create data directories: mkdir -p data/reports data/logs data/faiss_index")
    else:
        print("✗ Some files or directories are missing!")
    
    return all_good


if __name__ == "__main__":
    import sys
    sys.exit(0 if verify_structure() else 1)
