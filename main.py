from fastapi import FastAPI, Response, HTTPException
import cloudscraper
import urllib3
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = FastAPI(title="Justin M3U Proxy Generator", version="16.0")

DOMAIN_API_URL = "https://data-reality.com/domain.php"
MATCHES_API_URL = "https://data-reality.com/matches.php"
AMP_INDEX_URL = "https://raw.githubusercontent.com/eniyiyayinci/taraftarium-amp/refs/heads/main/index.html"

# Sabit kanallar
STATIC_CHANNELS_HTML = """
<a class="single-match show " href="channel?id=zirve" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
<div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">BEIN SPORTS 1</div>
        <div class="away" style="text-align:right;"><img src="img/beinsports1.png" style="border-radius:0px !important; margin-top:-10px;" width="100" loading="lazy"></div>
    </div>
</div>
</a>
<a class="single-match show " href="channel?id=b2" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">BEIN SPORTS 2</div>
        <div class="away" style="text-align:right;"><img src="img/beinsports2.png" style="border-radius:0px !important; margin-top:-10px;" width="100" loading="lazy"></div>
    </div>
</div>
</a>
<a class="single-match show " href="channel?id=b3" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">BEIN SPORTS 3</div>
        <div class="away" style="text-align:right;"><img src="img/beinsports3.png" style="border-radius:0px !important; margin-top:-10px;" width="100" loading="lazy"></div>
    </div>
</div>
</a>
 <a class="single-match show " href="channel?id=b4" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">BEIN SPORTS 4</div>
        <div class="away" style="text-align:right;"><img src="img/beinsports4.png" style="border-radius:0px !important; margin-top:-10px;" width="100" loading="lazy"></div>
    </div>
</div>
</a>
<a class="single-match show " href="channel?id=b5" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">BEIN SPORTS 5</div>
        <div class="away" style="text-align:right;"><img src="img/beinsports5.png" style="border-radius:0px !important; margin-top:-10px;" width="100" loading="lazy"></div>
    </div>
</div>
</a>
<a class="single-match show " href="channel?id=bm1" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">BEIN SPORTS MAX 1</div>
        <div class="away" style="text-align:right;"><img src="img/beinsportsmax1.png" style="border-radius:0px !important; margin-top:-10px;" width="100" loading="lazy"></div>
    </div>
</div>
</a>
 <a class="single-match show " href="channel?id=bm2" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">BEIN SPORTS MAX 2</div>
        <div class="away" style="text-align:right;"><img src="img/beinsportsmax2.png" style="border-radius:0px !important; margin-top:-10px;" width="100" loading="lazy"></div>
    </div>
</div>
</a>
<a class="single-match show " href="channel?id=ss" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">S SPORT</div>
        <div class="away" style="text-align:right;"><img src="img/ssport1.png" style="border-radius:0px !important; margin-top:-10px;" width="100" loading="lazy"></div>
    </div>
</div>
</a>
 <a class="single-match show " href="channel?id=ss2" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">S SPORT 2</div>
        <div class="away" style="text-align:right;"><img src="img/ssport2.png" style="border-radius:0px !important; margin-top:-10px;" width="100" loading="lazy"></div>
    </div>
</div>
</a>
 <a class="single-match show " href="channel?id=smarts" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">SMART SPOR</div>
        <div class="away" style="text-align:right;"><img src="img/smartspor.png" style="border-radius:0px !important; margin-top:-10px;" width="100" loading="lazy"></div>
    </div>
</div>
</a>
 <a class="single-match show " href="channel?id=sms2" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">SMART SPOR 2</div>
        <div class="away" style="text-align:right;"><img src="img/smartspor2.png" style="border-radius:0px !important; margin-top:-10px;" width="100" loading="lazy"></div>
    </div>
</div>
</a>
 <a class="single-match show " href="channel?id=t1" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">TIVIBU SPOR 1</div>
        <div class="away" style="text-align:right;"><img src="img/tivibu1.png" style="border-radius:0px !important; margin-top:-10px;" width="100" loading="lazy"></div>
    </div>
</div>
</a>
 <a class="single-match show " href="channel?id=t2" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">TIVIBU SPOR 2</div>
        <div class="away" style="text-align:right;"><img src="img/tivibu2.png" style="border-radius:0px !important; margin-top:-10px;" width="100" loading="lazy"></div>
    </div>
</div>
</a>
<a class="single-match show " href="channel?id=t3" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">TIVIBU SPOR 3</div>
        <div class="away" style="text-align:right;"><img src="img/tivibu3.png" style="border-radius:0px !important; margin-top:-10px;" width="100" loading="lazy"></div>
    </div>
</div>
</a>
<a class="single-match show " href="channel?id=t4" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">TIVIBU SPOR 4</div>
        <div class="away" style="text-align:right;"><img src="img/tivibu4.png" style="border-radius:0px !important; margin-top:0px;" width="50" loading="lazy"></div>
    </div>
</div>
</a>
<a class="single-match show " href="channel?id=trtspor" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">TRT SPOR</div>
        <div class="away" style="text-align:right;"><img src="img/trtspornew.png" style="border-radius:0px !important; margin-top:-10px;" width="75" loading="lazy"></div>
    </div>
</div>
</a>
<a class="single-match show " href="channel?id=trtspor2" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">TRT SPOR YILDIZ</div>
        <div class="away" style="text-align:right;"><img src="img/trtspor2.png" style="border-radius:0px !important; margin-top:-10px;" width="75" loading="lazy"></div>
    </div>
</div>
</a>
<a class="single-match show " href="channel?id=trt1" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">TRT 1</div>
        <div class="away" style="text-align:right;"><img src="img/trt1.png" style="border-radius:0px !important; margin-top:0px;" width="75" loading="lazy"></div>
    </div>
</div>
</a>
<a class="single-match show " href="channel?id=as" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">A SPOR</div>
        <div class="away" style="text-align:right;"><img src="img/aspornew.png" style="border-radius:0px !important; margin-top:0px;" width="35" loading="lazy"></div>
    </div>
</div>
</a>
<a class="single-match show " href="channel?id=atv" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">ATV</div>
        <div class="away" style="text-align:right;"><img src="img/atv.png" style="border-radius:0px !important; margin-top:0px;" width="35" loading="lazy"></div>
    </div>
</div>
</a>
<a class="single-match show " href="channel?id=tv8" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">TV 8</div>
        <div class="away" style="text-align:right;"><img src="img/tv8.png" style="border-radius:0px !important; margin-top:0px;" width="35" loading="lazy"></div>
    </div>
</div>
</a>
<a class="single-match show " href="channel?id=tv85" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">TV 8,5</div>
        <div class="away" style="text-align:right;"><img src="img/tv85.png" style="border-radius:0px !important; margin-top:0px;" width="35" loading="lazy"></div>
    </div>
</div>
</a>
<a class="single-match show " href="channel?id=eu1" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">EURO SPORT 1</div>
        <div class="away" style="text-align:right;"><img src="img/eurosport1.png" style="border-radius:0px !important; margin-top:-10px;" width="100" loading="lazy"></div>
    </div>
</div>
</a>
<a class="single-match show " href="channel?id=eu2" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">EURO SPORT 2</div>
        <div class="away" style="text-align:right;"><img src="img/eurosport2.png" style="border-radius:0px !important; margin-top:-10px;" width="100" loading="lazy"></div>
    </div>
</div>
</a>
<a class="single-match show " href="channel?id=ex7" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">TABII SPOR</div>
        <div class="away" style="text-align:right;"><img src="img/tabii.png" style="border-radius:0px !important; margin-top:-10px;" width="100" loading="lazy"></div>
    </div>
</div>
</a>
 <a class="single-match show " href="channel?id=ex1" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">TABII SPOR 1</div>
        <div class="away" style="text-align:right;"><img src="img/tabii.png" style="border-radius:0px !important; margin-top:-10px;" width="100" loading="lazy"></div>
    </div>
</div>
</a>
 <a class="single-match show " href="channel?id=ex2" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">TABII SPOR 2</div>
        <div class="away" style="text-align:right;"><img src="img/tabii.png" style="border-radius:0px !important; margin-top:-10px;" width="100" loading="lazy"></div>
    </div>
</div>
</a>
 <a class="single-match show " href="channel?id=ex3" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">TABII SPOR 3</div>
        <div class="away" style="text-align:right;"><img src="img/tabii.png" style="border-radius:0px !important; margin-top:-10px;" width="100" loading="lazy"></div>
    </div>
</div>
</a>
 <a class="single-match show " href="channel?id=ex4" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">TABII SPOR 4</div>
        <div class="away" style="text-align:right;"><img src="img/tabii.png" style="border-radius:0px !important; margin-top:-10px;" width="100" loading="lazy"></div>
    </div>
</div>
</a>
 <a class="single-match show " href="channel?id=ex5" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">TABII SPOR 5</div>
        <div class="away" style="text-align:right;"><img src="img/tabii.png" style="border-radius:0px !important; margin-top:-10px;" width="100" loading="lazy"></div>
    </div>
</div>
</a>
 <a class="single-match show " href="channel?id=ex6" data-matchtype="Zirve" target="macth-video">
<img src="img/tv.png" style="border-radius:0px !important;" width="20" height="20" loading="lazy">
<div class="match-detail">
    <div class="event"><span class="lives">7/24</span></div>
    <div class="teams">
        <div class="home">TABII SPOR 6</div>
        <div class="away" style="text-align:right;"><img src="img/tabii.png" style="border-radius:0px !important; margin-top:-10px;" width="100" loading="lazy"></div>
    </div>
</div>
</a>
"""

