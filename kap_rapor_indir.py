import requests
import os
import sys
import io
from datetime import datetime
import argparse
from bs4 import BeautifulSoup
from enum import Enum

# On Windows, printing to the console can fail if the output contains special characters.
# To prevent a 'charmap' codec can't encode character' error, we force stdout to use UTF-8.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class FundAssetGroup(Enum):
    EUROBOND = "Eurobond"
    HISSE_SENEDI = "Hisse Senedi"
    ALTIN = "Altın"
    BORCLANMA_ARACLARI = "Borçlanma Araçları"
    PARA_PIYASASI = "Para Piyasası"

    def __str__(self):
        return self.value


# HTTP istekleri için başlık bilgisi (Header)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def get_fund_management_fee(fund_code):
    """
    Verilen fon koduna göre KAP'tan fon yönetim ücretini çeker.
    """
    fund_code = fund_code.upper()
    print(f"\n'{fund_code}' için fon yönetim ücreti bilgisi alınıyor... 펀")

    # --- Adım 1: Fon Kodu ile memberOrFundOid'yi al ---
    search_url = "https://www.kap.org.tr/tr/api/search/combined"
    search_payload = {
        "keyword": fund_code,
        "discClass": "ALL",
        "lang": "tr",
        "channel": "WEB"
    }
    try:
        response = requests.post(search_url, json=search_payload, headers=HEADERS)
        response.raise_for_status()
        search_data = response.json()
        fund_info = next((item for item in search_data if item['category'] == 'companyOrFunds'), None)
        if not fund_info or not fund_info['results']:
            print(f"HATA: '{fund_code}' kodu ile eşleşen bir fon bulunamadı. ❌")
            return
        
        result = fund_info['results'][0]
        if result.get('searchType') != 'F':
            print(f"HATA: '{fund_code}' bir fon kodu değil, şirket kodu olabilir. ❌")
            return
            
        member_oid = result['memberOrFundOid']
        print(f"Fon OID'si bulundu: {member_oid}")

    except requests.exceptions.RequestException as e:
        print(f"HATA: Fon aranırken bir ağ hatası oluştu: {e} ❌")
        return

    # --- Adım 2: Fonun genel bilgi sayfasını al ---
    fund_page_url = f"https://www.kap.org.tr/tr/fon-bilgileri/genel/{member_oid}"
    try:
        response = requests.get(fund_page_url, headers=HEADERS)
        response.raise_for_status()
        html_content = response.text
        print("Fonun genel bilgi sayfası başarıyla alındı.")
    except requests.exceptions.RequestException as e:
        print(f"HATA: Fon sayfası alınırken bir ağ hatası oluştu: {e} ❌")
        return

    # --- Adım 3: HTML'i ayrıştır ve yönetim ücretini bul ---
    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # "KOMİSYON VE GİDER BİLGİLERİ" başlığını içeren bölümü bul
        commission_title = soup.find('span', class_='company__sgbf-accordion-title',
                                     string=lambda t: t and 'KOMİSYON VE GİDER BİLGİLERİ' in t)

        if not commission_title:
            print("HATA: HTML içinde 'KOMİSYON VE GİDER BİLGİLERİ' bölümü bulunamadı. ❌")
            return

        # İlgili accordion'un içeriğini bul
        accordion_content = commission_title.find_parent('button').find_next_sibling('div')

        if not accordion_content:
            print("HATA: Komisyon bölümünün içeriği bulunamadı. ❌")
            return

        # "Yönetim Ücreti Oranı (Yıllık) (%)" başlığını tam eşleşme ile ara
        fee_header_text = 'Yönetim Ücreti Oranı (Yıllık) (%)'
        
        all_headers = accordion_content.find_all('th')
        target_header = None
        for header in all_headers:
            if header.get_text(strip=True) == fee_header_text:
                target_header = header
                break
        
        if not target_header:
            print(f"HATA: '{fee_header_text}' başlığı komisyon tablosunda bulunamadı. ❌")
            return

        # Başlığın sütun indeksini al
        headers_in_row = target_header.find_parent('tr').find_all('th')
        fee_index = headers_in_row.index(target_header)
        
        # Tablo gövdesinde aynı indeksteki değeri bul
        table_body = target_header.find_parent('table').find('tbody')
        first_row_cells = table_body.find('tr').find_all('td')

        if len(first_row_cells) <= fee_index:
            print("HATA: Yönetim ücreti değeri sütunu bulunamadı. ❌")
            return

        fee_value = first_row_cells[fee_index].get_text(strip=True)
        
        if not fee_value:
            print(f"HATA: '{fund_code}' için yönetim ücreti değeri boş. ❌")
            return

        print("\n--- Bilgiler ---")
        print(f"Fon Kodu: {fund_code}")
        print(f"Fon Yönetim Ücreti Oranı (Yıllık) (%): {fee_value}")
        print("----------------\n")

    except Exception as e:
        print(f"HATA: HTML ayrıştırılırken bir hata oluştu: {e} ❌")


