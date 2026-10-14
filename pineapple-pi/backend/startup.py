import logging
from backend.database import initialize_database

def initialize_application() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    initialize_database()
