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



import requests
import json
from datetime import datetime

def test_logger():
    """Script di test per il logger HTTP"""
    
    base_url = "http://localhost:5000"
    
    # Test dei diversi livelli di log
    test_cases = [
        {"source": "testApp", "level": "info", "message": "Applicazione avviata correttamente"},
        {"source": "database", "level": "warning", "message": "Connessione lenta al database"},
        {"source": "authentication", "level": "error", "message": "Tentativo di login fallito per utente admin"},
        {"source": "scheduler", "level": "debug", "message": "Esecuzione task schedulato completata"},
        {"source": "api", "level": "critical", "message": "Sistema critico non raggiungibile"}
    ]
    
    print("=== TEST LOGGER HTTP ===\n")
    
    # Test health check
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✓ Health check: OK")
            print(f"  Response: {response.json()}\n")
        else:
            print("✗ Health check: FAILED")
            return
    except requests.exceptions.ConnectionError:
        print("✗ Impossibile connettersi al server. Assicurati che il logger sia avviato.")
        print("  Per avviare il server: python src/main.py\n")
        return
    
    # Test dei log
    for i, test_case in enumerate(test_cases, 1):
        try:
            url = f"{base_url}/logger?source={test_case['source']}&level={test_case['level']}"
            headers = {'Content-Type': 'application/json'}
            payload = {"message": test_case['message']}
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                print(f"✓ Test {i}: {test_case['level'].upper()} da {test_case['source']}")
                result = response.json()
                print(f"  Timestamp: {result['timestamp']}")
            else:
                print(f"✗ Test {i}: FAILED (Status: {response.status_code})")
                print(f"  Error: {response.text}")
            
        except Exception as e:
            print(f"✗ Test {i}: ERRORE - {str(e)}")
        
        print()
    
    print("=== TEST COMPLETATI ===")
    print("Controlla:")
    print("1. La console del server per vedere i log stampati")
    print("2. La cartella 'logs/' per i file di log salvati")

if __name__ == "__main__":
    test_logger()