# AutoGATE MVP

## Visão Geral

O AutoGATE é um sistema MVP (Minimum Viable Product) projetado para automatizar o processo de check-in de veículos em um pátio logístico, eliminando a inserção manual de dados e o uso de papel. Ele utiliza QR Codes para identificação de veículos, cruza dados com uma base de carregamento prévia e registra operações em docas específicas de forma automática.

## Arquitetura

A arquitetura do AutoGATE é orientada a eventos, utilizando um broker MQTT para comunicação e uma API RESTful (FastAPI) para gerenciamento de dados. O banco de dados utilizado é o SQLite, ideal para prototipagem e MVPs.

### Componentes Principais:

*   **FastAPI**: API REST para cadastro e consulta de caminhões e logs.
*   **Paho-MQTT**: Biblioteca Python para interação com o broker MQTT.
*   **SQLAlchemy**: ORM (Object-Relational Mapper) para interação com o banco de dados SQLite.
*   **python-dotenv**: Para gerenciamento de variáveis de ambiente.

## Fluxo de Dados

O fluxo de dados do sistema é o seguinte:

1.  **Cadastro de Caminhão**: O front-end de expedição (simulado por scripts) cadastra os dados do caminhão no banco de dados SQLite via API FastAPI.
2.  **Escaneamento de QR Code**: Um aplicativo móvel (simulado pelo Binary Eye) escaneia o QR Code do caminhão na doca.
3.  **Publicação MQTT**: O ID do caminhão lido é publicado via MQTT em um tópico específico da doca (ex: `pátio/doca_XX/scan`).
4.  **Escuta MQTT**: Um serviço Python (MQTT Listener) "escuta" o broker MQTT, recebe o ID e interage com a API FastAPI.
5.  **Processamento e Registro**: A API FastAPI consulta os dados do caminhão no SQLite e registra a operação na tabela `SGI_Logs`.

Para uma representação visual do fluxo de dados, consulte o diagrama de sequência `autogate_data_flow.png`.

## Pré-requisitos

*   Python 3.8+
*   `pip` (gerenciador de pacotes Python)
*   Acesso à internet para o broker MQTT público (HiveMQ)

## Instalação e Execução

Siga os passos abaixo para configurar e executar o projeto:

1.  **Clone o repositório (se aplicável) ou navegue até o diretório do projeto:**

    ```bash
    cd /home/ubuntu/autogate_mvp
    ```

2.  **Crie e ative o ambiente virtual:**

    ```bash
    python3 -m venv venv
    . venv/bin/activate
    ```

3.  **Instale as dependências:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as variáveis de ambiente:**

    Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis (um exemplo `.env` já foi fornecido):

    ```ini
    # MQTT Configuration
    MQTT_BROKER=broker.hivemq.com
    MQTT_PORT=1883
    MQTT_TOPIC_PREFIX=patio/doca/
    MQTT_QOS=1

    # Database Configuration
    DATABASE_URL=sqlite:///./autogate.db

    # API Configuration
    API_HOST=0.0.0.0
    API_PORT=8000

    # Logging Configuration
    LOG_LEVEL=INFO
    ```

5.  **Inicialize o banco de dados (cria as tabelas):**

    Execute o arquivo `database.py` uma vez para criar as tabelas no SQLite.

    ```bash
    python3 database.py
    ```

6.  **Inicie a API FastAPI:**

    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000
    ```

    A API estará disponível em `http://localhost:8000`. A documentação interativa da API estará em `http://localhost:8000/docs`.

7.  **Inicie o MQTT Listener:**

    Em um terminal separado, execute:

    ```bash
    python3 mqtt_listener.py
    ```

8.  **Execute a simulação (opcional):**

    Para testar o fluxo completo, execute o script de simulação:

    ```bash
    python3 simulate_mvp.py
    ```

## Documentação da API

A API FastAPI gera automaticamente uma documentação interativa no padrão OpenAPI (Swagger UI). Para acessá-la, após iniciar a API, navegue para `http://localhost:8000/docs` em seu navegador. Lá você encontrará todos os endpoints disponíveis, seus parâmetros e modelos de resposta.

## Notas de Hardware

É importante notar que o desempenho de leitura de QR Codes e a latência da rede durante a fase de prototipagem podem ser afetados pelas limitações do hardware de teste (dispositivos móveis) e do ambiente de rede local (Intranet). O sistema foi projetado para ser resiliente a essas variações, utilizando recursos como QoS do MQTT para garantir a entrega de mensagens.

## Esquema de Mensagens MQTT

O sistema utiliza um esquema de mensagens JSON para a comunicação via MQTT, garantindo padronização e escalabilidade. O formato esperado para as mensagens de scan é:

```json
{
  "truck_id": "string",
  "doca_id": "string",
  "timestamp": "iso8601_datetime"
}
```

No entanto, o `mqtt_listener.py` extrai o `doca_id` do tópico MQTT e o `timestamp` é gerado no momento do registro no banco de dados, necessitando apenas do `truck_id` no payload da mensagem para o MVP.

## Logging Estruturado

O sistema utiliza logging estruturado com diferentes níveis (DEBUG, INFO, ERROR) para facilitar o diagnóstico em ambientes de produção. Os logs são configurados via variável de ambiente `LOG_LEVEL` no arquivo `.env`.
