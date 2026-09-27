from __future__ import annotations

import os
import re
from typing import Any

import pandas as pd
import pyodbc

SISTEM_VERITABANLARI = {"master", "model", "msdb", "tempdb", "distribution", "ReportServer", "ReportServerTempDB"}


def surucu_sec(istenen: str = "") -> str:
    if istenen:
        return istenen
    kurulu = pyodbc.drivers()
    adaylar = [d for d in kurulu if re.search(r"ODBC Driver \d+ for SQL Server", d)]
    if adaylar:
        return max(adaylar, key=lambda d: int(re.search(r"\d+", d).group()))
    if "SQL Server Native Client 11.0" in kurulu:
        return "SQL Server Native Client 11.0"
    if "SQL Server" in kurulu:
        return "SQL Server"
    raise RuntimeError(
        "SQL Server ODBC sürücüsü bulunamadı. 'ODBC Driver 17/18 for SQL Server' kurun: "
        "https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server"
    )


def baglanti_dizesi(ayar: dict[str, Any], veritabani: str | None = None) -> str:
    b = ayar["baglanti"]
    surucu = surucu_sec(b.get("surucu", ""))
    parcalar = [
        f"Driver={{{surucu}}}",
        f"Server={b['sunucu']}",
        f"Encrypt={'yes' if b.get('encrypt', True) else 'no'}",
        f"TrustServerCertificate={'yes' if b.get('trust_server_certificate', True) else 'no'}",
        f"Connect Timeout={b.get('baglanti_zaman_asimi', 30)}",
        "Application Name=ik-rapor-araci",
    ]
    vt = veritabani or b.get("veritabani") or ""
    if vt:
        parcalar.append(f"Database={vt}")
    if b.get("integrated_security", True):
        parcalar.append("Trusted_Connection=yes")
    else:
        kullanici = b.get("kullanici") or os.environ.get("MSSQL_USER", "")
        parola = b.get("parola") or os.environ.get("MSSQL_PASSWORD", "")
        if not kullanici:
            raise RuntimeError("integrated_security=false iken kullanici/parola (veya MSSQL_USER/MSSQL_PASSWORD) gerekir.")
        parcalar += [f"UID={kullanici}", f"PWD={parola}"]
    return ";".join(parcalar)


def baglan(ayar: dict[str, Any], veritabani: str | None = None) -> pyodbc.Connection:
    conn = pyodbc.connect(baglanti_dizesi(ayar, veritabani), autocommit=True)
    conn.timeout = int(ayar["baglanti"].get("komut_zaman_asimi", 300))
    return conn


def sorgula(conn: pyodbc.Connection, sql: str, params: tuple = ()) -> pd.DataFrame:
    cur = conn.cursor()
    cur.execute(sql, params)
    kolonlar = [c[0] for c in cur.description] if cur.description else []
    satirlar = cur.fetchall() if cur.description else []
    cur.close()
    return pd.DataFrame.from_records([tuple(r) for r in satirlar], columns=kolonlar)


def kullanici_veritabanlari(conn: pyodbc.Connection) -> list[str]:
    df = sorgula(
        conn,
        "SELECT name FROM sys.databases WHERE state_desc = 'ONLINE' AND database_id > 4 ORDER BY name",
    )
    return [n for n in df["name"].tolist() if n not in SISTEM_VERITABANLARI]


def koseli(ad: str) -> str:
    return "[" + ad.replace("]", "]]") + "]"
