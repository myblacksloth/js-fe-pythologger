# js-fe Web Logger / js-fe Web Logger

## 🇮🇹 Panoramica

js-fe Web Logger è un microservizio Flask che riceve eventi di log via HTTP, li persiste su disco e permette di consultarli tramite API. È pensato per ambienti con dischi lenti: l’I/O su file viene gestito da un worker asincrono così da non bloccare le richieste. Può essere eseguito via server di sviluppo o in produzione con Waitress oppure impacchettato in un eseguibile standalone tramite PyInstaller.

### Funzionalità principali
- Endpoint `POST /logger` per registrare log in vari livelli (`debug`, `info`, `warning`, `error`, `critical`).
- Persistenza su file in rotazione giornaliera nella cartella `logs/`.
- Coda asincrona e thread dedicato per le scritture su disco.
- Endpoint `GET /logs` per consultare i log in formato JSON.
- Endpoint `GET /health` per verificare lo stato del servizio.
- Script di build per Windows (`build.bat`) e Linux/macOS (`build.sh`) con PyInstaller.
- Script di run: `run.sh` (sviluppo) e `run-prod.sh` (produzione con Waitress).

### Requisiti
- Python 3.10+
- Ambiente virtuale `venv`
- Dipendenze elencate in `requirements.txt`

### Installazione rapida
```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

### Avvio in sviluppo
```bash
./run.sh
```

### Avvio in produzione (Waitress)
```bash
chmod +x run-prod.sh
./run-prod.sh
```

### Build eseguibile
- Linux/macOS: `chmod +x build.sh && ./build.sh`
- Windows: `build.bat`

L’eseguibile viene creato in `dist/`.

### API
- `POST /logger?source=<sorgente>&level=<livello>`
  - Body JSON: `{ "message": "...", "level": "info", "source": "client" }`
  - Restituisce stato e timestamp.
- `GET /logs?date=YYYY-MM-DD`
  - Restituisce elenco di log con `timestamp`, `logger`, `level`, `source`, `message`.
- `GET /health`
  - Restituisce lo stato corrente del servizio.

### Arresto controllato
Premere `CTRL+C` invia un segnale che svuota la coda dei log, aspetta la scrittura su disco e termina in modo pulito.

---

## 🇬🇧 Overview

js-fe Web Logger is a Flask microservice that receives log events over HTTP, persists them to disk, and exposes APIs to retrieve them. It targets environments with slow disks: disk I/O is handled in an asynchronous worker to keep request handling responsive. You can run it with the development server, use Waitress for production, or bundle it into a standalone executable via PyInstaller.

### Key Features
- `POST /logger` endpoint to record logs at multiple levels (`debug`, `info`, `warning`, `error`, `critical`).
- Daily rotating files stored under `logs/`.
- Asynchronous queue plus dedicated worker thread for disk writes.
- `GET /logs` endpoint returning JSON log entries.
- `GET /health` endpoint to check service status.
- Run scripts: `run.sh` (development) and `run-prod.sh` (production with Waitress).
- Build scripts: `build.bat` (Windows) and `build.sh` (Linux/macOS) using PyInstaller.

### Requirements
- Python 3.10+
- Virtual environment `venv`
- Dependencies listed in `requirements.txt`

### Quick Setup
```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

### Development Run
```bash
./run.sh
```

### Production Run (Waitress)
```bash
chmod +x run-prod.sh
./run-prod.sh
```

### Build Executable
- Windows: `build.bat`
- Linux/macOS: `chmod +x build.sh && ./build.sh`

The executable is generated inside `dist/`.

### API
- `POST /logger?source=<source>&level=<level>`
  - JSON body: `{ "message": "...", "level": "info", "source": "client" }`
  - Returns status information and timestamp.
- `GET /logs?date=YYYY-MM-DD`
  - Returns log entries with `timestamp`, `logger`, `level`, `source`, `message`.
- `GET /health`
  - Returns the current health status.

### Graceful Shutdown
Pressing `CTRL+C` triggers the signal handler: it flushes the queue, waits for pending logs, and exits cleanly.
