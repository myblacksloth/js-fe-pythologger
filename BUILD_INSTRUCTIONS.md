# Come generare il pacchetto eseguibile

## Requisiti di base

- Python 3.10 o superiore installato sul sistema
- Ambiente virtuale creato nella cartella `venv`
- Dipendenze installate (gestite automaticamente dagli script di build)

## Linux e macOS (binario standalone)

### Script automatico (consigliato)

1. Assicurati che lo script sia eseguibile (solo la prima volta):
   ```bash
   chmod +x build.sh
   ```
2. Esegui lo script dalla root del progetto:
   ```bash
   ./build.sh
   ```
3. Al termine troverai il binario in `dist/js-fe-pythologger` (senza estensione).

Lo script:
- Verifica la presenza dell'ambiente virtuale
- Attiva `venv/bin/activate`
- Installa le dipendenze definite in `requirements.txt`
- Rimuove le build precedenti
- Richiama PyInstaller con i parametri già configurati

### Procedura manuale

```bash
source venv/bin/activate
python3 -m pip install -r requirements.txt
pyinstaller --onefile --console --name="js-fe-pythologger" src/main.py
```

### Note per macOS

- Al primo avvio il sistema potrebbe bloccare il binario. Se necessario esegui:
  ```bash
  xattr -dr com.apple.quarantine dist/js-fe-pythologger
  ```
- La firma/notarizzazione non è inclusa; aggiungila se devi distribuire esternamente.


## Windows (file .exe)

### Script automatico (consigliato)

1. Esegui lo script `build.bat` con un doppio click oppure da PowerShell/CMD:
   ```cmd
   build.bat
   ```
2. Attendi il completamento dei quattro step stampati a video.
3. Troverai l'eseguibile pronto in `dist\js-fe-pythologger.exe`.

Lo script:
- Attiva l'ambiente virtuale
- Installa le dipendenze definite in `requirements.txt`
- Pulisce le cartelle `dist` e `build`
- Genera l'eseguibile finale

### Procedura manuale

```cmd
venv\Scripts\activate
pip install -r requirements.txt
pyinstaller --onefile --console --name="js-fe-pythologger" src/main.py
```

## Dove trovare l'output

- Linux/macOS: `dist/js-fe-pythologger`
- Windows: `dist\js-fe-pythologger.exe`

## Come usare il pacchetto

- Copia l'eseguibile nella cartella desiderata insieme alla directory `logs` (se già creata) oppure lascia che venga generata al primo avvio
- Avvia l'eseguibile; il server sarà disponibile su `http://localhost:5000`
- I log verranno salvati nella cartella `logs` accanto all'eseguibile

## Test rapidi

```bash
curl -X POST "http://localhost:5000/logger?source=test&level=info" -d "Test message"
curl http://localhost:5000/health
```

## Struttura post-build

```
dist/
├── js-fe-pythologger.exe      # Windows
└── js-fe-pythologger          # Linux/macOS
```

## Risoluzione problemi

- Verifica che l'ambiente virtuale sia attivo prima del build
- Controlla che la porta 5000 sia libera oppure modifica la porta nel codice
- Su macOS rimuovi l'attributo di quarantena se necessario
- Su Windows assicurati che l'antivirus non blocchi l'eseguibile

<!--
# js-fe-pythologger
# Copyright (C) 2026 Antonio Maulucci (https://github.com/myblacksloth)
#
# Questo programma è software libero: puoi ridistribuirlo e/o modificarlo
# secondo i termini della GNU Affero General Public License come pubblicata
# dalla Free Software Foundation, versione 3 della Licenza.
#
# Questo programma è distribuito nella speranza che sia utile, ma SENZA
# ALCUNA GARANZIA; senza neppure la garanzia implicita di COMMERCIABILITÀ
# o di IDONEITÀ PER UN PARTICOLARE SCOPO. Vedi la GNU Affero General Public License
# per maggiori dettagli.
#
# Dovresti aver ricevuto una copia della GNU Affero General Public License
# insieme a questo programma. In caso contrario, vedi <https://www.gnu.org/licenses/>.
-->
