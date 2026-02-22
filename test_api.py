import requests
import json

url = "http://127.0.0.1:8000/api/v1/analyze"
payload = {
    "chip_model": "KunPeng920",
    "raw_log": "ERROR: CPU fault detected - 0X010001 at core 0"
}

headers = {
    "Content-Type": "application/json"
}

print("Sending request to:", url)
print("Payload:", json.dumps(payload, indent=2))

response = requests.post(url, json=payload, headers=headers)

print("\nResponse Status:", response.status_code)
print("Response Body:")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
