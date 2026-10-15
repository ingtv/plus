from fastapi import FastAPI, Response
import requests
import urllib3
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = FastAPI(title="Justin M3U Generator", version="2.0")

# KAYNAKLAR
REDIRECT_SOURCE_URL = "http://raw.githack.com/eniyiyayinci/redirect-cdn/main/inattv.html"
DOMAIN_API_URL = "https://data-reality.com/domain.php"
MATCHES_API_URL = "https://data-reality.com/matches.php"
CHANNELS_API_URL = "https://data-reality.com/channels.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://canlimacizlejustin.online/"
}

def get_base_url_with_fallback():
    """Base URL'i al"""
    try:
        r = requests.get(DOMAIN_API_URL, headers=HEADERS, timeout=10, verify=False)
        data = r.json()
        base_url = data.get("baseurl", "")
        if base_url:
            base_url = base_url.replace("\\", "").rstrip('/')
            print(f"✅ Domain API'den base URL alındı: {base_url}")
            return base_url + "/"
    except Exception as e:
        print(f"⚠️ Domain API hatası: {e}")
    
    parsed = urlparse(MATCHES_API_URL)
    base_url = f"{parsed.scheme}://{parsed.netloc}/"
    print(f"⚠️ Varsayılan base URL: {base_url}")
    return base_url

def get_referrer_with_fallback():
    """Referrer adresini al"""
    try:
        parsed = urlparse(MATCHES_API_URL)
        referrer = f"{parsed.scheme}://{parsed.netloc}"
        return referrer
    except:
        return "https://canlimacizlejustin.online"

def parse_matches_from_html(html_content):
    """Maçları HTML'den parse et - İKİ LOGO DA ÇEKİLİYOR"""
    matches = []
    soup = BeautifulSoup(html_content, 'html.parser')
    match_links = soup.find_all('a', class_='single-match')
    
    for link in match_links:
        try:
            href = link.get('href', '')
            channel_id = href.replace('channel?id=', '') if 'channel?id=' in href else None
            
            imgs = link.find_all('img')
            home_logo = imgs[0].get('src') if len(imgs) > 0 else ''
            away_logo = imgs[1].get('src') if len(imgs) > 1 else ''
            
            detail_div = link.find('div', class_='match-detail')
            if not detail_div:
                continue
                
            date_div = detail_div.find('div', class_='date')
            match_type = date_div.text.strip() if date_div else 'football'
            
            event_div = detail_div.find('div', class_='event')
            event_text = event_div.text.strip() if event_div else ''
            
            time = ''
            league = ''
            if '|' in event_text:
                parts = event_text.split('|')
                time = parts[0].strip()
                league = parts[1].strip()
            else:
                league = event_text
            
            teams_div = detail_div.find('div', class_='teams')
            if teams_div:
                home_team = teams_div.find('div', class_='home')
                away_team = teams_div.find('div', class_='away')
                
                home = home_team.text.strip() if home_team else ''
                away = away_team.text.strip() if away_team else ''
                
                if channel_id and home and away:
                    channel_name = f"{home} - {away}"
                    if time:
                        channel_name += f" [{time}]"
                    
                    main_logo = home_logo or away_logo or ""
                    
                    matches.append({
                        'id': channel_id,
                        'name': channel_name,
                        'home': home,
                        'away': away,
                        'home_logo': home_logo,
                        'away_logo': away_logo,
                        'main_logo': main_logo,
                        'league': league,
                        'type': match_type.lower(),
                        'time': time,
                        'source': 'match'
                    })
        except Exception as e:
            continue
            
    return matches

def parse_channels_from_html(html_content):
    """Sabit kanalları HTML'den parse et"""
    channels = []
    soup = BeautifulSoup(html_content, 'html.parser')
    channel_links = soup.find_all('a', class_='single-match')
    
    for link in channel_links:
        try:
            href = link.get('href', '')
            channel_id = href.replace('channel?id=', '') if 'channel?id=' in href else None
            
            detail_div = link.find('div', class_='match-detail')
            if detail_div:
                event_div = detail_div.find('div', class_='event')
                if event_div and '7/24' in event_div.text:
                    teams_div = detail_div.find('div', class_='teams')
                    if teams_div:
                        home_div = teams_div.find('div', class_='home')
                        channel_name = home_div.text.strip() if home_div else ''
                        
                        away_div = teams_div.find('div', class_='away')
                        logo_img = away_div.find('img') if away_div else None
                        logo_url = logo_img.get('src') if logo_img else ''
                        
                        if channel_id and channel_name:
                            channels.append({
                                'id': channel_id,
                                'name': channel_name,
                                'logo': logo_url,
                                'type': 'static',
                                'source': 'channel'
                            })
        except Exception as e:
            continue
            
    return channels

def create_m3u_with_logos(matches, channels, base_url, referrer):
    """M3U playlist oluştur - tvg-logo olarak main_logo kullan"""
    m3u_list = ["#EXTM3U"]
    
    for match in matches:
        group = f"CANLI MAÇLAR - {match['league']}"
        extinf = f'#EXTINF:-1 tvg-logo="{match["main_logo"]}" group-title="{group}",{match["name"]}'
        
        m3u_list.append(extinf)
        m3u_list.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
        m3u_list.append(f'#EXTVLCOPT:http-referrer={referrer}/')
        m3u_list.append(f'{base_url}{match["id"]}/mono.m3u8')
        
    for channel in channels:
        extinf = f'#EXTINF:-1 tvg-logo="{channel["logo"]}" group-title="7/24 KANALLAR",{channel["name"]}'
        m3u_list.append(extinf)
        m3u_list.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
        m3u_list.append(f'#EXTVLCOPT:http-referrer={referrer}/')
        m3u_list.append(f'{base_url}{channel["id"]}/mono.m3u8')
        
    return m3u_list

@app.get("/")
def home():
    return {
        "status": "online", 
        "endpoints": {
            "playlist": "/playlist.m3u",
            "detaylar": "/detay.json"
        }
    }

@app.get("/playlist.m3u")
def get_playlist():
    base_url = get_base_url_with_fallback()
    referrer = get_referrer_with_fallback()
    
    all_matches = []
    all_channels = []
    
    try:
        r = requests.get(MATCHES_API_URL, headers=HEADERS, timeout=15, verify=False)
        all_matches = parse_matches_from_html(r.text)
    except Exception as e:
        print(f"⚠️ Maç hatası: {e}")
        
    try:
        r = requests.get(CHANNELS_API_URL, headers=HEADERS, timeout=15, verify=False)
        all_channels = parse_channels_from_html(r.text)
    except Exception as e:
        print(f"⚠️ Kanal hatası: {e}")
        
    m3u_list = create_m3u_with_logos(all_matches, all_channels, base_url, referrer)
    m3u_content = "\n".join(m3u_list)
    
    return Response(content=m3u_content, media_type="audio/x-mpegurl")

@app.get("/detay.json")
def get_details():
    all_matches = []
    all_channels = []
    
    try:
        r = requests.get(MATCHES_API_URL, headers=HEADERS, timeout=15, verify=False)
        all_matches = parse_matches_from_html(r.text)
    except Exception as e:
        pass
        
    try:
        r = requests.get(CHANNELS_API_URL, headers=HEADERS, timeout=15, verify=False)
        all_channels = parse_channels_from_html(r.text)
    except Exception as e:
        pass
        
    data = {
        'matches': all_matches,
        'channels': all_channels,
        'total_matches': len(all_matches),
        'total_channels': len(all_channels),
        'total_broadcasts': len(all_matches) + len(all_channels)
    }
    return data
