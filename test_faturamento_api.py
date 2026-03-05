"""
Test script to diagnose faturamento API endpoint using HTTP requests
"""
import requests
import json

print("=" * 80)
print("TESTING FATURAMENTO API ENDPOINT")
print("=" * 80)

base_url = "http://localhost:8000"
endpoint = "/api/faturamento/brand"
data_ini = "2022-01-01"
data_fim = "2022-01-31"

url = f"{base_url}{endpoint}?data_ini={data_ini}&data_fim={data_fim}"

print(f"\nTesting URL: {url}\n")

try:
    print("Sending GET request...")
    response = requests.get(url, timeout=30)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"\nResponse Type: {type(data)}")
            print(f"Response Length: {len(data) if isinstance(data, list) else 'N/A'}")
            
            if isinstance(data, list):
                if len(data) == 0:
                    print("\n⚠️  WARNING: Empty array returned!")
                    print("This could mean:")
                    print("  1. No data exists for this period")
                    print("  2. All data is filtered out (canceled/devoluções)")
                    print("  3. There's a query issue")
                else:
                    print(f"\n✅ Success! Found {len(data)} brands")
                    print("\nFirst 3 brands:")
                    for i, brand in enumerate(data[:3]):
                        print(f"  {i+1}. {json.dumps(brand, indent=2, default=str)}")
            else:
                print(f"\nResponse: {json.dumps(data, indent=2, default=str)}")
        except json.JSONDecodeError as e:
            print(f"\n❌ JSON decode error: {e}")
            print(f"Response text: {response.text[:500]}")
    else:
        print(f"\n❌ Error Status Code: {response.status_code}")
        print(f"Response text: {response.text[:500]}")
        
except requests.exceptions.ConnectionError:
    print("\n❌ ERROR: Could not connect to backend!")
    print("Make sure the backend is running on http://localhost:8000")
    print("\nTo start the backend:")
    print("  cd backend")
    print("  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
except requests.exceptions.Timeout:
    print("\n❌ ERROR: Request timed out!")
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
print("\nNext steps:")
print("  1. Check backend console/logs for detailed error messages")
print("  2. Verify database connection is working")
print("  3. Check if data exists for the date range")
