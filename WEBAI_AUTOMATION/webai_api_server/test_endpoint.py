import requests

r = requests.get(
    'http://localhost:8000/execute/1/steps',
    headers={'X-API-Key': 'o3-pxCyR0eY8dqI-iCHW6AVGGwrjQU8aJw-VBIt1f-8'}
)

print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Success! Got {len(data['steps'])} steps")
else:
    print(f"Error: {r.text[:200]}")