def get_latest_financial_report(ticker_symbol):
    """
    Verilen borsa koduna göre KAP'tan en güncel Finansal Raporu indirir
    ve 'faaliyet-raporu/YYYYQQ' formatındaki klasöre kaydeder.
    Klasör adı genel olduğu için değiştirilmedi, istenirse değiştirilebilir.
    """
    ticker_symbol = ticker_symbol.upper()
    print(f"\n'{ticker_symbol}' için işlem başlatıldı... 📈")

    # --- Adım 1: Şirket Kodu ile memberOrFundOid'yi al ---
    search_url = "https://www.kap.org.tr/tr/api/search/combined"
    search_payload = {
        "keyword": ticker_symbol,
        "discClass": "ALL",
        "lang": "tr",
        "channel": "WEB"
    }
    try:
        response = requests.post(search_url, json=search_payload, headers=HEADERS)
        response.raise_for_status()
        search_data = response.json()
        company_info = next((item for item in search_data if item['category'] == 'companyOrFunds'), None)
        if not company_info or not company_info['results']:
            print(f"HATA: '{ticker_symbol}' kodu ile eşleşen bir şirket bulunamadı. ❌")
            return
        member_oid = company_info['results'][0]['memberOrFundOid']
        print(f"Şirket OID'si bulundu: {member_oid}")
    except requests.exceptions.RequestException as e:
        print(f"HATA: Şirket aranırken bir ağ hatası oluştu: {e} ❌")
        return

    # --- Adım 2: Raporları al, "Finansal Rapor" içerenleri filtrele ve en günceli bul ---
    disclosures_url = f"https://www.kap.org.tr/tr/api/company-detail/sgbf-data/{member_oid}/FR/365"
    try:
        response = requests.get(disclosures_url, headers=HEADERS)
        response.raise_for_status()
        disclosures_data = response.json()
        
        financial_reports = []
        for report in disclosures_data:
            title = report.get('disclosureBasic', {}).get('title', '').lower()
            if 'finansal rapor' in title and report.get('disclosureBasic', {}).get('donem'):
                financial_reports.append(report)
        
        if not financial_reports:
            print(f"HATA: '{ticker_symbol}' için son 1 yılda dönemsel bir finansal rapor bulunamadı. ❌")
            return

        financial_reports.sort(
            key=lambda r: datetime.strptime(r['disclosureBasic']['publishDate'], '%d.%m.%Y %H:%M:%S'),
            reverse=True
        )

        latest_report = financial_reports[0]
        disclosure_basic_info = latest_report['disclosureBasic']
        disclosure_index = disclosure_basic_info['disclosureIndex']
        report_date = disclosure_basic_info['publishDate']
        report_year = disclosure_basic_info['year']
        report_quarter_num = disclosure_basic_info['donem']
        
        print(f"En güncel finansal rapor bulundu (Yayınlanma: {report_date})")
        print(f"Raporun Ait Olduğu Dönem: {report_year} - {report_quarter_num}. Çeyrek")
        
    except requests.exceptions.RequestException as e:
        print(f"HATA: Finansal raporlar listesi çekilirken bir hata oluştu: {e} ❌")
        return
        
    # --- Adım 3: Raporun eklerinden Türkçe PDF'in objId'sini al ---
    attachment_url = f"https://www.kap.org.tr/tr/api/notification/attachment-detail/{disclosure_index}"
    try:
        response = requests.get(attachment_url, headers=HEADERS)
        response.raise_for_status()
        attachment_data = response.json()
        pdf_attachment = None
        for attachment in attachment_data[0]['attachments']:
             if attachment['fileExtension'].lower() == 'pdf':
                pdf_attachment = attachment
                break
        if not pdf_attachment:
            print(f"HATA: Rapora ait bir PDF eki bulunamadı. ❌")
            return
        obj_id = pdf_attachment['objId']
        file_name = pdf_attachment['fileName']
        print(f"İndirilecek PDF eki bulundu: '{file_name}' (ObjectID: {obj_id})")
    except requests.exceptions.RequestException as e:
        print(f"HATA: Rapor ekleri alınırken bir hata oluştu: {e} ❌")
        return

    # --- Adım 4: PDF dosyasını indir ---
    download_url = f"https://www.kap.org.tr/tr/api/file/download/{obj_id}"
    try:
        print("Dosya indiriliyor, lütfen bekleyin... 📥")
        pdf_response = requests.get(download_url, headers=HEADERS, stream=True)
        pdf_response.raise_for_status()

        base_directory = "finansal-raporlar"
        
        quarter_map = {1: '03', 2: '06', 3: '09', 4: '12'}
        quarter_dir_suffix = quarter_map.get(report_quarter_num, '00')
        
        period_directory = f"{report_year}{quarter_dir_suffix}"
        
        output_directory = os.path.join(base_directory, period_directory)

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
            print(f"'{output_directory}' klasör yapısı oluşturuldu.")

        output_filename = f"{ticker_symbol}_Finansal_Rapor_{report_date.split(' ')[0].replace('.', '-')}.pdf"
        full_path = os.path.join(output_directory, output_filename)

        with open(full_path, 'wb') as f:
            for chunk in pdf_response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"\nBaşarılı! ✅\nFinansal rapor '{os.path.abspath(full_path)}' adresine kaydedildi.")

    except requests.exceptions.RequestException as e:
        print(f"HATA: PDF dosyası indirilirken bir hata oluştu: {e} ❌")
    except OSError as e:
        print(f"HATA: Dosya kaydedilirken bir sistem hatası oluştu: {e} ❌")


