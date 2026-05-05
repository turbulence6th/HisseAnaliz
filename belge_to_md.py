#!/usr/bin/env python3
"""
belge_to_md.py — Microsoft MarkItDown kullanarak belgeleri Markdown'a çevirir.

Desteklenen formatlar:
  PDF, Word (.docx), Excel (.xlsx), PowerPoint (.pptx),
  HTML, CSV, JSON, XML, resim dosyaları (JPEG, PNG, GIF, BMP, TIFF, WEBP),
  ses dosyaları (MP3, WAV), ZIP arşivleri, YouTube URL'leri, web sayfaları

Kullanım:
  python belge_to_md.py <dosya_veya_url>              # stdout'a yaz
  python belge_to_md.py <dosya_veya_url> -o <çıktı>  # dosyaya kaydet
  python belge_to_md.py <dosya_veya_url> --ayni-yer   # orijinalle aynı dizine .md kaydet
  python belge_to_md.py *.pdf --klasor ./markdown/    # klasöre toplu dönüştür

Örnekler:
  python belge_to_md.py rapor.pdf
  python belge_to_md.py sunum.pptx -o sunum.md
  python belge_to_md.py https://example.com/sayfa --ayni-yer
  python belge_to_md.py finansal-raporlar/2024/*.pdf --klasor cikti/
"""

import argparse
import sys
import os
from pathlib import Path

try:
    from markitdown import MarkItDown
except ImportError:
    print("Hata: markitdown kütüphanesi bulunamadı.", file=sys.stderr)
    print("Kurulum: pip install markitdown", file=sys.stderr)
    sys.exit(1)


def donustur(kaynak: str, md: MarkItDown) -> str:
    """Verilen kaynak (dosya yolu veya URL) için Markdown içeriği döndürür."""
    try:
        sonuc = md.convert(kaynak)
        return sonuc.text_content
    except Exception as e:
        raise RuntimeError(f"Dönüştürme hatası: {e}") from e


def kaydet(icerik: str, hedef: Path):
    """Markdown içeriğini dosyaya kaydeder."""
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text(icerik, encoding="utf-8")
    print(f"  ✓ Kaydedildi: {hedef}", file=sys.stderr)


def ayni_yer_yolu(kaynak: str) -> Path:
    """Kaynak dosyayla aynı dizinde .md uzantılı hedef yolu üretir."""
    p = Path(kaynak)
    return p.with_suffix(".md")


def klasor_yolu(kaynak: str, klasor: Path) -> Path:
    """Belirtilen klasör altında .md uzantılı hedef yolu üretir."""
    p = Path(kaynak)
    ad = p.stem + ".md"
    return klasor / ad


def main():
    parser = argparse.ArgumentParser(
        description="Belgeleri Markdown'a çevir (Microsoft MarkItDown)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "kaynaklar",
        nargs="+",
        metavar="KAYNAK",
        help="Dönüştürülecek dosya yolları veya URL'ler (glob destekli)",
    )
    cikti_grubu = parser.add_mutually_exclusive_group()
    cikti_grubu.add_argument(
        "-o", "--cikti",
        metavar="DOSYA",
        help="Çıktı dosyası (yalnızca tek kaynak kullanılırken geçerli)",
    )
    cikti_grubu.add_argument(
        "--ayni-yer",
        action="store_true",
        help="Her kaynak ile aynı dizine .md uzantılı dosya olarak kaydet",
    )
    cikti_grubu.add_argument(
        "--klasor",
        metavar="KLASOR",
        help="Tüm çıktıları bu klasöre kaydet",
    )
    parser.add_argument(
        "--sessiz",
        action="store_true",
        help="İlerleme mesajlarını bastır",
    )

    args = parser.parse_args()

    # Tek çıktı dosyası yalnızca tek kaynakla mantıklı
    if args.cikti and len(args.kaynaklar) > 1:
        parser.error("-o/--cikti yalnızca tek kaynak kullanılırken belirtilebilir.")

    md = MarkItDown()
    hatalar = []

    for kaynak in args.kaynaklar:
        if not args.sessiz:
            print(f"→ İşleniyor: {kaynak}", file=sys.stderr)

        try:
            icerik = donustur(kaynak, md)
        except RuntimeError as e:
            print(f"  ✗ {e}", file=sys.stderr)
            hatalar.append(kaynak)
            continue

        # Çıktı hedefini belirle
        if args.cikti:
            kaydet(icerik, Path(args.cikti))
        elif args.ayni_yer:
            hedef = ayni_yer_yolu(kaynak)
            kaydet(icerik, hedef)
        elif args.klasor:
            hedef = klasor_yolu(kaynak, Path(args.klasor))
            kaydet(icerik, hedef)
        else:
            # Tek kaynak → stdout
            if len(args.kaynaklar) > 1:
                print(f"\n{'='*60}")
                print(f"# {kaynak}")
                print(f"{'='*60}\n")
            print(icerik)

    if hatalar:
        print(f"\nToplam {len(hatalar)} dosyada hata oluştu:", file=sys.stderr)
        for h in hatalar:
            print(f"  - {h}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
