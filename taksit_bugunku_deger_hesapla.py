import argparse

def bugunku_deger_hesapla(toplam_odeme, taksit_sayisi, aylik_faiz_orani):
    """
    Taksitli bir alımın bugünkü peşin değerini hesaplar.

    Parametreler:
    toplam_odeme (float): Taksitler sonunda ödenecek toplam tutar.
    taksit_sayisi (int): Toplam taksit sayısı (ay).
    aylik_faiz_orani (float): Aylık enflasyon veya fırsat maliyeti faiz oranı (örneğin, %2.5 için 0.025).

    Döndürür:
    float: Hesaplanmış bugünkü değer.
    """
    # Faiz oranı 0 ise, bugünkü değer toplam ödemeye eşittir.
    if aylik_faiz_orani == 0:
        return toplam_odeme

    # Aylık ödemeyi hesapla
    aylik_odeme = toplam_odeme / taksit_sayisi
    
    # Anüitenin Bugünkü Değeri (Present Value of an Annuity) formülü
    # PV = Pmt * [1 - (1 + r)**-n] / r
    try:
        bugunku_deger = aylik_odeme * (1 - (1 + aylik_faiz_orani)**-taksit_sayisi) / aylik_faiz_orani
        return bugunku_deger
    except (ZeroDivisionError, ValueError):
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Taksitli Alışverişin Bugünkü Değerini Hesaplama Aracı.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog='''
Örnek Kullanım:
python taksit_bugunku_deger_hesapla.py --toplam-odeme 15000 --taksit-sayisi 6 --aylik-faiz 2.5
(6 ayda toplam 15000 TL ödenerek alınan bir ürünün bugünkü peşin değerini hesaplar)
'''
    )
    parser.add_argument("--toplam-odeme", type=float, required=True, help="Geri ödenecek toplam tutar.")
    parser.add_argument("--taksit-sayisi", type=int, required=True, help="Toplam taksit sayısı (ay olarak).")
    parser.add_argument("--aylik-faiz", type=float, required=True, help="Aylık faiz/enflasyon oranı (yüzde olarak, örn: 2.5).")

    args = parser.parse_args()

    try:
        if args.toplam_odeme <= 0 or args.taksit_sayisi <= 0 or args.aylik_faiz < 0:
            print("\nHata: Toplam ödeme ve taksit sayısı pozitif olmalı, faiz oranı negatif olmamalıdır.")
        else:
            # Faiz oranını ondalık formata çevir
            aylik_faiz_ondalik = args.aylik_faiz / 100.0
            
            hesaplanan_bugunku_deger = bugunku_deger_hesapla(args.toplam_odeme, args.taksit_sayisi, aylik_faiz_ondalik)

            if hesaplanan_bugunku_deger is not None:
                aylik_odeme = args.toplam_odeme / args.taksit_sayisi
                print("\n-----------------------------------------")
                print(f"Aylık Fırsat Maliyeti (Faiz): %{args.aylik_faiz:.2f}")
                print(f"Taksit Sayısı: {args.taksit_sayisi} ay")
                print(f"Toplam Ödenecek Tutar: {args.toplam_odeme:,.2f} TL")
                print(f"Aylık Taksit Tutarı: {aylik_odeme:,.2f} TL")
                print("-----------------------------------------")
                print(f"Alışverişin Bugünkü Peşin Değeri: {hesaplanan_bugunku_deger:,.2f} TL")
                print("-----------------------------------------")
            else:
                print("\nHata: Bugünkü değer hesaplanamadı. Lütfen girdiğiniz değerleri kontrol edin.")

    except Exception as e:
        print(f"\nBeklenmedik bir hata oluştu: {e}")