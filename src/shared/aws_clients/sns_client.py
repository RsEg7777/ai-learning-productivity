"""Amazon SNS client for push notifications."""

import logging
import os
import json
from typing import Any, Dict, Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class SNSClient:
    """Production SNS client for user notifications."""

    def __init__(self, region: Optional[str] = None) -> None:
        self.region = region or os.getenv("AWS_REGION", "ap-south-1")
        self.client = boto3.client("sns", region_name=self.region)
        self.topic_arn = os.getenv("SNS_TOPIC_ARN", "")
        logger.info(f"SNSClient initialised → region={self.region}")

    def publish(
        self,
        message: str,
        subject: Optional[str] = None,
        topic_arn: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Publish a message to SNS topic. Returns message ID or None if no topic configured."""
        target_arn = topic_arn or self.topic_arn
        if not target_arn:
            logger.debug("SNS topic ARN not configured — skipping notification")
            return None
        try:
            params: Dict[str, Any] = {
                "TopicArn": target_arn,
                "Message": message if isinstance(message, str) else json.dumps(message),
            }
            if subject:
                params["Subject"] = subject
            if attributes:
                params["MessageAttributes"] = {
                    k: {"DataType": "String", "StringValue": str(v)}
                    for k, v in attributes.items()
                }
            response = self.client.publish(**params)
            msg_id = response.get("MessageId", "")
            logger.info(f"SNS published → MessageId={msg_id}")
            return msg_id
        except ClientError as e:
            # Non-fatal: notifications failing should not break the main flow
            logger.warning(f"SNS publish failed: {e.response['Error']['Code']} — {e.response['Error']['Message']}")
            return None
        except Exception as e:
            logger.warning(f"SNS unexpected error: {e}")
            return None

    def notify_achievement(self, user_id: str, achievement_name: str, xp_reward: int) -> None:
        """Send achievement unlock notification."""
        self.publish(
            message=json.dumps({
                "type": "achievement_unlocked",
                "user_id": user_id,
                "achievement": achievement_name,
                "xp_reward": xp_reward,
            }),
            subject=f"🏆 Achievement Unlocked: {achievement_name}",
        )

    def notify_level_up(self, user_id: str, new_level: int) -> None:
        """Send level-up notification."""
        self.publish(
            message=json.dumps({
                "type": "level_up",
                "user_id": user_id,
                "new_level": new_level,
            }),
            subject=f"⬆️ Level Up! You reached Level {new_level}",
        )
