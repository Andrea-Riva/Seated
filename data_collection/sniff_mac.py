import subprocess

# Definisci il range IP della rete (modifica se necessario)
ip_range = "192.168.1.0/24"

# Indirizzi IP da escludere (router e Raspberry Pi)
exclude_ips = ["192.168.1.1", "192.168.1.184"]

# Definisci il comando NMAP
command = f"sudo nmap -sn {ip_range}"

# Esegui il comando NMAP tramite subprocess
def run_nmap(command):
    try:
        # Esegui il comando e cattura l'output
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        # Verifica se l'esecuzione è stata corretta
        if result.returncode == 0:
            return result.stdout
        else:
            print("Errore nell'esecuzione di nmap")
            return None
    except Exception as e:
        print(f"Si è verificato un errore: {e}")
        return None

# Funzione per salvare i risultati in un file con la struttura richiesta
def save_results(results, filename="nmap_results.txt"):
    # Conta i dispositivi connessi
    devices = []

    # Estrai l'IP e il MAC address dai risultati NMAP
    lines = results.splitlines()
    current_device = None

    for line in lines:
        # Rileva l'IP del dispositivo (linea che inizia con "Nmap scan report for")
        if line.startswith("Nmap scan report for"):
            # Estrai l'IP, rimuovendo eventuali parentesi
            ip = line.split(" ")[-1].strip('()')
            if ip not in exclude_ips:  # Esclude router e Raspberry Pi
                current_device = {"ip": ip, "mac": None}
                devices.append(current_device)
        # Rileva l'indirizzo MAC (linea che contiene "MAC Address")
        elif "MAC Address" in line and current_device is not None:
            mac = line.split(" ")[2]
            current_device["mac"] = mac

    # Rimuovi eventuali dispositivi con MAC None
    devices = [device for device in devices if device["mac"] is not None]

    # Salva i risultati nel file
    with open(filename, "w") as file:
        for device in devices:
            file.write(f"{device['ip']}, {device['mac']}\n")

        # Scrive il numero totale di dispositivi connessi, escludendo il router e il rasp pi zero 2w
        num_devices = len(devices)
        file.write(f"Numero totale di dispositivi connessi: {num_devices}\n")

    print(f"I risultati sono stati salvati in {filename}")

# Esegui la scansione e ottieni i risultati
nmap_results = run_nmap(command)

# Se ci sono risultati, salvali nel file
if nmap_results:
    save_results(nmap_results)
