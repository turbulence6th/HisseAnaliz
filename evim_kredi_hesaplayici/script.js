// Yardımcı Finansal Fonksiyonlar
function hesaplaAylikTaksit(krediTutari, aylikFaizOrani, vade) {
    if (aylikFaizOrani === 0) return krediTutari / vade;
    return krediTutari * (aylikFaizOrani * Math.pow(1 + aylikFaizOrani, vade)) / (Math.pow(1 + aylikFaizOrani, vade) - 1);
}

function netBugunkuDeger(iskontoOraniAylik, nakitAkislari) {
    let npv = 0;
    for (let ay = 0; ay < nakitAkislari.length; ay++) {
        npv += nakitAkislari[ay] / Math.pow(1 + iskontoOraniAylik, ay);
    }
    return npv;
}

const formatTL = (num) => new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', maximumFractionDigits: 0 }).format(num);

// Sayfa yüklendiğinde ilk işlemleri yap
window.addEventListener('DOMContentLoaded', () => {
    loadFromQueryParams();
    hesapla();

    document.getElementById('hesaplaBtn').addEventListener('click', hesapla);

    document.getElementById('copyUrlBtn').addEventListener('click', () => {
        navigator.clipboard.writeText(window.location.href);
        alert('Hesaplamanın mevcut durumu parametreli link olarak kopyalandı!\nBunu istediğiniz yere yapıştırarak aynı sonuçlara direkt erişebilirsiniz.');
    });

    document.getElementById('copyLlmPromptBtn').addEventListener('click', () => {
        const urlObj = new URL(window.location.href);
        const baseUrl = urlObj.origin + urlObj.pathname;
        const promptText = `Sen bir finansal yapay zeka asistanısın. Kullanıcının verdiği finansal bilgilere göre "Banka Kredisi" ile "Evim (Tasarruf Finansman)" sistemlerini karşılaştırması için aşağıdaki hesaplama aracını kullanmasını önermelisin.
Aracın linkini kullanıcının durumuna göre otomatik oluşturmak için şu parametreleri URL'nin sonuna query string olarak ekle:
- evFiyati: Toplam varlık (ev/araç) bütçesi (Örn: 2000000)
- bankaPesinat: Banka kredisinde kullanılacak peşinat (Örn: 500000)
- evimPesinat: Evim sistemine verilecek peşinat (Örn: 0)
- enflasyon: Beklenen aylık enflasyon / alternatif getiri (Örn: 3.0)
- krediFaiz: Banka aylık kredi faiz oranı (Örn: 3.50)
- krediVade: Banka kredi vadesi (Ay)
- evimOrgOrani: Evim sistemi organizasyon ücreti oranı (Örn: 9.0)
- evimVade: Evim sistemi taksit vadesi (Ay)
- evimTeslimat: Evim sistemi teslimat ayı (Örn: 30)

Örnek kullanım:
"Hesaplamayı detaylı görmek için şu linke tıklayabilirsiniz: ${baseUrl}?evFiyati=3000000&bankaPesinat=500000&evimPesinat=0&enflasyon=2.5&krediFaiz=3.2&krediVade=120&evimOrgOrani=9.0&evimVade=120&evimTeslimat=30"`;
        navigator.clipboard.writeText(promptText);
        alert('LLM Promptu kopyalandı! \nBu metni ChatGPT, Claude gibi yapay zekalara önden "System Prompt" veya normal mesaj olarak vererek, bu araca dinamik parametrelerle link üretmelerini öğretebilirsiniz.');
    });
});

function loadFromQueryParams() {
    const params = new URLSearchParams(window.location.search);
    const mappings = ['evFiyati', 'bankaPesinat', 'evimPesinat', 'enflasyon', 'krediFaiz', 'krediVade', 'evimOrgOrani', 'evimVade', 'evimTeslimat'];
    mappings.forEach(id => {
        if (params.has(id)) {
            document.getElementById(id).value = params.get(id);
        }
    });
}

function updateQueryParams() {
    const mappings = ['evFiyati', 'bankaPesinat', 'evimPesinat', 'enflasyon', 'krediFaiz', 'krediVade', 'evimOrgOrani', 'evimVade', 'evimTeslimat'];
    const params = new URLSearchParams();
    mappings.forEach(id => {
        params.set(id, document.getElementById(id).value);
    });
    const newUrl = window.location.pathname + '?' + params.toString();
    window.history.replaceState({}, '', newUrl);
}