def get_latest_activity_report(ticker_symbol):
    """
    Verilen borsa koduna göre KAP'tan en güncel Faaliyet Raporunu (Konsolide) indirir
    ve 'faaliyet-raporlari/YYYYQQ' formatındaki klasöre kaydeder.
    """
    ticker_symbol = ticker_symbol.upper()
    print(f"\n'{ticker_symbol}' için Faaliyet Raporu (Konsolide) işlemi başlatıldı... 📑")

    # --- Adım 1: Şirket Kodu ile memberOrFundOid'yi al ---
    search_url = "https://www.kap.org.tr/tr/api/search/combined"
    search_payload = {
        "keyword": ticker_symbol,
        "discClass": "ALL",
        "lang": "tr",
        "channel": "WEB"
    }
    try:
        response = requests.post(search_url, json=search_payload, headers=HEADERS)
        response.raise_for_status()
        search_data = response.json()
        company_info = next((item for item in search_data if item['category'] == 'companyOrFunds'), None)
        if not company_info or not company_info['results']:
            print(f"HATA: '{ticker_symbol}' kodu ile eşleşen bir şirket bulunamadı. ❌")
            return
        member_oid = company_info['results'][0]['memberOrFundOid']
        print(f"Şirket OID'si bulundu: {member_oid}")
    except requests.exceptions.RequestException as e:
        print(f"HATA: Şirket aranırken bir ağ hatası oluştu: {e} ❌")
        return

    # --- Adım 2: Raporları al, "Faaliyet Raporu (Konsolide)" içerenleri filtrele ve en günceli bul ---
    disclosures_url = f"https://www.kap.org.tr/tr/api/company-detail/sgbf-data/{member_oid}/FR/365"
    try:
        response = requests.get(disclosures_url, headers=HEADERS)
        response.raise_for_status()
        disclosures_data = response.json()
        
        activity_reports = []
        for report in disclosures_data:
            title = report.get('disclosureBasic', {}).get('title', '').lower()
            # Hem 'faaliyet raporu' hem de 'konsolide' içermeli ve dönemsel olmalı
            if 'faaliyet raporu' in title and 'konsolide' in title and report.get('disclosureBasic', {}).get('donem'):
                activity_reports.append(report)
        
        if not activity_reports:
            # Konsolide bulunamazsa, sadece faaliyet raporu ara
            activity_reports = []
            for report in disclosures_data:
                title = report.get('disclosureBasic', {}).get('title', '').lower()
                if 'faaliyet raporu' in title and report.get('disclosureBasic', {}).get('donem'):
                    activity_reports.append(report)
            
            if not activity_reports:
                print(f"HATA: '{ticker_symbol}' için son 1 yılda dönemsel bir faaliyet raporu bulunamadı. ❌")
                return
            else:
                print("Bilgi: Konsolide faaliyet raporu bulunamadı, konsolide olmayan rapor indirilecek.")


        activity_reports.sort(
            key=lambda r: datetime.strptime(r['disclosureBasic']['publishDate'], '%d.%m.%Y %H:%M:%S'),
            reverse=True
        )

        latest_report = activity_reports[0]
        disclosure_basic_info = latest_report['disclosureBasic']
        disclosure_index = disclosure_basic_info['disclosureIndex']
        report_date = disclosure_basic_info['publishDate']
        report_year = disclosure_basic_info['year']
        report_quarter_num = disclosure_basic_info['donem']
        
        print(f"En güncel faaliyet raporu bulundu (Yayınlanma: {report_date})")
        print(f"Raporun Ait Olduğu Dönem: {report_year} - {report_quarter_num}. Çeyrek")
        
    except requests.exceptions.RequestException as e:
        print(f"HATA: Faaliyet raporları listesi çekilirken bir hata oluştu: {e} ❌")
        return
        
    # --- Adım 3: Raporun eklerinden Türkçe PDF'in objId'sini al ---
    attachment_url = f"https://www.kap.org.tr/tr/api/notification/attachment-detail/{disclosure_index}"
    try:
        response = requests.get(attachment_url, headers=HEADERS)
        response.raise_for_status()
        attachment_data = response.json()
        pdf_attachment = None
        for attachment in attachment_data[0]['attachments']:
             if attachment['fileExtension'].lower() == 'pdf':
                pdf_attachment = attachment
                break
        if not pdf_attachment:
            print(f"HATA: Rapora ait bir PDF eki bulunamadı. ❌")
            return
        obj_id = pdf_attachment['objId']
        file_name = pdf_attachment['fileName']
        print(f"İndirilecek PDF eki bulundu: '{file_name}' (ObjectID: {obj_id})")
    except requests.exceptions.RequestException as e:
        print(f"HATA: Rapor ekleri alınırken bir hata oluştu: {e} ❌")
        return

    # --- Adım 4: PDF dosyasını indir ---
    download_url = f"https://www.kap.org.tr/tr/api/file/download/{obj_id}"
    try:
        print("Dosya indiriliyor, lütfen bekleyin... 📥")
        pdf_response = requests.get(download_url, headers=HEADERS, stream=True)
        pdf_response.raise_for_status()

        base_directory = "faaliyet-raporlari"
        
        quarter_map = {1: '03', 2: '06', 3: '09', 4: '12'}
        quarter_dir_suffix = quarter_map.get(report_quarter_num, '00')
        
        period_directory = f"{report_year}{quarter_dir_suffix}"
        
        output_directory = os.path.join(base_directory, period_directory)

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
            print(f"'{output_directory}' klasör yapısı oluşturuldu.")

        output_filename = f"{ticker_symbol}_Faaliyet_Raporu_{report_date.split(' ')[0].replace('.', '-')}.pdf"
        full_path = os.path.join(output_directory, output_filename)

        with open(full_path, 'wb') as f:
            for chunk in pdf_response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"\nBaşarılı! ✅\nFaaliyet raporu '{os.path.abspath(full_path)}' adresine kaydedildi.")

    except requests.exceptions.RequestException as e:
        print(f"HATA: PDF dosyası indirilirken bir hata oluştu: {e} ❌")
    except OSError as e:
        print(f"HATA: Dosya kaydedilirken bir sistem hatası oluştu: {e} ❌")


