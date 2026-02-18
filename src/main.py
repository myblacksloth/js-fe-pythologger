
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

from flask import Flask, request, jsonify
import logging
import os
import atexit
import queue
import threading
import signal
from datetime import datetime

app = Flask(__name__)

# Configurazione directory per i log
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

try:
    LOG_QUEUE_MAX_SIZE = int(os.getenv("LOG_QUEUE_MAX_SIZE", "10000"))
except ValueError:
    LOG_QUEUE_MAX_SIZE = 10000

# Coda condivisa per delegare la scrittura su disco a un thread dedicato - evita che la richiesta HTTP attenda l'I/O
log_queue = queue.Queue(maxsize=LOG_QUEUE_MAX_SIZE if LOG_QUEUE_MAX_SIZE > 0 else 0)
worker_lock = threading.Lock()
log_worker = None
shutdown_event = None
atexit_registered = False
signal_registered = False

# Configurazione del logger per file
def setup_file_logger():
    # Calcola il nome del file log in base alla data corrente (un file per giorno)
    today = datetime.now().strftime("%Y-%m-%d")
    log_filename = os.path.join(LOG_DIR, f"app_log_{today}.log")
    
    # Definisce il formato standard per timestamp, logger e messaggio
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Crea l'handler che scrive sul file a  UTF-8
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    # Recupera (o crea) il logger dedicato alla scrittura su file
    file_logger = logging.getLogger('file_logger')
    file_logger.setLevel(logging.DEBUG)
    
    # Scollega eventuali handler preesistenti per evitare duplicazioni
    for handler in file_logger.handlers[:]:
        file_logger.removeHandler(handler)
    
    # Associa il nuovo handler appena configurato
    file_logger.addHandler(file_handler)
    return file_logger

# Configurazione del logger per console
def setup_console_logger():
    # Definisce il formato coerente dei messaggi anche in console
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Prepara l'handler che scrive direttamente su stdout/stderr
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Recupera (o crea) il logger dedicato alla console
    console_logger = logging.getLogger('console_logger')
    console_logger.setLevel(logging.DEBUG)
    
    # Evita di accumulare handler duplicati su successive inizializzazioni
    for handler in console_logger.handlers[:]:
        console_logger.removeHandler(handler)
    
    # Collega l'handler configurato al logger console
    console_logger.addHandler(console_handler)
    return console_logger

# Utility per riallineare l'handler file in base al giorno corrente
def ensure_file_logger_current():
    global file_logger
    # Calcola la data odierna per determinare il file atteso
    current_date = datetime.now().strftime("%Y-%m-%d")
    expected_filename = os.path.join(LOG_DIR, f"app_log_{current_date}.log")
    current_file = None
    # Recupera il path attuale dell'handler se già esistente
    if file_logger and file_logger.handlers:
        current_file = file_logger.handlers[0].baseFilename
    # Se il file corrente non corrisponde a quello atteso (nuovo giorno), ricrea l'handler
    if current_file != os.path.abspath(expected_filename):
        file_logger = setup_file_logger()

def log_writer_worker():
    global file_logger
    while True:
        # Il worker resta in attesa di nuovi messaggi e termina solo quando è stato richiesto lo shutdown e la coda è vuota
        if shutdown_event and shutdown_event.is_set() and log_queue.empty():
            break
        try:
            # Estrae un elemento dalla coda con timeout per poter controllare periodicamente lo shutdown
            log_level, formatted_message = log_queue.get(timeout=0.5)
        except queue.Empty:
            # Nessun elemento disponibile: riprendi il loop e verifica di nuovo
            continue
        try:
            # Verifica giornalmente che l'handler punti al file corretto prima di scrivere
            ensure_file_logger_current()
            if file_logger:
                # Scrive fisicamente sul file usando il livello e il messaggio formattato
                file_logger.log(log_level, formatted_message)
        except Exception as log_error:
            if console_logger:
                # Logga in console eventuali errori di scrittura su disco
                console_logger.error(f"Errore durante la scrittura del log: {log_error}")
        finally:
            # Segnala alla coda che l'elemento è stato processato, anche se in errore
            log_queue.task_done()

def start_log_worker():
    global log_worker, shutdown_event, atexit_registered
    with worker_lock:
        # Evita di creare più thread se quello attuale è ancora operativo
        if log_worker and log_worker.is_alive():
            return
        # Crea il thread daemon che smaltisce la coda e registralo per una chiusura ordinata
        # Evento usato per segnalare al worker la richiesta di shutdown
        shutdown_event = threading.Event()
        # Thread daemon dedicato alla scrittura asincrona dei log
        log_worker = threading.Thread(target=log_writer_worker, name="LogWriterThread", daemon=True)
        # Avvio immediato del worker appena creato
        log_worker.start()
        if not atexit_registered:
            # Garantisce la chiusura pulita registrandosi all'uscita del processo
            atexit.register(stop_log_worker)
            atexit_registered = True

