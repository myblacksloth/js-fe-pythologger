@echo off

rem js-fe-pythologger
rem Copyright (C) 2026 Antonio Maulucci (https://github.com/myblacksloth)
rem
rem Questo programma è software libero: puoi ridistribuirlo e/o modificarlo
rem secondo i termini della GNU Affero General Public License come pubblicata
rem dalla Free Software Foundation, versione 3 della Licenza.
rem
rem Questo programma è distribuito nella speranza che sia utile, ma SENZA
rem ALCUNA GARANZIA; senza neppure la garanzia implicita di COMMERCIABILITÀ
rem o di IDONEITÀ PER UN PARTICOLARE SCOPO. Vedi la GNU Affero General Public License
rem per maggiori dettagli.
rem
rem Dovresti aver ricevuto una copia della GNU Affero General Public License
rem insieme a questo programma. In caso contrario, vedi <https://www.gnu.org/licenses/>.

echo ==========================================
echo     js-fe-pythologger - Build Script
echo ==========================================
echo.

REM Attiva l'ambiente virtuale
echo [1/4] Attivazione ambiente virtuale...
call venv\Scripts\activate
if errorlevel 1 (
    echo ERRORE: Impossibile attivare l'ambiente virtuale
    pause
    exit /b 1
)

REM Installa le dipendenze necessarie
echo [2/4] Installazione dipendenze...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERRORE: Installazione dipendenze fallita
    pause
    exit /b 1
)

REM Pulisci build precedenti
echo [3/4] Pulizia build precedenti...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

REM Crea l'eseguibile
echo [4/4] Creazione eseguibile...
pyinstaller --onefile --console --name="js-fe-pythologger" src/main.py
if errorlevel 1 (
    echo ERRORE: Creazione eseguibile fallita
    pause
    exit /b 1
)

echo.
echo ==========================================
echo           BUILD COMPLETATO!
echo ==========================================
echo.
echo L'eseguibile e' stato creato in: dist\js-fe-pythologger.exe
echo.
echo Come usare l'eseguibile:
echo 1. Copia 'js-fe-pythologger.exe' dove vuoi
echo 2. Esegui il file .exe
echo 3. Il server sara' disponibile su http://localhost:5000
echo 4. I log verranno salvati nella cartella 'logs' accanto all'exe
echo.
pause