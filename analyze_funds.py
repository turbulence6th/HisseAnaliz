#!/usr/bin/env python3
"""BIST 100 Dışı Fonların portföy dağılımlarını PDF raporlardan çıkarır."""

import re
import csv
import glob
import os
from collections import defaultdict

import pdfplumber


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "bist-100-disi.csv")
REPORT_DIR = os.path.join(BASE_DIR, "fon-raporlari", "2026-02")


def parse_tr_number(s):
    """'7,32' veya '7.084.818,00' gibi TR formatındaki sayıyı parse eder."""
    s = s.strip().rstrip("%")
    # Binlik ayırıcı nokta varsa kaldır, ondalık virgülü noktaya çevir
    if "," in s:
        parts = s.split(",")
        integer_part = parts[0].replace(".", "")
        return float(f"{integer_part}.{parts[1]}")
    return float(s.replace(".", ""))


def detect_format(text):
    if "Isin Kodu" in text and "Rayiç Değeri" in text:
        return "yapikredi"
    if "Grup%" in text or "Toplam%" in text:
        return "garanti"
    if "Birim Alış Fiyatı" in text or re.search(r"^\d+\s+\w+\.E\s+", text, re.MULTILINE):
        return "ziraat"
    if "FPD" in text or "FTD" in text:
        return "tefas"
    return "unknown"


def extract_full_text(pdf_path):
    """PDF'den tüm sayfa metinlerini birleştirir."""
    with pdfplumber.open(pdf_path) as pdf:
        pages = []
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                pages.append(t)
        return "\n".join(pages)


def find_stock_section(text):
    """Hisse senetleri bölümünü bulur."""
    # "HİSSE SENETLERİ" veya "A.PAY" ile başlayan bölümü bul
    patterns = [
        r"(?:A\)\s*)?HİSSE SENET(?:LER)?İ",
        r"A\.PAY",
    ]
    start = None
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            start = m.start()
            break
    if start is None:
        return text

    # Bölüm sonu: "GRUP TOPLAMI" veya sonraki ana bölüm
    end_patterns = [
        r"GRUP TOPLAMI",
        r"^[B-Z][\.\)]\s",
        r"T\.REPO",
        r"MEVDUAT",
        r"DİĞER",
        r"^[B-Z]\s*-\s*",
    ]
    end = len(text)
    for pat in end_patterns:
        m = re.search(pat, text[start + 50:], re.MULTILINE)
        if m:
            candidate = start + 50 + m.start()
            if candidate < end:
                end = candidate
    return text[start:end]


def extract_yapikredi(text):
    """YHB formatı: TICKER ISIN Company Nominal MarketValue Percentage"""
    stocks = defaultdict(float)
    stock_section = find_stock_section(text)
    # Her satırda ISIN kodu ara
    for line in stock_section.split("\n"):
        # TICKER ISIN_CODE ... number pattern
        m = re.match(r"^([A-Z][A-Z0-9]{1,5})\s+(TRE|TRA)\w+\s+", line)
        if m:
            ticker = m.group(1)
            # Son sayı yüzdelik oran
            numbers = re.findall(r"[\d,]+\.\d+", line)
            if numbers:
                last = numbers[-1]
                try:
                    pct = float(last.replace(",", ""))
                except ValueError:
                    continue
                if pct < 100:  # mantıklı bir yüzde
                    stocks[ticker] += pct
    return dict(stocks)


def extract_garanti(text):
    """GOH formatı: TICKER.E Company ISIN ... MarketValue Grup% Toplam%"""
    stocks = defaultdict(float)
    for line in text.split("\n"):
        # TICKER.E ile başlayan satırlar
        m = re.match(r"^([A-Z][A-Z0-9]{1,5})\.E\s+", line)
        if m:
            ticker = m.group(1)
            # Sondaki yüzdeleri bul (X.XX% formatı)
            pct_matches = re.findall(r"([\d.]+)%", line)
            if len(pct_matches) >= 2:
                # Son yüzde = Toplam%
                try:
                    pct = float(pct_matches[-1])
                except ValueError:
                    continue
                stocks[ticker] += pct
    return dict(stocks)


def extract_ziraat(text):
    """ZJL formatı: # TICKER.E Company Nominal MarketValue Oran(%) BirimAlış"""
    stocks = defaultdict(float)
    for line in text.split("\n"):
        # Numaralı satır: "1 AFYON.E AFYON ÇİMENTO 400.000,000 5.868.000,00 1,336773 14,301"
        m = re.match(r"^\d+\s+([A-Z][A-Z0-9]{1,5})\.E\s+", line)
        if m:
            ticker = m.group(1)
            # Sondaki sayıları bul - Oran(%) sondan ikinci
            numbers = re.findall(r"[\d.]+,\d+", line)
            if len(numbers) >= 2:
                try:
                    pct = parse_tr_number(numbers[-2])
                except (ValueError, IndexError):
                    continue
                if pct < 100:
                    stocks[ticker] += pct
    return dict(stocks)


