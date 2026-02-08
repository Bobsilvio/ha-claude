#!/usr/bin/env python3

"""Test script for Claude API."""

import json
import requests
from typing import Dict, Any

# Configuration
API_URL = "http://localhost:5000"
TIMEOUT = 10

# Colors for output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
END = '\033[0m'


def print_header(text: str) -> None:
    """Print colored header."""
    print(f"\n{BLUE}{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}{END}\n")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{GREEN}✓ {text}{END}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{RED}✗ {text}{END}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"{YELLOW}ℹ {text}{END}")


def test_health() -> bool:
    """Test health endpoint."""
    print_header("Testing Health Endpoint")
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Health check passed: {data}")
            return True
        else:
            print_error(f"Health check failed: HTTP {response.status_code}")
            return False
            
    except requests.ConnectionError:
        print_error("Cannot connect to API")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_entities() -> bool:
    """Test get entities endpoint."""
    print_header("Testing Get Entities")
    
    try:
        response = requests.get(f"{API_URL}/entities", timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            print_success(f"Retrieved {count} entities")
            return True
        else:
            print_error(f"Failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_automations() -> bool:
    """Test get automations endpoint."""
    print_header("Testing Get Automations")
    
    try:
        response = requests.get(f"{API_URL}/automations", timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            print_success(f"Retrieved {count} automations")
            return True
        else:
            print_error(f"Failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_scripts() -> bool:
    """Test get scripts endpoint."""
    print_header("Testing Get Scripts")
    
    try:
        response = requests.get(f"{API_URL}/scripts", timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            print_success(f"Retrieved {count} scripts")
            return True
        else:
            print_error(f"Failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_message() -> bool:
    """Test send message endpoint."""
    print_header("Testing Send Message")
    
    payload = {
        "message": "Test message from API",
        "context": "API test context"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/message",
            json=payload,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Message sent successfully")
            print_info(f"Response: {data}")
            return True
        else:
            print_error(f"Failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_webhook() -> bool:
    """Test webhook endpoint."""
    print_header("Testing Webhook")
    
    payload = {
        "action": "test_action",
        "data": "test_data"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/webhook/test_webhook",
            json=payload,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Webhook received")
            print_info(f"Response: {data}")
            return True
        else:
            print_error(f"Failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_404() -> bool:
    """Test 404 error handling."""
    print_header("Testing 404 Error Handling")
    
    try:
        response = requests.get(
            f"{API_URL}/nonexistent",
            timeout=TIMEOUT
        )
        
        if response.status_code == 404:
            print_success("404 error handled correctly")
            return True
        else:
            print_error(f"Expected 404, got HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def main() -> None:
    """Run all tests."""
    print(f"\n{BLUE}Claude API Test Suite{END}")
    print(f"API URL: {API_URL}\n")
    
    tests = [
        ("Health Check", test_health),
        ("Get Entities", test_entities),
        ("Get Automations", test_automations),
        ("Get Scripts", test_scripts),
        ("Send Message", test_message),
        ("Webhook", test_webhook),
        ("404 Error", test_404),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except KeyboardInterrupt:
            print_error("Tests interrupted by user")
            break
        except Exception as e:
            print_error(f"Unexpected error in {test_name}: {e}")
            results.append((test_name, False))
    
    # Print summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name}")
        else:
            print_error(f"{test_name}")
    
    print(f"\n{BLUE}Results: {passed}/{total} tests passed{END}\n")
    
    if passed == total:
        print_success("All tests passed! 🎉")
    else:
        print_error(f"Some tests failed. Check the above output.")


if __name__ == "__main__":
    main()
