@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

set "valid-python-version-list=3.14 3.13 3.12 3.11 3.10 3.9"
set "python-version=0"

(for %%v in (%valid-python-version-list%) do (
    py -%%v --version >nul 2>&1
    if !errorlevel! == 0 (
        set "python-version=%%v"
        goto run-gui
    )
))

echo [!] Python 3.9 이상이 설치되어 있어야 이 프로그램을 실행할 수 있습니다.
pause
goto end

:run-gui
echo 감지된 Python 버전: %python-version%
py -%python-version% ./source/main.py
if !errorlevel! equ 0 (
    goto end
) else (
    echo [!] 프로그램 오류로 종료됨. 아무 키나 누르면 창이 닫힙니다.
    pause
)

:end