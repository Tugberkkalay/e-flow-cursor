"""Parola korumalı Excel rapor şablonlarını yerelde açar ve yapısını (sayfa, kolon başlıkları, örnek satır) özetler.

Parola sadece bu bilgisayarda kullanılır; çıktı dosyasında yer almaz. Kişisel veri içermemesi için
varsayılan olarak hücre değerleri değil yalnızca başlıklar ve veri tipleri yazılır (--ornek ile ilk N satır eklenir).

Kullanım:  python -m ik_rapor.sablon_incele <klasor_veya_dosyalar...> [--ornek 3] [--kaydet]
"""
from __future__ import annotations

import argparse
import datetime as dt
import getpass
import io
import sys
from pathlib import Path

import msoffcrypto
import pandas as pd
from openpyxl import load_workbook

from . import ayarlar as ayar_mod
from .excel import calisma_kitabi_kaydet


def sifre_coz(dosya: Path, parola: str | None) -> io.BytesIO:
    with open(dosya, "rb") as f:
        of = msoffcrypto.OfficeFile(f)
        if not of.is_encrypted():
            return io.BytesIO(dosya.read_bytes())
        if parola is None:
            raise ValueError("Dosya şifreli; parola gerekli.")
        of.load_key(password=parola)
        out = io.BytesIO()
        of.decrypt(out)
        out.seek(0)
        return out


def _tip_adi(v) -> str:
    if v is None:
        return ""
    if isinstance(v, (dt.datetime, dt.date)):
        return "tarih"
    if isinstance(v, bool):
        return "mantiksal"
    if isinstance(v, (int, float)):
        return "sayi"
    return "metin"


def sablon_ozeti(dosya: Path, icerik: io.BytesIO, ornek: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    wb = load_workbook(icerik, read_only=True, data_only=True)
    sayfa_kayitlari, kolon_kayitlari, ornek_kayitlari = [], [], []
    for ws in wb.worksheets:
        satirlar = ws.iter_rows(values_only=True)
        baslik_satiri, baslik_no = None, 0
        for i, satir in enumerate(satirlar, start=1):
            dolu = [c for c in satir if c not in (None, "")]
            # Başlık: ilk, en az 2 dolu ve çoğunluğu metin olan satır
            if len(dolu) >= 2 and sum(isinstance(c, str) for c in dolu) >= len(dolu) * 0.6:
                baslik_satiri, baslik_no = satir, i
                break
        if baslik_satiri is None:
            sayfa_kayitlari.append({"Dosya": dosya.name, "Sayfa": ws.title, "BaslikSatiri": None, "KolonSayisi": 0, "VeriSatiri": 0})
            continue

        veri_satiri, tipler, bos_sayac = 0, {}, {}
        ornekler = []
        for i, satir in enumerate(ws.iter_rows(min_row=baslik_no + 1, values_only=True), start=baslik_no + 1):
            if all(c in (None, "") for c in satir):
                continue
            veri_satiri += 1
            if len(ornekler) < ornek:
                ornekler.append(satir)
            for j, v in enumerate(satir):
                if v in (None, ""):
                    bos_sayac[j] = bos_sayac.get(j, 0) + 1
                else:
                    tipler.setdefault(j, set()).add(_tip_adi(v))

        sayfa_kayitlari.append(
            {"Dosya": dosya.name, "Sayfa": ws.title, "BaslikSatiri": baslik_no,
             "KolonSayisi": sum(1 for c in baslik_satiri if c not in (None, "")), "VeriSatiri": veri_satiri}
        )
        for j, ad in enumerate(baslik_satiri):
            if ad in (None, ""):
                continue
            kolon_kayitlari.append(
                {"Dosya": dosya.name, "Sayfa": ws.title, "Sira": j + 1, "Kolon": str(ad).strip(),
                 "VeriTipi": "/".join(sorted(tipler.get(j, set()))) or "bos",
                 "BosOrani": round(bos_sayac.get(j, 0) / veri_satiri, 3) if veri_satiri else None}
            )
        for satir in ornekler:
            kayit = {"Dosya": dosya.name, "Sayfa": ws.title}
            for j, ad in enumerate(baslik_satiri):
                if ad not in (None, ""):
                    kayit[str(ad).strip()] = satir[j] if j < len(satir) else None
            ornek_kayitlari.append(kayit)
    wb.close()
    return pd.DataFrame(sayfa_kayitlari), pd.DataFrame(kolon_kayitlari), pd.DataFrame(ornek_kayitlari)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Şifreli Excel şablonlarının yapısını özetle")
    p.add_argument("yollar", nargs="+", help="Excel dosyaları veya klasörler")
    p.add_argument("--ornek", type=int, default=0, help="Her sayfadan yazılacak örnek satır sayısı (varsayılan 0)")
    p.add_argument("--kaydet", action="store_true", help="Şifresi çözülmüş kopyaları cikti/sablonlar/ altına kaydet")
    p.add_argument("--parola", help="Parola (verilmezse güvenli şekilde sorulur)")
    args = p.parse_args(argv)

    dosyalar: list[Path] = []
    for y in args.yollar:
        yol = Path(y)
        if yol.is_dir():
            dosyalar += sorted(list(yol.glob("*.xlsx")) + list(yol.glob("*.xlsm")) + list(yol.glob("*.xls")))
        elif yol.exists():
            dosyalar.append(yol)
        else:
            print(f"Bulunamadı: {yol}")
    if not dosyalar:
        return 1

    parola = args.parola
    sayfalar, kolonlar, ornekler, hatalar = [], [], [], []
    for d in dosyalar:
        print(f"  -> {d.name} ...", end=" ", flush=True)
        try:
            try:
                icerik = sifre_coz(d, parola)
            except ValueError:
                parola = getpass.getpass("Excel parolası: ")
                icerik = sifre_coz(d, parola)
            if args.kaydet:
                hedef = ayar_mod.cikti_klasoru(ayar_mod.yukle()) / "sablonlar" / d.name
                hedef.parent.mkdir(parents=True, exist_ok=True)
                hedef.write_bytes(icerik.getvalue())
                icerik.seek(0)
            s, k, o = sablon_ozeti(d, icerik, args.ornek)
            sayfalar.append(s); kolonlar.append(k); ornekler.append(o)
            print(f"{len(s)} sayfa, {len(k)} kolon")
        except Exception as e:  # noqa: BLE001
            print(f"HATA: {e}")
            hatalar.append({"Dosya": d.name, "Hata": str(e)})

    cikti = {"Sayfalar": pd.concat(sayfalar, ignore_index=True) if sayfalar else pd.DataFrame(),
             "Kolonlar": pd.concat(kolonlar, ignore_index=True) if kolonlar else pd.DataFrame()}
    if args.ornek:
        cikti["OrnekSatirlar"] = pd.concat(ornekler, ignore_index=True) if ornekler else pd.DataFrame()
    if hatalar:
        cikti["Hatalar"] = pd.DataFrame(hatalar)

    yol = ayar_mod.cikti_klasoru(ayar_mod.yukle()) / f"sablon_ozeti_{dt.datetime.now():%Y%m%d_%H%M}.xlsx"
    calisma_kitabi_kaydet(cikti, yol, {k: f"Şablon Özeti - {k}" for k in cikti})
    print(f"\nŞablon özeti yazıldı: {yol}")
    if not cikti["Kolonlar"].empty:
        print("\nKolon başlıkları:")
        for (dosya, sayfa), g in cikti["Kolonlar"].groupby(["Dosya", "Sayfa"], sort=False):
            print(f"  [{dosya} / {sayfa}] " + ", ".join(g["Kolon"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
