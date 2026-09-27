-- rapor: Organizasyon Değişikliği Tarihçesi Raporu
-- veritabani:
-- durum: taslak
-- aciklama: Birim, pozisyon, unvan ve yönetici değişiklikleri tarihçesi.
--
-- Bu rapor şeması netleşince doldurulacaktır. Kaynak tablolar sema_analizi çıktısındaki
-- "IK_Aday_Tablolar" sayfasından, kolon başlıkları ise sablon_incele çıktısından alınacaktır.
-- Parametreler: {baslangic_tarihi}, {bitis_tarihi}, {donem_yil}  (ayarlar.toml [raporlar.parametreler])
-- Hazır olduğunda "-- durum: hazir" yapın.
-- sayfa: Detay
SELECT
    CAST(NULL AS NVARCHAR(50)) AS SicilNo
    -- , diğer kolonlar
WHERE 1 = 0;
