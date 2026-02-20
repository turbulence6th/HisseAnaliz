#!/usr/bin/env python3
"""
BIST 100 Dışı fonların portföylerinde belirtilen hisselerin ağırlıklarını analiz eder.

Kullanım:
    python3 fon_portfoy_analiz.py ARDYZ ORGE SELEC AGESA AYGAZ
    python3 fon_portfoy_analiz.py --indir ARDYZ ORGE    # Raporları yeniden indir
"""

import argparse
import csv
import glob
import os
import re
import subprocess
import sys
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(SCRIPT_DIR, "bist-100-disi.csv")
FON_RAPOR_DIR = os.path.join(SCRIPT_DIR, "fon-raporlari")
TMP_DIR = "/tmp/fon_portfoy_txt"


def fon_listesi_oku():
    """CSV'den fon kodlarını ve kısa isimlerini oku."""
    fonlar = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # başlık satırını atla
        for row in reader:
            kod = row[0]
            # Kısa isim: "YAPI KREDİ PORTFÖY..." -> "Yapı Kredi"
            ad = row[1]
            # Portföy yönetim şirketinin adını çıkar
            kisa = ad.split(" PORTFÖY")[0].replace("PYŞ", "").strip()
            # Bazı düzeltmeler
            kisa = kisa.replace("DENİZ PORT. BST", "Deniz")
            if len(kisa) > 12:
                kisa = kisa[:12]
            fonlar.append({"kod": kod, "kisa": kisa, "ad": ad})
    return fonlar


def en_guncel_raporu_bul(fon_kodu):
    """Fon raporları dizininde en güncel PDF'i bul."""
    pattern = os.path.join(FON_RAPOR_DIR, "**", f"{fon_kodu}_Portfoy_Dagilim_*.pdf")
    dosyalar = glob.glob(pattern, recursive=True)
    if not dosyalar:
        return None
    # En son tarihli olanı seç
    dosyalar.sort(reverse=True)
    return dosyalar[0]


def raporlari_indir(fon_kodlari):
    """kap_rapor_indir.py ile portföy dağılım raporlarını indir."""
    print("Portföy dağılım raporları indiriliyor...", file=sys.stderr)
    cmd = [sys.executable, os.path.join(SCRIPT_DIR, "kap_rapor_indir.py"), "fon-rapor"] + fon_kodlari
    subprocess.run(cmd, cwd=SCRIPT_DIR)


def pdf_to_text(pdf_path):
    """pdftotext -layout ile PDF'i metne çevir."""
    txt_path = os.path.join(TMP_DIR, os.path.basename(pdf_path) + ".txt")
    if os.path.exists(txt_path) and os.path.getmtime(txt_path) >= os.path.getmtime(pdf_path):
        with open(txt_path, "r", encoding="utf-8") as f:
            return f.read()
    subprocess.run(["pdftotext", "-layout", pdf_path, txt_path],
                   capture_output=True, check=True)
    with open(txt_path, "r", encoding="utf-8") as f:
        return f.read()


def portfoy_parse(text, hedef_hisseler):
    """
    Fon portföy metninden hedef hisselerin ağırlıklarını çıkar.
    Birden fazla lot varsa toplayarak tek yüzde verir.
    """
    agirliklar = defaultdict(float)
    lines = text.split("\n")

    # Portföy bölümünü tespit et - satış/işlem bölümlerini hariç tut
    in_portfolio = False
    portfolio_lines = []

    for line in lines:
        upper = line.upper().strip()
        if "FON PORTFÖY DEĞERİ" in upper or "HİSSE SENET" in upper:
            in_portfolio = True
        if in_portfolio and any(kw in upper for kw in [
            "SATIŞLAR", "VII-", "VI-A", "V-AY İÇİNDE",
            "PORTFÖYDEN SATIŞ", "İTFALAR", "PORTFÖYE ALIŞ",
            "PAY ALIM SATIM DEF"
        ]):
            in_portfolio = False
        if in_portfolio:
            portfolio_lines.append(line)

    # Eğer portföy bölümü bulunamadıysa, tüm metni kullan (güvenlik için)
    if not portfolio_lines:
        portfolio_lines = lines

    for line in portfolio_lines:
        stripped = line.strip()
        if not stripped:
            continue

        for hisse in hedef_hisseler:
            matched = False

            # Format 1: "STOCK  TL  ISSUER  ISIN ..." (standart format)
            if re.match(rf"^{hisse}\s+TL\s+", stripped):
                matched = True

            # Format 2: "STOCK.E  ISSUER ..." (GOH format)
            elif re.match(rf"^{hisse}\.E\s+", stripped):
                matched = True

            # Format 3: "N STOCK.E  ISSUER ..." (ZJL format)
            elif re.match(rf"^\s*\d+\s+{hisse}\.E\s+", stripped):
                matched = True

            # Format 4: "STOCK   ISIN   ISSUER ..." (YHB format)
            elif re.match(rf"^{hisse}\s+TRE?\w{{5,}}", stripped):
                matched = True

            if matched:
                is_zjl = bool(re.match(rf"^\s*\d+\s+{hisse}\.E\s+", stripped))

                if is_zjl:
                    # ZJL format: "N STOCK.E ISSUER NOMINAL RAYIC ORAN(%) BIRIM_ALIS"
                    # Oran sütunu 6 ondalık basamaklı: "4,032189"
                    oran_match = re.findall(r"(\d+,\d{5,})", stripped)
                    if oran_match:
                        val = float(oran_match[0].replace(",", "."))
                        if 0 < val < 20:
                            agirliklar[hisse] += val
                else:
                    # Diğer formatlar: son sayısal değer genelde yüzde
                    nums = re.findall(r"(-?[\d]+[,.][\d]+)", stripped)
                    if len(nums) >= 2:
                        last_val = nums[-1].replace(",", ".")
                        try:
                            val = float(last_val)
                            if abs(val) < 20:
                                agirliklar[hisse] += val
                        except ValueError:
                            pass

    return dict(agirliklar)


