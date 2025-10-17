import requests
from bs4 import BeautifulSoup
import sys # Komut satırı argümanları için sys modülünü ekliyoruz

def get_stock_ratios(hisse_kodu):
    """
    İş Yatırım sitesinden belirtilen hisse için F/K ve PD/DD oranlarını çeker.
    Bu versiyon, sayfadaki ilgili tablo başlığını (th) bularak veriyi hedefler.
    """
    url = f"https://www.isyatirim.com.tr/tr-tr/analiz/hisse/Sayfalar/sirket-karti.aspx?hisse={hisse_kodu}"

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.8",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Cookie": "BehaviorPad_Profile=a0c3093e-09c3-4c5c-9592-cab735a99b9a; BIGipServer~P_ISYATIRIM~POOL-ISYATIRIM-HTTP=34031882.20480.0000; TS01e202c4=0157130bb9eddec1dbbe7bb1b6f687932fd21509bb680c9eb3c1d168b9e0e5f4c2f48ffd701c379166a28837c7de8b982b3bd147ca; ASP.NET_SessionId=bsntnudny2lnnqa050rwovxr; mi=-2; u=a; TS3bbf4f11027=08c4f7fb2cab20007e60c53fd889272586d7fe7350b7438df240f34187cc9e1eb5cd882496fc187508cfc21a58113000341ee1112ba3f8ae758098bd142e5bb8f8aeb412cec62017f604fe437786c2a45f9043bb6ef4cd282805c73a4f641ff5",
        "Referer": "https://www.google.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    }

    try:
        print(f"{hisse_kodu} için {url} adresinden veri çekiliyor...")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        print("HTML içeriği alındı, veriler parse ediliyor...")
        soup = BeautifulSoup(response.text, 'html.parser')

        fk_value = "N/A"
        pddd_value = "N/A"

        # Sayfadaki tüm 'th' etiketlerini bul
        all_th_tags = soup.find_all('th')

        for th_tag in all_th_tags:
            label = th_tag.text.strip()
            
            # Etiketi "F/K" olanı bul
            if label == 'F/K':
                # Yanındaki 'td' etiketini bul
                value_cell = th_tag.find_next_sibling('td')
                if value_cell:
                    fk_value = value_cell.text.strip()

            # Etiketi "PD/DD" olanı bul
            elif label == 'PD/DD':
                # Yanındaki 'td' etiketini bul
                value_cell = th_tag.find_next_sibling('td')
                if value_cell:
                    pddd_value = value_cell.text.strip()
            
            # İki değeri de bulduysak döngüden çıkabiliriz
            if fk_value != "N/A" and pddd_value != "N/A":
                break
        
        return {
            "F/K": fk_value,
            "PD/DD": pddd_value
        }

    except requests.exceptions.RequestException as e:
        print(f"Hata: Web sitesine ulaşılamadı. {e}")
        return None
    except Exception as e:
        print(f"Veri işlenirken bir hata oluştu: {e}")
        return None

if __name__ == "__main__":
    # Komut satırından argüman alınıp alınmadığını kontrol et
    if len(sys.argv) > 1:
        # İlk argümanı hisse kodu olarak al ve büyük harfe çevir
        hisse = sys.argv[1].upper()
    else:
        # Argüman yoksa kullanıcıyı bilgilendir ve çık
        print("Hata: Lütfen komut satırından bir hisse kodu girin.")
        print("Örnek kullanım: python hisse_veri_cek.py TCELL")
        sys.exit(1) # Script'i hata koduyla sonlandır

    ratios = get_stock_ratios(hisse)
    if ratios:
        print("-" * 30)
        print(f"{hisse} için finansal oranlar:")
        print(f"F/K: {ratios['F/K']}")
        print(f"PD/DD: {ratios['PD/DD']}")
        print("-" * 30)