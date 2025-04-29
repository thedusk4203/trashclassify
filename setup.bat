@echo off
echo ECO CLASSIFY - SETUP SCRIPT
echo =========================
echo.

REM Kiem tra phien ban Python
echo Dang kiem tra phien ban Python...
python --version > temp.txt 2>&1
set /p python_version=<temp.txt
del temp.txt

echo %python_version% | findstr /C:"Python 3.10" > nul
if %errorlevel% equ 0 (
    echo Python phien ban 3.10.x da duoc cai dat.
) else (
    echo Python phien ban 3.10.x chua duoc cai dat.
    echo Dang tai xuong Python 3.10.11...
    
    REM Tai xuong Python 3.10.11
    curl -o python-3.10.11-amd64.exe https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe
    
    echo Dang cai dat Python 3.10.11...
    REM Cai dat Python voi cac tuy chon: them vao PATH, cai pip
    python-3.10.11-amd64.exe /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1
    
    echo Cai dat Python 3.10.11 hoan tat.
    del python-3.10.11-amd64.exe
)

echo.
echo Dang tao moi truong ao...
python -m venv env
call env\Scripts\activate.bat

echo.
echo Dang cap nhat pip...
python -m pip install --upgrade pip

echo.
echo Dang cai dat cac thu vien tu requirements.txt...
pip install -r requirements.txt

echo.
echo Cai dat hoan tat!
echo.
echo Dang khoi dong ung dung...
echo Cho doi 20 giay truoc khi mo trinh duyet...
start /min cmd /c "timeout /t 60 /nobreak && start http://localhost:5000"
python app.py

pause