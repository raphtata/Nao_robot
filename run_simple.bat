@echo off
echo ============================================================
echo         CONTROLE DU ROBOT NAO V3 (Python 2.7)
echo ============================================================
echo.

if not exist "C:\Python27\python.exe" (
    echo ERREUR: Python 2.7 32-bit non trouve en C:\Python27\
    echo Installez-le depuis: https://www.python.org/ftp/python/2.7.18/python-2.7.18.msi
    pause
    exit /b 1
)

echo Python 2.7 trouve: C:\Python27\python.exe
echo.

C:\Python27\python.exe -c "import struct; print('Architecture: ' + ('64-bit' if struct.calcsize('P') * 8 == 64 else '32-bit'))"
echo.

SET PATH=C:\Program Files (x86)\Softbank Robotics\Choregraphe Suite 2.5\bin;%PATH%

C:\Python27\python.exe nao_with_local_sdk.py

pause
