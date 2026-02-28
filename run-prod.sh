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

if [[ ! -d "venv" ]]; then
    echo "ERRORE: ambiente virtuale non trovato. Crea venv prima di avviare." >&2
    exit 1
fi

source venv/bin/activate

if ! python3 -c "import waitress" >/dev/null 2>&1; then
    echo "Installazione waitress..."
    python3 -m pip install waitress
fi

if [[ ! -f "src/main.py" ]]; then
    echo "ERRORE: impossibile trovare src/main.py" >&2
    exit 1
fi

exec python3 -m waitress --listen=0.0.0.0:5000 src.main:app
