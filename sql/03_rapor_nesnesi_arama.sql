/*
  03 - Mevcut rapor tanımlarını arama
  -----------------------------------
  Uygulama (e-flow vb.) raporlarını çoğunlukla view / prosedür / rapor tanım tablolarında saklar.
  Bu betik tüm veritabanlarında, adında veya kodunda rapor anahtar kelimeleri geçen nesneleri bulur.
  Şablon dosya adlarıyla eşleşen kelimeler kullanılmıştır; gerekirse listeyi genişletin.
*/
SET NOCOUNT ON;

IF OBJECT_ID('tempdb..#nesne') IS NOT NULL DROP TABLE #nesne;
CREATE TABLE #nesne (Veritabani SYSNAME, Sema SYSNAME, Nesne SYSNAME, Tip NVARCHAR(60), EslesenKelime NVARCHAR(100), DegisiklikTarihi DATETIME);

DECLARE @vt SYSNAME, @sql NVARCHAR(MAX);
DECLARE vt_cur CURSOR LOCAL FAST_FORWARD FOR
    SELECT name FROM sys.databases WHERE database_id > 4 AND state_desc = 'ONLINE' AND HAS_DBACCESS(name) = 1 ORDER BY name;
OPEN vt_cur; FETCH NEXT FROM vt_cur INTO @vt;
WHILE @@FETCH_STATUS = 0
BEGIN
    SET @sql = N'USE ' + QUOTENAME(@vt) + N';
    INSERT INTO #nesne
    SELECT DB_NAME(), s.name, o.name, o.type_desc, k.kelime, o.modify_date
    FROM sys.objects o
    JOIN sys.schemas s ON s.schema_id = o.schema_id
    LEFT JOIN sys.sql_modules m ON m.object_id = o.object_id
    CROSS APPLY (SELECT kelime FROM (VALUES
        (N''ucret_tarih''),(N''UcretTarih''),(N''performans''),(N''perakende''),(N''organizasyon''),(N''OnayBekleyen''),(N''onay_bekleyen''),
        (N''KullanilanIzin''),(N''kullanilan_izin''),(N''IzinYuku''),(N''izin_yuku''),(N''fiili''),(N''cikis''),(N''ayrilan''),
        (N''case''),(N''iletisim''),(N''BelirliSureli''),(N''belirli_sureli''),(N''BagliYonetici''),(N''bagli_yonetici''),(N''rapor''),(N''report'')
    ) v(kelime)) k
    WHERE o.is_ms_shipped = 0 AND o.type IN (''U'',''V'',''P'',''FN'',''IF'',''TF'')
      AND (o.name COLLATE Turkish_CI_AI LIKE N''%'' + k.kelime + N''%''
           OR (o.type <> ''U'' AND m.definition COLLATE Turkish_CI_AI LIKE N''%'' + k.kelime + N''%''));';
    BEGIN TRY EXEC sp_executesql @sql; END TRY
    BEGIN CATCH INSERT INTO #nesne VALUES (@vt, N'-', N'HATA', ERROR_MESSAGE(), NULL, NULL); END CATCH
    FETCH NEXT FROM vt_cur INTO @vt;
END
CLOSE vt_cur; DEALLOCATE vt_cur;

SELECT Veritabani, Sema, Nesne, Tip, STRING_AGG(EslesenKelime, ', ') AS EslesenKelimeler, MAX(DegisiklikTarihi) AS DegisiklikTarihi
FROM #nesne
GROUP BY Veritabani, Sema, Nesne, Tip
ORDER BY COUNT(*) DESC, Veritabani, Nesne;
