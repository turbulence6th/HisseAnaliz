import argparse

def efektif_aylik_faiz_hesapla(ana_para, taksit_sayisi, aylik_odeme):
    """
    Verilen kredi bilgileriyle efektif aylık faiz oranını hesaplar.

    Parametreler:
    ana_para (float): Çekilen toplam kredi tutarı.
    taksit_sayisi (int): Toplam taksit sayısı (ay).
    aylik_odeme (float): Aylık ödeme tutarı.

    Döndürür:
    float: Efektif aylık faiz oranı. Faiz yoksa veya negatifse 0.0 döner.
           Hesaplama başarısız olursa None döner.
    """
    # Eğer toplam ödeme ana paradan az veya eşitse, faiz yoktur.
    if aylik_odeme * taksit_sayisi <= ana_para:
        return 0.0

    # Sayısal çözümleme için başlangıç değerleri
    epsilon = 0.000001  # İstenen hassasiyet
    max_iter = 1000     # Maksimum deneme sayısı
    dusuk_faiz = 0.0
    yuksek_faiz = 1.0   # Aylık %100 faiz, güvenli bir üst sınır

    tahmini_faiz = 0.0

    for i in range(max_iter):
        tahmini_faiz = (dusuk_faiz + yuksek_faiz) / 2
        
        # Faiz formülü (Anüite'nin Bugünkü Değeri)
        # PV = Pmt * [1 - (1 + r)**-n] / r
        # Bu formülü `ana_para` ile karşılaştırarak doğru faizi arıyoruz.
        try:
            hesaplanan_pv = aylik_odeme * (1 - (1 + tahmini_faiz)**-taksit_sayisi) / tahmini_faiz
        except ZeroDivisionError:
            hesaplanan_pv = aylik_odeme * taksit_sayisi

        if abs(hesaplanan_pv - ana_para) < epsilon:
            return tahmini_faiz

        if hesaplanan_pv > ana_para:
            # Hesaplanan değer çok yüksek, yani faiz oranı çok düşük.
            # Arama aralığının alt sınırını yükselt.
            dusuk_faiz = tahmini_faiz
        else:
            # Hesaplanan değer çok düşük, yani faiz oranı çok yüksek.
            # Arama aralığının üst sınırını düşür.
            yuksek_faiz = tahmini_faiz
            
    # Belirlenen deneme sayısında sonuca ulaşılamazsa
    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Efektif Aylık Faiz Hesaplama Aracı.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Örnek Kullanım:
python efektif_faiz_hesapla.py --ana-para 100000 --taksit-sayisi 12 --aylik-odeme 9500.50
"""
    )
    parser.add_argument("--ana-para", type=float, required=True, help="Toplam kredi tutarı (ana para).")
    parser.add_argument("--taksit-sayisi", type=int, required=True, help="Toplam taksit sayısı (ay olarak).")
    parser.add_argument("--aylik-odeme", type=float, required=True, help="Aylık ödeme tutarı.")

    args = parser.parse_args()

    try:
        if args.ana_para <= 0 or args.taksit_sayisi <= 0 or args.aylik_odeme <= 0:
            print("\nHata: Girdiğiniz tüm değerler pozitif olmalıdır.")
        else:
            faiz_orani = efektif_aylik_faiz_hesapla(args.ana_para, args.taksit_sayisi, args.aylik_odeme)

            if faiz_orani is not None:
                print("\n-----------------------------------------")
                print(f"Hesaplanan Efektif Aylık Faiz Oranı: %{faiz_orani * 100:.4f}")
                yillik_basit_faiz = faiz_orani * 12
                yillik_bilesik_faiz = ((1 + faiz_orani)**12) - 1
                print(f"Yıllık Basit Faiz Oranı (yaklaşık): %{yillik_basit_faiz * 100:.4f}")
                print(f"Yıllık Bileşik Faiz Oranı (efektif): %{yillik_bilesik_faiz * 100:.4f}")
                print("-----------------------------------------")
            else:
                print("\nHata: Faiz oranı hesaplanamadı. Lütfen girdiğiniz değerleri kontrol edin.")

    except Exception as e:
        print(f"\nBeklenmedik bir hata oluştu: {e}")