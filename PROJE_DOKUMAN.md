# KYO 2.0 — Proje Dokümantasyonu

> **Tek dosya SPA** (`kyo20.html`) — Tailwind CSS, Chart.js 4.4.3, Lucide ikonlar, Supabase auth.  
> Tüm veriler **localStorage**'da tutulur. Python proxy (`proxy.py`, port 8765) gerçek zamanlı hisse fiyatları için CORS katmanı sağlar.

---

## Genel Yapı

| Bileşen | Açıklama |
|---|---|
| `kyo20.html` | Tüm uygulama (HTML + CSS + JS, tek dosya) |
| `proxy.py` | Python HTTP sunucusu; Yahoo Finance CORS proxy + statik dosya sunumu |
| `localStorage` | Her sayfanın verisi ayrı anahtarla saklanır |
| `paramla-history-v1` | PARAMLA anlık geçmişi (zaman serisi) |
| `paramla-daily-log` | PARAMLA günlük portföy değerleri (01.06.2026'dan) |
| `kasa-data` | KASA tablo verisi |
| `hs-data` | HS (portföy) tablo verisi |
| `ort-data` | ORTAKLIK tablo verisi |
| `perf-data` | PERFORMANS tablo verisi |

### Sayfa Navigasyonu
Sol kenar çubuğundaki (hamburger menü) butonlar ile sayfalar arası geçiş yapılır. Aktif sayfanın `<section id="page-xxx">` elementi görünür, diğerleri gizlenir. Bazı başlık butonları (Grafik, Veri, Anlık Bakiye kartı) sadece ilgili sayfa aktifken belirir.

---

## 1. KASA Sayfası

### Amaç
Nakit akışı takibi. Her satır bir işlemi temsil eder.

### Sütunlar
| # | Sütun | Tür | Açıklama |
|---|---|---|---|
| 1 | TARİH | Manuel | İşlem tarihi (GG.AA.YYYY) |
| 2 | TUTAR | Manuel | İşlem tutarı (+/-) |
| 3 | İŞLEM | Manuel | İşlem açıklaması |
| 4 | KİŞİ | Manuel | İlgili kişi |
| 5 | BAKİYE | **Otomatik** | Kümülatif bakiye |

### BAKİYE Hesabı
```
BAKİYE[i] = TUTAR[i] + BAKİYE[i-1]
```
TUTAR boşsa o satırın BAKİYE'si de sıfırlanır. Tablonun herhangi bir satırı değiştiğinde o satırdan itibaren tüm BAKİYE sütunu yeniden hesaplanır.

### Anlık Bakiye Kartı (Header)
Tablodaki **son dolu BAKİYE** hücresi, üst başlıkta "KYO 2.0" yazısının sağında **cyan neon kart** içinde her zaman görünür. Her `kasaRecalcBalance()` çağrısında güncellenir.

### Özellikler
- **100 başlangıç satırı** (localStorage'dan yüklenmezse)
- Klavye navigasyonu: `←↑↓→`, `Enter/F2` (düzenleme), `Tab` (sağa geç), `Esc` (iptal)
- Hücre seçimi: `Shift+Arrow` ile blok seçim, satır başına tıklayarak tüm satır seçimi
- Kopyala/Yapıştır: `Ctrl+C`, `Ctrl+X`, `Ctrl+V` (Excel uyumlu)
- Sağ tıklama menüsü: Satır Ekle (üst/alt), Satır Sil
- Sayı otomatik formatı: hücre terk edildiğinde Türk formatına döner (`1.000,00`)
- Tarihler (`GG.AA.YYYY`) formatlanmaz
- CSV dışa/içe aktarım butonu
- Kaydet butonu → `localStorage['kasa-data']`

---

## 2. HS Sayfası (Portföy Defteri)

### Amaç
Hisse alım/satım kayıtlarının tutulması. Kâr/zarar ve maliyet otomatik hesaplanır.

### Sütunlar
| # | Sütun | Tür | Açıklama |
|---|---|---|---|
| 1 | ALİŞ TARİH | Manuel | Alış tarihi |
| 2 | HİSSE | Manuel | Hisse kodu (ör. THYAO) |
| 3 | ALİŞ FİYATI | Manuel | Alış fiyatı (TL) |
| 4 | ADET | Manuel | Adet |
| 5 | MALİYET | **Otomatik** | `ALİŞ FİYATI × ADET` |
| 6 | SATIŞ TARİH | Manuel | Satış tarihi (dolu ise satılmış sayılır) |
| 7 | SATIŞ FİYATI | Manuel | Satış fiyatı (TL) |
| 8 | SATIŞ TUTAR | **Otomatik** | `SATIŞ FİYATI × ADET` |
| 9 | KÂR/ZARAR | **Otomatik** | `SATIŞ TUTAR − MALİYET` |
| 10 | KÂR % | **Otomatik** | `(KÂR / MALİYET) × 100` |

### Portföyde Sayılma Koşulu (PARAMLA için)
Bir satır, PARAMLA'ya **aktif pozisyon** olarak yansır ancak:
- HİSSE sütunu dolu
- ADET > 0
- SATIŞ TARİH **boş** ve SATIŞ FİYATI = 0 ise

### Grafik Butonu
Sağ üstte belirir. İki grafik gösterir:
- **Pasta (Anlık Dağılım)**: Açık pozisyonların maliyet dağılımı
- **Zaman Serisi**: Alış/satış tarihlerine göre kâr/zarar timeline

### Özellikler
- **30 başlangıç satırı**
- KASA ile aynı klavye/kopyala/menü özellikleri
- Sütun başlığına tıklayarak sıralama (SEMBOL, ŞİRKET, FİYAT, DEĞİŞİM, DEĞ.%, HACİM)
- Kaydet butonu → `localStorage['hs-data']`

---

## 3. PARAMLA Sayfası (Canlı Portföy)

### Amaç
HS tablosundaki **açık pozisyonları** Yahoo Finance'den anlık fiyatla çekerek portföy değerini hesaplar.

### Çalışma Akışı
```
1. HS tablosundan sembol + adet listesi alınır (paramlaGetHoldings)
2. Yahoo Finance API'ye sorgu atılır (proxy üzerinden)
3. Her hisse: anlık değer = fiyat × adet
4. Toplam = tüm hisse değerlerinin toplamı
5. Pasta grafik + Portföy değer grafiği güncellenir
6. 30 sn'de bir otomatik tekrarlanır
```

### Bileşenler
| Bileşen | Açıklama |
|---|---|
| **Anlık Dağılım** (pasta) | Hangi hissede ne kadar para var, % oran |
| **Portföy Değer Grafiği** | 01.06.2026'dan itibaren her gün için kayıtlı değer (günlük log) |
| **Alt tablo** | Her hissenin anlık fiyatı, değeri, portföy oranı |
| **"Veri" butonu** | Günlük portföy değer tablosunu açar/kapatır |

### Günlük Log Mantığı
- Veri: `localStorage['paramla-daily-log']` → `[{ date: "DD.MM.YYYY", value: sayı|null }]`
- Sayfa her açıldığında 01.06.2026'dan bugüne eksik tarihler otomatik eklenir (değer: `null`)
- Her gün saat **19:00'dan sonra** PARAMLA yenilendiğinde o günün değeri doldurulur (yalnızca bir kez)
- Grafik bu log'dan oluşturulur; değeri `null` olan günler grafikte atlanır

### Başlık Butonları
| Buton | Açıklama |
|---|---|
| **Veri** | Grafik alanını gizler, günlük log tablosunu gösterir |
| **GÜNLÜK / HAFTALIK / YILLIK** | Grafik zaman aralığı (GÜNLÜK = günlük log kullanır) |
| **Yenile** | Manuel olarak fiyatları günceller |

---

## 4. HİSSE Sayfası (BIST Takip)

### Amaç
Tüm BIST hisselerini anlık olarak listeler ve takip eder.

### Sütunlar
`#, SEMBOL, ŞİRKET, FİYAT (₺), DEĞİŞİM, DEĞ.%, HACİM, SAAT`

### Çalışma Akışı
```
1. BIST_ALL listesinden tüm semboller alınır (~500+ hisse)
2. Yahoo Finance'ye toplu sorgu atılır (.IS eki eklenir)
3. Sonuçlar tabloya işlenir
4. Progress bar yükleme sürecini gösterir
```

### Özellikler
- Sütun başlığına tıklayarak artan/azalan sıralama
- Seçilen hisse HS tablosuna doğrudan eklenebilir (planlanan)
- Fiyat değişimi renkli gösterilir: yeşil (artış), kırmızı (düşüş)

---

## 5. UYARI Sayfası (Teknik Analiz)

### Amaç
Tüm BIST hisselerini teknik indikatörler açısından tarayarak alım/satım sinyali veren hisseleri listeler.

### Filtreler
| Filtre | İndikatör | Sinyal Mantığı |
|---|---|---|
| **MA 20/200** | Hareketli ortalama | Fiyat MA20 > MA200 ise yükseliş trendi |
| **MACD** | MACD çizgisi | MACD > sinyal çizgisi ise alım sinyali |
| **RSI** | RSI (14) | RSI < 30: aşırı satım, RSI > 70: aşırı alım |
| **Bollinger** | Bollinger Bantları | Fiyat alt banda yakınsa alım, üst banda yakınsa satım |
| **Hacim** | Günlük hacim | Ortalama üzeri hacim = ilgi artışı |

### Çalışma Akışı
```
1. Sayfa açıldığında uyariOnActivate() çalışır
2. Yahoo Finance'den geçmiş fiyat verisi çekilir (60 günlük)
3. İndikatörler hesaplanır
4. Sinyal veren hisseler kart formatında listelenir
5. Filtre butonları anlık olarak kartları filtreler
```

---

## 6. ORTAKLIK Sayfası

### Amaç
Ortaklara yapılan katkı payı ödemelerini ve kümülatif sermaye birikimini takip eder.

### Sütunlar
| Sütun | Tür | Açıklama |
|---|---|---|
| TARİH | Manuel | Kayıt tarihi |
| KGS | Manuel | KGS katkısı |
| TheVaner | Manuel | TheVaner katkısı |
| MERTCAN | Manuel | MERTCAN katkısı |
| MERT CAN | Manuel | MERT CAN katkısı |
| ASİYE | Manuel | ASİYE katkısı |
| ERKİN | Manuel | ERKİN katkısı |
| TUTAR | **Otomatik** | O satırdaki toplam katkı |
| SERMAYE | **Otomatik** | Kümülatif toplam sermaye |

### Hesaplar
```
TUTAR[i]   = KGS[i] + TheVaner[i] + MERTCAN[i] + ... (tüm ortaklar)
SERMAYE[i] = TUTAR[i] + SERMAYE[i-1]   (kümülatif)
```

### Sermaye Kartı (Header)
ORTAKLIK sayfasındayken Grafik butonunun sağında **mor neon kart** içinde tablodaki **son dolu SERMAYE** değeri gösterilir. Her hesaplama sonrası güncellenir.

### Grafik Butonu
Ortaklık grafiğini gösterir: her ortağın katkılarını zaman içinde karşılaştıran bar/çizgi grafik.

### Özellikler
- Yeni ortak sütunu eklenebilir (dinamik sütun)
- KASA ile aynı klavye/kopyala/menü özellikleri
- Kaydet → `localStorage['ort-data']`

---

## 7. PERFORMANS Sayfası

### Amaç
Fonun **hisse değerini** (birim fon değeri) günlük olarak takip eder.

### Sütunlar
| # | Sütun | Tür | Açıklama |
|---|---|---|---|
| 1 | TARİH | Otomatik/Manuel | 01.06.2026'dan itibaren her gün |
| 2 | HİSSE DEĞERİ | Otomatik/Manuel | Günlük fon birim değeri |
| 3 | GÜNLÜK | Manuel | Günlük değişim % |
| 4 | HAFTALIK | Manuel | Haftalık değişim % |
| 5 | AYLIK | Manuel | Aylık değişim % |
| 6 | YILLIK | Manuel | Yıllık değişim % |

### HİSSE DEĞERİ Hesabı (19:00 Otomatiği)
Her gün saat 19:00'dan sonra PARAMLA sayfası yenilendiğinde:
```
HİSSE DEĞERİ = (Kasa Son BAKİYE + PARAMLA Portföy Toplamı) / Ortaklık Son SERMAYE
```
- Hesap yalnızca o günün satırı **boşsa** yapılır (üzerine yazılmaz)
- Sonuç 4 ondalık basamakla kaydedilir
- `perfSave()` ile localStorage'a otomatik yazılır

### Tarih Otomatiği
- Sayfa açılışında `perfAutoFillAndExtend()` çalışır
- 01.06.2026'dan itibaren **30 başlangıç satırının** boş TARİH hücreleri doldurulur
- Bugünün tarihi son kayıtlı tarihten sonraysa aradaki her gün için yeni satır eklenir

### Grafik Butonu
Sağ üstte belirir. İki grafik gösterir:
- **Hisse Değeri Grafiği** (çizgi): Zaman içinde fon birim değeri
- **Performans Değişimi** (bar): Günlük/Haftalık/Aylık/Yıllık % değişim

---

## Ortak Özellikler (Tüm Tablolar)

| Özellik | Kısayol |
|---|---|
| Hücre düzenleme | `Enter` veya `F2` veya herhangi bir karakter |
| Düzenlemeyi bitir | `Enter`, `Tab`, `Escape` veya dışarı tıkla |
| Navigasyon | `←↑↓→` ok tuşları |
| Blok seçim | `Shift + ←↑↓→` |
| Kopyala | `Ctrl+C` |
| Kes | `Ctrl+X` |
| Yapıştır | `Ctrl+V` (Excel'den de çalışır) |
| Tümünü seç | `Ctrl+A` |
| Sağ tıklama | Satır ekle (üst/alt), satır sil |
| Sayı formatı | Hücre terk edilince `1.000,00` formatına dönüşür |
| Tarih koruması | `GG.AA.YYYY` formatı sayıya dönüştürülmez |

---

## Proxy Sunucusu (`proxy.py`)

| URL | Davranış |
|---|---|
| `http://127.0.0.1:8765/` | `kyo20.html` dosyasını sunar |
| `http://127.0.0.1:8765/kyo20.html` | `kyo20.html` dosyasını sunar |
| `http://127.0.0.1:8765/https://query1.finance.yahoo.com/...` | Yahoo Finance'e proxy geçiş (CORS bypass) |

Sunucu başlatma:
```bash
python proxy.py
```

---

## Veri Akışı Özeti

```
HS Tablosu (alım/satım kayıtları)
    │
    ├──► PARAMLA (anlık fiyat × adet = portföy değeri)
    │         │
    │         ├──► Günlük Log (19:00'da kaydedilir)
    │         │
    │         └──► PERFORMANS HİSSE DEĞERİ hesabına katılır
    │
KASA Tablosu (nakit bakiye)
    │
    ├──► Header "Anlık Bakiye" kartı
    └──► PERFORMANS HİSSE DEĞERİ hesabına katılır

ORTAKLIK Tablosu (sermaye birikimi)
    │
    ├──► Header "Sermaye" kartı (ortaklik sayfasında)
    └──► PERFORMANS HİSSE DEĞERİ için bölen (SERMAYE)

PERFORMANS = (Kasa BAKİYE + PARAMLA Toplam) / Ortaklık SERMAYE
```
