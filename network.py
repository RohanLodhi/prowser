import requests

def fetch_url(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return {
            "url": response.url,
            "content": response.text,
            "status": response.status_code
        }
    except Exception as e:
        return {"error": str(e)}