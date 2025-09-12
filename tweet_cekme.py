import tweepy
import os
import argparse  # Argüman yönetimi için kütüphaneyi dahil ettik

# --- AYARLAR ---

# Sabit KULLANICI_ADLARI listesini buradan kaldırdık.
# Artık parametre olarak alınacak.

# Her bir kullanıcı için en fazla kaç tweet çekmek istediğinizi belirtin.
CEKILECEK_TWEET_SAYISI = 10

# Bearer Token'ın okunacağı dosyanın adı.
TOKEN_DOSYASI = "twitter_bearer.txt"


# --- SCRIPT'İN ANA BÖLÜMÜ ---

def tokeni_dosyadan_oku(dosya_adi):
    """
    Bearer Token'ı belirtilen dosyadan okur ve döndürür.
    """
    if not os.path.exists(dosya_adi):
        print(f"HATA: '{dosya_adi}' adında bir dosya bulunamadı.")
        print(f"Lütfen Bearer Token'ınızı içeren '{dosya_adi}' dosyasını script ile aynı klasöre oluşturun.")
        return None
    
    try:
        with open(dosya_adi, 'r') as f:
            token = f.read().strip()
            if not token:
                print(f"HATA: '{dosya_adi}' dosyası boş. Lütfen token'ınızı bu dosyaya kaydedin.")
                return None
            return token
    except Exception as e:
        print(f"'{dosya_adi}' dosyası okunurken beklenmedik bir hata oluştu: {e}")
        return None


# Fonksiyonu, kullanıcı listesini parametre olarak alacak şekilde güncelledik
def tweetleri_cek(bearer_token, kullanici_listesi):
    """
    Belirtilen kullanıcıların son tweet'lerini çeker ve ekrana yazdırır.
    """
    try:
        client = tweepy.Client(bearer_token)
    except Exception as e:
        print(f"Hata: Tweepy istemcisi oluşturulurken bir sorun oluştu. Token'ınız geçerli mi?")
        print(f"Detay: {e}")
        return

    if not kullanici_listesi:
        print("Lütfen en az bir kullanıcı adı belirtin.")
        return

    print("--- Tweet Çekme İşlemi Başladı ---\n")

    # Listedeki her bir kullanıcı adı için döngü başlat
    for kullanici_adi in kullanici_listesi:
        try:
            print(f"-> '{kullanici_adi}' kullanıcısının tweet'leri alınıyor...")
            
            user_response = client.get_user(username=kullanici_adi)
            
            if not user_response.data:
                print(f"   Hata: '{kullanici_adi}' adında bir kullanıcı bulunamadı.")
                continue

            user_id = user_response.data.id

            response = client.get_users_tweets(
                id=user_id, 
                max_results=CEKILECEK_TWEET_SAYISI,
                tweet_fields=["created_at", "public_metrics"]
            )

            if not response.data:
                print(f"   Bu kullanıcı için gösterilecek tweet bulunamadı (hesap gizli olabilir).")
                continue

            for tweet in response.data:
                print("-" * 20)
                print(f"Tarih: {tweet.created_at}")
                print(f"Metin: {tweet.text}")
                print(f"Beğeni: {tweet.public_metrics['like_count']}, Retweet: {tweet.public_metrics['retweet_count']}")
                print("-" * 20)
            
            print(f"'{kullanici_adi}' için {len(response.data)} adet tweet başarıyla çekildi.\n")

        except tweepy.errors.TweepyException as e:
            print(f"'{kullanici_adi}' kullanıcısı için tweet çekilirken bir API hatası oluştu: {e}")
        except Exception as e:
            print(f"Beklenmedik bir hata oluştu: {e}")

    print("--- Tüm İşlemler Tamamlandı ---")


# Script'i çalıştıran ana bölüm
if __name__ == "__main__":
    # Argüman ayrıştırıcısını (parser) oluşturuyoruz
    parser = argparse.ArgumentParser(description="Belirtilen X kullanıcılarının son tweet'lerini çeker.")
    
    # Hangi argümanları kabul edeceğimizi tanımlıyoruz
    parser.add_argument('kullanici_adlari', 
                        metavar='KULLANICI_ADI', 
                        type=str, 
                        nargs='+',  # '+' -> bir veya daha fazla argüman alabileceğini belirtir
                        help="Tweet'leri çekilecek bir veya daha fazla kullanıcının adı (boşluklarla ayırarak girin)")

    # Komut satırından verilen argümanları ayrıştırıyoruz
    args = parser.parse_args()

    # Önce token'ı dosyadan okumayı deniyoruz
    bearer_token = tokeni_dosyadan_oku(TOKEN_DOSYASI)
    
    # Eğer token başarıyla okunduysa ana fonksiyonu çalıştırıyoruz
    if bearer_token:
        # Argüman olarak alınan kullanıcı listesini fonksiyona iletiyoruz
        tweetleri_cek(bearer_token, args.kullanici_adlari)
    else:
        print("\nİşlem durduruldu. Lütfen token dosyasını kontrol edip tekrar deneyin.")