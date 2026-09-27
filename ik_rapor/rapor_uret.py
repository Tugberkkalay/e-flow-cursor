"""raporlar/ klasöründeki SQL dosyalarını çalıştırıp biçimli Excel raporları üretir.

SQL dosyası başındaki yorum satırları rapor meta bilgisini taşır:
    -- rapor: Ücret Tarihçesi Raporu        (Excel'deki başlık)
    -- veritabani: EFLOW                    (boş ise ayarlar.toml'daki veritabanı)
    -- sayfa: Detay                         (sayfa adı; aynı dosyada birden çok sorgu için "-- sayfa:" ile ayrılır)
    -- durum: taslak                        (taslak olanlar çalıştırılmaz)
Parametreler {baslangic_tarihi} biçiminde yazılır ve ayarlar.toml [raporlar.parametreler] bölümünden doldurulur.

Kullanım:  python -m ik_rapor.rapor_uret [rapor_adi ...] [--hepsi] [--tek-dosya]
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from . import ayarlar as ayar_mod
from .baglanti import baglan, sorgula
from .excel import calisma_kitabi_kaydet

META_DESENI = re.compile(r"^\s*--\s*(rapor|veritabani|sayfa|durum|aciklama)\s*:\s*(.*?)\s*$", re.IGNORECASE)


@dataclass
class Rapor:
    dosya: Path
    ad: str
    baslik: str
    veritabani: str = ""
    durum: str = "hazir"
    aciklama: str = ""
    sayfalar: list[tuple[str, str]] = field(default_factory=list)  # (sayfa adı, sql)


def _parametreleri_uygula(sql: str, parametreler: dict) -> str:
    def degistir(m: re.Match) -> str:
        anahtar = m.group(1)
        if anahtar not in parametreler:
            raise KeyError(f"SQL parametresi ayarlar.toml'da tanımlı değil: {{{anahtar}}}")
        v = parametreler[anahtar]
        if isinstance(v, (dt.date, dt.datetime)):
            return f"'{v.isoformat()}'"
        if isinstance(v, str):
            return "'" + v.replace("'", "''") + "'"
        return str(v)

    return re.sub(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", degistir, sql)


def rapor_oku(dosya: Path) -> Rapor:
    r = Rapor(dosya=dosya, ad=dosya.stem, baslik=dosya.stem.replace("_", " ").title())
    govde: list[str] = []
    sayfa_adi = "Rapor"
    sayfalar: list[tuple[str, list[str]]] = []
    for satir in dosya.read_text(encoding="utf-8").splitlines():
        m = META_DESENI.match(satir)
        if not m:
            govde.append(satir)
            continue
        anahtar, deger = m.group(1).lower(), m.group(2)
        if anahtar == "rapor":
            r.baslik = deger or r.baslik
        elif anahtar == "veritabani":
            r.veritabani = deger
        elif anahtar == "durum":
            r.durum = deger.lower() or "hazir"
        elif anahtar == "aciklama":
            r.aciklama = deger
        elif anahtar == "sayfa":
            if "".join(govde).strip():
                sayfalar.append((sayfa_adi, govde))
            sayfa_adi, govde = deger or f"Sayfa{len(sayfalar) + 1}", []
    if "".join(govde).strip():
        sayfalar.append((sayfa_adi, govde))
    r.sayfalar = [(ad, "\n".join(s)) for ad, s in sayfalar]
    return r


def raporlari_bul(klasor: Path, secilen: list[str]) -> list[Rapor]:
    raporlar = [rapor_oku(p) for p in sorted(klasor.glob("*.sql"))]
    if secilen:
        istenen = {s.lower().removesuffix(".sql") for s in secilen}
        bulunan = [r for r in raporlar if r.ad.lower() in istenen]
        eksik = istenen - {r.ad.lower() for r in bulunan}
        if eksik:
            raise SystemExit(f"Bulunamayan rapor(lar): {', '.join(sorted(eksik))}. Mevcut: {', '.join(r.ad for r in raporlar)}")
        return bulunan
    return raporlar


def rapor_calistir(ayar: dict, r: Rapor) -> dict[str, pd.DataFrame]:
    parametreler = ayar.get("raporlar", {}).get("parametreler", {})
    sonuc: dict[str, pd.DataFrame] = {}
    with baglan(ayar, r.veritabani or None) as conn:
        for sayfa, sql in r.sayfalar:
            sql_son = _parametreleri_uygula(sql, parametreler)
            df = sorgula(conn, sql_son)
            sonuc[sayfa] = df
            print(f"      {sayfa}: {len(df):,} satır")
    return sonuc


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="SQL -> Excel rapor üretimi")
    p.add_argument("raporlar", nargs="*", help="Çalıştırılacak rapor adları (dosya adı, uzantısız). Boş = hazır olanların hepsi")
    p.add_argument("--hepsi", action="store_true", help="Taslak durumundaki raporları da dene")
    p.add_argument("--tek-dosya", action="store_true", help="Tüm raporları tek Excel dosyasında ayrı sayfalar olarak yaz")
    p.add_argument("--liste", action="store_true", help="Raporları listele ve çık")
    args = p.parse_args(argv)

    ayar = ayar_mod.yukle()
    klasor = ayar_mod.PROJE_KOKU / ayar.get("raporlar", {}).get("sql_klasoru", "raporlar")
    raporlar = raporlari_bul(klasor, args.raporlar)

    if args.liste:
        for r in raporlar:
            print(f"{r.ad:45} [{r.durum:6}] {r.baslik}  -> {len(r.sayfalar)} sayfa" + (f"  ({r.aciklama})" if r.aciklama else ""))
        return 0

    calisacak = [r for r in raporlar if args.hepsi or args.raporlar or r.durum != "taslak"]
    atlanan = [r.ad for r in raporlar if r not in calisacak]
    if atlanan:
        print(f"Taslak olduğu için atlanan raporlar: {', '.join(atlanan)}  (--hepsi ile zorlayabilirsiniz)")
    if not calisacak:
        print("Çalıştırılacak rapor yok.")
        return 1

    cikti = ayar_mod.cikti_klasoru(ayar)
    ek = f"_{dt.datetime.now():%Y%m%d_%H%M}" if ayar.get("raporlar", {}).get("tarih_eki", True) else ""
    birlesik: dict[str, pd.DataFrame] = {}
    basliklar: dict[str, str] = {}
    hata_sayisi = 0
    for r in calisacak:
        print(f"  -> {r.baslik} ({r.dosya.name})")
        try:
            sayfalar = rapor_calistir(ayar, r)
        except Exception as e:  # noqa: BLE001
            hata_sayisi += 1
            print(f"      HATA: {e}")
            continue
        if args.tek_dosya:
            for sayfa, df in sayfalar.items():
                anahtar = r.ad if len(sayfalar) == 1 else f"{r.ad[:20]}_{sayfa}"
                birlesik[anahtar] = df
                basliklar[anahtar] = f"{r.baslik} - {sayfa}" if len(sayfalar) > 1 else r.baslik
        else:
            yol = calisma_kitabi_kaydet(sayfalar, cikti / f"{r.ad}{ek}.xlsx", {s: r.baslik for s in sayfalar})
            print(f"      yazıldı: {yol}")
    if args.tek_dosya and birlesik:
        yol = calisma_kitabi_kaydet(birlesik, cikti / f"ik_raporlari{ek}.xlsx", basliklar)
        print(f"\nTüm raporlar yazıldı: {yol}")
    return 1 if hata_sayisi else 0


if __name__ == "__main__":
    sys.exit(main())
