from fastapi import FastAPI, Response
import requests
import urllib3
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = FastAPI(title="Justin M3U Generator", version="5.0")

SITEMAP_URL = "https://raw.githubusercontent.com/eniyiyayinci/taraftarium-amp/refs/heads/main/sitemap.xml"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://canlimacizlejustin.online/"
}

def get_dynamic_base_url():
    """Sitemap'ten ana adresi alır, oradan da sürekli değişen gerçek yayın domainine (xyz vb.) ulaşırsınız"""
    fallback_url = "https://taraftarium24.io/"
    
    try:
        # 1. Adım: Sitemap'ten ana domaini bul
        print("🔍 Sitemap okunuyor...")
        r = requests.get(SITEMAP_URL, headers=HEADERS, timeout=10, verify=False)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'xml')
            loc_tag = soup.find('loc')
            if loc_tag and loc_tag.text:
                fallback_url = loc_tag.text.strip()
        
        print(f"📡 Ana giriş adresi: {fallback_url}")

        # 2. Adım: Ana adrese istek atıp gerçek yönlendirildiği (xyz vb.) domaini yakala
        print("🔍 Güncel yayın domaini çözümleniyor...")
        r_main = requests.get(fallback_url, headers=HEADERS, timeout=10, verify=False, allow_redirects=True)
        
        # Gerçek son yönlendirildiği URL (Örn: https://taraftarium1086.xyz/)
        final_url = r_main.url
        parsed_final = urlparse(final_url)
        if parsed_final.netloc:
            base_url = f"{parsed_final.scheme}://{parsed_final.netloc}/"
            print(f"✅ Yakalanan güncel yayın domaini: {base_url}")
            return base_url

        # Eğer redirect yakalanamazsa sayfadaki script veya linklerden regex ile bulmaya çalış
        soup_main = BeautifulSoup(r_main.text, 'html.parser')
        for script in soup_main.find_all('script'):
            if script.string:
                urls = re.findall(r'https?://[^\s<>"]+', script.string)
                for u in urls:
                    if 'taraftarium' in u or '.xyz' in u or '.com' in u:
                        parsed_u = urlparse(u)
                        if parsed_u.netloc:
                            base_url = f"{parsed_u.scheme}://{parsed_u.netloc}/"
                            print(f"✅ Script içinden bulunan yayın domaini: {base_url}")
                            return base_url

    except Exception as e:
        print(f"⚠️ Domain çözümleme hatası: {e}")
        
    return fallback_url

def parse_matches_from_html(html_content):
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
        except Exception:
            continue
    return matches

def parse_channels_from_html(html_content):
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
        except Exception:
            continue
    return channels

@app.get("/")
def home():
    return {"status": "online", "endpoints": ["/playlist.m3u", "/detay.json"]}

@app.get("/playlist.m3u")
def generate_m3u():
    base_url = get_dynamic_base_url()
    matches_url = urljoin(base_url, "matches.php")
    channels_url = urljoin(base_url, "channels.php")
    
    all_matches = []
    all_channels = []
    
    try:
        r = requests.get(matches_url, headers=HEADERS, timeout=15, verify=False)
        all_matches = parse_matches_from_html(r.text)
    except Exception as e:
        print(f"⚠️ Maç hatası: {e}")
        
    try:
        r = requests.get(channels_url, headers=HEADERS, timeout=15, verify=False)
        all_channels = parse_channels_from_html(r.text)
    except Exception as e:
        print(f"⚠️ Kanal hatası: {e}")
        
    m3u_list = ["#EXTM3U"]
    
    for match in all_matches:
        group = f"CANLI MAÇLAR - {match['league']}"
        extinf = f'#EXTINF:-1 tvg-logo="{match["main_logo"]}" group-title="{group}",{match["name"]}'
        m3u_list.append(extinf)
        m3u_list.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
        m3u_list.append(f'#EXTVLCOPT:http-referrer={base_url}')
        m3u_list.append(f'{base_url}{match["id"]}/mono.m3u8')
        
    for channel in all_channels:
        extinf = f'#EXTINF:-1 tvg-logo="{channel["logo"]}" group-title="7/24 KANALLAR",{channel["name"]}'
        m3u_list.append(extinf)
        m3u_list.append(f'#EXTVLCOPT:http-user-agent={HEADERS["User-Agent"]}')
        m3u_list.append(f'#EXTVLCOPT:http-referrer={base_url}')
        m3u_list.append(f'{base_url}{channel["id"]}/mono.m3u8')
        
    return Response(content="\n".join(m3u_list), media_type="audio/x-mpegurl")

@app.get("/detay.json")
def generate_json():
    base_url = get_dynamic_base_url()
    matches_url = urljoin(base_url, "matches.php")
    channels_url = urljoin(base_url, "channels.php")
    
    all_matches = []
    all_channels = []
    
    try:
        r = requests.get(matches_url, headers=HEADERS, timeout=15, verify=False)
        all_matches = parse_matches_from_html(r.text)
    except Exception:
        pass
        
    try:
        r = requests.get(channels_url, headers=HEADERS, timeout=15, verify=False)
        all_channels = parse_channels_from_html(r.text)
    except Exception:
        pass
        
    return {
        'matches': all_matches,
        'channels': all_channels,
        'total_matches': len(all_matches),
        'total_channels': len(all_channels),
        'total_broadcasts': len(all_matches) + len(all_channels)
    }
