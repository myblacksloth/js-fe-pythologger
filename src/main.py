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

# pip install waitress

import sys
import os

# FIX 1 — PyInstaller su Windows: necessario per il multiprocessing/freeze
# Deve essere la prima cosa eseguita nel main, prima di qualsiasi import pesante
if sys.platform == "win32":
    import multiprocessing
    multiprocessing.freeze_support()

from flask import Flask, request, jsonify
import logging
import atexit
import queue
import threading
import signal
from datetime import datetime

# FIX 2 — Windows Quick Edit Mode: disabilita la modalità che blocca il processo
# quando l'utente clicca sulla finestra del terminale (causa il blocco che si risolve con Invio)
def disable_quick_edit_mode():
    if sys.platform != "win32":
        return
    try:
        import ctypes
        import ctypes.wintypes
        kernel32 = ctypes.windll.kernel32
        # Ottieni l'handle dello stdin
        handle = kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE
        # Leggi la modalità corrente
        mode = ctypes.wintypes.DWORD()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            # Rimuovi ENABLE_QUICK_EDIT_MODE (0x0040) e ENABLE_INSERT_MODE (0x0020)
            new_mode = mode.value & ~0x0040 & ~0x0020
            kernel32.SetConsoleMode(handle, new_mode)
    except Exception:
        pass  # Se fallisce (es. nessuna console), ignora silenziosamente

app = Flask(__name__)

# Configurazione directory per i log
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

try:
    LOG_QUEUE_MAX_SIZE = int(os.getenv("LOG_QUEUE_MAX_SIZE", "10000"))
except ValueError:
    LOG_QUEUE_MAX_SIZE = 10000

# Coda condivisa per delegare la scrittura su disco a un thread dedicato
log_queue = queue.Queue(maxsize=LOG_QUEUE_MAX_SIZE if LOG_QUEUE_MAX_SIZE > 0 else 0)
worker_lock = threading.Lock()
log_worker = None
shutdown_event = None
atexit_registered = False
signal_registered = False

def setup_file_logger():
    today = datetime.now().strftime("%Y-%m-%d")
    log_filename = os.path.join(LOG_DIR, f"app_log_{today}.log")
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_logger = logging.getLogger('file_logger')
    file_logger.setLevel(logging.DEBUG)
    for handler in file_logger.handlers[:]:
        file_logger.removeHandler(handler)
    file_logger.addHandler(file_handler)
    return file_logger

def setup_console_logger():
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # FIX 3 — Su Windows con exe senza console (--noconsole), stdout/stderr possono essere None
    # In quel caso non creare l'handler console per evitare crash
    if sys.stdout is None:
        console_logger = logging.getLogger('console_logger')
        console_logger.setLevel(logging.DEBUG)
        console_logger.addHandler(logging.NullHandler())
        return console_logger

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_logger = logging.getLogger('console_logger')
    console_logger.setLevel(logging.DEBUG)
    for handler in console_logger.handlers[:]:
        console_logger.removeHandler(handler)
    console_logger.addHandler(console_handler)
    return console_logger

def ensure_file_logger_current():
    global file_logger
    current_date = datetime.now().strftime("%Y-%m-%d")
    expected_filename = os.path.join(LOG_DIR, f"app_log_{current_date}.log")
    current_file = None
    if file_logger and file_logger.handlers:
        current_file = file_logger.handlers[0].baseFilename
    if current_file != os.path.abspath(expected_filename):
        file_logger = setup_file_logger()

def log_writer_worker():
    global file_logger
    while True:
        if shutdown_event and shutdown_event.is_set() and log_queue.empty():
            break
        try:
            log_level, formatted_message = log_queue.get(timeout=0.5)
        except queue.Empty:
            continue
        try:
            ensure_file_logger_current()
            if file_logger:
                file_logger.log(log_level, formatted_message)
        except Exception as log_error:
            if console_logger:
                try:
                    console_logger.error(f"Errore durante la scrittura del log: {log_error}")
                except Exception:
                    pass  # FIX 4 — evita crash del worker se anche la console fallisce
        finally:
            log_queue.task_done()

