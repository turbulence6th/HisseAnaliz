"""
PDF metin çıkarıcı — disk cache desteği ile.

Kullanım:
    python extract_pdf_text.py <pdf_yolu> [seçenekler]

Seçenekler:
    --pages 5-10      Sadece 5-10. sayfaları ekrana bas (cache tümünü içerir)
    --pages 3         Sadece 3. sayfayı ekrana bas
    --no-cache        Cache'i yoksay, yeniden çıkar
    --cache-only      Sadece cache'e yaz, ekrana basma

İlk çalıştırmada PDF'i çıkarır ve {pdf_yolu}.txt olarak kaydeder.
Sonraki çağrılar cache'ten anında okur (PDF yeniden parse edilmez).
Cache'i doğrudan Read aracıyla da okuyabilirsiniz.
"""

import sys
import os
import argparse
from io import StringIO


# ─── Cache yardımcıları ───────────────────────────────────────────────────────

def cache_path_for(pdf_path: str) -> str:
    return pdf_path + ".txt"


def cache_is_valid(pdf_path: str) -> bool:
    cp = cache_path_for(pdf_path)
    return (
        os.path.exists(cp)
        and os.path.getmtime(cp) >= os.path.getmtime(pdf_path)
    )


def read_cache(pdf_path: str) -> str:
    with open(cache_path_for(pdf_path), "r", encoding="utf-8") as f:
        return f.read()


def write_cache(pdf_path: str, text: str) -> None:
    cp = cache_path_for(pdf_path)
    with open(cp, "w", encoding="utf-8") as f:
        f.write(text)
    log(f"Cache kaydedildi → {cp}")


# ─── Ekstraksiyon motorları ───────────────────────────────────────────────────

def extract_with_pdfminer(pdf_path: str) -> list[tuple[int, str]]:
    from pdfminer.layout import LAParams
    from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
    from pdfminer.converter import TextConverter
    from pdfminer.pdfpage import PDFPage

    rsrcmgr = PDFResourceManager()
    pages = []
    with open(pdf_path, "rb") as fp:
        for page_num, page in enumerate(PDFPage.get_pages(fp), start=1):
            buf = StringIO()
            device = TextConverter(rsrcmgr, buf, laparams=LAParams())
            PDFPageInterpreter(rsrcmgr, device).process_page(page)
            device.close()
            pages.append((page_num, buf.getvalue().strip()))
            buf.close()
    return pages


def extract_with_pypdf(pdf_path: str) -> list[tuple[int, str]]:
    from pypdf import PdfReader
    reader = PdfReader(pdf_path)
    return [
        (i + 1, (page.extract_text() or "").strip())
        for i, page in enumerate(reader.pages)
    ]


def extract_pages(pdf_path: str) -> list[tuple[int, str]]:
    """pdfminer dener, başarısız olursa pypdf'e geçer."""
    try:
        return extract_with_pdfminer(pdf_path)
    except Exception as e:
        log(f"pdfminer başarısız: {e} — pypdf deneniyor...")
        return extract_with_pypdf(pdf_path)


# ─── Biçimlendirme / filtreleme ───────────────────────────────────────────────

def pages_to_text(pages: list[tuple[int, str]]) -> str:
    return "\n".join(
        f"--- Page {num} ---\n{text}" for num, text in pages
    )


def filter_text_by_range(full_text: str, start: int, end: int) -> str:
    """Cache'teki düz metinden sayfa aralığını filtreler."""
    lines = full_text.split("\n")
    result = []
    current = 0
    in_range = False

    for line in lines:
        if line.startswith("--- Page ") and line.endswith(" ---"):
            try:
                current = int(line[9:-4])
                in_range = start <= current <= end
            except ValueError:
                pass
        if in_range:
            result.append(line)

    return "\n".join(result)


def parse_pages_arg(s: str) -> tuple[int, int]:
    if "-" in s:
        a, b = s.split("-", 1)
        return int(a), int(b)
    n = int(s)
    return n, n


# ─── Yardımcı ─────────────────────────────────────────────────────────────────

def log(msg: str) -> None:
    print(f"[PDF] {msg}", file=sys.stderr)


# ─── Ana akış ─────────────────────────────────────────────────────────────────

def process(pdf_path: str, page_range, no_cache: bool, cache_only: bool) -> None:
    if not os.path.exists(pdf_path):
        log(f"Dosya bulunamadı: {pdf_path}")
        return

    # Cache geçerli mi?
    if not no_cache and cache_is_valid(pdf_path):
        log(f"Cache kullanılıyor ({cache_path_for(pdf_path)})")
        full_text = read_cache(pdf_path)
    else:
        log(f"Çıkarılıyor: {pdf_path}")
        pages = extract_pages(pdf_path)
        full_text = pages_to_text(pages)
        write_cache(pdf_path, full_text)

    if cache_only:
        return

    if page_range:
        print(filter_text_by_range(full_text, *page_range))
    else:
        print(full_text)


def main():
    parser = argparse.ArgumentParser(
        description="PDF metin çıkarıcı (cache destekli)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("pdf_path", nargs="+", help="PDF dosya yolu/yolları")
    parser.add_argument(
        "--pages", "-p",
        help="Ekrana basılacak sayfa aralığı (örn: 1-10, 5)",
    )
    parser.add_argument(
        "--no-cache", action="store_true",
        help="Cache'i yoksay, PDF'i yeniden çıkar",
    )
    parser.add_argument(
        "--cache-only", action="store_true",
        help="Sadece cache'e yaz, ekrana basma",
    )

    args = parser.parse_args()
    page_range = parse_pages_arg(args.pages) if args.pages else None

    for path in args.pdf_path:
        process(path, page_range, args.no_cache, args.cache_only)


if __name__ == "__main__":
    main()
