import os
import re
import sys
import requests
import json
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv()

def extract_user_id(profile_url):
    profile_url = profile_url.strip()
    if profile_url.startswith("spotify:user:"):
        return profile_url.split(":")[-1]
    match = re.search(r"open\.spotify\.com/user/([^/?#]+)", profile_url)
    if match:
        return match.group(1)
    return profile_url

def get_user_tracks(sp, user_id, max_tracks=30):
    try:
        playlists = sp.user_playlists(user_id)
    except Exception as e:
        return []
    if not playlists or not playlists.get('items'):
        return []
    tracks = []
    for playlist in playlists['items']:
        playlist_id = playlist['id']
        remaining = max_tracks - len(tracks)
        if remaining <= 0:
            break
        try:
            results = sp.playlist_tracks(playlist_id, limit=remaining)
            for item in results.get('items', []):
                track = item.get('track')
                if not track:
                    continue
                track_name = track['name']
                artists = ", ".join([artist['name'] for artist in track.get('artists', [])])
                tracks.append(f"{track_name} - {artists}")
                if len(tracks) >= max_tracks:
                    break
        except:
            continue
    return tracks

def analyze_music_taste(sarki_listesi_str):
    api_url = os.getenv("LLM_API_URL")
    api_key = os.getenv("LLM_API_KEY")
    model_name = os.getenv("LLM_MODEL", "gpt-4o-mini")
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    prompt = f"Sen bir müzik küratörüsün. Kullanıcının listesi: {sarki_listesi_str}. Bu listeye göre 1. Müzikal Aura, 2. Tarz Tespiti, 3. Nokta Atışı Öneri (1 sanatçı, 1 şarkı), 4. Neden Bu Öneri? başlıklarında samimi ve havalı bir analiz yap."
    payload = {"model": model_name, "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        return response.json()["choices"][0]["message"]["content"]
    except:
        return None

def main():
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))
    profile_input = input("Spotify Profil Linkini girin: ")
    user_id = extract_user_id(profile_input)
    tracks = get_user_tracks(sp, user_id, 30)
    sarki_listesi_str = ", ".join(tracks)
    analiz_sonucu = analyze_music_taste(sarki_listesi_str)
    print(analiz_sonucu)

if __name__ == "__main__":
    main()
