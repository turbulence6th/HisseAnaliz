
import os
import base64
import html2text
from datetime import datetime
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- DEĞİŞTİRİLEBİLİR AYARLAR ---
SENDER_EMAIL = "ziraatyatirim@e.ziraatyatirim.com.tr"
EMAIL_SUBJECT = "Sabah Stratejisi"
MARK_AS_READ = True
HTML_OUTPUT_DIR = "html_output"
MD_OUTPUT_DIR = "md_output"
# --- /DEĞİŞTİRİLEBİLİR AYARLAR ---

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

def authenticate_gmail():
    """Gmail API için kimlik doğrulama işlemini gerçekleştirir ve geçerli bir servis nesnesi döndürür."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Token yenilenemedi, lütfen tekrar giriş yapın: {e}")
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
                return authenticate_gmail()
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"Hata: '{CREDENTIALS_FILE}' dosyası bulunamadı.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            
    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except HttpError as error:
        print(f"Servis oluşturulurken bir hata oluştu: {error}")
        return None

def convert_html_to_markdown(html_content):
    """html2text kütüphanesini kullanarak HTML'i temiz bir Markdown'a çevirir."""
    # 1. BeautifulSoup ile görünmez gürültüyü temizle
    soup = BeautifulSoup(html_content, 'html.parser')
    # E-posta istemcilerinde önizleme için kullanılan görünmez div'i kaldır
    preheader = soup.find('div', class_='emdigital_preheader')
    if preheader:
        preheader.decompose()
    
    cleaned_html = str(soup)

    # 2. html2text ile dönüşümü yap
    h = html2text.HTML2Text()
    h.body_width = 0  # Satırları otomatik kaydırmayı devre dışı bırak
    h.ignore_images = True # Resimleri yoksay
    h.bypass_tables = False # Tabloları dönüştür

    markdown = h.handle(cleaned_html)
    return markdown

def fetch_and_save_emails(service):
    """E-postaları çeker, HTML olarak kaydeder ve temizlenmiş metni MD olarak ayıklar."""
    os.makedirs(HTML_OUTPUT_DIR, exist_ok=True)
    os.makedirs(MD_OUTPUT_DIR, exist_ok=True)

    query = f'from:"{SENDER_EMAIL}" subject:("{EMAIL_SUBJECT}")'
    
    try:
        results = service.users().messages().list(userId='me', q=query, maxResults=5).execute()
        messages = results.get('messages', [])

        if not messages:
            print("Kriterlere uyan e-posta bulunamadı.")
            return

        print(f"{len(messages)} adet e-posta bulundu. İşleniyor...")

        for message_info in reversed(messages):
            msg_id = message_info['id']
            message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            
            internal_date = datetime.fromtimestamp(int(message['internalDate']) / 1000)
            file_date_str = internal_date.strftime('%Y-%m-%d')
            
            html_filename = os.path.join(HTML_OUTPUT_DIR, f"ziraat-strateji-{file_date_str}.html")
            md_filename = os.path.join(MD_OUTPUT_DIR, f"ziraat-strateji-{file_date_str}.md")

            if os.path.exists(md_filename):
                print(f"'{md_filename}' zaten mevcut, bu e-posta atlanıyor.")
                continue

            payload = message.get('payload', {})
            html_content = ""
            if 'parts' in payload:
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/html':
                        data = part.get('body', {}).get('data', '')
                        if data:
                            html_content = base64.urlsafe_b64decode(data).decode('utf-8')
                            break
            elif payload.get('mimeType') == 'text/html':
                data = payload.get('body', {}).get('data', '')
                if data:
                    html_content = base64.urlsafe_b64decode(data).decode('utf-8')

            if not html_content:
                print(f"E-posta ID {msg_id} için HTML içerik bulunamadı, atlanıyor.")
                continue

            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"Orijinal HTML '{html_filename}' dosyasına kaydedildi.")

            markdown_content = convert_html_to_markdown(html_content)

            if not markdown_content or len(markdown_content) < 100:
                print(f"'{html_filename}' içinde anlamlı içerik bulunamadı.")
                continue

            with open(md_filename, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print(f"İşlenmiş içerik '{md_filename}' dosyasına kaydedildi.")

            if MARK_AS_READ:
                service.users().messages().modify(userId='me', id=msg_id, body={'removeLabelIds': ['UNREAD']}).execute()

    except HttpError as error:
        print(f"E-postalar alınırken bir hata oluştu: {error}")
    except Exception as e:
        print(f"Beklenmedik bir hata oluştu: {e}")

if __name__ == '__main__':
    gmail_service = authenticate_gmail()
    if gmail_service:
        fetch_and_save_emails(gmail_service)
