#!/usr/bin/env bash

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

set -euo pipefail

if [[ "${DEBUG:-}" != "" ]]; then
    set -x
fi

echo "=========================================="
echo "    js-fe-pythologger - Build Script"
echo "=========================================="
echo

echo "[1/4] Attivazione ambiente virtuale..."
if [[ ! -f "venv/bin/activate" ]]; then
    echo "ERRORE: Ambiente virtuale non trovato. Crea l'ambiente con 'python3 -m venv venv'"
    exit 1
fi
source venv/bin/activate || {
    echo "ERRORE: Impossibile attivare l'ambiente virtuale"
    exit 1
}

echo "[2/4] Installazione dipendenze..."
python3 -m pip install -r requirements.txt || {
    echo "ERRORE: Installazione dipendenze fallita"
    exit 1
}

echo "[3/4] Pulizia build precedenti..."
rm -rf dist build

echo "[4/4] Creazione eseguibile..."
pyinstaller --onefile --console --name="js-fe-pythologger" src/main.py || {
    echo "ERRORE: Creazione eseguibile fallita"
    exit 1
}

echo
echo "=========================================="
echo "          BUILD COMPLETATO!"
echo "=========================================="
echo
if [[ "$(uname -s)" == "Darwin" ]]; then
    TARGET="dist/js-fe-pythologger"
    echo "L'eseguibile e' stato creato in: ${TARGET}"
    echo "Nota: macOS potrebbe richiedere xattr -dr com.apple.quarantine ${TARGET}"
else
    echo "L'eseguibile e' stato creato in: dist/js-fe-pythologger"
fi
echo
echo "Come usare il pacchetto:" 
echo "1. Copia l'eseguibile dove preferisci"
echo "2. Esegui il file generato"
echo "3. Il server sara' disponibile su http://localhost:5000"
echo "4. I log verranno salvati nella cartella 'logs' accanto all'eseguibile"
echo