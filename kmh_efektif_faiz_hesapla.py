import argparse

def efektif_faiz_hesapla(kmh_tutari, gecen_gun_sayisi, odenen_faiz):
    """
    KMH (Kredi Kartı Nakit Avansı) çekiminin aylık efektif faiz oranını hesaplar.

    Parametreler:
    kmh_tutari (float): Çekilen KMH tutarı (TL).
    gecen_gun_sayisi (int): KMH çekiminden bu yana geçen gün sayısı.
    odenen_faiz (float): Toplam ödenen faiz tutarı (TL).

    Döndürür:
    dict: Günlük, aylık ve yıllık efektif faiz oranları ile diğer hesaplama detayları.
    """
    if kmh_tutari <= 0 or gecen_gun_sayisi <= 0 or odenen_faiz < 0:
        return None

    # Toplam geri ödenen tutar
    toplam_odeme = kmh_tutari + odenen_faiz

    # Günlük efektif faiz oranı (bileşik faiz formülü)
    # Toplam_Ödeme = Ana_Para * (1 + günlük_oran)^gün_sayısı
    # (1 + günlük_oran) = (Toplam_Ödeme / Ana_Para)^(1/gün_sayısı)
    try:
        gunluk_carpan = (toplam_odeme / kmh_tutari) ** (1 / gecen_gun_sayisi)
        gunluk_efektif_oran = gunluk_carpan - 1

        # Aylık efektif faiz oranı (30 gün kabul edilerek)
        aylik_efektif_oran = (1 + gunluk_efektif_oran) ** 30 - 1

        # Yıllık efektif faiz oranı (365 gün)
        yillik_efektif_oran = (1 + gunluk_efektif_oran) ** 365 - 1

        return {
            'gunluk_oran': gunluk_efektif_oran * 100,
            'aylik_oran': aylik_efektif_oran * 100,
            'yillik_oran': yillik_efektif_oran * 100,
            'toplam_odeme': toplam_odeme,
            'faiz_orani': (odenen_faiz / kmh_tutari) * 100
        }
    except (ZeroDivisionError, ValueError):
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="KMH Çekiminin Aylık Efektif Faiz Oranını Hesaplama Aracı.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog='''
Örnek Kullanım:
python kmh_efektif_faiz_hesapla.py --kmh-tutari 10000 --gun-sayisi 45 --odenen-faiz 450
(10000 TL KMH çekimi, 45 gün sonra 450 TL faiz ödenmiş ise aylık efektif faiz oranını hesaplar)
'''
    )
    parser.add_argument("--kmh-tutari", type=float, required=True, help="Çekilen KMH tutarı (TL).")
    parser.add_argument("--gun-sayisi", type=int, required=True, help="KMH çekiminden bu yana geçen gün sayısı.")
    parser.add_argument("--odenen-faiz", type=float, required=True, help="Toplam ödenen faiz tutarı (TL).")

    args = parser.parse_args()

    try:
        if args.kmh_tutari <= 0 or args.gun_sayisi <= 0 or args.odenen_faiz < 0:
            print("\nHata: KMH tutarı ve gün sayısı pozitif olmalı, faiz negatif olmamalıdır.")
        else:
            sonuc = efektif_faiz_hesapla(args.kmh_tutari, args.gun_sayisi, args.odenen_faiz)

            if sonuc is not None:
                print("\n" + "=" * 60)
                print("KMH EFEKTİF FAİZ ORANI HESAPLAMA SONUÇLARI")
                print("=" * 60)
                print(f"Çekilen KMH Tutarı: {args.kmh_tutari:,.2f} TL")
                print(f"Geçen Gün Sayısı: {args.gun_sayisi} gün")
                print(f"Ödenen Faiz Tutarı: {args.odenen_faiz:,.2f} TL")
                print(f"Toplam Geri Ödenen: {sonuc['toplam_odeme']:,.2f} TL")
                print("-" * 60)
                print(f"Basit Faiz Oranı: %{sonuc['faiz_orani']:.2f} ({args.gun_sayisi} gün için)")
                print("-" * 60)
                print("EFEKTİF FAİZ ORANLARI (Bileşik Faiz Hesabı):")
                print(f"  • Günlük Efektif Oran: %{sonuc['gunluk_oran']:.4f}")
                print(f"  • Aylık Efektif Oran: %{sonuc['aylik_oran']:.2f}")
                print(f"  • Yıllık Efektif Oran: %{sonuc['yillik_oran']:.2f}")
                print("=" * 60)
            else:
                print("\nHata: Efektif faiz oranı hesaplanamadı. Lütfen girdiğiniz değerleri kontrol edin.")

    except Exception as e:
        print(f"\nBeklenmedik bir hata oluştu: {e}")
