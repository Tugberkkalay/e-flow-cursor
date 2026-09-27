"""Sunucudaki veritabanlarının şemasını çıkarır ve tek bir Excel çalışma kitabına yazar.

Kullanım:  python -m ik_rapor.sema_analizi [--veritabani AD] [--cikti DOSYA]
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys

import pandas as pd

from . import ayarlar as ayar_mod
from .baglanti import baglan, koseli, kullanici_veritabanlari, sorgula
from .excel import calisma_kitabi_kaydet

SQL_TABLOLAR = """
SELECT
    s.name AS Sema, t.name AS Tablo,
    (SELECT SUM(p.rows) FROM sys.partitions p WHERE p.object_id = t.object_id AND p.index_id IN (0,1)) AS SatirSayisi,
    (SELECT COUNT(*) FROM sys.columns c WHERE c.object_id = t.object_id) AS KolonSayisi,
    t.create_date AS OlusturmaTarihi, t.modify_date AS DegisiklikTarihi,
    (SELECT CAST(SUM(a.total_pages) * 8 / 1024.0 AS DECIMAL(18,2))
     FROM sys.partitions p JOIN sys.allocation_units a ON a.container_id = p.partition_id
     WHERE p.object_id = t.object_id) AS BoyutMB
FROM sys.tables t
JOIN sys.schemas s ON s.schema_id = t.schema_id
WHERE t.is_ms_shipped = 0
ORDER BY SatirSayisi DESC, s.name, t.name
"""

SQL_KOLONLAR = """
SELECT
    s.name AS Sema, o.name AS Tablo, o.type_desc AS NesneTipi, c.column_id AS Sira, c.name AS Kolon,
    ty.name AS VeriTipi,
    CASE WHEN ty.name IN ('nvarchar','nchar') THEN IIF(c.max_length = -1, -1, c.max_length / 2)
         WHEN ty.name IN ('varchar','char','varbinary','binary') THEN c.max_length
         ELSE NULL END AS Uzunluk,
    IIF(ty.name IN ('decimal','numeric'), c.precision, NULL) AS Hassasiyet,
    IIF(ty.name IN ('decimal','numeric'), c.scale, NULL) AS Olcek,
    IIF(c.is_nullable = 1, 'EVET', 'HAYIR') AS BosOlabilir,
    IIF(c.is_identity = 1, 'EVET', '') AS Identity_,
    IIF(c.is_computed = 1, 'EVET', '') AS Hesaplanan,
    dc.definition AS Varsayilan,
    IIF(pk.column_id IS NOT NULL, 'PK', '') AS PK,
    IIF(fk.parent_column_id IS NOT NULL, 'FK', '') AS FK,
    CAST(ep.value AS NVARCHAR(500)) AS Aciklama
FROM sys.columns c
JOIN sys.objects o ON o.object_id = c.object_id AND o.type IN ('U','V')
JOIN sys.schemas s ON s.schema_id = o.schema_id
JOIN sys.types ty ON ty.user_type_id = c.user_type_id
LEFT JOIN sys.default_constraints dc ON dc.object_id = c.default_object_id
LEFT JOIN (
    SELECT ic.object_id, ic.column_id
    FROM sys.index_columns ic JOIN sys.indexes i ON i.object_id = ic.object_id AND i.index_id = ic.index_id
    WHERE i.is_primary_key = 1
) pk ON pk.object_id = c.object_id AND pk.column_id = c.column_id
LEFT JOIN (SELECT DISTINCT parent_object_id, parent_column_id FROM sys.foreign_key_columns) fk
    ON fk.parent_object_id = c.object_id AND fk.parent_column_id = c.column_id
