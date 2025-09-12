import requests
import os
import sys
from datetime import datetime

# HTTP istekleri için başlık bilgisi (Header)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def get_latest_financial_report(ticker_symbol):
    """
    Verilen borsa koduna göre KAP'tan en güncel Finansal Raporu indirir
    ve 'faaliyet-raporu/YYYYQQ' formatındaki klasöre kaydeder.
    Klasör adı genel olduğu için değiştirilmedi, istenirse değiştirilebilir.
    """
    ticker_symbol = ticker_symbol.upper()
    print(f"'{ticker_symbol}' için işlem başlatıldı... 📈")

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
        
        # --- DEĞİŞİKLİK BURADA ---
        financial_reports = []
        for report in disclosures_data:
            title = report.get('disclosureBasic', {}).get('title', '').lower()
            # Artık "finansal rapor" arıyoruz
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
        # Finansal Rapor ekleri genellikle doğrudan raporun kendisidir ve birden fazla olabilir.
        # Genellikle ilk PDF ana rapordur.
        for attachment in attachment_data[0]['attachments']:
             if attachment['fileExtension'].lower() == 'pdf':
                # Türkçe olup olmadığını anlamak zor olabilir, genellikle ilk PDF'i seçmek işe yarar.
                # Eğer belirli bir isimlendirme kuralı varsa (örn: ...TR.pdf), o da eklenebilir.
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

        base_directory = "finansal-raporlar" # Klasör adını da güncelledim
        
        quarter_map = {1: '03', 2: '06', 3: '09', 4: '12'}
        quarter_dir_suffix = quarter_map.get(report_quarter_num, '00')
        
        period_directory = f"{report_year}{quarter_dir_suffix}"
        
        output_directory = os.path.join(base_directory, period_directory)

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
            print(f"'{output_directory}' klasör yapısı oluşturuldu.")

        # --- DEĞİŞİKLİK BURADA (Dosya Adı) ---
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

# --- Script'i Çalıştırma ---
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("\nKullanım Hatası! ❌")
        print("Lütfen şirketin BIST kodunu tek bir parametre olarak girin.")
        print("Örnek Kullanım: python kap_rapor_indir.py SOKM\n")
        sys.exit(1)

    company_ticker = sys.argv[1]
    get_latest_financial_report(company_ticker)