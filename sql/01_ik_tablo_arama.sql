/*
  01 - İK verisinin hangi veritabanı/tablolarda olduğunu bulma
  ------------------------------------------------------------
  VS Code (mssql eklentisi) veya SSMS'te, sunucuya bağlıyken çalıştırın (seçili veritabanı önemli değil).
  Tüm çevrimiçi kullanıcı veritabanlarını tarar; adı veya kolon adı İK anahtar kelimeleriyle eşleşen tabloları listeler.
  Sonucu sağ tık -> "Save as Excel" / "Save as CSV" ile kaydedip paylaşın.
*/
SET NOCOUNT ON;

DECLARE @kelimeler TABLE (kelime NVARCHAR(50));
INSERT INTO @kelimeler VALUES
 (N'personel'),(N'sicil'),(N'calisan'),(N'çalışan'),(N'employee'),(N'izin'),(N'leave'),(N'ucret'),(N'ücret'),(N'maas'),(N'maaş'),
 (N'salary'),(N'wage'),(N'performans'),(N'organizasyon'),(N'departman'),(N'birim'),(N'pozisyon'),(N'unvan'),(N'yonetici'),(N'yönetici'),
 (N'manager'),(N'cikis'),(N'çıkış'),(N'ayrilma'),(N'ayrılma'),(N'giris'),(N'giriş'),(N'hire'),(N'termination'),(N'case'),(N'vaka'),
 (N'iletisim'),(N'iletişim'),(N'telefon'),(N'phone'),(N'email'),(N'mail'),(N'sozlesme'),(N'sözleşme'),(N'contract'),(N'belirli'),
 (N'perakende'),(N'magaza'),(N'mağaza'),(N'store'),(N'onay'),(N'approval'),(N'puantaj'),(N'fiili'),(N'bordro'),(N'payroll');

DECLARE @liste NVARCHAR(MAX) =
    STUFF((SELECT N',(N''' + REPLACE(kelime, '''', '''''') + N''')' FROM @kelimeler FOR XML PATH(''), TYPE).value('.', 'NVARCHAR(MAX)'), 1, 1, N'');

IF OBJECT_ID('tempdb..#sonuc') IS NOT NULL DROP TABLE #sonuc;
CREATE TABLE #sonuc (
    Veritabani SYSNAME, Sema SYSNAME, Tablo SYSNAME, SatirSayisi BIGINT, KolonSayisi INT,
    EslesenKolonlar NVARCHAR(MAX), EslesmeSayisi INT
);

DECLARE @vt SYSNAME, @sql NVARCHAR(MAX);
DECLARE vt_cur CURSOR LOCAL FAST_FORWARD FOR
    SELECT name FROM sys.databases
    WHERE database_id > 4 AND state_desc = 'ONLINE' AND HAS_DBACCESS(name) = 1
      AND name NOT IN ('ReportServer', 'ReportServerTempDB', 'distribution')
    ORDER BY name;
OPEN vt_cur;
FETCH NEXT FROM vt_cur INTO @vt;
WHILE @@FETCH_STATUS = 0
BEGIN
    SET @sql = N'
    USE ' + QUOTENAME(@vt) + N';
    WITH k AS (SELECT kelime FROM (VALUES ' + @liste + N') v(kelime)),
    kolon_eslesme AS (
        SELECT c.object_id, c.name AS Kolon
        FROM sys.columns c
        WHERE EXISTS (SELECT 1 FROM k WHERE c.name COLLATE Turkish_CI_AI LIKE N''%'' + k.kelime + N''%'')
    ),
    tablo_eslesme AS (
        SELECT t.object_id
        FROM sys.tables t
        WHERE EXISTS (SELECT 1 FROM k WHERE t.name COLLATE Turkish_CI_AI LIKE N''%'' + k.kelime + N''%'')
    )
    INSERT INTO #sonuc
    SELECT DB_NAME(), s.name, t.name,
           (SELECT SUM(p.rows) FROM sys.partitions p WHERE p.object_id = t.object_id AND p.index_id IN (0,1)),
           (SELECT COUNT(*) FROM sys.columns c WHERE c.object_id = t.object_id),
           STUFF((SELECT N'', '' + ke.Kolon FROM kolon_eslesme ke WHERE ke.object_id = t.object_id
                  FOR XML PATH(''''), TYPE).value(''.'', ''NVARCHAR(MAX)''), 1, 2, N''''),
           (SELECT COUNT(*) FROM kolon_eslesme ke WHERE ke.object_id = t.object_id)
             + CASE WHEN EXISTS (SELECT 1 FROM tablo_eslesme te WHERE te.object_id = t.object_id) THEN 3 ELSE 0 END
    FROM sys.tables t JOIN sys.schemas s ON s.schema_id = t.schema_id
    WHERE t.is_ms_shipped = 0
      AND (EXISTS (SELECT 1 FROM kolon_eslesme ke WHERE ke.object_id = t.object_id)
           OR EXISTS (SELECT 1 FROM tablo_eslesme te WHERE te.object_id = t.object_id));';
    BEGIN TRY
        EXEC sp_executesql @sql;
    END TRY
    BEGIN CATCH
        INSERT INTO #sonuc VALUES (@vt, N'-', N'HATA', NULL, NULL, ERROR_MESSAGE(), -1);
    END CATCH
    FETCH NEXT FROM vt_cur INTO @vt;
END
CLOSE vt_cur; DEALLOCATE vt_cur;

-- 1) Veritabanı bazında özet: İK verisinin muhtemelen nerede olduğu
SELECT Veritabani, COUNT(*) AS EslesenTablo, SUM(SatirSayisi) AS ToplamSatir, SUM(EslesmeSayisi) AS ToplamEslesme
FROM #sonuc WHERE EslesmeSayisi >= 0
GROUP BY Veritabani ORDER BY ToplamEslesme DESC;

-- 2) Tablo detayı
SELECT * FROM #sonuc ORDER BY EslesmeSayisi DESC, SatirSayisi DESC;
