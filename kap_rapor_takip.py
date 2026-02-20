import requests
import time
import json
from datetime import datetime
import platform
import os

if platform.system() == "Windows":
    import winsound  # Ses çalmak için eklendi

# curl komutundan alınan cookie bilgileri.
# DİKKAT: Bu çerezlerin bir son kullanma tarihi vardır.
# Betik çalışmazsa, tarayıcıdan yeni bir curl komutu alıp bu alanı güncellemeniz gerekebilir.
cookies = {
    'client-ip': '31.223.74.22',
    'NSC_xxx.lbq.psh.us_tjuf_zfoj': '7ce2a3d9ddad9f0439920efb260b36acad4a64f3df2ef79bda6c88b7f8de60bb9ae4e5ca',
    'AGVY-Cookie': 'MDMAAAcAo_SrGgAAAAAf30oWX6_3aAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEpz2EYfmr9W3cPP1WZGdsyXke45X6_3aAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAANtNMYEvn0lq_XvHjtRANVkS1xD8',
    'KAP': 'AAY7q6f3aDtFNoYDAAAAADsUL9ZOBg_0wi2-O57XgFXK6nyr3tUnRWQn_px49Y17Ow==i7D3aA==nPDM9SKNMaRZr2AVhL81PjYg3xU=',
}

# curl komutundan alınan header bilgileri
headers = {
    'Accept': '*/*',
    'Accept-Language': 'tr',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'Origin': 'https://www.kap.org.tr',
    'Referer': 'https://www.kap.org.tr/tr',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-GPC': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Brave";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

# Daha önce ekrana yazdırılan raporların ID'lerini saklamak için bir set
seen_disclosure_ids = set()
# Aynı gün içinde aynı hisse için tekrar bildirim yapmamak için set
seen_stock_day_reports = set()

def get_financial_reports():
    """
    KAP API'sine istek atarak güncel finansal raporları çeker.
    """
    today_str = datetime.now().strftime('%d.%m.%Y')
    
    payload = {
        "fromDate": today_str,
        "toDate": today_str,
        "disclosureTypes": ["FR"],
        "fundTypes": [],
        "memberTypes": ["IGS", "DDK"],
        "mkkMemberOid": None
    }
    
    try:
        response = requests.post(
            'https://www.kap.org.tr/tr/api/disclosure/list/main',
            cookies=cookies,
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"\nAPI isteği sırasında bir hata oluştu: {e}")
        return None

def check_for_new_reports():
    """
    Yeni faaliyet raporu olup olmadığını kontrol eder ve varsa ekrana yazdırır.
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Yeni faaliyet raporları için KAP kontrol ediliyor...")
    disclosures = get_financial_reports()

    if disclosures is None:
        return

    new_reports_found_this_run = False

    for report in reversed(disclosures):
        basic_info = report['disclosureBasic']
        disclosure_id = basic_info['disclosureId']
        title = basic_info['title']
        stock_code = basic_info['stockCode']
        publish_date_only = basic_info['publishDate'].split(' ')[0] # Sadece tarih kısmını al
        
        # Aynı disclosure_id'ye sahip raporu ve aynı hisse senedi için aynı gün içindeki raporu tekrar yazdırma
        if disclosure_id not in seen_disclosure_ids and \
           (stock_code, publish_date_only) not in seen_stock_day_reports and \
           ("Faaliyet Raporu" in title or "Finansal Rapor" in title):
            
            if not new_reports_found_this_run:
                print("-"*50)
            
            print(f"🔔 YENİ RAPOR: {stock_code} - {basic_info['companyTitle']} ({basic_info['publishDate']})")
            
            new_reports_found_this_run = True
            seen_disclosure_ids.add(disclosure_id)
            seen_stock_day_reports.add((stock_code, publish_date_only))
            
    if new_reports_found_this_run:
        print("-"*50)
        # Yeni rapor(lar) bulunduğu için bir kez sesli bildirim ver
        if platform.system() == "Windows":
            winsound.Beep(600, 200)  # Frekans: 600Hz, Süre: 200ms
            time.sleep(0.05) # Notalar arası kısa bir duraklama
            winsound.Beep(800, 250)  # Frekans: 800Hz, Süre: 250ms
        elif platform.system() == "Darwin":
            os.system('afplay /System/Library/Sounds/Glass.aiff')
        else:
            print('\a')
    else:
        print("Yeni bir rapor bulunamadı.")

def main():
    """
    Ana döngü. Betiği başlatır ve periyodik olarak kontrol eder.
    """
    print("KAP Faaliyet Raporu Takip Betiği Başlatıldı.")
    check_interval_seconds = 180  # 5 dakika

    while True:
        check_for_new_reports()
        print(f"\nSonraki kontrol {check_interval_seconds} saniye sonra... (Çıkmak için Ctrl+C)")
        time.sleep(check_interval_seconds)

if __name__ == "__main__":
    main()
