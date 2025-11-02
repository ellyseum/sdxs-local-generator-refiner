import requests
import sys
import time
from datetime import datetime
import json

class SDXSAPITester:
    def __init__(self, base_url="https://sdxs-generator.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            
            if success:
                self.log_test(name, True, f"Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                error_detail = f"Expected {expected_status}, got {response.status_code}"
                try:
                    error_detail += f" - {response.json()}"
                except:
                    error_detail += f" - {response.text[:200]}"
                self.log_test(name, False, error_detail)
                return False, {}

        except requests.exceptions.Timeout:
            self.log_test(name, False, f"Request timeout after {timeout}s")
            return False, {}
        except Exception as e:
            self.log_test(name, False, f"Error: {str(e)}")
            return False, {}

    def test_refiner_prepare_small_sd_v0(self):
        """Test Small SD V0 refiner preparation"""
        print("⚠️  This test will download Small SD V0 model (~2GB) and may take several minutes...")
        success, response = self.run_test(
            "Refiner Prepare - Small SD V0",
            "POST",
            "refiner/prepare",
            200,
            data={
                "modelCardUrl": "https://huggingface.co/OFA-Sys/small-stable-diffusion-v0",
                "modelType": "small-sd-v0"
            },
            timeout=600  # 10 minutes timeout for model download
        )
        
        if success and response.get('ok'):
            print(f"   Small SD V0 refiner loaded: {response.get('message')}")
            return True
        return False

    def test_refine_image_small_sd_v0(self, original_filename):
        """Test image refinement with Small SD V0"""
        if not original_filename:
            self.log_test("Refine Image - Small SD V0", False, "No original image filename provided")
            return False, None
            
        success, response = self.run_test(
            "Refine Image - Small SD V0",
            "POST",
            "refiner/refine",
            200,
            data={
                "originalImageFilename": original_filename,
                "refinementPrompt": "make it more vibrant and colorful",
                "modelType": "small-sd-v0",
                "strength": 0.75,
                "steps": 20,
                "guidance": 7.5
            },
            timeout=120  # 2 minutes for refinement
        )
        
        if success and response.get('ok'):
            print(f"   Refined image: {response.get('filename')}")
            print(f"   Refined path: {response.get('refinedImagePath')}")
            return True, response.get('refinedImagePath')
        return False, None

    def test_get_refined_image(self, refined_image_path):
        """Test retrieving refined image"""
        if not refined_image_path:
            self.log_test("Get Refined Image - Small SD V0", False, "No refined image path provided")
            return False
            
        # Extract filename from path
        filename = refined_image_path.split('/')[-1]
        
        success, response = self.run_test(
            "Get Refined Image - Small SD V0",
            "GET",
            f"images/refined/{filename}",
            200,
            timeout=30
        )
        return success

def main():
    print("🚀 Testing Small SD V0 Refiner Functionality")
    print("=" * 50)
    
    tester = SDXSAPITester()
    
    # We'll assume SDXS model is already loaded and we have a generated image
    # Let's use a known filename from the previous test
    original_filename = "56104c41-41b1-4b95-80db-e246d3a88a09.png"
    
    print(f"Using original image: {original_filename}")
    
    # Test Small SD V0 Refiner preparation
    small_sd_refiner_success = tester.test_refiner_prepare_small_sd_v0()
    
    if small_sd_refiner_success:
        # Test refinement with Small SD V0
        small_sd_refine_success, small_sd_refined_path = tester.test_refine_image_small_sd_v0(original_filename)
        
        if small_sd_refine_success and small_sd_refined_path:
            # Test retrieving Small SD V0 refined image
            tester.test_get_refined_image(small_sd_refined_path)
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Small SD V0 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    # Print detailed results
    print("\n📋 Detailed Results:")
    for result in tester.test_results:
        status = "✅" if result['success'] else "❌"
        print(f"   {status} {result['test']}")
        if not result['success'] and result['details']:
            print(f"      └─ {result['details']}")
    
    if tester.tests_passed == tester.tests_run:
        print("\n🎉 All Small SD V0 tests passed!")
        return 0
    else:
        print(f"\n❌ {tester.tests_run - tester.tests_passed} Small SD V0 tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())