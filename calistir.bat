@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

if not exist .venv (
    echo [1/3] Sanal ortam olusturuluyor...
    py -3 -m venv .venv || python -m venv .venv || goto :hata
)
call .venv\Scripts\activate.bat
echo [2/3] Bagimliliklar kuruluyor...
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt || goto :hata

if "%~1"=="" goto :menu
echo [3/3] Calistiriliyor: %*
python -m ik_rapor.%*
goto :son

:menu
echo.
echo  ================= IK Rapor Araci =================
echo   1 - Sema analizi         (tum veritabanlari -^> Excel)
echo   2 - Veri profili         (en buyuk tablolar -^> Excel)
echo   3 - Raporlari uret       (raporlar\*.sql -^> cikti\*.xlsx)
echo   4 - Raporlari listele
echo   5 - Sablonlari incele    (sifreli Excel sablonlari -^> yapi ozeti)
echo   6 - Baglanti testi
echo  ==================================================
set /p secim=Secim (1-6):
if "%secim%"=="1" python -m ik_rapor.sema_analizi
if "%secim%"=="2" python -m ik_rapor.veri_profili
if "%secim%"=="3" python -m ik_rapor.rapor_uret
if "%secim%"=="4" python -m ik_rapor.rapor_uret --liste
if "%secim%"=="5" (
    set /p klasor=Sablon klasoru veya dosya yolu:
    python -m ik_rapor.sablon_incele "%klasor%"
)
if "%secim%"=="6" python -m ik_rapor.baglanti_testi
goto :son

:hata
echo HATA: Kurulum basarisiz. Python 3.11+ kurulu mu? https://www.python.org/downloads/
:son
echo.
pause
