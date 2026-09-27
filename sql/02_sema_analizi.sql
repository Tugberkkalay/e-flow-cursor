/*
  02 - Tek veritabanı için şema analizi
  -------------------------------------
  VS Code'da bağlantı çubuğundan İK verisinin bulunduğu veritabanını seçin (veya aşağıdaki USE satırını düzenleyin)
  ve tümünü çalıştırın. 5 sonuç kümesi döner: Tablolar, Kolonlar, İlişkiler, İndeksler, View/Prosedürler.
  Her sonucu sağ tık -> "Save as Excel" ile kaydedin; dosyalar rapor SQL'lerini yazmak için yeterlidir.
*/
-- USE [VERITABANI_ADI];
SET NOCOUNT ON;

-- 1) Tablolar
SELECT DB_NAME() AS Veritabani, s.name AS Sema, t.name AS Tablo,
       (SELECT SUM(p.rows) FROM sys.partitions p WHERE p.object_id = t.object_id AND p.index_id IN (0,1)) AS SatirSayisi,
       (SELECT COUNT(*) FROM sys.columns c WHERE c.object_id = t.object_id) AS KolonSayisi,
       t.create_date AS OlusturmaTarihi, t.modify_date AS DegisiklikTarihi
FROM sys.tables t JOIN sys.schemas s ON s.schema_id = t.schema_id
WHERE t.is_ms_shipped = 0
ORDER BY SatirSayisi DESC, s.name, t.name;

-- 2) Kolonlar (tablo + view)
SELECT DB_NAME() AS Veritabani, s.name AS Sema, o.name AS Tablo, o.type_desc AS NesneTipi, c.column_id AS Sira, c.name AS Kolon,
       ty.name AS VeriTipi,
       CASE WHEN ty.name IN ('nvarchar','nchar') THEN IIF(c.max_length = -1, -1, c.max_length / 2)
            WHEN ty.name IN ('varchar','char','varbinary','binary') THEN c.max_length END AS Uzunluk,
       IIF(ty.name IN ('decimal','numeric'), c.precision, NULL) AS Hassasiyet,
       IIF(ty.name IN ('decimal','numeric'), c.scale, NULL) AS Olcek,
       IIF(c.is_nullable = 1, 'EVET', 'HAYIR') AS BosOlabilir,
       IIF(c.is_identity = 1, 'EVET', '') AS Identity_,
       IIF(pk.column_id IS NOT NULL, 'PK', '') AS PK,
       IIF(fk.parent_column_id IS NOT NULL, 'FK', '') AS FK,
       dc.definition AS Varsayilan,
       CAST(ep.value AS NVARCHAR(500)) AS Aciklama
FROM sys.columns c
JOIN sys.objects o ON o.object_id = c.object_id AND o.type IN ('U','V')
JOIN sys.schemas s ON s.schema_id = o.schema_id
JOIN sys.types ty ON ty.user_type_id = c.user_type_id
LEFT JOIN sys.default_constraints dc ON dc.object_id = c.default_object_id
LEFT JOIN (SELECT ic.object_id, ic.column_id
           FROM sys.index_columns ic JOIN sys.indexes i ON i.object_id = ic.object_id AND i.index_id = ic.index_id
           WHERE i.is_primary_key = 1) pk ON pk.object_id = c.object_id AND pk.column_id = c.column_id
LEFT JOIN (SELECT DISTINCT parent_object_id, parent_column_id FROM sys.foreign_key_columns) fk
       ON fk.parent_object_id = c.object_id AND fk.parent_column_id = c.column_id
LEFT JOIN sys.extended_properties ep ON ep.major_id = c.object_id AND ep.minor_id = c.column_id AND ep.name = 'MS_Description'
WHERE o.is_ms_shipped = 0
ORDER BY s.name, o.name, c.column_id;

-- 3) İlişkiler (FK)
SELECT DB_NAME() AS Veritabani, fk.name AS Kisit,
       sp.name AS KaynakSema, tp.name AS KaynakTablo, cp.name AS KaynakKolon,
       sr.name AS HedefSema, tr.name AS HedefTablo, cr.name AS HedefKolon
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id = fk.object_id
JOIN sys.tables tp ON tp.object_id = fk.parent_object_id
JOIN sys.schemas sp ON sp.schema_id = tp.schema_id
JOIN sys.columns cp ON cp.object_id = fkc.parent_object_id AND cp.column_id = fkc.parent_column_id
JOIN sys.tables tr ON tr.object_id = fk.referenced_object_id
JOIN sys.schemas sr ON sr.schema_id = tr.schema_id
JOIN sys.columns cr ON cr.object_id = fkc.referenced_object_id AND cr.column_id = fkc.referenced_column_id
ORDER BY sp.name, tp.name, fk.name;

-- 4) İndeksler
SELECT DB_NAME() AS Veritabani, s.name AS Sema, t.name AS Tablo, i.name AS Indeks, i.type_desc AS Tip,
       IIF(i.is_primary_key = 1, 'EVET', '') AS PK, IIF(i.is_unique = 1, 'EVET', '') AS Tekil,
       STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) AS Kolonlar
FROM sys.indexes i
JOIN sys.tables t ON t.object_id = i.object_id
JOIN sys.schemas s ON s.schema_id = t.schema_id
JOIN sys.index_columns ic ON ic.object_id = i.object_id AND ic.index_id = i.index_id AND ic.is_included_column = 0
JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id
WHERE i.type > 0 AND t.is_ms_shipped = 0
GROUP BY s.name, t.name, i.name, i.type_desc, i.is_primary_key, i.is_unique
ORDER BY s.name, t.name, i.name;

-- 5) View / prosedür / fonksiyon tanımları (mevcut raporların SQL'i genelde buradadır)
SELECT DB_NAME() AS Veritabani, s.name AS Sema, o.name AS Nesne, o.type_desc AS Tip,
       o.create_date AS OlusturmaTarihi, o.modify_date AS DegisiklikTarihi,
       LEFT(m.definition, 30000) AS Tanim
FROM sys.objects o
JOIN sys.schemas s ON s.schema_id = o.schema_id
LEFT JOIN sys.sql_modules m ON m.object_id = o.object_id
WHERE o.type IN ('V','P','FN','IF','TF') AND o.is_ms_shipped = 0
ORDER BY o.type_desc, s.name, o.name;