def get_funds_by_asset_group(asset_group: FundAssetGroup):
    """
    Verilen bir varlık grubuna ait fonları ve getirilerini TEFAS'tan çeker.
    """
    print(f"\n'{asset_group.value}' varlık grubuna ait fonlar ve getirileri TEFAS'tan alınıyor...")

    tefas_url = "https://www.tefas.gov.tr/api/DB/BindComparisonFundReturns"
    
    # Tarayıcıdan alınan header'ları taklit et
    tefas_headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://www.tefas.gov.tr",
        "Referer": "https://www.tefas.gov.tr/FonKarsilastirma.aspx",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }

    # curl komutundan alınan form verileri
    form_data = {
        "calismatipi": "2",
        "fontip": "YAT",
        "sfontur": "",
        "kurucukod": "",
        "fongrup": "",
        "bastarih": "Başlangıç",
        "bittarih": "Bitiş",
        "fonturkod": "",
        "fonunvantip": asset_group.value,
        "strperiod": "1,1,1,1,1,1,1",
        "islemdurum": "1",
    }

    try:
        response = requests.post(tefas_url, headers=tefas_headers, data=form_data)
        response.raise_for_status()
        funds_data = response.json()

        if not funds_data.get('data'):
            print("Bu varlık grubu için fon bulunamadı veya bir hata oluştu.")
            return

        print("\n--- Fon Listesi ve Getirileri ---")
        for fund in funds_data['data']:
            print(f"- {fund['FONKODU']}: {fund['FONUNVAN']}")
            getiri_1a = fund.get('GETIRI1A') or 0.0
            getiri_6a = fund.get('GETIRI6A') or 0.0
            getiri_1y = fund.get('GETIRI1Y') or 0.0
            getiri_3y = fund.get('GETIRI3Y') or 0.0
            print(f"    Getiriler -> 1A: %{getiri_1a:.2f} | 6A: %{getiri_6a:.2f} | 1Y: %{getiri_1y:.2f} | 3Y: %{getiri_3y:.2f}")
        print("-----------------------------------\n")

    except requests.exceptions.RequestException as e:
        print(f"HATA: TEFAS API'sine istek gönderilirken bir ağ hatası oluştu: {e} ❌")
    except ValueError: # JSON decode hatalarını yakala
        print(f"HATA: TEFAS API'sinden gelen yanıt JSON formatında değil. Yanıt: {response.text} ❌")