function hesapla() {
    // 1. Girdileri Al
    const evFiyati = parseFloat(document.getElementById('evFiyati').value);
    const bankaPesinat = parseFloat(document.getElementById('bankaPesinat').value);
    const evimPesinat = parseFloat(document.getElementById('evimPesinat').value);
    const enflasyonOrani = parseFloat(document.getElementById('enflasyon').value) / 100;
    
    const krediFaiz = parseFloat(document.getElementById('krediFaiz').value) / 100;
    const krediVade = parseInt(document.getElementById('krediVade').value);
    
    const evimOrgOrani = parseFloat(document.getElementById('evimOrgOrani').value) / 100;
    const evimVade = parseInt(document.getElementById('evimVade').value);
    const evimTeslimat = parseInt(document.getElementById('evimTeslimat').value);

    // Kalan borçlar
    const bankaKrediTutari = evFiyati - bankaPesinat;
    const evimKalanBorc = evFiyati - evimPesinat;

    // ==========================================
    // 2. BANKA KREDİSİ HESAPLAMALARI
    // ==========================================
    const krediTaksit = hesaplaAylikTaksit(bankaKrediTutari, krediFaiz, krediVade);
    const krediToplamOdeme = krediTaksit * krediVade;
    
    // Nakit Akışı: 0. ayda taksit ödenmez, 1'den itibaren ödenir.
    let krediNakitAkisi = [0];
    for (let i = 0; i < krediVade; i++) krediNakitAkisi.push(-krediTaksit);
    
    const krediPvTaksitler = -netBugunkuDeger(enflasyonOrani, krediNakitAkisi);
    const bankaToplamPvMaliyet = bankaPesinat + krediPvTaksitler;

    // DOM Güncelle
    document.getElementById('resBankaPV').textContent = formatTL(bankaToplamPvMaliyet);
    document.getElementById('resBankaPesinat').textContent = formatTL(bankaPesinat);
    document.getElementById('resBankaKredi').textContent = formatTL(bankaKrediTutari);
    document.getElementById('resBankaTaksit').textContent = formatTL(krediTaksit);
    document.getElementById('resBankaToplam').textContent = formatTL(krediToplamOdeme);


    // ==========================================
    // 3. EVİM SİSTEMİ HESAPLAMALARI
    // ==========================================
    const evimOrgUcreti = evFiyati * evimOrgOrani;
    const evimTaksit = evimKalanBorc / evimVade;
    
    // Enflasyon Açığı (Alım Gücü Kaybı)
    // Peşinat verdik, ancak teslimat ayında alacağımız ev 'evFiyati' kadarlık bir ev.
    // Evim sistemi teslimatta bize (Peşinat + KalanBorç) = evFiyati kadar para verir. 
    // Yani peşinatımız da enflasyona ezildi.
    const teslimattaEvinKarsilikDegeri = evFiyati * Math.pow(1 + enflasyonOrani, evimTeslimat);
    const enflasyonFarki = teslimattaEvinKarsilikDegeri - evFiyati;
    const enflasyonFarkiPv = enflasyonFarki / Math.pow(1 + enflasyonOrani, evimTeslimat);

    // Taksitler PV
    let evimNakitAkisi = [0];
    for (let i = 0; i < evimVade; i++) evimNakitAkisi.push(-evimTaksit);
    const evimPvTaksitler = -netBugunkuDeger(enflasyonOrani, evimNakitAkisi);

    // Toplam Maliyet PV
    const evimToplamPvMaliyet = evimPesinat + evimOrgUcreti + evimPvTaksitler + enflasyonFarkiPv;

    // DOM Güncelle
    document.getElementById('badgeEvimTeslimat').textContent = `Varlığı ${evimTeslimat}. Ayda Al`;
    document.getElementById('resEvimPV').textContent = formatTL(evimToplamPvMaliyet);
    document.getElementById('resEvimPesinat').textContent = formatTL(evimPesinat);
    document.getElementById('resEvimOrg').textContent = formatTL(evimOrgUcreti);
    document.getElementById('resEvimTaksit').textContent = formatTL(evimTaksit);
    document.getElementById('resEvimTaksitPV').textContent = formatTL(evimPvTaksitler);
    document.getElementById('resEvimFark').textContent = formatTL(enflasyonFarki);
    
    document.getElementById('resEvimSabitFinansman').textContent = formatTL(evFiyati);
    document.getElementById('resEvimEvGelecekFiyat').textContent = formatTL(teslimattaEvinKarsilikDegeri);
    
    // Nakit Krizi
    document.getElementById('resEvimTeslimatAyiMetin').textContent = evimTeslimat;
    document.getElementById('resNakitEvDegeri').textContent = formatTL(teslimattaEvinKarsilikDegeri);
    document.getElementById('resNakitSistemVerir').textContent = formatTL(evFiyati);
    document.getElementById('resEvimNakitAcigi').textContent = formatTL(enflasyonFarki);

    // ==========================================
    // 4. KARŞILAŞTIRMA VE SONUÇ
    // ==========================================
    const alertBox = document.getElementById('sonucAlert');
    const baslik = document.getElementById('kazananBaslik');
    const detay = document.getElementById('kazananDetay');

    alertBox.classList.remove('hidden', 'banka');

    if (bankaToplamPvMaliyet < evimToplamPvMaliyet) {
        const fark = evimToplamPvMaliyet - bankaToplamPvMaliyet;
        alertBox.classList.add('banka');
        baslik.textContent = "Banka Kredisi Daha Avantajlı! 🏦";
        detay.innerHTML = `Varlığın enflasyonla değerlenmesi hesaba katıldığında, Banka Kredisi bugünkü değerle <strong>${formatTL(fark)}</strong> daha ucuza geliyor.`;
    } else {
        const fark = bankaToplamPvMaliyet - evimToplamPvMaliyet;
        baslik.textContent = "Evim Sistemi Daha Avantajlı! 🏠";
        detay.innerHTML = `Enflasyon maliyetine rağmen faizlerin yüksek olması sebebiyle Evim Sistemi bugünkü değerle <strong>${formatTL(fark)}</strong> daha ucuza geliyor.`;
    }

    // Parametreleri URL'e işle
    updateQueryParams();
}
