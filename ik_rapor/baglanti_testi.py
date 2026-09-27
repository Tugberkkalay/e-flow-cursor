"""Bağlantı ayarlarını doğrular: sürücü, sunucu, kullanıcı ve erişilebilen veritabanları.

Kullanım:  python -m ik_rapor.baglanti_testi
"""
from __future__ import annotations

import sys

import pyodbc

from . import ayarlar as ayar_mod
from .baglanti import baglan, baglanti_dizesi, kullanici_veritabanlari, sorgula


def main() -> int:
    ayar = ayar_mod.yukle()
    print("Kurulu ODBC sürücüleri:", ", ".join(pyodbc.drivers()) or "(yok)")
    try:
        dize = baglanti_dizesi(ayar)
        print("Bağlantı dizesi:", ";".join(p for p in dize.split(";") if not p.startswith("PWD=")))
        with baglan(ayar, "master") as conn:
            bilgi = sorgula(conn, "SELECT @@SERVERNAME AS Sunucu, SUSER_SNAME() AS Kullanici, @@VERSION AS Surum")
            print(f"Bağlandı. Sunucu: {bilgi.at[0, 'Sunucu']}  Kullanıcı: {bilgi.at[0, 'Kullanici']}")
            print("Sürüm:", str(bilgi.at[0, "Surum"]).splitlines()[0])
            vtler = kullanici_veritabanlari(conn)
            print(f"Erişilebilen kullanıcı veritabanları ({len(vtler)}): {', '.join(vtler) or '-'}")
        return 0
    except Exception as e:  # noqa: BLE001
        print("BAĞLANTI HATASI:", e)
        print("\nKontrol listesi:\n"
              " - Şirket ağında / VPN'de misiniz ve BISVM-SQL2019 makinesine ping atılabiliyor mu?\n"
              " - 'ODBC Driver 17/18 for SQL Server' kurulu mu?\n"
              " - Windows hesabınızın SQL Server'da giriş yetkisi var mı? (Integrated Security)\n"
              " - Encrypt=yes ise sertifika sorunu için trust_server_certificate=true olmalı.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
