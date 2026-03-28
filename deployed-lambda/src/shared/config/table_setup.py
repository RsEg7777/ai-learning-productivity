"""DynamoDB table setup and initialization."""

import logging
from typing import List, Dict
from .config_validator import ConfigValidator

logger = logging.getLogger(__name__)


class TableSetup:
    """Setup and initialize DynamoDB tables."""

    def __init__(self, region: str = "us-east-1", table_prefix: str = "ai-learning-"):
        """Initialize table setup."""
        self.region = region
        self.table_prefix = table_prefix
        self.validator = ConfigValidator(region=region)

    def setup_all_tables(self) -> bool:
        """
        Create all required tables if they don't exist.
        
        Returns:
            True if all tables were created/exist, False otherwise
        """
        logger.info("Setting up DynamoDB tables...")
        
        tables_config = [
            self._get_tutor_sessions_config(),
            self._get_quiz_results_config(),
            self._get_user_progress_config(),
            self._get_flashcards_config(),
            self._get_achievements_config(),
        ]
        
        success = True
        for config in tables_config:
            table_name = f"{self.table_prefix}{config['name']}"
            result = self.validator.create_table_if_not_exists(
                table_name=table_name,
                key_schema=config['key_schema'],
                attribute_definitions=config['attribute_definitions'],
            )
            if not result:
                success = False
                logger.error(f"Failed to setup table: {table_name}")
        
        if success:
            logger.info("✅ All tables setup successfully")
        else:
            logger.error("❌ Some tables failed to setup")
        
        return success

    def _get_tutor_sessions_config(self) -> Dict:
        """Get tutor sessions table configuration."""
        return {
            'name': 'tutor-sessions',
            'key_schema': [
                {'AttributeName': 'session_id', 'KeyType': 'HASH'},
            ],
            'attribute_definitions': [
                {'AttributeName': 'session_id', 'AttributeType': 'S'},
            ],
        }

    def _get_quiz_results_config(self) -> Dict:
        """Get quiz results table configuration."""
        return {
            'name': 'quiz-results',
            'key_schema': [
                {'AttributeName': 'result_id', 'KeyType': 'HASH'},
            ],
            'attribute_definitions': [
                {'AttributeName': 'result_id', 'AttributeType': 'S'},
            ],
        }

    def _get_user_progress_config(self) -> Dict:
        """Get user progress table configuration."""
        return {
            'name': 'user-progress',
            'key_schema': [
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
            ],
            'attribute_definitions': [
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
            ],
        }

    def _get_flashcards_config(self) -> Dict:
        """Get flashcards table configuration."""
        return {
            'name': 'flashcards',
            'key_schema': [
                {'AttributeName': 'card_id', 'KeyType': 'HASH'},
            ],
            'attribute_definitions': [
                {'AttributeName': 'card_id', 'AttributeType': 'S'},
            ],
        }

    def _get_achievements_config(self) -> Dict:
        """Get achievements table configuration."""
        return {
            'name': 'achievements',
            'key_schema': [
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'achievement_id', 'KeyType': 'RANGE'},
            ],
            'attribute_definitions': [
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'achievement_id', 'AttributeType': 'S'},
            ],
        }


def setup_tables(region: str = "us-east-1", table_prefix: str = "ai-learning-") -> bool:
    """
    Convenience function to setup all tables.
    
    Args:
        region: AWS region
        table_prefix: Prefix for table names
        
    Returns:
        True if successful, False otherwise
    """
    setup = TableSetup(region=region, table_prefix=table_prefix)
    return setup.setup_all_tables()
