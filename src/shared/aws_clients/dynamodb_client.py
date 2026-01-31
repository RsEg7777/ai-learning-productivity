"""DynamoDB client for data storage."""

import logging
from typing import Any, Dict, List, Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class DynamoDBClient:
    """Client for AWS DynamoDB operations."""

    def __init__(self, table_name: str, region: Optional[str] = None) -> None:
        """
        Initialize DynamoDB client.

        Args:
            table_name: DynamoDB table name
            region: AWS region (optional)
        """
        self.table_name = table_name
        self.region = region or "us-east-1"
        self.dynamodb = boto3.resource("dynamodb", region_name=self.region)
        self.table = self.dynamodb.Table(table_name)
        logger.info(f"Initialized DynamoDBClient for table: {table_name}")

    def put_item(self, item: Dict[str, Any]) -> None:
        """
        Put an item into the table.

        Args:
            item: Item to store

        Raises:
            ClientError: If operation fails
        """
        try:
            self.table.put_item(Item=item)
            logger.info(f"Successfully put item into {self.table_name}")
        except ClientError as e:
            logger.error(f"Failed to put item: {e}")
            raise

    def get_item(self, key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get an item from the table.

        Args:
            key: Primary key of the item

        Returns:
            Item if found, None otherwise

        Raises:
            ClientError: If operation fails
        """
        try:
            response = self.table.get_item(Key=key)
            item = response.get("Item")
            if item:
                logger.info(f"Successfully retrieved item from {self.table_name}")
            return item
        except ClientError as e:
            logger.error(f"Failed to get item: {e}")
            raise

    def update_item(
        self,
        key: Dict[str, Any],
        update_expression: str,
        expression_values: Dict[str, Any],
        expression_names: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Update an item in the table.

        Args:
            key: Primary key of the item
            update_expression: Update expression
            expression_values: Expression attribute values
            expression_names: Expression attribute names (optional)

        Returns:
            Updated item attributes

        Raises:
            ClientError: If operation fails
        """
        try:
            params = {
                "Key": key,
                "UpdateExpression": update_expression,
                "ExpressionAttributeValues": expression_values,
                "ReturnValues": "ALL_NEW",
            }

            if expression_names:
                params["ExpressionAttributeNames"] = expression_names

            response = self.table.update_item(**params)
            logger.info(f"Successfully updated item in {self.table_name}")
            return response.get("Attributes", {})
        except ClientError as e:
            logger.error(f"Failed to update item: {e}")
            raise

    def delete_item(self, key: Dict[str, Any]) -> None:
        """
        Delete an item from the table.

        Args:
            key: Primary key of the item

        Raises:
            ClientError: If operation fails
        """
        try:
            self.table.delete_item(Key=key)
            logger.info(f"Successfully deleted item from {self.table_name}")
        except ClientError as e:
            logger.error(f"Failed to delete item: {e}")
            raise

    def query(
        self,
        key_condition_expression: str,
        expression_values: Dict[str, Any],
        index_name: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query items from the table.

        Args:
            key_condition_expression: Key condition expression
            expression_values: Expression attribute values
            index_name: Global secondary index name (optional)
            limit: Maximum number of items to return (optional)

        Returns:
            List of items matching the query

        Raises:
            ClientError: If operation fails
        """
        try:
            params = {
                "KeyConditionExpression": key_condition_expression,
                "ExpressionAttributeValues": expression_values,
            }

            if index_name:
                params["IndexName"] = index_name

            if limit:
                params["Limit"] = limit

            response = self.table.query(**params)
            items = response.get("Items", [])
            logger.info(f"Successfully queried {len(items)} items from {self.table_name}")
            return items
        except ClientError as e:
            logger.error(f"Failed to query items: {e}")
            raise

    def scan(
        self,
        filter_expression: Optional[str] = None,
        expression_values: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Scan items from the table.

        Args:
            filter_expression: Filter expression (optional)
            expression_values: Expression attribute values (optional)
            limit: Maximum number of items to return (optional)

        Returns:
            List of items

        Raises:
            ClientError: If operation fails
        """
        try:
            params = {}

            if filter_expression:
                params["FilterExpression"] = filter_expression

            if expression_values:
                params["ExpressionAttributeValues"] = expression_values

            if limit:
                params["Limit"] = limit

            response = self.table.scan(**params)
            items = response.get("Items", [])
            logger.info(f"Successfully scanned {len(items)} items from {self.table_name}")
            return items
        except ClientError as e:
            logger.error(f"Failed to scan items: {e}")
            raise