def get_dynamic_player_base():
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
                    return player_base
    except Exception as e:
        print(f"⚠️ Player base çözme hatası: {e}")
    return player_base

def get_api_headers(player_base):
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
            return base_url + "/"
    except Exception as e:
        print(f"⚠️ Domain API hatası: {e}")
    return "https://5ln.zirvedesin244.cfd/"

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
    
    for link in match_links:
        try:
            href = link.get('href', '')
            channel_id = href.replace('channel?id=', '') if 'channel?id=' in href else None
            
            detail_div = link.find('div', class_='match-detail')
            if detail_div:
                teams_div = detail_div.find('div', class_='teams')
                if teams_div:
                    home_div = teams_div.find('div', class_='home')
                    channel_name = home_div.text.strip() if home_div else ''
                    
                    away_div = teams_div.find('div', class_='away')
                    logo_img = away_div.find('img') if away_div else None
                    logo_url = logo_img.get('src') if logo_img else ''
                    if logo_url and not logo_url.startswith('http'):
                        logo_url = f"https://data-reality.com/{logo_url}"
                    
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

# 🔥 PROXY ENDPOINT: ExoPlayer doğrudan buraya bağlanacak, sunucumuz arkada her şeyi çözecek!
@app.get("/proxy/{channel_id}/{file_name}")
def proxy_stream(channel_id: str, file_name: str, request: fastapi.Request = None):
    player_base = get_dynamic_player_base()
    stream_base_url = get_stream_base_url(player_base)
    target_url = f"{stream_base_url}{channel_id}/{file_name}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": player_base,
        "Origin": player_base.rstrip('/')
    }
    
    try:
        # Eğer istek .m3u8 dosyası ise içeriğini çekip içindeki linkleri de proxy üzerinden yönlendirelim
        if file_name.endswith('.m3u8'):
            resp = requests.get(target_url, headers=headers, timeout=10)
            content = resp.text
            # m3u8 içindeki segment (ts/m4s) linklerini de proxy'ye yönlendir
            base_proxy_url = f"{request.base_url}proxy/{channel_id}/"
            
            lines = content.splitlines()
            new_lines = []
            for line in lines:
                if line and not line.startswith('#'):
                    if not line.startswith('http'):
                        line = base_proxy_url + line
                    else:
                        # Eğer tam URL ise onu da proxy'den geçirebiliriz veya direkt bırakabiliriz
                        pass
                new_lines.append(line)
            
            return Response(content="\n".join(new_lines), media_type="application/vnd.apple.mpegurl")
        
        # Eğer parça dosyası (.ts, .m4s vb.) ise direkt stream olarak aktar
        req = requests.get(target_url, headers=headers, stream=True, timeout=10)
        return Response(content=req.content, status_code=req.status_code, media_type=req.headers.get("content-type"))
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/playlist.m3u")
def generate_m3u(request: fastapi.Request):
    scraper = cloudscraper.create_scraper()
    player_base = get_dynamic_player_base()
    
    all_matches = []
    all_channels = parse_channels_from_html(STATIC_CHANNELS_HTML)
    
    headers = get_api_headers(player_base)
    try:
        r = scraper.get(MATCHES_API_URL, headers=headers, timeout=15)
        all_matches = parse_matches_from_html(r.text)
    except Exception as e:
        print(f"⚠️ Maç hatası: {e}")
        
    m3u_list = ["#EXTM3U"]
    base_url = str(request.base_url).rstrip('/')
    
    for match in all_matches:
        group = f"CANLI MAÇLAR - {match['league']}"
        extinf = f'#EXTINF:-1 tvg-logo="{match["main_logo"]}" group-title="{group}",{match["name"]}'
        m3u_list.append(extinf)
        # ExoPlayer için tertemiz proxy linki (Hiçbir ek ayar gerektirmez)
        m3u_list.append(f'{base_url}/proxy/{match["id"]}/mono.m3u8')
        
    for channel in all_channels:
        extinf = f'#EXTINF:-1 tvg-logo="{channel["logo"]}" group-title="7/24 KANALLAR",{channel["name"]}'
        m3u_list.append(extinf)
        m3u_list.append(f'{base_url}/proxy/{channel["id"]}/mono.m3u8')
        
    return Response(content="\n".join(m3u_list), media_type="audio/x-mpegurl")
