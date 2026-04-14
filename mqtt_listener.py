import os
import json
import logging
import datetime
from paho.mqtt import client as mqtt_client
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database import SessionLocal, SGILog, Truck

load_dotenv()

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MQTT_Listener")

# MQTT Configuration
BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
PORT = int(os.getenv("MQTT_PORT", 1883))
TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "patio/doca/")
QOS = int(os.getenv("MQTT_QOS", 1))
CLIENT_ID = f'autogate-listener-{os.getpid()}'

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info("Connected to MQTT Broker!")
        # Subscribe to all doca scan topics
        client.subscribe(f"{TOPIC_PREFIX}+/scan", qos=QOS)
        logger.info(f"Subscribed to {TOPIC_PREFIX}+/scan")
    else:
        logger.error(f"Failed to connect, return code {rc}")

def process_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = msg.payload.decode()
        logger.info(f"Received message from topic `{topic}`: {payload}")

        # Extract doca_id from topic (e.g., patio/doca/01/scan -> 01)
        topic_parts = topic.split('/')
        if len(topic_parts) >= 3:
            doca_id = topic_parts[2]
        else:
            doca_id = "unknown"

        # Parse payload
        data = json.loads(payload)
        truck_id = data.get("truck_id")

        if not truck_id:
            logger.warning("Message payload missing `truck_id`")
            return

        # Database operation
        db: Session = SessionLocal()
        try:
            # Verify if truck exists
            truck = db.query(Truck).filter(Truck.id == truck_id).first()
            if not truck:
                logger.error(f"Truck ID `{truck_id}` not found in database. Ignoring scan.")
                return

            # Create log entry
            new_log = SGILog(
                truck_id=truck_id,
                doca_id=doca_id,
                timestamp=datetime.datetime.utcnow()
            )
            db.add(new_log)
            db.commit()
            logger.info(f"Successfully registered scan for Truck `{truck_id}` at Doca `{doca_id}`")
        except Exception as e:
            db.rollback()
            logger.error(f"Database error during message processing: {e}")
        finally:
            db.close()

    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON payload: {msg.payload}")
    except Exception as e:
        logger.error(f"Unexpected error in message processing: {e}")

def run():
    client = mqtt_client.Client(client_id=CLIENT_ID, callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = process_message

    try:
        client.connect(BROKER, PORT)
        client.loop_forever()
    except Exception as e:
        logger.critical(f"MQTT Listener could not start: {e}")

if __name__ == '__main__':
    run()
