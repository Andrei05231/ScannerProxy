#!/usr/bin/env python3
"""
Simple runner for the Scanner Proxy application.
Handles all path issues automatically.
"""
import sys
import os
from pathlib import Path

def main():
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    src_dir = script_dir / "src"
    
    # Add src directory to Python path
    sys.path.insert(0, str(src_dir))
    
    # Change to the src directory for relative imports
    os.chdir(str(src_dir))
    
    try:
        # Import and run the main application
        from src.main import main as app_main
        return app_main()
    except Exception as e:
        print(f"Error running application: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
