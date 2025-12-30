import requests
import json

BASE_URL = 'https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070'
API_KEY = '579b464db66ec23bdd00000162112b7dd11f40117613f282ddc07b6e'

def deep_inspect():
    params = {'api-key': API_KEY, 'format': 'json', 'limit': 1000}
    res = requests.get(BASE_URL, params=params)
    if res.status_code != 200:
        print(f"Error: {res.status_code}")
        return

    records = res.json().get('records', [])
    print(f"Fetched {len(records)} records.")

    # 1. Find all Unique States
    states = sorted(list(set(r.get('state') for r in records if r.get('state'))))
    print(f"States found: {states}")

    # 2. Find Punjab records
    punjab_records = [r for r in records if r.get('state') == 'Punjab']
    print(f"Punjab records found (case sensitive 'Punjab'): {len(punjab_records)}")
    if punjab_records:
        print("Sample Punjab record:", json.dumps(punjab_records[0], indent=2))
        districts = sorted(list(set(r.get('district') for r in punjab_records)))
        print(f"Districts in Punjab batch: {districts}")

    # 3. Search for 'Bathinda' in all records
    bathinda_records = [r for r in records if 'Bathinda' in str(r.values()) or 'bathinda' in str(r.values())]
    print(f"Bathinda found in any record: {len(bathinda_records)}")
    if bathinda_records:
        print("Sample Bathinda record:", json.dumps(bathinda_records[0], indent=2))

    # 4. Check 'Wheat' in all records
    wheat_records = [r for r in records if 'Wheat' in str(r.values()) or 'wheat' in str(r.values())]
    print(f"Wheat found in any record: {len(wheat_records)}")
    if wheat_records:
        print("Sample Wheat record:", json.dumps(wheat_records[0], indent=2))
        commodities = sorted(list(set(r.get('commodity') for r in records if 'Wheat' in r.get('commodity', ''))))
        print(f"Exact wheat-related commodity names: {commodities}")

deep_inspect()
