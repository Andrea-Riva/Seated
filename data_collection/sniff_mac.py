import sqlite3
import subprocess
from datetime import datetime

# Funzione per eseguire il comando NMAP
def run_nmap(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout
        else:
            print("Errore nell'esecuzione di nmap")
            return None
    except Exception as e:
        print(f"Si è verificato un errore: {e}")
        return None

# Funzione per creare il database e la tabella dispositivi
def create_database():
    conn = sqlite3.connect('devices.db')
    cursor = conn.cursor()

    # Verifica se la tabella devices esiste, altrimenti la crea
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT UNIQUE,
            mac TEXT
        )
    ''')

    # Verifica se la tabella scans esiste, altrimenti la crea
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_datetime TEXT
        )
    ''')

    conn.commit()
    conn.close()

# Funzione per inserire i dispositivi nel database
def insert_devices(devices):
    conn = sqlite3.connect('devices.db')
    cursor = conn.cursor()

    for device in devices:
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO devices (ip, mac)
                VALUES (?, ?)
            ''', (device['ip'], device['mac']))
        except sqlite3.IntegrityError:
            print(f"Errore durante l'inserimento del dispositivo: {device['ip']}")

    conn.commit()
    conn.close()

# Funzione per registrare una nuova scansione
def insert_scan(scan_datetime):
    conn = sqlite3.connect('devices.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO scans (scan_datetime)
        VALUES (?)
    ''', (scan_datetime,))

    conn.commit()
    conn.close()

# Funzione per ottenere la lista degli IP dai dispositivi rilevati
def get_current_ips(devices):
    return {device['ip'] for device in devices}

# Funzione per eliminare i dispositivi che non sono più rilevati
def delete_old_devices(current_ips):
    conn = sqlite3.connect('devices.db')
    cursor = conn.cursor()

    # Elimina i dispositivi che non sono presenti nell'ultimo scan
    cursor.execute('''
        DELETE FROM devices
        WHERE ip NOT IN ({})
    '''.format(','.join('?' for _ in current_ips)), tuple(current_ips))

    conn.commit()
    conn.close()

# Funzione per eseguire la scansione e salvare i risultati nel database
def save_scan_results(results):
    devices = []
    lines = results.splitlines()
    current_device = None

    for line in lines:
        if line.startswith("Nmap scan report for"):
            ip = line.split(" ")[-1].strip('()')
            current_device = {"ip": ip, "mac": None}
            devices.append(current_device)
        elif "MAC Address" in line and current_device is not None:
            mac = line.split(" ")[2]
            current_device["mac"] = mac

    # Rimuovi dispositivi senza MAC address
    devices = [device for device in devices if device["mac"] is not None]

    # Prendi gli IP correnti dei dispositivi
    current_ips = get_current_ips(devices)

    # Aggiungi dispositivi al database
    insert_devices(devices)

    # Elimina i dispositivi non presenti nell'ultimo scan
    delete_old_devices(current_ips)

    # Registra la scansione
    insert_scan(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # Stampa il numero di dispositivi nel database
    conn = sqlite3.connect('devices.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM devices')
    count = cursor.fetchone()[0]
    print(f"Numero totale di dispositivi connessi: {count}")
    conn.close()

# Comando NMAP da eseguire
ip_range = "192.168.1.0/24"
exclude_ips = ["192.168.1.1", "192.168.1.184"]  # Escludi router e Raspberry Pi
command = f"sudo nmap -sn {ip_range}"

# Creare il database e le tabelle (solo la prima volta)
create_database()

# Esegui il comando NMAP
nmap_results = run_nmap(command)

# Se ci sono risultati, salvali nel database
if nmap_results:
    save_scan_results(nmap_results)