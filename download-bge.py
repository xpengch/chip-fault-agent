#!/usr/bin/env python
"""
Download BGE model for offline deployment
Run this on a machine with internet access
"""
import os
import shutil
from pathlib import Path

MODEL_NAME = "BAAI/bge-large-zh-v1.5"
OUTPUT_DIR = "offline-package/bge-model"

def download_bge_model():
    print("=" * 50)
    print(" BGE Model Download for Offline Deployment")
    print("=" * 50)
    print()
    
    # Create output directory
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"[1/3] Target directory: {output_path}")
    print()
    
    # Set cache directory
    cache_dir = str(output_path)
    os.environ['TRANSFORMERS_CACHE'] = cache_dir
    os.environ['HF_HOME'] = cache_dir
    
    print("[2/3] Downloading model...")
    print(f"    Model: {MODEL_NAME}")
    print(f"    Size: ~1.3GB")
    print(f"    Please wait...")
    print()
    
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(MODEL_NAME)
        
        # Test the model
        test_embedding = model.encode("测试文本")
        print(f"[OK] Model downloaded and tested")
        print(f"    Embedding dimension: {len(test_embedding)}")
        print()
        
        # Get directory size
        total_size = sum(f.stat().st_size for f in output_path.rglob('*') if f.is_file())
        size_mb = total_size / (1024 * 1024)
        print(f"[3/3] Download complete!")
        print(f"    Total size: {size_mb:.1f} MB")
        print()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Download failed: {e}")
        return False

if __name__ == "__main__":
    success = download_bge_model()
    if success:
        print("=" * 50)
        print(" Model ready for offline deployment!")
        print("=" * 50)
        print()
        print("Next steps:")
        print("1. Copy the 'offline-package' folder to target machine")
        print("2. The model will be automatically loaded")
        print()
    else:
        print("Download failed. Please check:")
        print("- Internet connection")
        print("- HuggingFace access (may need VPN)")
        print()
        exit(1)
