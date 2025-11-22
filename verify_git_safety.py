"""
Verify that sensitive files are not being tracked by Git.
Run this before pushing to GitHub.
"""

import os
import subprocess
from pathlib import Path


def check_git_status():
    """Check if sensitive files are being tracked."""
    print("=" * 60)
    print("Git Safety Check")
    print("=" * 60)
    
    # Check if .env exists
    if Path(".env").exists():
        print("\n✓ .env file exists (good)")
    else:
        print("\n⚠ .env file not found (you'll need to create it)")
    
    # Check if git is initialized
    try:
        result = subprocess.run(
            ["git", "status"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            print("\n⚠ Git not initialized. Run: git init")
            return
        
        print("\n✓ Git is initialized")
        
    except FileNotFoundError:
        print("\n✗ Git not found. Install Git first.")
        return
    
    # Check tracked files
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True,
            text=True,
            check=True
        )
        
        tracked_files = result.stdout.strip().split("\n")
        
        # Check for sensitive files
        sensitive_files = [".env", "data/", "*.log"]
        found_sensitive = []
        
        for tracked in tracked_files:
            if ".env" in tracked or tracked.startswith("data/") or tracked.endswith(".log"):
                found_sensitive.append(tracked)
        
        if found_sensitive:
            print("\n✗ DANGER: Sensitive files are tracked!")
            print("  Files that should NOT be in Git:")
            for f in found_sensitive:
                print(f"    - {f}")
            print("\n  Remove them with:")
            for f in found_sensitive:
                print(f"    git rm --cached {f}")
        else:
            print("\n✓ No sensitive files tracked")
        
    except subprocess.CalledProcessError:
        print("\n⚠ Could not check tracked files")
    
    # Check .gitignore
    if Path(".gitignore").exists():
        gitignore_content = Path(".gitignore").read_text()
        
        required_ignores = [".env", "data/", "*.log"]
        missing = []
        
        for pattern in required_ignores:
            if pattern not in gitignore_content:
                missing.append(pattern)
        
        if missing:
            print("\n⚠ .gitignore missing patterns:")
            for pattern in missing:
                print(f"    - {pattern}")
        else:
            print("✓ .gitignore properly configured")
    else:
        print("\n✗ .gitignore not found!")
    
    # Check for API keys in tracked files
    print("\n" + "=" * 60)
    print("Checking for exposed API keys in tracked files...")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            ["git", "grep", "-i", "hf_[a-zA-Z0-9]"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0 and result.stdout:
            print("\n✗ DANGER: Found potential API keys in tracked files!")
            print(result.stdout)
            print("\n  These files contain 'hf_' patterns. Review them!")
        else:
            print("\n✓ No API keys found in tracked files")
            
    except subprocess.CalledProcessError:
        pass
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print("\nBefore pushing to GitHub:")
    print("  1. Ensure .env is NOT tracked")
    print("  2. Ensure data/ directory is NOT tracked")
    print("  3. Ensure no API keys in code")
    print("  4. Review: git status")
    print("  5. Then: git push")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    check_git_status()
