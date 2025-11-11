# Dizin Genel Bakışı

Bu dizin, bir hisse senedi portföyünü yönetmek için kişisel bir bilgi tabanı ve karar alma çerçevesi olarak hizmet vermektedir. Bu, yatırım stratejilerini belgelemeye, bireysel hisseler üzerinde derinlemesine analiz yapmaya ve şirketlerin finansal raporları ile piyasa koşullarına dayalı temel analizlere göre portföy değişikliklerini izlemeye odaklanan bir kod projesi değildir.

Temel felsefe, sermayeyi düşük performans gösteren varlıklardan daha güçlü temellere ve daha net büyüme hikayelerine sahip olanlara döndürmeyi içeren "Dinamik Portföy Yönetimi"dir.

# Anahtar Dosyalar ve Yapı

*   **`GENEL_STRATEJI.md`**: Bu ana belgedir. "Çekirdek ve Uydu" stratejisi de dahil olmak üzere üst düzey yatırım felsefesini içerir. Portföydeki her hisse için gerçek zamanlı bir karar (AL/SAT/TUT) sunar ve bu kararların gerekçelerini özetler. Bu dosya, portföyün durumu için birincil kontrol panelidir.

*   **`hisse-analiz/`**: Bu dizin, şimdiye kadar analiz edilen veya tutulan her hisse için ayrı Markdown dosyaları içerir.
    *   **`hisse-analiz/{HİSSE_KODU}.md`** (ör. `AEFES.md`, `TCELL.md`): Her dosya, tek bir hisse için ayrıntılı bir yatırım tezidir. İçeriği:
        *   Temel yatırım tezi ("neden").
        *   Son çeyrek finansal raporlarından notlar.
        *   Potansiyel pozitif katalizörler ve riskler.

*   **`siyasi-analiz/`**: Türkiye'deki siyasi konjonktürün yatırım kararları üzerindeki etkisini analiz etmek için kullanılır. Bu dizin, takip edilen siyasi aktörlerin veya konuların analizlerini içerir.
    *   **`siyasi-analiz/{AKTÖR_ADI}.md`**: Belirli bir siyasi aktörün veya konunun periyodik analizini ve yorumunu içerir.

*   **`hisse_proxy.py`**: Yahoo Finance'ten son 1 yıllık günlük hisse senedi verilerini hızlıca çekmek için bir komut satırı yardımcı programıdır. Bu, terminalden ayrılmadan hızlı teknik kontroller ve veri alımı için kullanılır.

*   **`tweet_cekme.py`**: Belirtilen Twitter kullanıcılarının son tweet'lerini çeken bir komut satırı yardımcı programıdır. Siyasi konjonktür takibi için veri toplama amacıyla kullanılır.

*   **`ARBITRAJ_HS_YOGUN_FONLAR.md`** & **`EUROBOND_FONLARI.md`**: Bunlar, öncelikli olarak yönetim ücretleri ve portföy içindeki stratejik uyuma odaklanarak farklı yatırım fonu türlerini karşılaştıran özel araştırma notlarıdır.

# Kullanım ve İş Akışı

İş akışı veriye dayalı ve disiplinlidir:

1.  **Analiz (Temel):** Yatırım kararları, üç aylık ve yıllık finansal raporların (`Faaliyet Raporu`) derinlemesine incelenmesine dayanır.
2.  **Analiz (Siyasi):** Türkiye'deki siyasi gelişmeler, yatırım ortamını önemli ölçüde etkileyebilir. Bu nedenle, `tweet_cekme.py` gibi araçlar kullanılarak takip edilen siyasi aktörlerin söylemleri periyodik olarak analiz edilir ve `siyasi-analiz/` dizininde belgelenir.
3.  **Belgeleme (Hisse):** Her hisse senedi için yapılan temel analiz, `hisse-analiz/` dizinindeki kendi özel dosyasına belgelenir.
4.  **Strateji Güncellemesi:** Temel ve siyasi analizlere dayanarak, ana `GENEL_STRATEJI.md` dosyası yeni kararlar (AL, SAT, TUT) ve gerekçeleri ile güncellenir.
5.  **Uygulama:** İşlemler, güncellenmiş stratejiye göre yapılır.
6.  **Veri Alma (Teknik):** Hızlı fiyat ve hacim kontrolleri için `hisse_proxy.py` betiği kullanılır. Bu betikten gelen anlık veriler, `hisse-analiz/` klasöründeki ilgili hissenin `.md` dosyasında belirtilen kademeli alım/satım seviyelerinin yeniden değerlendirilmesi ve güncellenmesi için temel oluşturur.

### `hisse_proxy.py` Nasıl Kullanılır:

Borsa İstanbul'daki bir hisse senedi için en son 1 yıllık verileri almak için:

```bash
python hisse_proxy.py <HİSSE_KODU>
```

**Örnek:**

```bash
python hisse_proxy.py TUPRS
```

Betik, standart çıktıya hissenin grafik verilerini içeren bir JSON nesnesi yazdıracaktır.

### `tweet_cekme.py` Nasıl Kullanılır:

Bir veya daha fazla Twitter kullanıcısının son tweet'lerini çekmek için:

