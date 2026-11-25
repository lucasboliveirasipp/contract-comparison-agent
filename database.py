# database.py
from pymongo import MongoClient
from .config import Config
import logging
import streamlit as st

logger = logging.getLogger(__name__)

class MongoDB:
    def __init__(self):
        try:
            self.client = MongoClient(Config.MONGODB_URI)
            self.db = self.client[Config.MONGODB_DB]
            self.analyses = self.db[Config.MONGODB_COLLECTIONS['analyses']]
            self.feedback = self.db[Config.MONGODB_COLLECTIONS['feedback']]
            self.prompts = self.db[Config.MONGODB_COLLECTIONS['prompts']]
            self.padrao_ouro = self.db['padrao_ouro']

            logger.info("MongoDB connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    def init_collections(self):
        """Inicializa as collections com índices necessários"""
        try:
            self.analyses.create_index("timestamp")
            self.feedback.create_index([("analysis_id", 1), ("timestamp", -1)])
            self.prompts.create_index("analysis_id", unique=True)
            logger.info("MongoDB collections initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize collections: {str(e)}")
            raise
        
# if 'db' not in st.session_state:
#     st.session_state.db = MongoDB()
# db = st.session_state.db   
  