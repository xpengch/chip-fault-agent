# -*- coding: utf-8 -*-
"""Copy BGE model to offline deployment package"""

import os
import shutil
from pathlib import Path

print("[INFO] Copying BGE model...")

# Target directory
target_dir = Path("D:/ai_dir/chip_fault_agent/offline-package/bge-model")
target_dir.mkdir(parents=True, exist_ok=True)

# Source BGE model directory (HuggingFace cache structure)
user_profile = os.environ.get('USERPROFILE', '')
cache_base = Path(user_profile) / '.cache' / 'huggingface' / 'hub' if user_profile else Path.home() / '.cache' / 'huggingface' / 'hub'

# Look for BGE model in the hub directory
bge_model_dir = None
for item in cache_base.iterdir():
    if 'bge' in item.name.lower() and 'BAAI' in item.name:
        bge_model_dir = item
        break

if not bge_model_dir:
    print("[ERROR] BGE model not found in cache")
    print(f"[INFO] Checked: {cache_base}")
    exit(1)

print(f"[INFO] Found BGE model: {bge_model_dir.name}")

# Copy the entire model directory
target_path = target_dir / bge_model_dir.name

if target_path.exists():
    shutil.rmtree(target_path)

shutil.copytree(bge_model_dir, target_path)

# Calculate size
total_size = 0
for f in target_path.rglob('*'):
    if f.is_file():
        total_size += f.stat().st_size

size_mb = total_size / (1024 * 1024)
size_gb = total_size / (1024 * 1024 * 1024)

print(f"[OK] BGE model copied successfully!")
print(f"     Size: {size_mb:.1f} MB ({size_gb:.2f} GB)")
print(f"     Source: {bge_model_dir}")
print(f"     Target: {target_path}")
print()
print("=" * 50)
print("BGE model included in offline package!")
print("=" * 50)
