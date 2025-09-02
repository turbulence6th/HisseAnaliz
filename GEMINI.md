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
        *   Bir işlem günlüğü (`İşlem Kayıt Defteri`).

*   **`hisse_proxy.py`**: Yahoo Finance'ten son 1 yıllık günlük hisse senedi verilerini hızlıca çekmek için bir komut satırı yardımcı programıdır. Bu, terminalden ayrılmadan hızlı teknik kontroller ve veri alımı için kullanılır.

*   **`ARBITRAJ_HS_YOGUN_FONLAR.md`** & **`EUROBOND_FONLARI.md`**: Bunlar, öncelikli olarak yönetim ücretleri ve portföy içindeki stratejik uyuma odaklanarak farklı yatırım fonu türlerini karşılaştıran özel araştırma notlarıdır.

# Kullanım ve İş Akışı

İş akışı veriye dayalı ve disiplinlidir:

1.  **Analiz:** Yatırım kararları, üç aylık ve yıllık finansal raporların (`Faaliyet Raporu`) derinlemesine incelenmesine dayanır.
2.  **Belgeleme:** Her hisse senedi için yapılan analiz, `hisse-analiz/` dizinindeki kendi özel dosyasına belgelenir.
3.  **Strateji Güncellemesi:** Analize dayanarak, ana `GENEL_STRATEJI.md` dosyası yeni karar (AL, SAT, TUT) ve gerekçesi ile güncellenir.
4.  **Uygulama:** İşlemler, güncellenmiş stratejiye göre yapılır. İşlem daha sonra ilgili hissenin `.md` dosyasına kaydedilir.
5.  **Veri Alma:** Hızlı fiyat ve hacim kontrolleri için `hisse_proxy.py` betiği kullanılır. Bu betikten gelen anlık veriler, `hisse-analiz/` klasöründeki ilgili hissenin `.md` dosyasında belirtilen kademeli alım/satım seviyelerinin yeniden değerlendirilmesi ve güncellenmesi için temel oluşturur.

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