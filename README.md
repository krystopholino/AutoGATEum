# AutoGATE MVP v1.0

## 1. Visão Geral (Scope Statement)

O **AutoGATE** é um sistema de missão crítica projetado para automatizar o check-in de veículos em pátios logísticos. O MVP elimina o uso de papel e a inserção manual de dados, capturando a identidade do veículo via QR Code, cruzando com uma base de dados prévia e registrando a operação em docas específicas de forma automática e auditável.

## 2. Arquitetura e Fluxo de Dados (Event-Driven)

O sistema opera sob uma arquitetura orientada a eventos, garantindo integridade de dados e rastreabilidade total de ponta a ponta.

1.  **Input Origin (Expedição)**: Cadastro prévio do caminhão via API FastAPI (tabela `trucks`).
2.  **Trigger (Doca)**: Scan do QR Code pelo dispositivo móvel utilizando o aplicativo **IoT MQTT Panel**.
3.  **Transport (Broker Privado)**: O ID lido é publicado via protocolo **MQTT sobre TLS (Porta 8883)** no tópico `patio/doca/XX/scan` no **HiveMQ Cloud**.
4.  **Processing (Listener)**: O serviço `mqtt_listener.py` escuta o broker, valida a existência do caminhão e registra o evento na tabela `sgi_logs`.
5.  **Output (SGI Logs)**: O banco de dados SQLite é atualizado em tempo real, fornecendo histórico de doca, caminhão e timestamp exato.

## 3. Estrutura do Projeto (Modularização)

```text
/autogate_mvp
├── main.py            # API FastAPI (Rotas REST, Cadastro e Consulta)
├── database.py        # Camada de Dados (SQLAlchemy, Modelos Trucks e Logs)
├── mqtt_listener.py   # Serviço de Escuta (Integração Broker -> DB)
├── simulate_mvp.py    # Script de Simulação e Teste de Carga
├── .env               # Variáveis de Ambiente (Configurações Sensíveis)
├── requirements.txt   # Dependências do Projeto
└── autogate.db        # Banco de Dados SQLite (Produção/MVP)
```

## 4. Protocolo de Instalação e Execução

### 4.1. Ambiente Virtual e Dependências
```powershell
python -m venv venv
# Windows: .\venv\Scripts\Activate.ps1 | Linux: source venv/bin/activate
pip install -r requirements.txt
```

### 4.2. Configuração de Variáveis (.env)
O sistema exige segurança de ponta a ponta via TLS no HiveMQ Cloud:
```ini
MQTT_BROKER=seu-cluster-id.s1.eu.hivemq.cloud
MQTT_PORT=8883
MQTT_USERNAME=seu_usuario
MQTT_PASSWORD=sua_senha
DATABASE_URL=sqlite:///./autogate.db
```

### 4.3. Execução dos Serviços
1.  **API**: `uvicorn main:app --host 0.0.0.0 --port 8000`
2.  **Listener**: `python mqtt_listener.py`

## 5. Configuração do Hardware (IoT MQTT Panel)

Para que o dispositivo móvel atue como o scanner oficial:
*   **Protocolo**: SSL/TLS (Obrigatório).
*   **Porta**: 8883.
*   **Tópico (Publish)**: `patio/doca/01/scan`
*   **Payload Template**: `{"truck_id": "<payload>"}` (Utilizar tags `<>` para substituição dinâmica do conteúdo do QR Code).

## 6. Notas Técnicas e Resiliência

*   **Integridade**: O sistema ignora scans de IDs não cadastrados previamente na tabela `trucks`.
*   **QoS (Quality of Service)**: Configurado como **QoS 1** (At Least Once) para garantir a entrega da mensagem mesmo em redes instáveis.
*   **Logging**: Logs estruturados em níveis (INFO/ERROR) para auditoria rápida via terminal ou arquivos de log.
*   **Hardware**: A latência de leitura e rede corporativa pode exigir a porta 443 (WebSockets) caso a 8883 esteja bloqueada por firewall.