LEFT JOIN sys.extended_properties ep ON ep.major_id = c.object_id AND ep.minor_id = c.column_id AND ep.name = 'MS_Description'
WHERE o.is_ms_shipped = 0
ORDER BY s.name, o.name, c.column_id
"""

SQL_ILISKILER = """
SELECT
    fk.name AS Kisit,
    sp.name AS KaynakSema, tp.name AS KaynakTablo, cp.name AS KaynakKolon,
    sr.name AS HedefSema, tr.name AS HedefTablo, cr.name AS HedefKolon,
    fk.delete_referential_action_desc AS SilmeKurali, fk.update_referential_action_desc AS GuncellemeKurali
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id = fk.object_id
JOIN sys.tables tp ON tp.object_id = fk.parent_object_id
JOIN sys.schemas sp ON sp.schema_id = tp.schema_id
JOIN sys.columns cp ON cp.object_id = fkc.parent_object_id AND cp.column_id = fkc.parent_column_id
JOIN sys.tables tr ON tr.object_id = fk.referenced_object_id
JOIN sys.schemas sr ON sr.schema_id = tr.schema_id
JOIN sys.columns cr ON cr.object_id = fkc.referenced_object_id AND cr.column_id = fkc.referenced_column_id
ORDER BY sp.name, tp.name, fk.name
"""

SQL_INDEKSLER = """
SELECT s.name AS Sema, t.name AS Tablo, i.name AS Indeks, i.type_desc AS Tip,
       IIF(i.is_primary_key = 1, 'EVET', '') AS PK, IIF(i.is_unique = 1, 'EVET', '') AS Tekil,
       STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) AS Kolonlar
FROM sys.indexes i
JOIN sys.tables t ON t.object_id = i.object_id
JOIN sys.schemas s ON s.schema_id = t.schema_id
JOIN sys.index_columns ic ON ic.object_id = i.object_id AND ic.index_id = i.index_id AND ic.is_included_column = 0
JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id
WHERE i.type > 0 AND t.is_ms_shipped = 0
GROUP BY s.name, t.name, i.name, i.type_desc, i.is_primary_key, i.is_unique
ORDER BY s.name, t.name, i.name
"""

SQL_GORUNUMLER = """
SELECT s.name AS Sema, v.name AS Gorunum, v.create_date AS OlusturmaTarihi, v.modify_date AS DegisiklikTarihi,
       LEFT(m.definition, 30000) AS Tanim
FROM sys.views v
JOIN sys.schemas s ON s.schema_id = v.schema_id
LEFT JOIN sys.sql_modules m ON m.object_id = v.object_id
WHERE v.is_ms_shipped = 0
ORDER BY s.name, v.name
"""

SQL_PROSEDURLER = """
SELECT s.name AS Sema, o.name AS Nesne, o.type_desc AS Tip, o.create_date AS OlusturmaTarihi, o.modify_date AS DegisiklikTarihi,
       LEFT(m.definition, 30000) AS Tanim
