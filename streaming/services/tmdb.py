import requests
import os
from dotenv import load_dotenv
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"


def search_movie(title):
    url = f"{BASE_URL}/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": title
    }
    return requests.get(url, params=params,timeout=10).json()


def get_watch_providers(movie_id, region="IN"):
    url = f"{BASE_URL}/movie/{movie_id}/watch/providers"
    params = {"api_key": TMDB_API_KEY}
    data = requests.get(url, params=params).json()
    return data.get("results", {}).get(region, {})


def get_movie_details(movie_id):
    url = f"{BASE_URL}/movie/{movie_id}"
    params = {
        "api_key": TMDB_API_KEY
    }
    return requests.get(url, params=params, timeout=10).json()
