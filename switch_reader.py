from opcua import Client
import logging
from opcua import ua

logger = logging.getLogger(__name__)

class OPCReader:
    def __init__(self, url="opc.tcp://192.168.60.101:4840"):
        self.url = url
        self.client = None

    def connect(self):
        try:
            self.client = Client(self.url)
            self.client.connect()
            logger.info("OPC Client connected.")
        except Exception as e:
            logger.error(f"OPC connection failed: {e}")
            raise

    def disconnect(self):
        if self.client:
            self.client.disconnect()
            logger.info("OPC Client disconnected.")

    def read_node(self, node_id: str):
        try:
            node = self.client.get_node(node_id)
            value = node.get_value()
            logger.info(f"Read from node {node_id}: {value}")
            return value
        except Exception as e:
            logger.error(f"Error reading node {node_id}: {e}")
            return None

    def write_node(self, node_id: str, value):
        try:
            node = self.client.get_node(node_id)
            variant_type = node.get_data_type_as_variant_type()

            # Ensure correct type
            if variant_type == ua.VariantType.Boolean:
                 value = str(value).lower() in ["1", "true", "on"]
            elif variant_type == ua.VariantType.Int32:
                value = int(value)
            elif variant_type == ua.VariantType.Float:
                value = float(value)

            variant = ua.Variant(value, variant_type)
            node.set_value(variant)
            print(f"[OPC WRITE] Wrote {value} ({variant_type}) to {node_id}")
            return True
        except Exception as e:
            print(f"[OPC WRITE ERROR] {e}")
            return False