def start_log_worker():
    global log_worker, shutdown_event, atexit_registered
    with worker_lock:
        if log_worker and log_worker.is_alive():
            return
        shutdown_event = threading.Event()
        log_worker = threading.Thread(target=log_writer_worker, name="LogWriterThread", daemon=True)
        log_worker.start()
        if not atexit_registered:
            atexit.register(stop_log_worker)
            atexit_registered = True

def stop_log_worker():
    global log_worker, shutdown_event
    with worker_lock:
        if shutdown_event:
            shutdown_event.set()
        if log_worker and log_worker.is_alive():
            log_worker.join(timeout=2)
        log_worker = None
        shutdown_event = None

def handle_interrupt(signum, frame):
    if console_logger:
        try:
            console_logger.info("Ricevuto segnale di interruzione: completamento log in corso...")
        except Exception:
            pass
    if shutdown_event:
        shutdown_event.set()
    try:
        log_queue.join()
    except Exception as join_error:
        if console_logger:
            try:
                console_logger.error(f"Errore durante l'attesa della coda: {join_error}")
            except Exception:
                pass
    stop_log_worker()
    raise SystemExit(0)

def register_signal_handlers():
    global signal_registered
    if signal_registered or threading.current_thread() is not threading.main_thread():
        return
    try:
        signal.signal(signal.SIGINT, handle_interrupt)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, handle_interrupt)
        signal_registered = True
    except (OSError, ValueError):
        # FIX 5 — Su Windows con exe, la registrazione dei segnali può fallire
        # in thread non-main o in contesti senza console: ignora silenziosamente
        pass

file_logger = None
console_logger = None

def initialize_loggers():
    global file_logger, console_logger
    with worker_lock:
        if console_logger is None:
            console_logger = setup_console_logger()
        if file_logger is None:
            file_logger = setup_file_logger()
    start_log_worker()
    register_signal_handlers()

def get_log_level(level_str):
    level_map = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'warn': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }
    return level_map.get(level_str.lower(), logging.INFO)