```bash
python tweet_cekme.py <KULLANICI_ADI_1> <KULLANICI_ADI_2>
```

**Örnek:**

```bash
python tweet_cekme.py samiltayyar27 elonmusk
```

Betik, tweet'leri standart çıktıya yazdıracaktır. Bu çıktının analiz edilerek ilgili `siyasi-analiz/{AKTÖR_ADI}.md` dosyasına işlenmesi beklenir.

### `efektif_faiz_hesapla.py` Nasıl Kullanılır:

Bir kredi veya taksitli alım için efektif aylık faiz oranını hesaplamak amacıyla kullanılır. Kredinin ödemesiz (erteleme) dönemi varsa bu da hesaba katılabilir. Gerekli parametreler komut satırı argümanları olarak sağlanmalıdır.

```bash
python efektif_faiz_hesapla.py --ana-para <TUTAR> --taksit-sayisi <AY> --aylik-odeme <TUTAR> [--erteleme <AY>]
```

**Örnekler:**

```bash
# Standart kredi
python efektif_faiz_hesapla.py --ana-para 100000 --taksit-sayisi 12 --aylik-odeme 9500.50

# 3 ay ertelemeli kredi
python efektif_faiz_hesapla.py --ana-para 100000 --taksit-sayisi 12 --aylik-odeme 10500 --erteleme 3
```

Betik, hesaplanan efektif aylık ve yıllık faiz oranlarını standart çıktıya yazdıracaktır.

### `taksit_bugunku_deger_hesapla.py` Nasıl Kullanılır:

Taksitli bir alışverişin bugünkü peşin değerini, yani bugünkü nakit fiyatının ne olması gerektiğini hesaplamak için kullanılır. Aylık faiz oranı olarak, paranın alternatif yatırım (örneğin mevduat faizi) getirisini veya aylık enflasyon oranını girebilirsiniz.

```bash
python taksit_bugunku_deger_hesapla.py --toplam-odeme <TUTAR> --taksit-sayisi <AY> --aylik-faiz <YÜZDE>
```

**Örnek:**

```bash
python taksit_bugunku_deger_hesapla.py --toplam-odeme 15000 --taksit-sayisi 6 --aylik-faiz 2.5
```

Betik, alışverişin bugünkü peşin değerini standart çıktıya yazdıracaktır.

### `kap_rapor_indir.py` Nasıl Kullanılır:

Bu komut satırı yardımcı programı, Kamuyu Aydınlatma Platformu (KAP) ve TEFAS üzerinden birkaç temel işlemi gerçekleştirmek için kullanılır:

1.  **Finansal Rapor İndirme:** Belirtilen bir BIST şirketinin en güncel dönemsel finansal raporunu (PDF formatında) indirir.
2.  **Fon Yönetim Ücreti Öğrenme:** Belirtilen bir yatırım fonunun yıllık yönetim ücreti oranını çeker.
3.  **Portföy Dağılım Raporu İndirme:** Belirtilen bir veya daha fazla yatırım fonunun en güncel portföy dağılım raporunu (PDF veya XLSX formatında) indirir.
4.  **Varlık Grubuna Göre Fon Listeleme:** Belirtilen bir varlık grubundaki (örn: Hisse Senedi, Eurobond) fonları TEFAS'tan çeker ve getirilerini listeler.

#### Finansal Rapor İndirme:

```bash
python kap_rapor_indir.py rapor <HİSSE_KODU>
```

**Örnek:**

```bash
python kap_rapor_indir.py rapor SOKM
```

Betik, raporu `finansal-raporlar/{YIL}{ÇEYREK}` dizinine `{HİSSE_KODU}_Finansal_Rapor_{TARİH}.pdf` adıyla kaydeder.

#### Fon Yönetim Ücreti Öğrenme:

```bash
python kap_rapor_indir.py fon-ucret <FON_KODU>
```

**Örnek:**

```bash
python kap_rapor_indir.py fon-ucret TZL
```

Betik, ilgili fonun yıllık yönetim ücretini standart çıktıya yazdıracaktır.

#### Portföy Dağılım Raporu İndirme:

```bash
python kap_rapor_indir.py fon-rapor <FON_KODU_1> <FON_KODU_2> ...
```

**Örnek:**

```bash
python kap_rapor_indir.py fon-rapor TZL IIH
```

Betik, raporları `fon-raporlari/{YIL}-{AY}` dizinine `{FON_KODU}_Portfoy_Dagilim_{TARIH}.pdf` veya `.xlsx` adıyla kaydeder.

#### Varlık Grubuna Göre Fon Listeleme:

```bash
python kap_rapor_indir.py fon-liste <VARLIK_GRUBU>
```

**Örnek:**

```bash
python kap_rapor_indir.py fon-liste "Hisse Senedi"
```

Betik, ilgili fonları ve getiri bilgilerini standart çıktıya yazdıracaktır.

# Gemini'ye Eklenen Hafıza Kuralları

*   Finansal rapor analizi istendiğinde, raporu `GENEL_STRATEJI.md` belgesine göre değerlendir ve ardından ilgili hissenin `hisse-analiz` klasöründeki `.md` dosyasını güncelle.
