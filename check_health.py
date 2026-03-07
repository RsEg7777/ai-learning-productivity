"""
Quick health check script.
Verifies the API server is running and healthy.

Usage: python check_health.py
"""

import requests
import sys
import json

API_URL = "http://localhost:8000"

def check_health():
    """Check API health."""
    try:
        print("Checking API health...")
        print(f"URL: {API_URL}/health\n")
        
        response = requests.get(f"{API_URL}/health", timeout=5)
        data = response.json()
        
        status = data.get('status', 'unknown')
        message = data.get('message', 'No message')
        
        # Print status with color
        if status == 'healthy':
            print("✅ Status: HEALTHY")
            print(f"   {message}\n")
        elif status == 'degraded':
            print("⚠️  Status: DEGRADED")
            print(f"   {message}\n")
        else:
            print("❌ Status: UNHEALTHY")
            print(f"   {message}\n")
        
        # Print services
        services = data.get('services', {})
        if services:
            print("Services:")
            for service, is_ok in services.items():
                icon = "✓" if is_ok else "✗"
                print(f"  {icon} {service}")
            print()
        
        # Print errors
        errors = data.get('errors', [])
        if errors:
            print("Errors:")
            for error in errors:
                print(f"  ❌ {error}")
            print()
        
        # Print warnings
        warnings = data.get('warnings', [])
        if warnings:
            print("Warnings:")
            for warning in warnings:
                print(f"  ⚠️  {warning}")
            print()
        
        # Return exit code
        if status == 'healthy':
            return 0
        elif status == 'degraded':
            print("Note: Server is running but some services are unavailable.")
            return 0
        else:
            print("Error: Server is unhealthy. Check the errors above.")
            return 1
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server")
        print(f"   Make sure the server is running at {API_URL}")
        print("\n   Start the server with:")
        print("   Windows: .\\start-server.ps1")
        print("   Linux/Mac: python -m uvicorn app:app --reload --port 8000")
        return 1
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        print("   The server is not responding. Check if it's running.")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(check_health())