def extract_tefas(text):
    """TEFAS formatı: TICKER TL Company ISIN ... MarketValue GrupPct FPDPct FTDPct"""
    stocks = defaultdict(float)
    for line in text.split("\n"):
        # TICKER TL ile başlayan satırlar
        m = re.match(r"^([A-Z][A-Z0-9]{1,5})\s+TL\s+", line)
        if m:
            ticker = m.group(1)
            # ISIN kodu doğrulama
            if not re.search(r"(TRE|TRA)\w{8,}", line):
                continue
            # Sondaki 3 sayı: Grup%, FPD%, FTD%
            # TR formatı: virgüllü sayılar
            numbers = re.findall(r"(\d+,\d+)", line)
            if len(numbers) >= 3:
                try:
                    pct = parse_tr_number(numbers[-1])  # FTD %
                except ValueError:
                    continue
                if pct < 100:
                    stocks[ticker] += pct
    return dict(stocks)


def extract_stocks(pdf_path):
    """PDF'den hisse dağılımını çıkarır."""
    text = extract_full_text(pdf_path)
    fmt = detect_format(text)

    extractors = {
        "yapikredi": extract_yapikredi,
        "garanti": extract_garanti,
        "ziraat": extract_ziraat,
        "tefas": extract_tefas,
    }

    extractor = extractors.get(fmt)
    if extractor is None:
        print(f"  [!] Bilinmeyen format: {pdf_path}")
        return {}

    stocks = extractor(text)
    # Yüzdeleri yuvarla, 0.01'den küçükleri filtrele
    return {k: round(v, 2) for k, v in stocks.items() if round(v, 2) >= 0.01}


def load_fund_codes():
    """CSV'den fon kodlarını yükler."""
    codes = []
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            codes.append(row["Fon Kodu"])
    return codes


def find_pdf(fund_code):
    """Fon koduna ait PDF dosyasını bulur."""
    pattern = os.path.join(REPORT_DIR, f"{fund_code}_*.pdf")
    files = glob.glob(pattern)
    return files[0] if files else None


def main():
    fund_codes = load_fund_codes()
    all_stocks = set()
    fund_portfolios = {}

    print("=" * 70)
    print("BIST 100 DIŞI FON PORTFÖY DAĞILIMLARI")
    print("=" * 70)

    for code in fund_codes:
        pdf_path = find_pdf(code)
        if not pdf_path:
            print(f"\n[!] {code}: PDF bulunamadı")
            continue

        stocks = extract_stocks(pdf_path)
        fund_portfolios[code] = stocks
        all_stocks.update(stocks.keys())

        print(f"\n{'─' * 50}")
        print(f"  {code} - {len(stocks)} hisse")
        print(f"{'─' * 50}")
        # Yüzdeye göre sırala
        for ticker, pct in sorted(stocks.items(), key=lambda x: -x[1]):
            print(f"  {ticker:<8} {pct:>6.2f}%")
        total = sum(stocks.values())
        print(f"  {'TOPLAM':<8} {total:>6.2f}%")

    # Ortak hisseler analizi
    if len(fund_portfolios) > 1:
        print(f"\n{'=' * 70}")
        print("ORTAK HİSSE ANALİZİ")
        print(f"{'=' * 70}")

        stock_funds = defaultdict(list)
        for code, stocks in fund_portfolios.items():
            for ticker, pct in stocks.items():
                if pct >= 0.1:  # Anlamlı pozisyonlar
                    stock_funds[ticker].append((code, pct))

        # En çok fonda bulunan hisseler
        common = sorted(stock_funds.items(), key=lambda x: (-len(x[1]), x[0]))
        print(f"\n{'Hisse':<8} {'Fon Sayısı':>10}  Fonlar")
        print("─" * 70)
        for ticker, funds in common:
            if len(funds) >= 2:
                fund_str = ", ".join(f"{c}(%{p:.1f})" for c, p in sorted(funds))
                print(f"{ticker:<8} {len(funds):>10}  {fund_str}")

    # Toplam ağırlık tablosu
    if fund_portfolios:
        print(f"\n{'=' * 70}")
        print("TÜM FONLARDA ORTALAMA AĞIRLIK (en az 3 fonda bulunanlar)")
        print(f"{'=' * 70}")

        stock_weights = defaultdict(list)
        for code, stocks in fund_portfolios.items():
            for ticker, pct in stocks.items():
                if pct >= 0.1:
                    stock_weights[ticker].append(pct)

        print(f"\n{'Hisse':<8} {'Ort %':>8} {'Min %':>8} {'Max %':>8} {'Fon #':>6}")
        print("─" * 45)
        for ticker, weights in sorted(
            stock_weights.items(),
            key=lambda x: -sum(x[1]) / len(x[1]),
        ):
            if len(weights) >= 3:
                avg = sum(weights) / len(weights)
                print(
                    f"{ticker:<8} {avg:>8.2f} {min(weights):>8.2f} "
                    f"{max(weights):>8.2f} {len(weights):>6}"
                )


if __name__ == "__main__":
    main()