def download_fund_portfolio_report(fund_code):
    """
    Verilen fon koduna göre KAP'tan en güncel Portföy Dağılım Raporunu indirir
    ve 'fon-raporlari/YYYY-AA' formatındaki klasöre kaydeder.
    """
    fund_code = fund_code.upper()
    print(f"\n'{fund_code}' için Portföy Dağılım Raporu indirme işlemi başlatıldı... 펀")

    # --- Adım 1: Fon Kodu ile memberOrFundOid'yi al ---
    search_url = "https://www.kap.org.tr/tr/api/search/combined"
    search_payload = {
        "keyword": fund_code,
        "discClass": "ALL",
        "lang": "tr",
        "channel": "WEB"
    }
    try:
        response = requests.post(search_url, json=search_payload, headers=HEADERS)
        response.raise_for_status()
        search_data = response.json()
        fund_info = next((item for item in search_data if item['category'] == 'companyOrFunds'), None)
        if not fund_info or not fund_info['results']:
            print(f"HATA: '{fund_code}' kodu ile eşleşen bir fon bulunamadı. ❌")
            return
        
        result = fund_info['results'][0]
        if result.get('searchType') != 'F':
            print(f"HATA: '{fund_code}' bir fon kodu değil, şirket kodu olabilir. ❌")
            return
            
        member_oid = result['memberOrFundOid']
        print(f"Fon OID'si bulundu: {member_oid}")

    except requests.exceptions.RequestException as e:
        print(f"HATA: Fon aranırken bir ağ hatası oluştu: {e} ❌")
        return

    # --- Adım 2: Portföy Dağılım Raporlarını al ve en günceli bul ---
    # Bu OID, "Portföy Dağılım Raporu" bildirim türü için statik bir ID'dir.
    report_type_oid = "8aca490d502e34b801502e380044002b"
    disclosures_url = f"https://www.kap.org.tr/tr/api/disclosure/filter/FILTERYFBF/{member_oid}/{report_type_oid}/365"
    
    try:
        response = requests.get(disclosures_url, headers=HEADERS)
        response.raise_for_status()
        portfolio_reports = response.json()
        
        if not portfolio_reports:
            print(f"HATA: '{fund_code}' için son 1 yılda 'Portföy Dağılım Raporu' bulunamadı. ❌")
            return

        # API zaten tarihe göre sıralı geliyor gibi ama garantiye alalım.
        portfolio_reports.sort(
            key=lambda r: datetime.strptime(r['disclosureBasic']['publishDate'], '%d.%m.%Y %H:%M:%S'),
            reverse=True
        )

        latest_report = portfolio_reports[0]
        disclosure_basic_info = latest_report['disclosureBasic']
        disclosure_index = disclosure_basic_info['disclosureIndex']
        report_date_str = disclosure_basic_info['publishDate'] # '07.10.2025 20:20:21'
        report_date_obj = datetime.strptime(report_date_str, '%d.%m.%Y %H:%M:%S')
        
        print(f"En güncel portföy dağılım raporu bulundu (Yayınlanma: {report_date_str})")
        
    except requests.exceptions.RequestException as e:
        print(f"HATA: Raporlar listesi çekilirken bir hata oluştu: {e} ❌")
        return
    except ValueError: # JSON decode hatası
        print(f"HATA: KAP API'sinden gelen yanıt JSON formatında değil. Yanıt: {response.text} ❌")
        return
        
    # --- Adım 3: Raporun eklerinden PDF/XLSX'in objId'sini al ---
    attachment_url = f"https://www.kap.org.tr/tr/api/notification/attachment-detail/{disclosure_index}"
    try:
        response = requests.get(attachment_url, headers=HEADERS)
        response.raise_for_status()
        attachment_data = response.json()
        file_attachment = None
        # Önce PDF ara
        for attachment in attachment_data[0]['attachments']:
             if attachment['fileExtension'].lower() == 'pdf':
                file_attachment = attachment
                break
        # PDF yoksa XLSX ara
        if not file_attachment:
            for attachment in attachment_data[0]['attachments']:
                if attachment['fileExtension'].lower() == 'xlsx':
                    file_attachment = attachment
                    break

        if not file_attachment:
            print(f"HATA: Rapora ait bir PDF veya XLSX eki bulunamadı. ❌")
            return
            
        obj_id = file_attachment['objId']
        file_name = file_attachment['fileName']
        file_ext = file_attachment['fileExtension']
        print(f"İndirilecek ek bulundu: '{file_name}' (ObjectID: {obj_id})")
    except requests.exceptions.RequestException as e:
        print(f"HATA: Rapor ekleri alınırken bir hata oluştu: {e} ❌")
        return

    # --- Adım 4: Dosyayı indir ---
    download_url = f"https://www.kap.org.tr/tr/api/file/download/{obj_id}"
    try:
        print("Dosya indiriliyor, lütfen bekleyin... 📥")
        file_response = requests.get(download_url, headers=HEADERS, stream=True)
        file_response.raise_for_status()

        base_directory = "fon-raporlari"
        period_directory = report_date_obj.strftime('%Y-%m') # YYYY-AA formatı
        
        output_directory = os.path.join(base_directory, period_directory)

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
            print(f"'{output_directory}' klasör yapısı oluşturuldu.")

        # Dosya adını oluştur
        date_for_filename = report_date_obj.strftime('%Y-%m-%d')
        output_filename = f"{fund_code}_Portfoy_Dagilim_{date_for_filename}.{file_ext.lower()}"
        full_path = os.path.join(output_directory, output_filename)

        with open(full_path, 'wb') as f:
            for chunk in file_response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"\nBaşarılı! ✅\nRapor '{os.path.abspath(full_path)}' adresine kaydedildi.")

    except requests.exceptions.RequestException as e:
        print(f"HATA: Dosya indirilirken bir hata oluştu: {e} ❌")
    except OSError as e:
        print(f"HATA: Dosya kaydedilirken bir sistem hatası oluştu: {e} ❌")