@app.route('/logger', methods=['POST'])
def log_message():
    global file_logger, log_worker
    try:
        if console_logger is None or file_logger is None or not log_worker or not log_worker.is_alive():
            initialize_loggers()

        source = request.args.get('source')
        level = request.args.get('level')

        if request.is_json:
            data = request.get_json()
            message = data.get('message', '') if data else ''
            if data:
                source = data.get('source', source)
                level = data.get('level', level)
        else:
            message = request.get_data(as_text=True)

        if not message:
            return jsonify({
                'error': 'Nessun messaggio fornito nel corpo della richiesta'
            }), 400

        log_level = get_log_level(level or 'info')

        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            client_ip = forwarded_for.split(',')[0].strip()
        else:
            client_ip = request.remote_addr or 'unknown'

        source_value = source or 'unknown'
        formatted_message = f"[{source_value}@{client_ip}] {message}"

        if console_logger:
            try:
                console_logger.log(log_level, formatted_message)
            except Exception:
                pass  # FIX 6 — non far crashare la request se la console non è disponibile

        try:
            log_queue.put_nowait((log_level, formatted_message))
        except queue.Full:
            overload_msg = "Coda di logging piena; richiesta scartata"
            if console_logger:
                try:
                    console_logger.error(overload_msg)
                except Exception:
                    pass
            return jsonify({'error': overload_msg}), 503

        return jsonify({
            'status': 'success',
            'message': 'Log registrato con successo',
            'source': source_value,
            'remote_ip': client_ip,
            'level': (level or 'info'),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 200

    except Exception as e:
        error_msg = f"Errore durante la registrazione del log: {str(e)}"
        if console_logger:
            try:
                console_logger.error(error_msg)
            except Exception:
                pass
        if log_worker and log_worker.is_alive():
            try:
                log_queue.put_nowait((logging.ERROR, error_msg))
            except queue.Full:
                pass
        return jsonify({'error': error_msg}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }), 200

@app.route('/logs', methods=['GET'])
def get_logs():
    requested_date = request.args.get('date') or datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(LOG_DIR, f"app_log_{requested_date}.log")
    if not os.path.exists(log_path):
        return jsonify([]), 200

    entries = []
    try:
        with open(log_path, 'r', encoding='utf-8') as log_file:
            for raw_line in log_file:
                line = raw_line.strip()
                if not line:
                    continue
                parts = line.split(' - ', 3)
                if len(parts) == 4:
                    timestamp, logger_name, level_name, message = parts
                    source_value = None
                    client_ip = None
                    if message.startswith('['):
                        closing = message.find(']')
                        if closing != -1:
                            bracket_content = message[1:closing]
                            if '@' in bracket_content:
                                source_value, client_ip = bracket_content.split('@', 1)
                            else:
                                source_value = bracket_content
                            message = message[closing + 1:].lstrip()
                    entries.append({
                        'timestamp': timestamp,
                        'logger': logger_name,
                        'level': level_name,
                        'source': source_value,
                        'remote_ip': client_ip,
                        'message': message
                    })
                else:
                    entries.append({'raw': line})
    except OSError as read_error:
        if console_logger:
            try:
                console_logger.error(f"Errore durante la lettura del log: {read_error}")
            except Exception:
                pass
        return jsonify({'error': 'Impossibile leggere il file di log richiesto'}), 500

    return jsonify(entries), 200

if __name__ == '__main__':
    # FIX 1 — disabilita Quick Edit Mode prima di qualsiasi output
    disable_quick_edit_mode()

    initialize_loggers()

    print("==========================================")
    print("      js-fe Web Logger - Server")
    print("==========================================")
    license_banner = """
js-fe-pythologger
Copyright (C) 2026 Antonio Maulucci (https://github.com/myblacksloth)

Questo programma è software libero: puoi ridistribuirlo e/o modificarlo
secondo i termini della GNU Affero General Public License come pubblicata
dalla Free Software Foundation, versione 3 della Licenza.

Questo programma è distribuito nella speranza che sia utile, ma SENZA
ALCUNA GARANZIA; senza neppure la garanzia implicita di COMMERCIABILITÀ
o di IDONEITÀ PER UN PARTICOLARE SCOPO. Vedi la GNU Affero General Public License
per maggiori dettagli.

Dovresti aver ricevuto una copia della GNU Affero General Public License
insieme a questo programma. In caso contrario, vedi <https://www.gnu.org/licenses/>.
"""
    print(license_banner)
    print("==========================================")
    print("Stato: in avvio")
    print("Endpoint disponibili:")
    print("  POST /logger?source=<sorgente>&level=<livello>")
    print("  GET  /health")
    print("  GET  /logs?date=YYYY-MM-DD")
    print(f"Log salvati in: {os.path.abspath(LOG_DIR)}")
    print("Premi CTRL+C per un arresto controllato")
    print("==========================================")

    # FIX 7 — usa waitress invece di Flask dev server in produzione/exe
    # Flask dev server (app.run) non è thread-safe e su Windows con exe
    # causa lentezze e instabilità. Waitress è un WSGI server production-ready.
    # Installa con: pip install waitress
    try:
        from waitress import serve
        print("Server WSGI: waitress (production)")
        print("==========================================")
        serve(app, host='0.0.0.0', port=5000, threads=4)
    except ImportError:
        # Fallback al dev server se waitress non è installato
        print("ATTENZIONE: waitress non trovato, uso Flask dev server (non consigliato per exe)")
        print("Installa waitress con: pip install waitress")
        print("==========================================")
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True, use_reloader=False)


