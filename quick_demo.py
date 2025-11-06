#!/usr/bin/env python3
"""
Quick installer demo - shows the installer works without taking forever
This skips data generation to finish in ~2 minutes instead of 10
"""

import subprocess
import sys

print("\n" + "="*70)
print("QUICK DEMO INSTALLER (skips sample data)")
print("="*70 + "\n")

print("Running: python3 install.py --skip-data --api-key DEMO_KEY\n")
print("This will:")
print("  ✓ Check Python version")
print("  ✓ Create virtual environment")
print("  ✓ Install dependencies (this takes 2-3 minutes)")
print("  ✓ Create database schema")
print("  ✗ SKIP sample data (you can generate it later)")
print("\nStarting in 3 seconds...\n")

import time
time.sleep(3)

# Run the installer with flags to make it faster
result = subprocess.run([
    sys.executable,
    "install.py",
    "--skip-data",
    "--api-key",
    "sk-demo-key-you-can-change-this-later"
])

sys.exit(result.returncode)