# --- Script'i Çalıştırma ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="KAP'tan finansal rapor indirme veya fon bilgisi çekme aracı.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command', required=True, help='Çalıştırılacak komut')

    # Rapor indirme komutu
    parser_report = subparsers.add_parser('rapor', help='Belirtilen şirket için en son finansal raporu indirir.')
    parser_report.add_argument('ticker', type=str, help='Raporu indirilecek şirketin BIST kodu (örn: SOKM)')

    # Faaliyet Raporu indirme komutu
    parser_activity_report = subparsers.add_parser('faaliyet-raporu', help='Belirtilen şirket için en son konsolide faaliyet raporunu indirir.')
    parser_activity_report.add_argument('ticker', type=str, help='Raporu indirilecek şirketin BIST kodu (örn: SOKM)')

    # Fon yönetim ücreti komutu
    parser_fund = subparsers.add_parser(
        'fon-ucret', 
        help='Belirtilen fonun yönetim ücreti oranını çeker.\nÖrnek: python kap_rapor_indir.py fon-ucret TZL',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser_fund.add_argument('fund_code', type=str, help='Bilgisi çekilecek fonun kodu (örn: TZL)')

    # Fon portföy dağılım raporu komutu
    parser_fund_report = subparsers.add_parser(
        'fon-rapor',
        help='Belirtilen fon(lar) için en son portföy dağılım raporunu indirir.\nÖrnek: python kap_rapor_indir.py fon-rapor TZL IIH',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser_fund_report.add_argument('fund_codes', nargs='+', type=str, help='Raporu indirilecek fon kod(ları) (örn: TZL IIH)')

    # Fon listeleme komutu
    parser_list_funds = subparsers.add_parser(
        'fon-liste',
        help='Belirtilen varlık grubuna ait fonları TEFAS\'tan listeler.\nÖrnek: python kap_rapor_indir.py fon-liste Eurobond',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser_list_funds.add_argument(
        'asset_group', 
        type=FundAssetGroup, 
        choices=list(FundAssetGroup),
        help=f"Fonun dahil olduğu varlık grubu (Seçenekler: {', '.join([e.value for e in FundAssetGroup])})"
    )


    # Eğer hiç komut girilmezse yardım mesajını göster
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
        
    args = parser.parse_args()

    # Gerekli kütüphanelerin kontrolü
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError as e:
        print(f"HATA: Gerekli bir kütüphane eksik: {e.name}. ❌")
        print(f"Lütfen 'pip install {e.name}' komutu ile kurun.")
        sys.exit(1)

    if args.command == 'rapor':
        get_latest_financial_report(args.ticker)
    elif args.command == 'faaliyet-raporu':
        get_latest_activity_report(args.ticker)
    elif args.command == 'fon-ucret':
        get_fund_management_fee(args.fund_code)
    elif args.command == 'fon-rapor':
        for fund_code in args.fund_codes:
            download_fund_portfolio_report(fund_code)
    elif args.command == 'fon-liste':
        get_funds_by_asset_group(args.asset_group)