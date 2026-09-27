from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

BASLIK_DOLGU = PatternFill("solid", fgColor="1F4E78")
BASLIK_YAZI = Font(bold=True, color="FFFFFF")
INCE = Side(style="thin", color="BFBFBF")
KENARLIK = Border(left=INCE, right=INCE, top=INCE, bottom=INCE)
MAKS_GENISLIK = 60
MAKS_SATIR = 1_048_575  # Excel sınırı (başlık hariç)


def _sayfa_adi(ad: str) -> str:
    yasak = '[]:*?/\\'
    temiz = "".join("_" if c in yasak else c for c in ad).strip()
    return (temiz or "Sayfa")[:31]


def _hucre_degeri(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, pd.Timestamp):
        return v.to_pydatetime()
    if isinstance(v, (bytes, bytearray, memoryview)):
        return bytes(v).hex()
    if isinstance(v, (dict, list, tuple, set)):
        return str(v)
    return v


def dataframe_yaz(ws: Worksheet, df: pd.DataFrame, baslik: str | None = None) -> None:
    satir = 1
    if baslik:
        ws.cell(row=1, column=1, value=baslik).font = Font(bold=True, size=13)
        ws.cell(row=2, column=1, value=f"Oluşturma: {dt.datetime.now():%d.%m.%Y %H:%M}   Satır: {len(df):,}").font = Font(
            italic=True, color="7F7F7F"
        )
        satir = 4

    kolonlar = [str(c) for c in df.columns]
    for j, ad in enumerate(kolonlar, start=1):
        h = ws.cell(row=satir, column=j, value=ad)
        h.fill, h.font, h.border = BASLIK_DOLGU, BASLIK_YAZI, KENARLIK
        h.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    if len(df) > MAKS_SATIR:
        df = df.head(MAKS_SATIR)

    tarih_kolonlari = {i for i, t in enumerate(df.dtypes) if "datetime" in str(t)}
    sayi_kolonlari = {i for i, t in enumerate(df.dtypes) if "float" in str(t)}
    for r, kayit in enumerate(df.itertuples(index=False, name=None), start=satir + 1):
        for j, v in enumerate(kayit):
            c = ws.cell(row=r, column=j + 1, value=_hucre_degeri(v))
            if j in tarih_kolonlari:
                c.number_format = "dd.mm.yyyy" if _sadece_tarih(v) else "dd.mm.yyyy hh:mm"
            elif j in sayi_kolonlari:
                c.number_format = "#,##0.00"

    son_satir = satir + len(df)
    son_kolon = max(len(kolonlar), 1)
    ws.auto_filter.ref = f"A{satir}:{get_column_letter(son_kolon)}{son_satir}"
    ws.freeze_panes = ws.cell(row=satir + 1, column=1)
    _genislik_ayarla(ws, df, kolonlar, satir)


def _sadece_tarih(v) -> bool:
    if isinstance(v, (pd.Timestamp, dt.datetime)):
        return v.hour == 0 and v.minute == 0 and v.second == 0
    return True


def _genislik_ayarla(ws: Worksheet, df: pd.DataFrame, kolonlar: list[str], baslik_satiri: int) -> None:
    ornek = df.head(500)
    for j, ad in enumerate(kolonlar, start=1):
        en_uzun = len(ad)
        if len(ornek):
            seri = ornek.iloc[:, j - 1]
            if "datetime" in str(seri.dtype):
                en_uzun = max(en_uzun, 16)
            else:
                en_uzun = max(en_uzun, int(seri.astype(str).str.len().max() or 0))
        ws.column_dimensions[get_column_letter(j)].width = min(max(en_uzun + 2, 8), MAKS_GENISLIK)
    ws.row_dimensions[baslik_satiri].height = 30


def calisma_kitabi_kaydet(sayfalar: dict[str, pd.DataFrame], yol: Path, basliklar: dict[str, str] | None = None) -> Path:
    wb = Workbook()
    wb.remove(wb.active)
    kullanilan: set[str] = set()
    for ad, df in sayfalar.items():
        sayfa = _sayfa_adi(ad)
        i = 2
        while sayfa in kullanilan:
            sayfa = _sayfa_adi(f"{ad[:27]}_{i}")
            i += 1
        kullanilan.add(sayfa)
        ws = wb.create_sheet(sayfa)
        dataframe_yaz(ws, df, (basliklar or {}).get(ad))
    yol.parent.mkdir(parents=True, exist_ok=True)
    wb.save(yol)
    return yol
