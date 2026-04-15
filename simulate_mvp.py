import requests
import json
import time
import os
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

BROKER = os.getenv("MQTT_BROKER")
PORT = int(os.getenv("MQTT_PORT", 8883))
USER = os.getenv("MQTT_USERNAME")
PASS = os.getenv("MQTT_PASSWORD")

API_URL = "http://localhost:8000"
MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "patio/doca/")

def register_truck_via_api(truck_id, motorista, cpf, lote, modelo):
    print(f"--- Registrando caminhão {truck_id} via API ---")
    payload = {
        "id": truck_id,
        "motorista": motorista,
        "cpf_motorista": cpf,
        "lote": lote,
        "modelo_veiculo": modelo
    }
    try:
        response = requests.post(f"{API_URL}/register", json=payload)
        if response.status_code == 201:
            print(f"Sucesso: {response.json()}")
        else:
            print(f"Erro ao registrar: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Falha na conexão com a API: {e}")

def simulate_mqtt_scan(truck_id, doca_id):
    print(f"--- Simulando Scan do QR Code para Caminhão {truck_id} na Doca {doca_id} ---")
    topic = f"{MQTT_TOPIC_PREFIX}{doca_id}/scan"
    payload = json.dumps({"truck_id": truck_id})
    
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(os.getenv("MQTT_USERNAME"), os.getenv("MQTT_PASSWORD"))
    client.tls_set()
    
    try:
        client.connect(os.getenv("MQTT_BROKER"), 8883)
        
        # O SEGREDO ESTÁ AQUI:
        client.loop_start() # Inicia o processamento em segundo plano
        info = client.publish(topic, payload, qos=1)
        info.wait_for_publish() # ESPERA a mensagem ser entregue de fato
        
        print(f"Mensagem publicada com sucesso no tópico `{topic}`")
        client.loop_stop()
        client.disconnect()
    except Exception as e:
        print(f"Falha ao publicar no MQTT: {e}")

def check_logs_via_api():
    print("--- Consultando logs no SGI via API ---")
    try:
        response = requests.get(f"{API_URL}/logs")
        if response.status_code == 200:
            logs = response.json()
            print(f"Logs encontrados: {len(logs)}")
            for log in logs:
                print(f"  ID: {log['log_id']} | Truck: {log['truck_id']} | Doca: {log['doca_id']} | Time: {log['timestamp']}")
        else:
            print(f"Erro ao consultar logs: {response.status_code}")
    except Exception as e:
        print(f"Falha na conexão com a API: {e}")

if __name__ == "__main__":
    print("Iniciando Simulação do MVP AutoGATE...")
    
    # 1. Registrar caminhões
    register_truck_via_api("TRK-1234", "João Silva", "123.456.789-00", "LOTE-A1", "Volvo FH 540")
    register_truck_via_api("TRK-5678", "Maria Oliveira", "987.654.321-11", "LOTE-B2", "Scania R450")
    
    # 2. Aguardar um pouco para os serviços estarem prontos
    time.sleep(2)
    
    # 3. Simular scans nas docas
    simulate_mqtt_scan("TRK-1234", "01")
    time.sleep(1)
    simulate_mqtt_scan("TRK-5678", "02")
    time.sleep(1)
    simulate_mqtt_scan("TRK-1234", "02") # Mesmo caminhão em outra doca
    
    # 4. Aguardar processamento do listener
    print("Aguardando processamento do MQTT Listener...")
    time.sleep(3)
    
    # 5. Verificar logs
    check_logs_via_api()