def tablo_yazdir(fonlar, tum_agirliklar, hedef_hisseler, negatif=None):
    """Sonuçları tablo formatında yazdır."""
    if negatif is None:
        negatif = set()

    # Sütun genişlikleri
    hisse_w = max(len(h) for h in hedef_hisseler) + 2
    hisse_w = max(hisse_w, 7)
    col_w = 7

    # Başlık
    header = f"{'Hisse':<{hisse_w}}"
    for f in fonlar:
        header += f"{f['kod']:>{col_w}}"
    header += f"  {'#':>2}"
    print(header)
    print("─" * len(header))

    # Satırlar
    fon_toplamlari = defaultdict(float)
    has_negatif = bool(negatif)
    negatif_printed = False

    for hisse in hedef_hisseler:
        is_neg = hisse in negatif

        # Negatif bölümü başlamadan önce ayırıcı çiz
        if is_neg and not negatif_printed:
            print("─" * len(header))
            negatif_printed = True

        label = f"-{hisse}" if is_neg else hisse
        row = f"{label:<{hisse_w}}"
        count = 0

        for fon in fonlar:
            fk = fon["kod"]
            val = tum_agirliklar.get(fk, {}).get(hisse, 0)
            if val > 0.01:
                row += f"{val:>{col_w}.2f}"
                count += 1
                if is_neg:
                    fon_toplamlari[fk] -= val
                else:
                    fon_toplamlari[fk] += val
            else:
                row += f"{'─':>{col_w}}"

        row += f"  {count:>2}"
        print(row)

    # Toplam satırı
    print("─" * len(header))
    toplam_row = f"{'TOPLAM':<{hisse_w}}"
    genel_toplam = 0.0
    for fon in fonlar:
        fk = fon["kod"]
        ft = fon_toplamlari.get(fk, 0)
        if abs(ft) > 0.01:
            toplam_row += f"{ft:>{col_w}.1f}"
        else:
            toplam_row += f"{'─':>{col_w}}"
    toplam_row += "    "
    print(toplam_row)

    print("─" * len(header))
    print("# = fon sayısı, - = toplamdan düşürülür" if negatif else "# = fon sayısı")


def main():
    # argparse yerine manuel parse - çünkü "-ALBRK" gibi negatif hisseler var
    indir = "--indir" in sys.argv
    raw_args = [a for a in sys.argv[1:] if a != "--indir"]

    if not raw_args or raw_args == ["-h"] or raw_args == ["--help"]:
        print("Kullanım: python3 fon_portfoy_analiz.py [--indir] HISSE1 HISSE2 [-NEG1] [-NEG2]")
        print()
        print("  HISSE      : Pozitif hisse (toplama eklenir)")
        print("  -HISSE     : Negatif hisse (toplamdan düşürülür)")
        print("  --indir    : Portföy raporlarını yeniden indir")
        print()
        print("Örnek: python3 fon_portfoy_analiz.py ARDYZ ORGE SELEC -ALBRK -TRGYO")
        sys.exit(0)

    # Pozitif ve negatif hisseleri ayır
    pozitif = []
    negatif = set()
    for h in raw_args:
        h = h.upper()
        if h.startswith("-"):
            kod = h[1:]
            negatif.add(kod)
            pozitif.append(kod)
        else:
            pozitif.append(h)
    hedef_hisseler = pozitif

    class Args:
        pass
    args = Args()
    args.indir = indir

    # Fon listesini oku
    fonlar = fon_listesi_oku()
    fon_kodlari = [f["kod"] for f in fonlar]

    # Gerekirse raporları indir
    eksik = []
    for fk in fon_kodlari:
        if not en_guncel_raporu_bul(fk):
            eksik.append(fk)

    if args.indir or eksik:
        indirilecek = fon_kodlari if args.indir else eksik
        if eksik and not args.indir:
            print(f"Eksik raporlar indiriliyor: {', '.join(eksik)}", file=sys.stderr)
        raporlari_indir(indirilecek)

    # Tmp dizinini oluştur
    os.makedirs(TMP_DIR, exist_ok=True)

    # Her fon için portföyü parse et
    tum_agirliklar = {}
    for fon in fonlar:
        fk = fon["kod"]
        pdf_path = en_guncel_raporu_bul(fk)
        if not pdf_path:
            print(f"UYARI: {fk} için rapor bulunamadı, atlanıyor.", file=sys.stderr)
            continue

        try:
            text = pdf_to_text(pdf_path)
            agirliklar = portfoy_parse(text, hedef_hisseler)
            tum_agirliklar[fk] = agirliklar
        except Exception as e:
            print(f"HATA: {fk} parse edilemedi: {e}", file=sys.stderr)

    # Tabloyu yazdır
    print()
    tablo_yazdir(fonlar, tum_agirliklar, hedef_hisseler, negatif)
    print()


if __name__ == "__main__":
    main()
