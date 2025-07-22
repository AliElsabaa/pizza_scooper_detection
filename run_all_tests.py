"""
Comprehensive Test Runner for Pizza Scooper Violation Detection
This script runs all individual tests and provides a summary report.
"""

import subprocess
import sys
import os
import time

def run_test(test_name, test_file):
    """Run a specific test and return success status"""
    print(f"\n{'='*60}")
    print(f"🧪 Running {test_name}...")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Test completed successfully")
            print(result.stdout)
            return True
        else:
            print("❌ Test failed")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Test timed out")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    print("🚀 Starting Comprehensive Test Suite for Pizza Scooper Violation Detection")
    print("="*80)
    
    # Define tests to run
    tests = [
        ("YOLO Model", "test_model.py"),
        ("ROI Configuration", "test_roi.py"),
        ("Frame Reader", "test_frame_reader.py"),
        ("Streaming Service", "test_streaming_service.py"),
        ("Frontend", "test_frontend.py")
    ]
    
    # Run all tests
    results = {}
    start_time = time.time()
    
    for test_name, test_file in tests:
        if os.path.exists(test_file):
            success = run_test(test_name, test_file)
            results[test_name] = success
        else:
            print(f"❌ Test file not found: {test_file}")
            results[test_name] = False
    
    # Generate summary report
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\n{'='*80}")
    print("📊 TEST SUMMARY REPORT")
    print(f"{'='*80}")
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"⏱️  Total test time: {total_time:.2f} seconds")
    print(f"📈 Results: {passed}/{total} tests passed")
    print(f"📊 Success rate: {passed/total*100:.1f}%")
    
    print(f"\n📋 Detailed Results:")
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    # Check if all core components are working
    core_tests = ["YOLO Model", "ROI Configuration", "Frame Reader"]
    core_passed = all(results.get(test, False) for test in core_tests)
    
    print(f"\n🎯 CORE COMPONENTS STATUS:")
    if core_passed:
        print("✅ All core components are working correctly")
        print("✅ Ready for end-to-end testing with Kafka")
    else:
        print("❌ Some core components have issues")
        print("❌ Fix core components before proceeding")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if passed == total:
        print("✅ All tests passed! Your system is ready for deployment.")
        print("✅ You can now proceed with Docker deployment or Kafka testing.")
    elif core_passed:
        print("⚠️  Core components work, but some optional tests failed.")
        print("✅ You can proceed with end-to-end testing.")
    else:
        print("❌ Core components have issues that need to be fixed first.")
        print("🔧 Check the failed tests above for specific issues.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 