"""Seçili tabloların kolon bazlı veri profilini çıkarır (boş oranı, tekil değer, min/max, örnek değerler).

Kullanım:  python -m ik_rapor.veri_profili [--tablo VT.sema.tablo ...] [--cikti DOSYA]
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys

import pandas as pd

from . import ayarlar as ayar_mod
from .baglanti import baglan, koseli, kullanici_veritabanlari, sorgula
from .excel import calisma_kitabi_kaydet

SAYISAL = {"int", "bigint", "smallint", "tinyint", "decimal", "numeric", "float", "real", "money", "smallmoney", "bit"}
TARIH = {"date", "datetime", "datetime2", "smalldatetime", "datetimeoffset", "time"}
METIN = {"varchar", "nvarchar", "char", "nchar", "uniqueidentifier"}
# text/ntext DISTINCT ve GROUP BY desteklemez; ikili/uzamsal tipler profillenmez.
ATLA = {"xml", "image", "text", "ntext", "varbinary", "binary", "geography", "geometry", "hierarchyid", "sql_variant", "timestamp"}


def _tablo_kolonlari(conn, sema: str, tablo: str) -> pd.DataFrame:
    return sorgula(
        conn,
        """SELECT c.name AS Kolon, ty.name AS VeriTipi, c.column_id AS Sira
           FROM sys.columns c JOIN sys.types ty ON ty.user_type_id = c.user_type_id
           WHERE c.object_id = OBJECT_ID(?) ORDER BY c.column_id""",
        (f"{koseli(sema)}.{koseli(tablo)}",),
    )


def _profil_sorgusu(sema: str, tablo: str, kolonlar: pd.DataFrame, ornekle: bool) -> str:
    ifadeler = ["COUNT_BIG(*) AS __toplam"]
    for _, k in kolonlar.iterrows():
        ad, tip = koseli(k["Kolon"]), k["VeriTipi"]
        if tip in ATLA:
            continue
        i = int(k["Sira"])
        ifadeler.append(f"SUM(CASE WHEN {ad} IS NULL THEN 1 ELSE 0 END) AS [__bos_{i}]")
        ifadeler.append(f"COUNT_BIG(DISTINCT {ad}) AS [__tekil_{i}]")
        if tip == "bit":
            # MIN/MAX bit tipinde çalışmaz
            ifadeler.append(f"MIN(CAST({ad} AS TINYINT)) AS [__min_{i}]")
            ifadeler.append(f"MAX(CAST({ad} AS TINYINT)) AS [__max_{i}]")
            ifadeler.append(f"AVG(CAST({ad} AS FLOAT)) AS [__ort_{i}]")
        elif tip in SAYISAL or tip in TARIH:
            ifadeler.append(f"MIN({ad}) AS [__min_{i}]")
            ifadeler.append(f"MAX({ad}) AS [__max_{i}]")
            if tip in SAYISAL:
                ifadeler.append(f"AVG(CAST({ad} AS FLOAT)) AS [__ort_{i}]")
        elif tip in METIN:
            ifadeler.append(f"MIN(LEN(CAST({ad} AS NVARCHAR(MAX)))) AS [__min_{i}]")
            ifadeler.append(f"MAX(LEN(CAST({ad} AS NVARCHAR(MAX)))) AS [__max_{i}]")
            ifadeler.append(f"SUM(CASE WHEN LTRIM(RTRIM(CAST({ad} AS NVARCHAR(MAX)))) = '' THEN 1 ELSE 0 END) AS [__bosmetin_{i}]")
    kaynak = f"{koseli(sema)}.{koseli(tablo)}" + (" TABLESAMPLE SYSTEM (10 PERCENT)" if ornekle else "")
    return f"SELECT {', '.join(ifadeler)} FROM {kaynak}"


def _ornek_degerler(conn, sema: str, tablo: str, kolon: str, adet: int = 5) -> str:
    try:
        df = sorgula(
            conn,
            f"SELECT TOP {adet} {koseli(kolon)} AS v, COUNT_BIG(*) AS n FROM {koseli(sema)}.{koseli(tablo)} "
            f"WHERE {koseli(kolon)} IS NOT NULL GROUP BY {koseli(kolon)} ORDER BY n DESC",
        )
        return " | ".join(f"{str(v)[:40]} ({n:,})" for v, n in zip(df["v"], df["n"]))
    except Exception:  # noqa: BLE001
        return ""


def tablo_profili(conn, vt: str, sema: str, tablo: str, satir_sayisi: int | None, esik: int) -> pd.DataFrame:
    kolonlar = _tablo_kolonlari(conn, sema, tablo)
    if kolonlar.empty:
        return pd.DataFrame()
    ornekle = bool(satir_sayisi and satir_sayisi > esik)
    sonuc = sorgula(conn, _profil_sorgusu(sema, tablo, kolonlar, ornekle))
    toplam = int(sonuc.at[0, "__toplam"]) if len(sonuc) else 0
    satirlar = []
    for _, k in kolonlar.iterrows():
        i = int(k["Sira"])
        kayit = {
            "Veritabani": vt, "Sema": sema, "Tablo": tablo, "Kolon": k["Kolon"], "VeriTipi": k["VeriTipi"],
            "ToplamSatir": toplam, "Orneklendi": "EVET" if ornekle else "",
        }
        if k["VeriTipi"] in ATLA or toplam == 0:
            satirlar.append(kayit)
            continue
        bos = int(sonuc.at[0, f"__bos_{i}"] or 0)
        tekil = int(sonuc.at[0, f"__tekil_{i}"] or 0)
        kayit.update(
            {
                "BosSayisi": bos, "BosOrani": round(bos / toplam, 4), "TekilDeger": tekil,
                "TekilOrani": round(tekil / toplam, 4),
                "Min": sonuc.at[0, f"__min_{i}"] if f"__min_{i}" in sonuc else None,
                "Max": sonuc.at[0, f"__max_{i}"] if f"__max_{i}" in sonuc else None,
                "Ortalama": round(float(sonuc.at[0, f"__ort_{i}"]), 2) if f"__ort_{i}" in sonuc and sonuc.at[0, f"__ort_{i}"] is not None else None,
                "BosMetin": int(sonuc.at[0, f"__bosmetin_{i}"] or 0) if f"__bosmetin_{i}" in sonuc else None,
                "AnahtarAdayi": "EVET" if bos == 0 and tekil == toplam else "",
            }
        )
        if k["VeriTipi"] in METIN and 1 < tekil <= 200:
            kayit["EnSikDegerler"] = _ornek_degerler(conn, sema, tablo, k["Kolon"])
        satirlar.append(kayit)
    return pd.DataFrame(satirlar)


def _hedef_tablolar(ayar: dict, istenen: list[str]) -> list[tuple[str, str, str, int | None]]:
    varsayilan_vt = ayar["baglanti"].get("veritabani") or ""
    hedefler: list[tuple[str, str, str, int | None]] = []
    if istenen:
        for t in istenen:
            parca = t.split(".")
            if len(parca) == 3:
                hedefler.append((parca[0], parca[1], parca[2], None))
            elif len(parca) == 2:
                if not varsayilan_vt:
                    raise SystemExit(f"'{t}' için veritabanı belirtin (VT.sema.tablo) veya ayarlar.toml'da veritabani doldurun.")
                hedefler.append((varsayilan_vt, parca[0], parca[1], None))
            else:
                raise SystemExit(f"Geçersiz tablo adı: {t} (beklenen: VT.sema.tablo)")
        return hedefler

    n = int(ayar.get("veri_profili", {}).get("en_buyuk_n_tablo", 40))
    with baglan(ayar, "master") as conn:
        vtler = [varsayilan_vt] if varsayilan_vt else (ayar.get("sema_analizi", {}).get("veritabanlari") or kullanici_veritabanlari(conn))
    tumu = []
    for vt in vtler:
        with baglan(ayar, vt) as conn:
            df = sorgula(
                conn,
                """SELECT s.name AS Sema, t.name AS Tablo, SUM(p.rows) AS Satir
                   FROM sys.tables t JOIN sys.schemas s ON s.schema_id = t.schema_id
                   JOIN sys.partitions p ON p.object_id = t.object_id AND p.index_id IN (0,1)
                   WHERE t.is_ms_shipped = 0 GROUP BY s.name, t.name HAVING SUM(p.rows) > 0""",
            )
            tumu += [(vt, r.Sema, r.Tablo, int(r.Satir)) for r in df.itertuples()]
    tumu.sort(key=lambda x: x[3], reverse=True)
    return tumu[:n]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Tablo veri profili -> Excel")
    p.add_argument("--tablo", "-t", action="append", default=[], help="VT.sema.tablo (birden çok kez verilebilir)")
    p.add_argument("--cikti", "-o", help="Çıktı dosyası (.xlsx)")
    args = p.parse_args(argv)

    ayar = ayar_mod.yukle()
    istenen = args.tablo or ayar.get("veri_profili", {}).get("tablolar", [])
    hedefler = _hedef_tablolar(ayar, istenen)
    esik = int(ayar.get("veri_profili", {}).get("ornekleme_esigi", 2_000_000))
    print(f"{len(hedefler)} tablo profillenecek.")

    parcalar, hatalar = [], []
    for vt, sema, tablo, satir in hedefler:
        print(f"  -> {vt}.{sema}.{tablo} ({satir if satir is not None else '?'} satır) ...", end=" ", flush=True)
        try:
            with baglan(ayar, vt) as conn:
                df = tablo_profili(conn, vt, sema, tablo, satir, esik)
            parcalar.append(df)
            print("ok")
        except Exception as e:  # noqa: BLE001
            print(f"HATA: {e}")
            hatalar.append({"Veritabani": vt, "Sema": sema, "Tablo": tablo, "Hata": str(e)})

    profil = pd.concat(parcalar, ignore_index=True) if parcalar else pd.DataFrame()
    sayfalar = {"KolonProfili": profil}
    if len(profil):
        ozet = (
            profil.groupby(["Veritabani", "Sema", "Tablo"], as_index=False)
            .agg(ToplamSatir=("ToplamSatir", "first"), KolonSayisi=("Kolon", "count"), OrtBosOrani=("BosOrani", "mean"),
                 AnahtarAdayiKolonlar=("AnahtarAdayi", lambda s: int((s == "EVET").sum())))
            .sort_values("ToplamSatir", ascending=False)
        )
        sayfalar = {"TabloOzeti": ozet, **sayfalar}
    if hatalar:
        sayfalar["Hatalar"] = pd.DataFrame(hatalar)

    yol = ayar_mod.cikti_klasoru(ayar) / (args.cikti or f"veri_profili_{dt.datetime.now():%Y%m%d_%H%M}.xlsx")
    calisma_kitabi_kaydet(sayfalar, yol, {k: f"Veri Profili - {k}" for k in sayfalar})
    print(f"\nVeri profili yazıldı: {yol}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
