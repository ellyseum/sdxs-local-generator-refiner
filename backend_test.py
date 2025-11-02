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

    def test_refiner_prepare_sdxs(self):
        """Test SDXS refiner preparation (should use existing model)"""
        success, response = self.run_test(
            "Refiner Prepare - SDXS",
            "POST",
            "refiner/prepare",
            200,
            data={
                "modelCardUrl": "https://huggingface.co/IDKiro/sdxs-512-0.9",
                "modelType": "sdxs"
            }
        )
        
        if success and response.get('ok'):
            print(f"   SDXS refiner ready: {response.get('message')}")
            return True
        return False

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

    def test_refine_image_sdxs(self, original_filename):
        """Test image refinement with SDXS"""
        if not original_filename:
            self.log_test("Refine Image - SDXS", False, "No original image filename provided")
            return False, None
            
        success, response = self.run_test(
            "Refine Image - SDXS",
            "POST",
            "refiner/refine",
            200,
            data={
                "originalImageFilename": original_filename,
                "refinementPrompt": "make it more vibrant and colorful",
                "modelType": "sdxs",
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
            self.log_test("Get Refined Image", False, "No refined image path provided")
            return False
            
        # Extract filename from path
        filename = refined_image_path.split('/')[-1]
        
        success, response = self.run_test(
            "Get Refined Image",
            "GET",
            f"images/refined/{filename}",
            200,
            timeout=30
        )
        return success

    def test_get_nonexistent_refined_image(self):
        """Test retrieving non-existent refined image"""
        success, response = self.run_test(
            "Get Non-existent Refined Image",
            "GET",
            "images/refined/nonexistent.png",
            404
        )
        return success

    def test_refine_without_model(self):
        """Test refinement without loading refiner model first"""
        success, response = self.run_test(
            "Refine Image - No Refiner Loaded",
            "POST",
            "refiner/refine",
            400,  # Should fail without refiner
            data={
                "originalImageFilename": "test.png",
                "refinementPrompt": "test prompt",
                "modelType": "small-sd-v0"
            }
        )
        return success

    def test_refine_nonexistent_image(self):
        """Test refinement with non-existent original image"""
        success, response = self.run_test(
            "Refine Image - Non-existent Original",
            "POST",
            "refiner/refine",
            500,  # Should fail with non-existent image
            data={
                "originalImageFilename": "nonexistent.png",
                "refinementPrompt": "test prompt",
                "modelType": "sdxs"
            }
        )
        return success

def main():
    print("🚀 Starting SD-XS API Tests with Refiner Functionality")
    print("=" * 60)
    
    tester = SDXSAPITester()
    
    # Basic API Tests
    print("\n📋 BASIC API TESTS")
    print("-" * 30)
    
    # Test 1: Root endpoint
    tester.test_root_endpoint()
    
    # Test 2: Invalid model URL
    tester.test_model_prepare_invalid_url()
    
    # Test 3: Generate without model (should fail)
    tester.test_generate_without_model()
    
    # Test 4: Get non-existent image
    tester.test_get_nonexistent_image()
    
    # Test 5: Get non-existent refined image
    tester.test_get_nonexistent_refined_image()
    
    # Test 6: Refine without model (should fail)
    tester.test_refine_without_model()
    
    # Test 7: Refine non-existent image (should fail)
    tester.test_refine_nonexistent_image()
    
    # SD-XS Model Tests
    print("\n🎨 SD-XS MODEL TESTS")
    print("-" * 30)
    
    # Test 8: Valid model preparation (this takes time)
    model_success, model_response = tester.test_model_prepare_valid_url()
    
    original_filename = None
    if model_success:
        # Test 9: Generate image with loaded model
        gen_success, image_path = tester.test_generate_with_model()
        
        if gen_success and image_path:
            # Test 10: Retrieve generated image
            tester.test_get_image(image_path)
            # Extract filename for refinement tests
            original_filename = image_path.split('/')[-1]
    else:
        print("⚠️  Skipping image generation tests due to model loading failure")
        tester.log_test("Generate Image - With Model", False, "Skipped due to model loading failure")
        tester.log_test("Get Generated Image", False, "Skipped due to model loading failure")
    
    # Refiner Tests
    print("\n🔧 REFINER FUNCTIONALITY TESTS")
    print("-" * 30)
    
    if original_filename:
        # Test 11: SDXS Refiner preparation (should use existing model)
        sdxs_refiner_success = tester.test_refiner_prepare_sdxs()
        
        if sdxs_refiner_success:
            # Test 12: Refine image with SDXS
            sdxs_refine_success, sdxs_refined_path = tester.test_refine_image_sdxs(original_filename)
            
            if sdxs_refine_success and sdxs_refined_path:
                # Test 13: Retrieve SDXS refined image
                tester.test_get_refined_image(sdxs_refined_path)
        
        # Test 14: Small SD V0 Refiner preparation (optional - may be slow)
        print("\n⚠️  Small SD V0 tests are optional due to large download size")
        user_input = input("Run Small SD V0 tests? (y/N): ").strip().lower()
        
        if user_input == 'y':
            small_sd_refiner_success = tester.test_refiner_prepare_small_sd_v0()
            
            if small_sd_refiner_success:
                # Test 15: Refine image with Small SD V0
                small_sd_refine_success, small_sd_refined_path = tester.test_refine_image_small_sd_v0(original_filename)
                
                if small_sd_refine_success and small_sd_refined_path:
                    # Test 16: Retrieve Small SD V0 refined image
                    tester.test_get_refined_image(small_sd_refined_path)
        else:
            print("⏭️  Skipping Small SD V0 tests")
            tester.log_test("Refiner Prepare - Small SD V0", False, "Skipped by user choice")
            tester.log_test("Refine Image - Small SD V0", False, "Skipped by user choice")
            tester.log_test("Get Refined Image - Small SD V0", False, "Skipped by user choice")
    else:
        print("⚠️  Skipping refiner tests due to no generated image")
        tester.log_test("Refiner Prepare - SDXS", False, "Skipped due to no generated image")
        tester.log_test("Refine Image - SDXS", False, "Skipped due to no generated image")
        tester.log_test("Get Refined Image - SDXS", False, "Skipped due to no generated image")
        tester.log_test("Refiner Prepare - Small SD V0", False, "Skipped due to no generated image")
        tester.log_test("Refine Image - Small SD V0", False, "Skipped due to no generated image")
        tester.log_test("Get Refined Image - Small SD V0", False, "Skipped due to no generated image")
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    # Print detailed results
    print("\n📋 Detailed Results:")
    for result in tester.test_results:
        status = "✅" if result['success'] else "❌"
        print(f"   {status} {result['test']}")
        if not result['success'] and result['details']:
            print(f"      └─ {result['details']}")
    
    if tester.tests_passed == tester.tests_run:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n❌ {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())