FROM sys.objects o
JOIN sys.schemas s ON s.schema_id = o.schema_id
LEFT JOIN sys.sql_modules m ON m.object_id = o.object_id
WHERE o.type IN ('P','FN','IF','TF','TR') AND o.is_ms_shipped = 0
ORDER BY o.type_desc, s.name, o.name
"""


def _anahtar_kelime_eslesmeleri(kolonlar: pd.DataFrame, tablolar: pd.DataFrame, kelimeler: list[str]) -> pd.DataFrame:
    if kolonlar.empty or not kelimeler:
        return pd.DataFrame(columns=["Veritabani", "Sema", "Tablo", "SatirSayisi", "EslesenKelimeler", "EslesenKolonlar"])
    kelimeler_kucuk = [k.lower() for k in kelimeler]
    satirlar = []
    for (vt, sema, tablo), grup in kolonlar.groupby(["Veritabani", "Sema", "Tablo"], sort=False):
        metin_tablo = tablo.lower()
        eslesen_kelime, eslesen_kolon = set(), []
        for k in kelimeler_kucuk:
            if k in metin_tablo:
                eslesen_kelime.add(k)
        for kolon in grup["Kolon"]:
            kl = str(kolon).lower()
            for k in kelimeler_kucuk:
                if k in kl:
                    eslesen_kelime.add(k)
                    eslesen_kolon.append(kolon)
                    break
        if eslesen_kelime:
            satir_sayisi = tablolar.loc[
                (tablolar["Veritabani"] == vt) & (tablolar["Sema"] == sema) & (tablolar["Tablo"] == tablo), "SatirSayisi"
            ]
            satirlar.append(
                {
                    "Veritabani": vt, "Sema": sema, "Tablo": tablo,
                    "SatirSayisi": int(satir_sayisi.iloc[0]) if len(satir_sayisi) else None,
                    "EslesmeSayisi": len(eslesen_kelime) + len(eslesen_kolon),
                    "EslesenKelimeler": ", ".join(sorted(eslesen_kelime)),
                    "EslesenKolonlar": ", ".join(eslesen_kolon),
                }
            )
    df = pd.DataFrame(satirlar)
    return df.sort_values(["EslesmeSayisi", "SatirSayisi"], ascending=False) if len(df) else df


def analiz_et(ayar: dict, veritabanlari: list[str] | None = None) -> dict[str, pd.DataFrame]:
    with baglan(ayar, "master") as conn:
        sunucu = sorgula(conn, "SELECT @@SERVERNAME AS Sunucu, @@VERSION AS Surum, SUSER_SNAME() AS Kullanici")
        hedefler = veritabanlari or ayar.get("sema_analizi", {}).get("veritabanlari") or []
        if not hedefler:
            hedefler = kullanici_veritabanlari(conn)
        vt_bilgi = sorgula(
            conn,
            """SELECT d.name AS Veritabani, d.create_date AS OlusturmaTarihi, d.collation_name AS Collation,
                      d.recovery_model_desc AS KurtarmaModeli, d.compatibility_level AS UyumlulukSeviyesi,
                      CAST(SUM(mf.size) * 8 / 1024.0 AS DECIMAL(18,2)) AS BoyutMB
               FROM sys.databases d JOIN sys.master_files mf ON mf.database_id = d.database_id
               WHERE d.database_id > 4 GROUP BY d.name, d.create_date, d.collation_name, d.recovery_model_desc, d.compatibility_level
               ORDER BY d.name""",
        )
    print(f"Sunucu: {sunucu.at[0, 'Sunucu']}  Kullanıcı: {sunucu.at[0, 'Kullanici']}")
    print(f"Taranacak veritabanları ({len(hedefler)}): {', '.join(hedefler)}")

    parcalar: dict[str, list[pd.DataFrame]] = {k: [] for k in ["Tablolar", "Kolonlar", "Iliskiler", "Indeksler", "Gorunumler", "Prosedurler"]}
    sorgular = {
        "Tablolar": SQL_TABLOLAR, "Kolonlar": SQL_KOLONLAR, "Iliskiler": SQL_ILISKILER,
        "Indeksler": SQL_INDEKSLER, "Gorunumler": SQL_GORUNUMLER, "Prosedurler": SQL_PROSEDURLER,
    }
    hatalar = []
    for vt in hedefler:
        print(f"  -> {vt} ...", end=" ", flush=True)
        try:
            with baglan(ayar, vt) as conn:
                for ad, sql in sorgular.items():
                    df = sorgula(conn, sql)
                    df.insert(0, "Veritabani", vt)
                    parcalar[ad].append(df)
            print(f"{len(parcalar['Tablolar'][-1])} tablo, {len(parcalar['Kolonlar'][-1])} kolon")
        except Exception as e:  # noqa: BLE001
            print(f"HATA: {e}")
            hatalar.append({"Veritabani": vt, "Hata": str(e)})

    sonuc = {
        "Ozet": pd.concat([sunucu.assign(Tarih=dt.datetime.now(), TaranacakVT=", ".join(hedefler))], ignore_index=True),
        "Veritabanlari": vt_bilgi[vt_bilgi["Veritabani"].isin(hedefler)].reset_index(drop=True),
    }
    for ad, liste in parcalar.items():
        sonuc[ad] = pd.concat(liste, ignore_index=True) if liste else pd.DataFrame()
    sonuc["IK_Aday_Tablolar"] = _anahtar_kelime_eslesmeleri(
        sonuc["Kolonlar"], sonuc["Tablolar"], ayar.get("sema_analizi", {}).get("anahtar_kelimeler", [])
    )
    if hatalar:
        sonuc["Hatalar"] = pd.DataFrame(hatalar)
    return sonuc


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="SQL Server şema analizi -> Excel")
    p.add_argument("--veritabani", "-d", action="append", help="Taranacak veritabanı (birden çok kez verilebilir)")
    p.add_argument("--cikti", "-o", help="Çıktı dosyası (.xlsx)")
    args = p.parse_args(argv)

    ayar = ayar_mod.yukle()
    sayfalar = analiz_et(ayar, args.veritabani)
    yol = ayar_mod.cikti_klasoru(ayar) / (args.cikti or f"sema_analizi_{dt.datetime.now():%Y%m%d_%H%M}.xlsx")
    basliklar = {k: f"Şema Analizi - {k}" for k in sayfalar}
    calisma_kitabi_kaydet(sayfalar, yol, basliklar)
    print(f"\nŞema analizi yazıldı: {yol}")
    print("Bu dosyayı paylaşarak rapor SQL'lerinin hazırlanmasını sağlayabilirsiniz.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
