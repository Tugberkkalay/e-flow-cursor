# e-flow-cursor - İK Rapor Aracı

`BISVM-SQL2019` sunucusuna **kendi bilgisayarınızdan, Windows kimlik doğrulaması (Integrated Security)** ile bağlanıp:

1. tüm veritabanlarının **şema analizini** (tablolar, kolonlar, PK/FK ilişkileri, indeksler, view/prosedürler, İK ile ilgili aday tablolar),
2. seçili tabloların **veri profilini** (boş oranı, tekil değer, min/max, en sık değerler),
3. `raporlar/*.sql` dosyalarından **biçimli Excel raporlarını**

üreten Python aracı. Hiçbir veri bilgisayarınızın dışına çıkmaz.

## Gereksinimler

- Windows, şirket ağı/VPN erişimi ve SQL Server'da yetkili Windows hesabı
- Python 3.11+ (https://www.python.org/downloads/ — kurulumda "Add to PATH" işaretli)
- **ODBC Driver 17 veya 18 for SQL Server** (VS Code mssql / SSMS kuruluysa genellikle vardır):
  https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server

## Hızlı başlangıç

```bat
git clone <bu repo>
cd e-flow-cursor
calistir.bat
```

`calistir.bat` sanal ortamı kurar, bağımlılıkları yükler ve bir menü açar. Komut satırından da çalıştırılabilir:

```bat
calistir.bat baglanti_testi                 :: 1) bağlantıyı doğrula
calistir.bat sema_analizi                   :: 2) cikti\sema_analizi_*.xlsx
calistir.bat sema_analizi -d EFLOW          ::    sadece bir veritabanı
calistir.bat veri_profili                   :: 3) en büyük 40 tablo -> cikti\veri_profili_*.xlsx
calistir.bat veri_profili -t EFLOW.dbo.Personel -t EFLOW.dbo.Izin
calistir.bat rapor_uret --liste             :: 4) tanımlı raporlar
calistir.bat rapor_uret                     ::    hazır raporların hepsi -> cikti\<rapor>_*.xlsx
calistir.bat rapor_uret izin_yuku_raporu    ::    tek rapor
calistir.bat rapor_uret --tek-dosya         ::    hepsi tek Excel, sayfa sayfa
calistir.bat sablon_incele C:\Raporlar      :: 5) şifreli şablonların yapısını çıkar (parola sorar)
```

Ayarlar `ayarlar.toml` dosyasında: sunucu, varsayılan veritabanı, taranacak veritabanları, rapor parametreleri
(`baslangic_tarihi`, `bitis_tarihi`, `donem_yil`).

## Çalışma akışı (rapor SQL'lerinin hazırlanması)

Şablon Excel dosyaları parola korumalı olduğu ve veritabanına dışarıdan erişim olmadığı için raporlar adım adım hazırlanır:

1. **İK verisini bul** - VS Code (mssql eklentisi) veya SSMS'te sunucuya bağlıyken `sql/01_ik_tablo_arama.sql` betiğini
   çalıştırın. Tüm veritabanlarını tarar ve İK anahtar kelimeleriyle eşleşen tabloları listeler. Sonuç ızgarasında
   sağ tık → **Save as Excel** ile kaydedip paylaşın.
2. **Şema analizi** - İK verisinin olduğu veritabanı seçiliyken `sql/02_sema_analizi.sql` betiğini çalıştırın ve 5 sonucu
   Excel olarak kaydedin (ya da Python ile `calistir.bat sema_analizi -d <VT>`; tek dosyada tüm sayfaları üretir).
   `sql/03_rapor_nesnesi_arama.sql` mevcut rapor view/prosedürlerini bulur; varsa raporlar doğrudan bunlardan türetilir.
3. **Şablon inceleme** - `calistir.bat sablon_incele <şablon klasörü>`. Parola yalnızca yerelde kullanılır;
   üretilen `cikti\sablon_ozeti_*.xlsx` yalnızca sayfa adları, kolon başlıkları ve veri tiplerini içerir (kişisel veri yok).
   Bu dosyayı da paylaşın.
4. Bu çıktılara göre `raporlar/*.sql` dosyaları doldurulur ve `-- durum: hazir` yapılır; sonra `rapor_uret` ile Excel'ler üretilir.

> `ayarlar.toml → [baglanti].sunucu` değerini bağlandığınız sunucu adıyla (örn. `BISVM-SQL2019` veya `CLOUDPRODUCTS`) eşleyin.

## Rapor SQL dosyası biçimi

```sql
-- rapor: İzin Yükü Raporu          (Excel başlığı)
-- veritabani: EFLOW                 (boş ise ayarlar.toml'daki veritabanı)
-- durum: hazir                      (taslak olanlar çalıştırılmaz)
-- sayfa: Detay                      (birden çok sayfa için tekrar edilir)
SELECT ... FROM ... WHERE Tarih BETWEEN {baslangic_tarihi} AND {bitis_tarihi};
-- sayfa: Ozet
SELECT ... ;
```

`{parametre}` yer tutucuları `ayarlar.toml → [raporlar.parametreler]` bölümünden doldurulur (metinler otomatik tırnaklanır).

## Tanımlı raporlar

| Dosya | Rapor | Durum |
|---|---|---|
| `ornek_sunucu_ozeti` | Örnek - Sunucu ve Tablo Özeti | hazır (doğrulama amaçlı) |
| `ucret_tarihcesi_raporu` | Ücret Tarihçesi Raporu | taslak |
| `performans_durum_raporu` | Performans Durum Raporu | taslak |
| `perakende_raporu` | Perakende Raporu | taslak |
| `organizasyon_degisikligi_tarihcesi_raporu` | Organizasyon Değişikliği Tarihçesi Raporu | taslak |
| `onay_bekleyen_izin_listesi` | Onay Bekleyen İzin Listesi | taslak |
| `kullanilan_izin_raporu` | Kullanılan İzin Raporu (Yıllık, Diğer, Saatlik) | taslak |
| `izin_yuku_raporu` | İzin Yükü Raporu | taslak |
| `fiili_rapor_ucretsiz` | Fiili Rapor - Ücretsiz | taslak |
| `fiili_rapor_ucretli` | Fiili Rapor - Ücretli | taslak |
| `cikis_raporu_ayrilan_personel` | Çıkış Raporu (Ayrılan Personel) | taslak |
| `case_raporu` | Case Raporu | taslak |
| `calisan_iletisim_bilgileri` | Çalışan İletişim Bilgileri | taslak |
| `belirli_sureli_takip_raporu` | Belirli Süreli Takip Raporu | taslak |
| `bagli_yonetici_raporu` | Bağlı Yönetici Raporu | taslak |

## Güvenlik notları

- Parola/kimlik bilgisi saklanmaz; Integrated Security ile mevcut Windows oturumunuz kullanılır.
- `cikti/` klasörü, `*.xlsx` dosyaları ve şifresi çözülmüş şablonlar `.gitignore` ile repo dışında tutulur.
- Araç yalnızca `SELECT` sorguları çalıştırır; veritabanında değişiklik yapmaz.
