#!/usr/bin/env python3
"""
IPEDS Data Analysis Toolkit - Automated Installer

This script automates the complete setup process:
1. Checks Python version compatibility
2. Creates virtual environment
3. Installs dependencies
4. Configures OpenAI API key
5. Creates database schema
6. Optionally generates sample data
7. Provides next steps

Usage:
    python install.py
    python install.py --skip-data    # Skip sample data generation
    python install.py --api-key YOUR_KEY    # Provide API key directly
"""

import sys
import os
import subprocess
import platform
import argparse
from pathlib import Path

# Color codes for terminal output
if platform.system() == "Windows":
    # Enable ANSI colors on Windows 10+
    os.system("")

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(message):
    """Print a formatted header message."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message:^70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")

def print_success(message):
    """Print a success message."""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

def print_error(message):
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def print_warning(message):
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")

def print_info(message):
    """Print an info message."""
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")

def check_python_version():
    """Check if Python version is 3.8 or higher."""
    print_header("Checking Python Version")

    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    print(f"Python version: {version_str}")

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python 3.8 or higher is required. You have {version_str}")
        print_info("Please upgrade Python and try again.")
        print_info("Download from: https://www.python.org/downloads/")
        return False

    print_success(f"Python {version_str} is compatible")
    return True

def create_virtual_environment():
    """Create a virtual environment."""
    print_header("Creating Virtual Environment")

    venv_path = Path("venv")

    if venv_path.exists():
        print_warning("Virtual environment already exists")
        response = input("Do you want to recreate it? (y/N): ").strip().lower()
        if response == 'y':
            print_info("Removing existing virtual environment...")
            import shutil
            shutil.rmtree(venv_path)
        else:
            print_info("Using existing virtual environment")
            return True

    try:
        print_info("Creating virtual environment (this may take a minute)...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print_success("Virtual environment created successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to create virtual environment: {e}")
        return False

def get_venv_python():
    """Get the path to the Python executable in the virtual environment."""
    if platform.system() == "Windows":
        return Path("venv") / "Scripts" / "python.exe"
    else:
        return Path("venv") / "bin" / "python"

def get_venv_pip():
    """Get the path to pip in the virtual environment."""
    if platform.system() == "Windows":
        return Path("venv") / "Scripts" / "pip.exe"
    else:
        return Path("venv") / "bin" / "pip"

def install_dependencies():
    """Install Python dependencies from requirements.txt."""
    print_header("Installing Dependencies")

    pip_path = get_venv_pip()

    if not Path("requirements.txt").exists():
        print_error("requirements.txt not found")
        return False

    try:
        print_info("Installing packages (this may take a few minutes)...")
        subprocess.run(
            [str(pip_path), "install", "--upgrade", "pip"],
            check=True,
            capture_output=True
        )
        subprocess.run(
            [str(pip_path), "install", "-r", "requirements.txt"],
            check=True
        )
        print_success("All dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies: {e}")
        return False

def configure_api_key(provided_key=None):
    """Configure OpenAI API key."""
    print_header("Configuring OpenAI API Key")

    env_file = Path(".env")
    env_example = Path(".env.example")

    # Check if .env already exists
    if env_file.exists():
        print_warning(".env file already exists")
        with open(env_file, 'r') as f:
            content = f.read()
            if "OPENAI_API_KEY=" in content and "your_openai_api_key_here" not in content:
                print_success("API key appears to be already configured")
                response = input("Do you want to update it? (y/N): ").strip().lower()
                if response != 'y':
                    return True

    # Get API key
    api_key = provided_key

    if not api_key:
        print_info("You need an OpenAI API key to use the AI assistant features.")
        print_info("Get one at: https://platform.openai.com/api-keys")
        print_info("(You can skip this and add it later to the .env file)")
        print()
        api_key = input("Enter your OpenAI API key (or press Enter to skip): ").strip()

    if not api_key:
        print_warning("Skipping API key configuration")
        print_info("To add it later, edit the .env file")
        # Still create .env from example
        if env_example.exists():
            with open(env_example, 'r') as f:
                content = f.read()
            with open(env_file, 'w') as f:
                f.write(content)
        return True

    # Validate key format (basic check)
    if not api_key.startswith('sk-'):
        print_warning("API key doesn't start with 'sk-'. This might not be valid.")
        response = input("Continue anyway? (y/N): ").strip().lower()
        if response != 'y':
            return False

    # Write to .env file
    try:
        with open(env_file, 'w') as f:
            f.write(f"# OpenAI API Configuration\n")
            f.write(f"# Generated by installer on {platform.system()}\n\n")
            f.write(f"OPENAI_API_KEY={api_key}\n")
        print_success("API key configured successfully")
        return True
    except Exception as e:
        print_error(f"Failed to write .env file: {e}")
        return False

def create_database_schema():
    """Create the database schema."""
    print_header("Creating Database Schema")

    python_path = get_venv_python()

    if not Path("create_ipeds_db_schema.py").exists():
        print_error("create_ipeds_db_schema.py not found")
        return False

    try:
        print_info("Creating database schema...")
        result = subprocess.run(
            [str(python_path), "create_ipeds_db_schema.py"],
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        print_success("Database schema created successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to create database schema: {e}")
        if e.stderr:
            print(e.stderr)
        return False

def generate_sample_data():
    """Generate sample data."""
    print_header("Generating Sample Data")

    python_path = get_venv_python()

    if not Path("SyntheticDataforSchema2.py").exists():
        print_error("SyntheticDataforSchema2.py not found")
        return False

    print_info("This will generate ~2000 students across 8 years of data")
    print_info("Estimated time: 10-30 seconds")

    try:
        print_info("Generating data...")
        result = subprocess.run(
            [str(python_path), "SyntheticDataforSchema2.py"],
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        print_success("Sample data generated successfully")

        # Check database size
        db_path = Path("ipeds_data.db")
        if db_path.exists():
            size_mb = db_path.stat().st_size / (1024 * 1024)
            print_info(f"Database size: {size_mb:.2f} MB")

        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to generate sample data: {e}")
        if e.stderr:
            print(e.stderr)
        return False

def print_next_steps():
    """Print next steps for the user."""
    print_header("Installation Complete!")

    print(f"{Colors.OKGREEN}{Colors.BOLD}✓ Setup completed successfully!{Colors.ENDC}\n")

    print(f"{Colors.BOLD}Next Steps:{Colors.ENDC}\n")

    if platform.system() == "Windows":
        print(f"1. Launch the AI Assistant:")
        print(f"   {Colors.OKCYAN}start.bat{Colors.ENDC}")
        print(f"   Or manually: venv\\Scripts\\activate && python ai_sql_python_assistant.py\n")
    else:
        print(f"1. Launch the AI Assistant:")
        print(f"   {Colors.OKCYAN}./start.sh{Colors.ENDC}")
        print(f"   Or manually: source venv/bin/activate && python ai_sql_python_assistant.py\n")

    print(f"2. Open your browser to: {Colors.OKCYAN}http://localhost:7860{Colors.ENDC}\n")

    print(f"3. Try asking questions like:")
    print(f"   • What are the retention rates by race and ethnicity?")
    print(f"   • Show me average GPA by class year")
    print(f"   • How many students graduated in each program?\n")

    print(f"{Colors.BOLD}Other Useful Scripts:{Colors.ENDC}\n")
    print(f"   • Generate CSV data: {Colors.OKCYAN}python generate_synthetic_data.py{Colors.ENDC}")
    print(f"   • Validate CSV data: {Colors.OKCYAN}python validate_data.py{Colors.ENDC}")
    print(f"   • Anonymize data: {Colors.OKCYAN}python anonymize_data.py input.csv output.csv translation.csv{Colors.ENDC}\n")

    print(f"{Colors.BOLD}Documentation:{Colors.ENDC}\n")
    print(f"   • README.md - Full documentation")
    print(f"   • docs/SETUP_WINDOWS.md - Windows guide")
    print(f"   • docs/SETUP_MAC.md - Mac/Linux guide\n")

    if not Path(".env").exists() or Path(".env").stat().st_size < 50:
        print_warning("Remember to configure your OpenAI API key in .env file!")
        print_info("Edit .env and add: OPENAI_API_KEY=sk-your-key-here\n")

def main():
    """Main installer function."""
    parser = argparse.ArgumentParser(description="IPEDS Data Analysis Toolkit Installer")
    parser.add_argument('--skip-data', action='store_true', help='Skip sample data generation')
    parser.add_argument('--api-key', type=str, help='OpenAI API key')
    parser.add_argument('--no-venv', action='store_true', help='Skip virtual environment creation')
    args = parser.parse_args()

    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║                                                                    ║")
    print("║         IPEDS Data Analysis Toolkit - Automated Installer         ║")
    print("║                                                                    ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")

    # Step 1: Check Python version
    if not check_python_version():
        sys.exit(1)

    # Step 2: Create virtual environment
    if not args.no_venv:
        if not create_virtual_environment():
            sys.exit(1)
    else:
        print_warning("Skipping virtual environment creation (--no-venv)")

    # Step 3: Install dependencies
    if not install_dependencies():
        print_error("Installation failed at dependency installation step")
        sys.exit(1)

    # Step 4: Configure API key
    if not configure_api_key(args.api_key):
        print_warning("API key configuration skipped or failed")
        print_info("You can add it manually to .env file later")

    # Step 5: Create database schema
    if not create_database_schema():
        print_error("Installation failed at database creation step")
        sys.exit(1)

    # Step 6: Generate sample data (optional)
    if not args.skip_data:
        response = input("\nGenerate sample data now? (Y/n): ").strip().lower()
        if response != 'n':
            if not generate_sample_data():
                print_warning("Sample data generation failed, but you can run it later")
    else:
        print_info("Skipping sample data generation (--skip-data)")
        print_info("Run 'python SyntheticDataforSchema2.py' later to generate data")

    # Final step: Print next steps
    print_next_steps()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Installation cancelled by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
