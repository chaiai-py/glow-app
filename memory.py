from azure.cosmos import CosmosClient
from config import COSMOS_ENDPOINT, COSMOS_KEY, COSMOS_DB, COSMOS_CONTAINER
from azure.cosmos import PartitionKey

container = None


def get_container():
    global container

    if container is not None:
        return container

    client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
    database = client.create_database_if_not_exists(id=COSMOS_DB)
    container = database.create_container_if_not_exists(
        id=COSMOS_CONTAINER,
        partition_key=PartitionKey(path="/user_id")
    )
    return container

def get_memory(user_id: str):
    try:
        return get_container().read_item(item=user_id, partition_key=user_id)
    except Exception as e:
        print(f"Memory read warning: {e}")
        return None

def save_memory(user_id: str, message: str, intent: str):
    existing = get_memory(user_id)
    memory_container = get_container()

    if existing:
        existing["history"].append(message)
        existing["last_intent"] = intent
        memory_container.upsert_item(existing)
    else:
        memory_container.upsert_item({
            "id": user_id,
            "user_id": user_id,
            "history": [message],
            "last_intent": intent
        })
