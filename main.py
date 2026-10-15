from fastapi import FastAPI, Response
import cloudscraper
import urllib3
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = FastAPI(title="Justin M3U Generator", version="12.0")

# Orijinal API Kaynakları
DOMAIN_API_URL = "https://data-reality.com/domain.php"
MATCHES_API_URL = "https://data-reality.com/matches.php"
CHANNELS_API_URL = "https://data-reality.com/channels.php"

# Player base'i bulacağımız kaynak
AMP_INDEX_URL = "https://raw.githubusercontent.com/eniyiyayinci/taraftarium-amp/refs/heads/main/index.html"

def get_dynamic_player_base():
    """gettotv56.com gibi sürekli değişen player adresini otomatik bulur"""
    scraper = cloudscraper.create_scraper()
    player_base = "https://gettotv56.com/"
    
    try:
        r_idx = scraper.get(AMP_INDEX_URL, timeout=10)
        if r_idx.status_code == 200:
            found_urls = re.findall(r'https?://[^\s<>"]+gettotv[^\s<>"]*', r_idx.text)
            if found_urls:
                parsed = urlparse(found_urls[0])
                if parsed.netloc:
                    player_base = f"{parsed.scheme}://{parsed.netloc}/"
                    print(f"✅ Dinamik Player Base yakalandı: {player_base}")
                    return player_base
    except Exception as e:
        print(f"⚠️ Player base çözme hatası: {e}")
        
    return player_base

def get_api_headers(player_base):
    """Loglarda yakaladığımız gibi Origin ve Referer değerlerini dinamik player base'e ayarlar"""
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": player_base,
        "Origin": player_base.rstrip('/'),
        "Accept": "*/*",
        "Accept-Language": "tr,en;q=0.9",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "cors"
    }

def get_stream_base_url(player_base):
    scraper = cloudscraper.create_scraper()
    headers = get_api_headers(player_base)
    try:
        r = scraper.get(DOMAIN_API_URL, headers=headers, timeout=10)
        data = r.json()
        base_url = data.get("baseurl", "")
        if base_url:
            base_url = base_url.replace("\\", "").rstrip('/')
            print(f"✅ Domain API'den stream base alındı: {base_url}")
            return base_url + "/"
    except Exception as e:
        print(f"⚠️ Domain API hatası: {e}")
    return "https://5ln.zirvedesin244.cfd/"

def parse_matches_from_html(html_content):
    matches = []
    soup = BeautifulSoup(html_content, 'html.parser')
    match_links = soup.find_all('a', class_='single-match')
    print(f"🔍 Parse edilen maç linki sayısı: {len(match_links)}")
    
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
            match_type = date_div.text.strip() if date_div else 'futbol'
            
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
        except Exception:
            continue
    return matches

def parse_channels_from_html(html_content):
    channels = []
    soup = BeautifulSoup(html_content, 'html.parser')
    match_links = soup.find_all('a', class_='single-match')
    print(f"🔍 Parse edilen kanal linki sayısı: {len(match_links)}")
    
    for link in match_links:
        try:
            href = link.get('href', '')
            channel_id = href.replace('channel?id=', '') if 'channel?id=' in href else None
            
            detail_div = link.find('div', class_='match-detail')
            if detail_div:
                event_div = detail_div.find('div', class_='event')
                if event_div and ('7/24' in event_div.text or link.get('data-matchtype') == 'Zirve'):
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
        except Exception:
            continue
    return channels

@app.get("/")
def home():
    return {"status": "online", "endpoints": ["/playlist.m3u", "/detay.json"]}

@app.get("/playlist.m3u")
def generate_m3u():
    scraper = cloudscraper.create_scraper()
    player_base = get_dynamic_player_base()
    headers = get_api_headers(player_base)
    stream_base_url = get_stream_base_url(player_base)
    
    all_matches = []
    all_channels = []
    
    try:
        r = scraper.get(MATCHES_API_URL, headers=headers, timeout=15)
        print(f"📡 Matches API Status: {r.status_code}")
        all_matches = parse_matches_from_html(r.text)
    except Exception as e:
        print(f"⚠️ Maç hatası: {e}")
        
    try:
        r = scraper.get(CHANNELS_API_URL, headers=headers, timeout=15)
        print(f"📡 Channels API Status: {r.status_code}")
        all_channels = parse_channels_from_html(r.text)
    except Exception as e:
        print(f"⚠️ Kanal hatası: {e}")
        
    m3u_list = ["#EXTM3U"]
    
    for match in all_matches:
        group = f"CANLI MAÇLAR - {match['league']}"
        extinf = f'#EXTINF:-1 tvg-logo="{match["main_logo"]}" group-title="{group}",{match["name"]}'
        m3u_list.append(extinf)
        m3u_list.append(f'#EXTVLCOPT:http-user-agent={headers["User-Agent"]}')
        m3u_list.append(f'#EXTVLCOPT:http-referrer={player_base}')
        m3u_list.append(f'{stream_base_url}{match["id"]}/mono.m3u8')
        
    for channel in all_channels:
        extinf = f'#EXTINF:-1 tvg-logo="{channel["logo"]}" group-title="7/24 KANALLAR",{channel["name"]}'
        m3u_list.append(extinf)
        m3u_list.append(f'#EXTVLCOPT:http-user-agent={headers["User-Agent"]}')
        m3u_list.append(f'#EXTVLCOPT:http-referrer={player_base}')
        m3u_list.append(f'{stream_base_url}{channel["id"]}/mono.m3u8')
        
    return Response(content="\n".join(m3u_list), media_type="audio/x-mpegurl")

@app.get("/detay.json")
def generate_json():
    scraper = cloudscraper.create_scraper()
    player_base = get_dynamic_player_base()
    headers = get_api_headers(player_base)
    stream_base_url = get_stream_base_url(player_base)
    
    all_matches = []
    all_channels = []
    
    try:
        r = scraper.get(MATCHES_API_URL, headers=headers, timeout=15)
        all_matches = parse_matches_from_html(r.text)
    except Exception as e:
        print(f"⚠️ JSON Maç hatası: {e}")
        
    try:
        r = scraper.get(CHANNELS_API_URL, headers=headers, timeout=15)
        all_channels = parse_channels_from_html(r.text)
    except Exception as e:
        print(f"⚠️ JSON Kanal hatası: {e}")
        
    return {
        'player_base': player_base,
        'stream_base': stream_base_url,
        'matches': all_matches,
        'channels': all_channels,
        'total_matches': len(all_matches),
        'total_channels': len(all_channels),
        'total_broadcasts': len(all_matches) + len(all_channels)
    }