def stop_log_worker():
    global log_worker, shutdown_event
    with worker_lock:
        # Se esiste un evento di shutdown, segnala al worker di terminare appena possibile
        if shutdown_event:
            shutdown_event.set()
        # Se il thread è vivo, aspetta fino a 2 secondi per una chiusura ordinata
        if log_worker and log_worker.is_alive():
            log_worker.join(timeout=2)
        # Svuota i riferimenti per permettere future reinizializzazioni pulite
        log_worker = None
        shutdown_event = None

# Gestisce SIGINT/SIGTERM assicurandosi che la coda venga svuotata prima di uscire
def handle_interrupt(signum, frame):
    if console_logger:
        console_logger.info("Ricevuto segnale di interruzione: completamento log in corso...")
    if shutdown_event:
        shutdown_event.set()
    try:
        log_queue.join()
    except Exception as join_error:
        if console_logger:
            console_logger.error(f"Errore durante l'attesa della coda: {join_error}")
    stop_log_worker()
    if console_logger:
        console_logger.info("Scrittura log completata. Arresto del servizio.")
    raise SystemExit(0)

def register_signal_handlers():
    global signal_registered
    if signal_registered or threading.current_thread() is not threading.main_thread():
        return
    signal.signal(signal.SIGINT, handle_interrupt)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handle_interrupt)
    signal_registered = True

# Inizializza i logger
file_logger = None
console_logger = None

def initialize_loggers():
    """Inizializza i logger globalmente"""
    global file_logger, console_logger
    with worker_lock:
        # Prepara il logger console se non è ancora stato creato
        if console_logger is None:
            console_logger = setup_console_logger()
        # Prepara il logger file (handler rotazione giornaliero) se assente
        if file_logger is None:
            file_logger = setup_file_logger()
    # Avvia o riattiva il worker che gestisce la scrittura asincrona
    start_log_worker()
    # Installa gli handler di segnale una sola volta per gestire Ctrl+C
    register_signal_handlers()

def get_log_level(level_str):
    """Converte il livello di log da stringa a costante logging"""
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
        # Riattiva il pipeline asincrono se il worker non è disponibile (es. reload hot o crash thread)
        if console_logger is None or file_logger is None or not log_worker or not log_worker.is_alive():
            initialize_loggers()
        
        # Estrai parametri dalla query string
        source = request.args.get('source')
        level = request.args.get('level')

        # Estrai il messaggio dal corpo della richiesta
        if request.is_json:
            data = request.get_json()
            message = data.get('message', '') if data else ''
            # Permetti al body JSON di valorizzare source e livello se non forniti via query
            if data:
                source = data.get('source', source)
                level = data.get('level', level)
        else:
            message = request.get_data(as_text=True)
        
        if not message:
            return jsonify({
                'error': 'Nessun messaggio fornito nel corpo della richiesta'
            }), 400
        
        # Ottieni il livello di log numerico
        log_level = get_log_level(level or 'info')
        
        # Determina l'IP remoto, considerando eventuali proxy
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            client_ip = forwarded_for.split(',')[0].strip()
        else:
            client_ip = request.remote_addr or 'unknown'

        # Crea il messaggio formattato con source e IP remoto
        source_value = source or 'unknown'
        formatted_message = f"[{source_value}@{client_ip}] {message}"
        
        # Log su console
        if console_logger:
            console_logger.log(log_level, formatted_message)

        try:
            # Inserisci il messaggio nella coda senza bloccare la richiesta - in caso di overflow scarta con 503
            log_queue.put_nowait((log_level, formatted_message))
        except queue.Full:
            overload_msg = "Coda di logging piena; richiesta scartata"
            if console_logger:
                console_logger.error(overload_msg)
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
            console_logger.error(error_msg)
        if log_worker and log_worker.is_alive():
            try:
                log_queue.put_nowait((logging.ERROR, error_msg))
            except queue.Full:
                if console_logger:
                    console_logger.error("Coda di logging piena durante la gestione dell'errore")
        
        return jsonify({
            'error': error_msg
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint per verificare lo stato del servizio"""
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }), 200

@app.route('/logs', methods=['GET'])
def get_logs():
    """Restituisce i log del giorno richiesto in formato JSON"""
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
            console_logger.error(f"Errore durante la lettura del log: {read_error}")
        return jsonify({'error': 'Impossibile leggere il file di log richiesto'}), 500

    return jsonify(entries), 200

if __name__ == '__main__':
    # Inizializza i logger
    initialize_loggers()
    
    print("==========================================")
    print("      js-fe Web Logger - Server")
    print("==========================================")
    license_banner = """
js-fe-pythologger
Copyright (C) 2026 Antonio Maulucci (https://github.com/myblacksloth)

Questo programma è software libero: puoi ridistribuirlo e/o modificarlo
secondo i termini della GNU Affero General Public License come pubblicata
dalla Free Software Foundation, versione 3 della Licenza.a

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
    
    app.run(host='0.0.0.0', port=5000, debug=True)
