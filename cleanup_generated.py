#!/usr/bin/env python3
"""
Cleanup script for the ABP Simulator.

This script cleans up the core/generated directory by removing
all files that accumulate during simulation runs and demos.
"""

import os
import shutil
import sys
from pathlib import Path


def cleanup_generated_directory():
    """
    Clean up the core/generated directory by removing all files.
    """
    generated_dir = Path("core/generated")
    
    if not generated_dir.exists():
        print("Info: core/generated directory does not exist. Nothing to clean.")
        return
    
    # Get list of files to remove
    files_to_remove = []
    for file_path in generated_dir.iterdir():
        if file_path.is_file():
            files_to_remove.append(file_path)
    
    if not files_to_remove:
        print("Info: core/generated directory is already clean.")
        return
    
    # Show what will be removed
    print(f"Found {len(files_to_remove)} files to remove:")
    for file_path in files_to_remove:
        file_size = file_path.stat().st_size
        print(f"  - {file_path.name} ({file_size:,} bytes)")
    
    # Ask for confirmation
    response = input("\nDo you want to remove these files? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        removed_count = 0
        total_size = 0
        
        for file_path in files_to_remove:
            try:
                file_size = file_path.stat().st_size
                file_path.unlink()
                removed_count += 1
                total_size += file_size
                print(f"Removed: {file_path.name}")
            except Exception as e:
                print(f"Error removing {file_path.name}: {e}")
        
        print(f"\nCleanup completed:")
        print(f"  - Files removed: {removed_count}")
        print(f"  - Space freed: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)")
        
    else:
        print("Cleanup cancelled.")


def cleanup_with_confirmation():
    """
    Clean up with automatic confirmation (for script usage).
    """
    generated_dir = Path("core/generated")
    
    if not generated_dir.exists():
        print("Info: core/generated directory does not exist. Nothing to clean.")
        return
    
    files_to_remove = [f for f in generated_dir.iterdir() if f.is_file()]
    
    if not files_to_remove:
        print("Info: core/generated directory is already clean.")
        return
    
    removed_count = 0
    total_size = 0
    
    for file_path in files_to_remove:
        try:
            file_size = file_path.stat().st_size
            file_path.unlink()
            removed_count += 1
            total_size += file_size
        except Exception as e:
            print(f"Error removing {file_path.name}: {e}")
    
    print(f"Cleanup completed: {removed_count} files removed, {total_size:,} bytes freed")


def main():
    """
    Main function with command line argument handling.
    """
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        # Automatic cleanup without confirmation
        cleanup_with_confirmation()
    else:
        # Interactive cleanup with confirmation
        cleanup_generated_directory()


if __name__ == "__main__":
    print("=" * 60)
    print("ABP Simulator - Generated Files Cleanup")
    print("=" * 60)
    main()
