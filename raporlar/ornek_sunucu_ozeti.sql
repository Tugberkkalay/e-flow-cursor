-- rapor: Örnek - Sunucu ve Tablo Özeti
-- veritabani: master
-- durum: hazir
-- aciklama: Boru hattını doğrulamak için her sunucuda çalışan örnek rapor; gerçek İK verisi içermez.
-- sayfa: Veritabanlari
SELECT d.name AS Veritabani, d.state_desc AS Durum, d.create_date AS OlusturmaTarihi,
       d.collation_name AS Collation, d.compatibility_level AS Uyumluluk
FROM sys.databases d
WHERE d.database_id > 4
ORDER BY d.name;

-- sayfa: Oturum
SELECT @@SERVERNAME AS Sunucu, SUSER_SNAME() AS Kullanici, GETDATE() AS SunucuSaati,
       {donem_yil} AS DonemYil, {baslangic_tarihi} AS Baslangic, {bitis_tarihi} AS Bitis;
