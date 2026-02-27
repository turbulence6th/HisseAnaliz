#!/usr/bin/env python3
"""
Hisse Senedi Çarpan Hesaplayıcı
================================
Verilen finansal girdilerden standart değerleme çarpanlarını hesaplar.

Kullanım:
    python carpan_hesapla.py --hisse ASELS --fiyat 309.25 --hisse-sayisi 4560 \
        --net-kar 29917 --ebit 49145 --favok 47500 --hasılat 180444 \
        --ozkaynaklar 250430 --fin-borc 43100 --nakit 29100

    # TMS 29 parasal kayıp varsa (net kârı düzeltiyor):
    python carpan_hesapla.py --hisse ASELS --fiyat 309.25 --hisse-sayisi 4560 \
        --net-kar 29917 --ebit 49145 --favok 47500 --hasılat 180444 \
        --ozkaynaklar 250430 --fin-borc 43100 --nakit 29100 \
        --parasal-kayip 13552

Tüm tutarlar Milyon TL cinsinden girilmelidir (hisse sayısı Milyon adet).
Fiyat TL cinsindendir.
"""

import argparse
import sys


# ── Renk sabitleri ─────────────────────────────────────────────────────────────
class C:
    BOLD   = "\033[1m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    CYAN   = "\033[96m"
    GRAY   = "\033[90m"
    RESET  = "\033[0m"

    @staticmethod
    def renklendir(deger, esik_iyi, esik_kotu, ters=False):
        """Değeri eşiklere göre renklendir. ters=True → düşük iyi (borç gibi)."""
        if deger is None:
            return f"{C.GRAY}—{C.RESET}"
        if not ters:
            if deger <= esik_iyi:
                return f"{C.GREEN}{deger:.2f}{C.RESET}"
            elif deger <= esik_kotu:
                return f"{C.YELLOW}{deger:.2f}{C.RESET}"
            else:
                return f"{C.RED}{deger:.2f}{C.RESET}"
        else:
            if deger <= esik_iyi:
                return f"{C.GREEN}{deger:.2f}{C.RESET}"
            elif deger <= esik_kotu:
                return f"{C.YELLOW}{deger:.2f}{C.RESET}"
            else:
                return f"{C.RED}{deger:.2f}{C.RESET}"


# ── Yardımcı ──────────────────────────────────────────────────────────────────
def bold(s):
    return f"{C.BOLD}{s}{C.RESET}"

def fmt(deger, suffix="x", renk=None):
    if deger is None:
        return f"{C.GRAY}—{C.RESET}"
    s = f"{deger:.2f}{suffix}"
    return f"{renk}{s}{C.RESET}" if renk else s

def fmt_tlb(milyon_tl):
    """Milyon TL → okunabilir string (B / M)"""
    if milyon_tl is None:
        return "—"
    if abs(milyon_tl) >= 1_000_000:
        return f"{milyon_tl / 1_000_000:.3f} Trilyon TL"
    elif abs(milyon_tl) >= 1_000:
        return f"{milyon_tl / 1_000:.3f} Milyar TL"
    else:
        return f"{milyon_tl:.1f} Milyon TL"

def safe_div(pay, payda):
    if pay is None or payda is None or payda == 0:
        return None
    return pay / payda


# ── Çarpan hesaplama çekirdeği ────────────────────────────────────────────────
def hesapla(args):
    fiyat        = args.fiyat
    n_hisse      = args.hisse_sayisi          # Milyon adet
    net_kar      = args.net_kar               # Milyon TL
    ebit         = args.ebit                  # Milyon TL (Esas Faaliyet Kârı)
    favok        = args.favok                 # Milyon TL
    hasilat      = args.hasilat               # Milyon TL
    ozkaynaklar  = args.ozkaynaklar           # Milyon TL
    fin_borc     = args.fin_borc              # Milyon TL (toplam finansal borç)
    nakit        = args.nakit                 # Milyon TL
    temettü      = args.temettu               # TL/hisse (brüt)
    parasal_kayip= args.parasal_kayip         # Milyon TL (TMS 29 etkisi, pozitif girin)

    # ── Temel hesaplar ──────────────────────────────────────────────────────────
    piyasa_degeri = fiyat * n_hisse if n_hisse else None          # Milyon TL

    net_borc = None
    if fin_borc is not None and nakit is not None:
        net_borc = fin_borc - nakit                               # + → borçlu, - → net nakit

    firma_degeri = None
    if piyasa_degeri is not None and net_borc is not None:
        firma_degeri = piyasa_degeri + net_borc                   # EV = PD + Net Borç

    # TMS 29 düzeltmesi: Parasal kayıp net kârı deprese ediyorsa EBIT daha temiz
    net_kar_duzeltilmis = None
    if net_kar is not None and parasal_kayip is not None:
        # Parasal kayıp vergi sonrası etkisini kabaca hesapla (%25 kurumlar vergisi varsayımı)
        net_kar_duzeltilmis = net_kar + parasal_kayip * 0.75

    # ── Hisse başına değerler ───────────────────────────────────────────────────
    eps = safe_div(net_kar, n_hisse)                              # TL/hisse
    eps_duz = safe_div(net_kar_duzeltilmis, n_hisse)
    eps_ebit = safe_div(ebit, n_hisse)                            # EAK bazlı EPS
    defter_hisse = safe_div(ozkaynaklar, n_hisse)                 # TL/hisse
    net_nakit_hisse = None
    if net_borc is not None and n_hisse:
        net_nakit_hisse = -net_borc / n_hisse                     # + → nakit fazlası/hisse

    # ── Çarpanlar ───────────────────────────────────────────────────────────────
    fk            = safe_div(fiyat, eps)
    fk_duz        = safe_div(fiyat, eps_duz)
    fk_ebit       = safe_div(fiyat, eps_ebit)
    fk_nakit_adj  = None
    if eps and net_nakit_hisse is not None:
        fiyat_nakit_arilmis = fiyat - (-net_nakit_hisse) if net_nakit_hisse > 0 else fiyat
        fk_nakit_adj = safe_div(fiyat_nakit_arilmis, eps)

    pd_dd         = safe_div(piyasa_degeri, ozkaynaklar)
    ev_favok      = safe_div(firma_degeri, favok)
    ev_ebit       = safe_div(firma_degeri, ebit)
    ev_hasilat    = safe_div(firma_degeri, hasilat)
    pd_hasilat    = safe_div(piyasa_degeri, hasilat)

    # ── Kârlılık ve verimlilik ─────────────────────────────────────────────────
    net_kar_marji = safe_div(net_kar, hasilat) * 100 if (net_kar and hasilat) else None
    ebit_marji    = safe_div(ebit, hasilat) * 100 if (ebit and hasilat) else None
    favok_marji   = safe_div(favok, hasilat) * 100 if (favok and hasilat) else None
    roe           = safe_div(net_kar, ozkaynaklar) * 100 if (net_kar and ozkaynaklar) else None

    # Net Borç / FAVÖK
    net_borc_favok = safe_div(net_borc, favok)

    # Temettü verimi
    temettu_verimi = safe_div(temettü, fiyat) * 100 if temettü else None

    return {
        # Temel
        "piyasa_degeri": piyasa_degeri,
        "firma_degeri": firma_degeri,
        "net_borc": net_borc,
        # Hisse başına
        "eps": eps,
        "eps_duz": eps_duz,
        "eps_ebit": eps_ebit,
        "defter_hisse": defter_hisse,
        "net_nakit_hisse": net_nakit_hisse,
        # Çarpanlar
        "fk": fk,
        "fk_duz": fk_duz,
        "fk_ebit": fk_ebit,
        "fk_nakit_adj": fk_nakit_adj,
        "pd_dd": pd_dd,
        "ev_favok": ev_favok,
        "ev_ebit": ev_ebit,
        "ev_hasilat": ev_hasilat,
        "pd_hasilat": pd_hasilat,
        # Marjlar
        "net_kar_marji": net_kar_marji,
        "ebit_marji": ebit_marji,
        "favok_marji": favok_marji,
        "roe": roe,
        "net_borc_favok": net_borc_favok,
        "temettu_verimi": temettu_verimi,
    }


# ── Çıktı yazdırma ────────────────────────────────────────────────────────────
def yazdir(args, s):
    fiyat   = args.fiyat
    hisse   = args.hisse or "—"
    n_hisse = args.hisse_sayisi

    print()
    print(bold(f"{'━'*58}"))
    print(bold(f"  {hisse}  —  Çarpan Analizi"))
    print(bold(f"{'━'*58}"))
    print(f"  Fiyat          : {C.CYAN}{fiyat:.2f} TL{C.RESET}")
    if n_hisse:
        print(f"  Hisse Sayısı   : {n_hisse:,.0f} Milyon ({n_hisse/1000:.3f} Milyar)")
    if s["piyasa_degeri"]:
        print(f"  Piyasa Değeri  : {C.CYAN}{fmt_tlb(s['piyasa_degeri'])}{C.RESET}")
    if s["firma_degeri"]:
        print(f"  Firma Değeri   : {C.CYAN}{fmt_tlb(s['firma_degeri'])}{C.RESET}")
    if s["net_borc"] is not None:
        isaretli = f"+{s['net_borc']:.0f}" if s["net_borc"] > 0 else f"{s['net_borc']:.0f}"
        renk = C.RED if s["net_borc"] > 0 else C.GREEN
        print(f"  Net Borç/Nakit : {renk}{fmt_tlb(s['net_borc'])} ({'+' if s['net_borc']>0 else ''}borçlu / nakit){C.RESET}")

    # ── Hisse Başına Değerler ──────────────────────────────────────────────────
    print()
    print(bold("  ── Hisse Başına Değerler ─────────────────────────────"))
    if s["eps"] is not None:
        print(f"  EPS (Net Kâr)          : {s['eps']:.4f} TL")
    if s["eps_duz"] is not None:
        print(f"  EPS (TMS 29 düzelt.)   : {s['eps_duz']:.4f} TL  {C.GRAY}(parasal kayıp geri eklendi){C.RESET}")
    if s["eps_ebit"] is not None:
        print(f"  EPS (EBIT/EAK bazlı)   : {s['eps_ebit']:.4f} TL")
    if s["defter_hisse"] is not None:
        print(f"  Defter Değeri/Hisse    : {s['defter_hisse']:.4f} TL")
    if s["net_nakit_hisse"] is not None:
        renk = C.GREEN if s["net_nakit_hisse"] > 0 else C.RED
        print(f"  Net Nakit/Hisse        : {renk}{s['net_nakit_hisse']:+.4f} TL{C.RESET}")

    # ── Değerleme Çarpanları ───────────────────────────────────────────────────
    print()
    print(bold("  ── Değerleme Çarpanları ──────────────────────────────"))

    def satir(etiket, deger, esik_iyi, esik_kotu, ters=False, suffix="x", not_str=""):
        if deger is None:
            return
        s_renk = C.renklendir(deger, esik_iyi, esik_kotu, ters=ters)
        not_bölüm = f"  {C.GRAY}{not_str}{C.RESET}" if not_str else ""
        print(f"  {etiket:<26}: {s_renk}{suffix}{not_bölüm}")

    satir("F/K (Net Kâr)",           s["fk"],          12, 25,  suffix="x")
    satir("F/K (TMS 29 düzelt.)",    s["fk_duz"],      12, 25,  suffix="x", not_str="parasal kayıp arındırılmış")
    satir("F/K (EBIT/EAK bazlı)",    s["fk_ebit"],     12, 25,  suffix="x", not_str="operasyonel gerçek")
    satir("F/K (Net Nakit adj.)",     s["fk_nakit_adj"],10, 20,  suffix="x", not_str="nakit düşülmüş piyasa değeri")
    satir("PD/DD",                   s["pd_dd"],        1,  3,   suffix="x")
    satir("EV/FAVÖK",                s["ev_favok"],     6, 15,  suffix="x")
    satir("EV/EBIT",                 s["ev_ebit"],      8, 20,  suffix="x")
    satir("EV/Hasılat",              s["ev_hasilat"],   1,  4,   suffix="x")
    satir("PD/Hasılat",              s["pd_hasilat"],   1,  3,   suffix="x")
    if s["temettu_verimi"] is not None:
        satir("Temettü Verimi",      s["temettu_verimi"], 6, 3, ters=True, suffix="%")

    # ── Kârlılık ──────────────────────────────────────────────────────────────
    print()
    print(bold("  ── Kârlılık ve Kaldıraç ─────────────────────────────"))
    if s["favok_marji"] is not None:
        satir("FAVÖK Marjı",         s["favok_marji"],  20, 10, ters=True, suffix="%")
    if s["ebit_marji"] is not None:
        satir("EBIT Marjı",          s["ebit_marji"],   15,  8, ters=True, suffix="%")
    if s["net_kar_marji"] is not None:
        satir("Net Kâr Marjı",       s["net_kar_marji"], 12, 6, ters=True, suffix="%")
    if s["roe"] is not None:
        satir("ROE",                 s["roe"],           20, 10, ters=True, suffix="%")
    if s["net_borc_favok"] is not None:
        satir("Net Borç/FAVÖK",      s["net_borc_favok"], 2,  4, suffix="x",
              not_str="<0 = net nakit" if s["net_borc_favok"] < 0 else "")

    print()
    print(bold(f"{'━'*58}"))
    print(f"{C.GRAY}  Renk rehberi: {C.GREEN}İyi{C.RESET} | {C.YELLOW}Dikkat{C.RESET} | {C.RED}Pahalı/Riskli{C.RESET} {C.GRAY}(sektöre göre değişir){C.RESET}")
    print()


# ── Argümanlar ────────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(
        description="Hisse senedi değerleme çarpanlarını hesaplar.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  # ASELS (FY2025)
  python carpan_hesapla.py --hisse ASELS --fiyat 309.25 --hisse-sayisi 4560 \\
      --net-kar 29917 --ebit 49145 --favok 47500 --hasilat 180444 \\
      --ozkaynaklar 250430 --fin-borc 43100 --nakit 29100 \\
      --parasal-kayip 13552

  # TUPRS (FY2025)
  python carpan_hesapla.py --hisse TUPRS --fiyat 216.20 --hisse-sayisi 1927 \\
      --net-kar 29523 --favok 82600 --hasilat 830356 \\
      --ozkaynaklar 369828 --fin-borc 50250 --nakit 107237 \\
      --temettu 17.13

  # SISE (FY2025)
  python carpan_hesapla.py --hisse SISE --fiyat 46.04 --hisse-sayisi 2794 \\
      --net-kar 9878 --favok 22100 --hasilat 224527 \\
      --ozkaynaklar 242571 --fin-borc 161900 --nakit 38145

Tüm finansal tutarlar Milyon TL, hisse sayısı Milyon adet cinsinden.
"""
    )

    p.add_argument("--hisse",          type=str,   help="Hisse kodu (ör: ASELS)")
    p.add_argument("--fiyat",          type=float, required=True,  help="Hisse fiyatı (TL)")
    p.add_argument("--hisse-sayisi",   type=float, dest="hisse_sayisi", help="Hisse sayısı (Milyon adet)")

    # Gelir tablosu
    p.add_argument("--net-kar",        type=float, dest="net_kar",   help="Net dönem kârı (Milyon TL)")
    p.add_argument("--ebit",           type=float,                   help="Esas Faaliyet Kârı / EBIT (Milyon TL)")
    p.add_argument("--favok",          type=float,                   help="FAVÖK / EBITDA (Milyon TL)")
    p.add_argument("--hasilat",        type=float,                   help="Hasılat / Ciro (Milyon TL)")

    # Bilanço
    p.add_argument("--ozkaynaklar",    type=float,                   help="Ana Ortaklığa ait özkaynaklar (Milyon TL)")
    p.add_argument("--fin-borc",       type=float, dest="fin_borc",  help="Toplam finansal borç (Milyon TL)")
    p.add_argument("--nakit",          type=float,                   help="Nakit ve nakit benzerleri (Milyon TL)")

    # Opsiyoneller
    p.add_argument("--temettu",        type=float,                   help="Brüt temettü (TL/hisse)")
    p.add_argument("--parasal-kayip",  type=float, dest="parasal_kayip",
                   help="TMS 29 parasal kayıp (Milyon TL, pozitif girin — net kâr düzeltmesi için)")

    return p.parse_args()


# ── Ana akış ──────────────────────────────────────────────────────────────────
def main():
    args = parse_args()
    sonuclar = hesapla(args)
    yazdir(args, sonuclar)


if __name__ == "__main__":
    main()
