import requests

# Test your new token
token = "lip_q9w9l1KiSKyqoFR7BnCq"  # Replace with actual token
headers = {'Authorization': f'Bearer {token}'}
response = requests.get('https://lichess.org/api/account', headers=headers)

if response.status_code == 200:
    account_info = response.json()
    print(f"✅ Success! Account: {account_info.get('username')}")
    print(f"Title: {account_info.get('title', 'Regular User')}")
else:
    print(f"❌ Still failing: {response.status_code}")
    print(f"Response: {response.text}")
