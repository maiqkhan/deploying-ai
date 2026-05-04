import requests
import pandas as pd
import time

destinations = [
    "Tokyo", "Paris", "Bali", "New York City", "London",
    "Bangkok", "Rome", "Barcelona", "Amsterdam", "Sydney",
    "Dubai", "Singapore", "Istanbul", "Prague", "Lisbon",
    "Mexico City", "Buenos Aires", "Cape Town", "Marrakech",
    "Kyoto", "Seoul", "Vienna", "Copenhagen", "Zurich"
]

def get_wikipedia_intro(city: str, retries: int = 3) -> dict:
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + city.replace(" ", "_")
    
    for attempt in range(retries):
        resp = requests.get(url, headers={"User-Agent": "travel-assistant-project/1.0"})
        
        if resp.status_code == 200 and resp.text.strip():
            data = resp.json()
            return {
                "id":    city.lower().replace(" ", "_"),
                "title": data.get("title", city),
                "text":  data.get("extract", ""),
                "url":   data.get("content_urls", {}).get("desktop", {}).get("page", "")
            }
        
        print(f"  attempt {attempt + 1} failed (status {resp.status_code}), retrying...")
        time.sleep(2 ** attempt)  # exponential backoff: 1s, 2s, 4s
    
    raise Exception(f"Failed after {retries} attempts")

rows = []
for dest in destinations:
    try:
        row = get_wikipedia_intro(dest)
        rows.append(row)
        print(f"✓ {dest} ({len(row['text'])} chars)")
    except Exception as e:
        print(f"✗ {dest}: {e}")
    
    time.sleep(0.5)  # 500ms between every request

df = pd.DataFrame(rows)
df.to_csv("./embeddings/data/articles.csv", index=False)
print(f"\nSaved {len(df)} articles to data/articles.csv")