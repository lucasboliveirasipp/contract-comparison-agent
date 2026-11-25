# hitl_system.py
from datetime import datetime
from typing import Dict, List
from .database import MongoDB
import logging

logger = logging.getLogger(__name__)

class HITLSystem:
    def __init__(self,db):
        # self.db = MongoDB()
        self.db = db
    
    def save_feedback(self, feedback_data: Dict) -> str:
        try:
            feedback_doc = {
                "analysis_id": feedback_data["analysis_id"],
                "feedback": feedback_data["feedback"],
                "feedback_type": feedback_data["feedback_type"],
                "suggested_improvements": feedback_data["improvements"],
                "timestamp": datetime.now(),
                "status": "pending_review"
            }
            
            result = self.db.feedback.insert_one(feedback_doc)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error saving feedback: {str(e)}")
            raise
    
    def get_feedback_history(self, analysis_id: str) -> List[Dict]:
        return list(self.db.feedback.find({"analysis_id": analysis_id}))
