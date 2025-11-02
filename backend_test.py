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

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        return self.run_test("Root API Endpoint", "GET", "", 200)

    def test_model_prepare_invalid_url(self):
        """Test model prepare with invalid URL"""
        success, response = self.run_test(
            "Model Prepare - Invalid URL",
            "POST",
            "model/prepare",
            500,  # Expecting error for invalid URL
            data={"modelCardUrl": "invalid-url"}
        )
        return success

    def test_model_prepare_valid_url(self):
        """Test model prepare with valid HuggingFace URL"""
        # This will take a long time as it downloads the model
        print("⚠️  This test will download a large model (~2GB) and may take several minutes...")
        success, response = self.run_test(
            "Model Prepare - Valid URL",
            "POST",
            "model/prepare",
            200,
            data={"modelCardUrl": "https://huggingface.co/IDKiro/sdxs-512-0.9"},
            timeout=600  # 10 minutes timeout for model download
        )
        
        if success and response.get('ok'):
            print(f"   Model loaded: {response.get('repoId')}")
            print(f"   Message: {response.get('message')}")
            return True, response
        return False, response

    def test_generate_without_model(self):
        """Test image generation without loading a model first"""
        success, response = self.run_test(
            "Generate Image - No Model Loaded",
            "POST",
            "generate",
            400,  # Should fail without model
            data={"prompt": "a beautiful sunset"}
        )
        return success

    def test_generate_with_model(self):
        """Test image generation with loaded model"""
        success, response = self.run_test(
            "Generate Image - With Model",
            "POST",
            "generate",
            200,
            data={
                "prompt": "a beautiful sunset over mountains",
                "size": "512x512",
                "steps": 8,
                "guidance": 4.0
            },
            timeout=120  # 2 minutes for image generation
        )
        
        if success and response.get('ok'):
            print(f"   Image generated: {response.get('filename')}")
            print(f"   Image path: {response.get('imagePath')}")
            return True, response.get('imagePath')
        return False, None

    def test_get_image(self, image_path):
        """Test retrieving generated image"""
        if not image_path:
            self.log_test("Get Generated Image", False, "No image path provided")
            return False
            
        # Extract filename from path
        filename = image_path.split('/')[-1]
        
        success, response = self.run_test(
            "Get Generated Image",
            "GET",
            f"images/{filename}",
            200,
            timeout=30
        )
        return success

    def test_get_nonexistent_image(self):
        """Test retrieving non-existent image"""
        success, response = self.run_test(
            "Get Non-existent Image",
            "GET",
            "images/nonexistent.png",
            404
        )
        return success

def main():
    print("🚀 Starting SD-XS API Tests")
    print("=" * 50)
    
    tester = SDXSAPITester()
    
    # Test 1: Root endpoint
    tester.test_root_endpoint()
    
    # Test 2: Invalid model URL
    tester.test_model_prepare_invalid_url()
    
    # Test 3: Generate without model (should fail)
    tester.test_generate_without_model()
    
    # Test 4: Get non-existent image
    tester.test_get_nonexistent_image()
    
    # Test 5: Valid model preparation (this takes time)
    model_success, model_response = tester.test_model_prepare_valid_url()
    
    if model_success:
        # Test 6: Generate image with loaded model
        gen_success, image_path = tester.test_generate_with_model()
        
        if gen_success and image_path:
            # Test 7: Retrieve generated image
            tester.test_get_image(image_path)
    else:
        print("⚠️  Skipping image generation tests due to model loading failure")
        tester.log_test("Generate Image - With Model", False, "Skipped due to model loading failure")
        tester.log_test("Get Generated Image", False, "Skipped due to model loading failure")
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())