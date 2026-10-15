from fastapi import FastAPI, Response
import requests
import urllib3
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = FastAPI(title="Justin M3U Generator", version="3.0")

# Güncel domain adresini bu GitHub yönlendirme dosyasından alıyoruz
REDIRECT_SOURCE_URL = "http://raw.githack.com/eniyiyayinci/redirect-cdn/main/inattv.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://canlimacizlejustin.online/"
}

def get_live_urls():
    """Yönlendirme adresinden güncel domain ve API yollarını dinamik olarak bulur"""
    base_url = "https://data-reality.com/"
    
    try:
        print("🔍 Güncel domain yönlendirme kaynağından sorgulanıyor...")
        r = requests.get(REDIRECT_SOURCE_URL, headers=HEADERS, timeout=10, verify=False)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # 1. Meta Refresh kontrolü
            meta_refresh = soup.find('meta', attrs={'http-equiv': 'refresh'})
            if meta_refresh and 'content' in meta_refresh.attrs:
                content = meta_refresh['content']
                if 'url=' in content.lower():
                    url_part = content.split('url=')[-1].strip('"\'')
                    parsed = urlparse(url_part)
                    if parsed.netloc:
                        base_url = f"{parsed.scheme}://{parsed.netloc}/"
                        print(f"✅ Meta Refresh ile bulunan domain: {base_url}")
                        return base_url

            # 2. Script içerisindeki yönlendirmeleri regex ile ara
            for script in soup.find_all('script'):
                if script.string:
                    urls = re.findall(r'https?://[^\s<>"]+', script.string)
                    for u in urls:
                        if 'data-reality' not in u and 'githack' not in u:
                            parsed = urlparse(u)
                            if parsed.netloc:
                                base_url = f"{parsed.scheme}://{parsed.netloc}/"
                                print(f"✅ Script içinden bulunan domain: {base_url}")
                                return base_url
                                
            # 3. Sayfadaki herhangi bir linki kontrol et
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('http'):
                    parsed = urlparse(href)
                    if parsed.netloc and 'githack' not in parsed.netloc:
                        base_url = f"{parsed.scheme}://{parsed.netloc}/"
                        print(f"✅ Link üzerinden bulunan domain: {base_url}")
                        return base_url
                        
    except Exception as e:
        print(f"⚠️ Domain çözümleme hatası: {e}")
        
    return base_url

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
    base_url = get_live_urls()
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
    base_url = get_live_urls()
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
