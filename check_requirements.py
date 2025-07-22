"""
Requirements Checker for Pizza Scooper Violation Detection
This script checks if all required dependencies are installed and available.
"""

import importlib
import sys
import os

def check_package(package_name, import_name=None):
    """Check if a package is available"""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        return True
    except ImportError:
        return False

def check_file_exists(file_path, description):
    """Check if a file exists"""
    if os.path.exists(file_path):
        return True
    else:
        return False

def main():
    print("Checking Requirements for Pizza Scooper Violation Detection")
    print("="*70)
    
    # Required Python packages
    packages = [
        ("torch", "torch"),
        ("torchvision", "torchvision"),
        ("ultralytics", "ultralytics"),
        ("opencv-python", "cv2"),
        ("numpy", "numpy"),
        ("matplotlib", "matplotlib"),
        ("tqdm", "tqdm"),
        ("Pillow", "PIL"),
        ("kafka-python", "kafka"),
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("streamlit", "streamlit"),
        ("requests", "requests"),
        ("json", "json"),
        ("base64", "base64"),
        ("time", "time"),
        ("threading", "threading")
    ]
    
    # Required files
    files = [
        ("model/yolo12m-v2.pt", "YOLO Model"),
        ("data/videos/Sah b3dha ghalt.mp4", "Test Video 1"),
        ("data/videos/Sah w b3dha ghalt (2).mp4", "Test Video 2"),
        ("data/videos/Sah w b3dha ghalt (3).mp4", "Test Video 3"),
        ("data/rois/rois.json", "ROI Configuration"),
        ("frame_reader/main.py", "Frame Reader Service"),
        ("detection_service/main.py", "Detection Service"),
        ("streaming_service/main.py", "Streaming Service"),
        ("frontend/app.py", "Frontend Service")
    ]
    
    # Check packages
    print("Checking Python packages...")
    package_results = {}
    
    for package_name, import_name in packages:
        available = check_package(package_name, import_name)
        package_results[package_name] = available
        status = "OK" if available else "MISSING"
        print(f"   {status} {package_name}")
    
    # Check files
    print("\nChecking required files...")
    file_results = {}
    
    for file_path, description in files:
        exists = check_file_exists(file_path, description)
        file_results[file_path] = exists
        status = "OK" if exists else "MISSING"
        print(f"   {status} {description}: {file_path}")
    
    # Summary
    print(f"\nSUMMARY:")
    
    package_count = len(packages)
    package_available = sum(package_results.values())
    print(f"   Packages: {package_available}/{package_count} available")
    
    file_count = len(files)
    file_available = sum(file_results.values())
    print(f"   Files: {file_available}/{file_count} available")
    
    # Recommendations
    print(f"\nRECOMMENDATIONS:")
    
    if package_available < package_count:
        print("Missing packages detected!")
        print("   Install missing packages with:")
        print("   pip install torch torchvision ultralytics opencv-python numpy matplotlib tqdm Pillow kafka-python fastapi uvicorn streamlit requests")
    
    if file_available < file_count:
        print("Missing files detected!")
        print("   Ensure all required files are in the correct locations.")
    
    if package_available == package_count and file_available == file_count:
        print("All requirements are satisfied!")
        print("   You can now run the test suite.")
    
    # Return overall status
    overall_success = package_available == package_count and file_available == file_count
    
    if overall_success:
        print(f"\nRequirements check PASSED!")
        print(f"   Ready to run tests and deploy the system.")
    else:
        print(f"\nRequirements check FAILED!")
        print(f"   Please install missing dependencies and ensure all files are present.")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 