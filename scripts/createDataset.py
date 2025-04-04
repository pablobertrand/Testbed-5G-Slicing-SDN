import time
import pandas as pd
import subprocess
import re

# Limitado a 1 segundo de muestreo
def get_bytes_dev(interface):
    with open('/proc/net/dev', 'r') as f:
        data = f.readlines()
    for line in data:
        if interface in line:
            parts = line.split()
            recv_bytes = int(parts[1])  # Bytes recibidos
            #sent_bytes = int(parts[9])  # Bytes enviados
            return recv_bytes
    return 0

# Limitado a 1 segundo de muestreo
def get_bytes_sys_class(interface):
    with open(f"/sys/class/net/{interface}/statistics/rx_bytes", 'r') as f:
        data = f.readlines()
        cleaned_data = int(data[0].strip())
        return cleaned_data

# Limitado a 1 segundo de muestreo
def get_throughput(interface):    
    dataset = pd.DataFrame(columns=['throughput'])
    rx_prev = get_bytes_dev(interface)
    
    try:
        while True:
            time.sleep(1)

            # Segunda lectura
            rx_now = get_bytes_dev(interface)

            # Diferencia
            rx_diff = rx_now - rx_prev

            # Throughput en Mbps
            rx_mbps = (rx_diff * 8) / 1000000  # *8 (bits) - /500 ms - /1000 Mb        
            
            print(rx_mbps)

            nueva_fila = pd.DataFrame([rx_mbps], columns=['throughput'])

            dataset = pd.concat([dataset, nueva_fila.dropna(axis=1)], ignore_index=True)

            # Actualizar valores anteriores
            rx_prev = rx_now

    except KeyboardInterrupt:
        rows = len(dataset.index)
        # Captura la interrupción de teclado (Ctrl+C)
        print(f"\nInterrupción detectada. Guardando los datos en 'dataset{rows}.csv'...")        
        dataset.to_csv(f"dataset{rows}.csv", index=False)  # Guardar DataFrame en CSV
        print(f"Datos guardados exitosamente en 'dataset{rows}.csv'.")

# Hasta 300 ms de frecuencia de actualización
def get_nload_throughput(interface):
    # Ejecuta nload en modo no interactivo con actualización cada 500ms y utiliza Mb/s como unidad
    # nload -u m -m -t 500 <interface>
    command = ["nload", "-u", "m", "-m", "-t", "500", interface]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    dataset = pd.DataFrame(columns=['throughput'])
    try:
        for line in process.stdout:
            if not line:
                break

            # Buscar valores de Curr:
            incoming_match = re.search(r"Curr:\s+([\d.]+) (\w+)", line)            
            if incoming_match:                
                incoming_value = incoming_match.group(1)
                nueva_fila = pd.DataFrame([incoming_value], columns=['throughput'])
                dataset = pd.concat([dataset, nueva_fila.dropna(axis=1)], ignore_index=True)
                print(incoming_value)

    except KeyboardInterrupt:
        rows = len(dataset.index)
        # Captura la interrupción de teclado (Ctrl+C)
        print(f"\nInterrupción detectada. Guardando los datos en 'dataset{rows}.csv'...")        
        dataset.to_csv(f"dataset{rows}.csv", index=False) 
        print(f"Datos guardados exitosamente en 'dataset{rows}.csv'.")
        process.terminate()
    

if __name__ == "__main__":
    get_nload_throughput('eno8303')
