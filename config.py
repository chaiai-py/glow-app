import os
from dotenv import load_dotenv
load_dotenv()
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://glow-openai.openai.azure.com/")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "2AG5LPHxHfvzGf27MG1y5OjcRN5jhnZjiI3jC6COxtD1hlmbLrb0JQQJ99CEACqBBLyXJ3w3AAAAACOGOigC")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "glow-gpt")

AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "https://glow-search.search.windows.net")
AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY", "lwbHnApJ4yHVPeSCVA8pBG7S2dUzr9IniEl9RnmVmrAzSeAXPl9V")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX", "search-1777820141929")

COSMOS_ENDPOINT = os.getenv("COSMOS_ENDPOINT", "https://glow-cosmos.documents.azure.com:443/")
COSMOS_KEY = os.getenv("COSMOS_KEY", "Vn6xj/OALre7dmxgjBAZKf6dzMFuWcnBPdRLmWPuFlzLRy1MsdkxB92yqFXp5a0XpJANQo0F6uIs+AStdRyoPw==")
COSMOS_DB = os.getenv("COSMOS_DB", "glowstorage7")
COSMOS_CONTAINER = os.getenv("COSMOS_CONTAINER", "glow-data")