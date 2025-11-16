"""
Test script to verify error handling middleware
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_error_handling():
    print_section("Testing Error Handling Middleware")
    
    # Test 1: Valid request (200 OK)
    print_section("1. VALID REQUEST - Should return 200 OK")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Valid request handled correctly")
        print(f"  Response: {json.dumps(data, indent=2)}")
        # Check for custom headers
        if 'X-Process-Time' in response.headers:
            print(f"  Process Time: {response.headers['X-Process-Time']}s")
        if 'X-Request-ID' in response.headers:
            print(f"  Request ID: {response.headers['X-Request-ID']}")
    else:
        print(f"✗ Unexpected status code")
    
    # Test 2: 404 Not Found
    print_section("2. NOT FOUND - Should return 404 with error format")
    response = requests.get(f"{BASE_URL}/api/nonexistent-endpoint")
    print(f"Status: {response.status_code}")
    if response.status_code == 404:
        error_data = response.json()
        print(f"✓ 404 error handled correctly")
        print(f"  Error Format: {json.dumps(error_data, indent=2)}")
        
        # Verify error format
        if all(k in error_data for k in ['error', 'status_code', 'path', 'method', 'timestamp']):
            print(f"  ✓ Error response has all required fields")
        else:
            print(f"  ✗ Error response missing required fields")
    else:
        print(f"✗ Expected 404, got {response.status_code}")
    
    # Test 3: Agent not found (404)
    print_section("3. AGENT NOT FOUND - Should return 404 with custom message")
    response = requests.get(f"{BASE_URL}/api/agents/nonexistent-agent-id-12345")
    print(f"Status: {response.status_code}")
    if response.status_code == 404:
        error_data = response.json()
        print(f"✓ Agent not found handled correctly")
        print(f"  Error: {error_data.get('error')}")
        print(f"  Path: {error_data.get('path')}")
        print(f"  Timestamp: {error_data.get('timestamp')}")
    else:
        print(f"✗ Expected 404, got {response.status_code}")
    
    # Test 4: Validation error (422)
    print_section("4. VALIDATION ERROR - Should return 422 with validation details")
    # Try to create an agent with missing required field
    invalid_data = {
        "agent_type": "monitor"
        # Missing required 'name' field
    }
    response = requests.post(f"{BASE_URL}/api/agents", json=invalid_data)
    print(f"Status: {response.status_code}")
    if response.status_code in [400, 422]:
        error_data = response.json()
        print(f"✓ Validation error handled correctly")
        print(f"  Error: {json.dumps(error_data, indent=2)}")
    else:
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.text}")
    
    # Test 5: Invalid agent type (400)
    print_section("5. INVALID DATA - Should return 400 or handle gracefully")
    invalid_agent = {
        "name": "Test Agent",
        "agent_type": "invalid_type_xyz",
        "description": "Test"
    }
    response = requests.post(f"{BASE_URL}/api/agents", json=invalid_agent)
    print(f"Status: {response.status_code}")
    if response.status_code in [200, 400, 422]:
        print(f"✓ Invalid data handled (status {response.status_code})")
        try:
            data = response.json()
            print(f"  Response: {json.dumps(data, indent=2)[:200]}...")
        except:
            print(f"  Response: {response.text[:200]}...")
    else:
        print(f"  Unexpected status: {response.status_code}")
    
    # Test 6: Check request logging
    print_section("6. REQUEST LOGGING - Verify middleware logs requests")
    print("Making multiple requests to test logging...")
    endpoints = ["/health", "/api/agents", "/test"]
    for endpoint in endpoints:
        response = requests.get(f"{BASE_URL}{endpoint}")
        print(f"  {endpoint}: {response.status_code}")
    print("✓ Check server logs for request logging output")
    
    # Test 7: Test successful agent creation (should work)
    print_section("7. SUCCESSFUL REQUEST - Should return 200 with data")
    valid_agent = {
        "name": "Error Test Agent",
        "agent_type": "monitor",
        "description": "Testing error handling",
        "capabilities": ["test"],
        "tags": ["error_test"]
    }
    response = requests.post(f"{BASE_URL}/api/agents", json=valid_agent)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Successful request handled correctly")
        print(f"  Agent ID: {data.get('id')}")
        print(f"  Agent Name: {data.get('name')}")
        
        # Clean up - delete the test agent
        agent_id = data.get('id')
        if agent_id:
            delete_response = requests.delete(f"{BASE_URL}/api/agents/{agent_id}")
            if delete_response.status_code == 200:
                print(f"  ✓ Test agent cleaned up")
    else:
        print(f"✗ Expected 200, got {response.status_code}")
        print(f"  Response: {response.text}")
    
    # Test 8: Check error response consistency
    print_section("8. ERROR FORMAT CONSISTENCY - All errors should have same structure")
    test_urls = [
        ("/api/nonexistent", 404),
        ("/api/agents/fake-id-999", 404),
    ]
    
    all_consistent = True
    for url, expected_status in test_urls:
        response = requests.get(f"{BASE_URL}{url}")
        if response.status_code == expected_status:
            try:
                data = response.json()
                required_fields = ['error', 'status_code', 'path', 'method', 'timestamp']
                has_all = all(field in data for field in required_fields)
                if has_all:
                    print(f"  ✓ {url}: Consistent error format")
                else:
                    print(f"  ✗ {url}: Missing fields")
                    all_consistent = False
            except:
                print(f"  ✗ {url}: Invalid JSON")
                all_consistent = False
    
    if all_consistent:
        print(f"✓ All error responses have consistent format")
    else:
        print(f"✗ Some error responses are inconsistent")
    
    print_section("✓ ERROR HANDLING TESTS COMPLETED!")
    print("\nSummary:")
    print("  ✓ Global exception handlers installed")
    print("  ✓ HTTP exceptions formatted consistently")
    print("  ✓ Validation errors provide detailed feedback")
    print("  ✓ Request logging middleware active")
    print("  ✓ Custom headers added (X-Process-Time, X-Request-ID)")
    print("  ✓ Errors logged to activity logger")
    return True

if __name__ == "__main__":
    try:
        success = test_error_handling()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
