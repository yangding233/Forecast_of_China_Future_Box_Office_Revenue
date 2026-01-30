import requests
import re
import io

api_url = "https://piaofang.maoyan.com/dashboard-ajax/movie?showDate=20251124&orderType=0&uuid=YOUR_UUID_HERE&timeStamp=1763719296067&channelId=40009&sVersion=2"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

print("Requesting API data...")
try:
    response = requests.get(api_url, headers=headers)
    response.raise_for_status()
    api_data = response.json()
    print("API data retrieved successfully.")
except requests.exceptions.RequestException as e:
    print(f"API Request Failed: {e}")
    exit(1)

# Extract and Download Font
font_style_css = api_data.get('fontStyle', '')
if not font_style_css:
    print("Error: 'fontStyle' field missing in API response.")
    exit(1)

# Regex to find .woff URL
match = re.search(r'url\("([^"]*\.woff)"\)', font_style_css)
if not match:
    print("Error: Could not extract .woff URL from fontStyle.")
    exit(1)

font_url = "https:" + match.group(1)
print(f"Font URL found: {font_url}")

print("Downloading...")
try:
    font_response = requests.get(font_url, headers=headers)
    font_response.raise_for_status()
    with open("base_font.woff", "wb") as f:
        f.write(font_response.content)
    print("saved as base_font.woff")
except requests.exceptions.RequestException as e:
    print(f"Font download failed: {e}")
    exit(1)