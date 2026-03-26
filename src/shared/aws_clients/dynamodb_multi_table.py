"""DynamoDB client that supports multiple tables."""

import logging
from typing import Any, Dict, List, Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class DynamoDBMultiTableClient:
    """Client for AWS DynamoDB operations across multiple tables."""

    def __init__(self, region: Optional[str] = None) -> None:
        """
        Initialize DynamoDB multi-table client.

        Args:
            region: AWS region (optional)
        """
        self.region = region or "us-east-1"
        self.dynamodb = boto3.resource("dynamodb", region_name=self.region)
        self._table_cache = {}
        logger.info("Initialized DynamoDBMultiTableClient")

    def _get_table(self, table_name: str):
        """Get or create table reference."""
        if table_name not in self._table_cache:
            self._table_cache[table_name] = self.dynamodb.Table(table_name)
        return self._table_cache[table_name]

    def put_item(self, table_name: str, item: Dict[str, Any]) -> None:
        """Put an item into a table."""
        try:
            table = self._get_table(table_name)
            table.put_item(Item=item)
            logger.info(f"Successfully put item into {table_name}")
        except ClientError as e:
            logger.error(f"Failed to put item: {e}")
            raise

    def get_item(self, table_name: str, key: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get an item from a table."""
        try:
            table = self._get_table(table_name)
            response = table.get_item(Key=key)
            item = response.get("Item")
            if item:
                logger.info(f"Successfully retrieved item from {table_name}")
            return item
        except ClientError as e:
            logger.error(f"Failed to get item: {e}")
            raise

    def update_item(
        self,
        table_name: str,
        key: Dict[str, Any],
        update_expression: str,
        expression_values: Dict[str, Any],
        expression_names: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Update an item in a table."""
        try:
            table = self._get_table(table_name)
            params = {
                "Key": key,
                "UpdateExpression": update_expression,
                "ExpressionAttributeValues": expression_values,
                "ReturnValues": "ALL_NEW",
            }
            if expression_names:
                params["ExpressionAttributeNames"] = expression_names

            response = table.update_item(**params)
            logger.info(f"Successfully updated item in {table_name}")
            return response.get("Attributes", {})
        except ClientError as e:
            logger.error(f"Failed to update item: {e}")
            raise

    def delete_item(self, table_name: str, key: Dict[str, Any]) -> None:
        """Delete an item from a table."""
        try:
            table = self._get_table(table_name)
            table.delete_item(Key=key)
            logger.info(f"Successfully deleted item from {table_name}")
        except ClientError as e:
            logger.error(f"Failed to delete item: {e}")
            raise

    def query_items(
        self,
        table_name: str,
        key_condition: str,
        expression_values: Dict[str, Any],
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Query items from a table."""
        try:
            table = self._get_table(table_name)
            params = {
                "KeyConditionExpression": key_condition,
                "ExpressionAttributeValues": expression_values,
            }
            if limit:
                params["Limit"] = limit

            response = table.query(**params)
            items = response.get("Items", [])
            logger.info(f"Successfully queried {len(items)} items from {table_name}")
            return items
        except ClientError as e:
            logger.error(f"Failed to query items: {e}")
            raise

    def scan_table(
        self,
        table_name: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Scan a table."""
        try:
            table = self._get_table(table_name)
            params = {}
            if limit:
                params["Limit"] = limit

            response = table.scan(**params)
            items = response.get("Items", [])
            logger.info(f"Successfully scanned {len(items)} items from {table_name}")
            return items
        except ClientError as e:
            logger.error(f"Failed to scan table: {e}")
            raise

    def query_items(self, table_name: str, key_conditions: dict) -> list:
        """Query items matching key conditions (simple equality scan fallback)."""
        try:
            from boto3.dynamodb.conditions import Attr
            table = self._get_table(table_name)
            filter_expr = None
            for k, v in key_conditions.items():
                cond = Attr(k).eq(v)
                filter_expr = cond if filter_expr is None else filter_expr & cond
            if filter_expr:
                resp = table.scan(FilterExpression=filter_expr)
            else:
                resp = table.scan()
            return resp.get("Items", [])
        except ClientError as e:
            logger.error(f"query_items error: {e}")
            return []
