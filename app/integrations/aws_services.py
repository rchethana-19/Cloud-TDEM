from __future__ import annotations

import json
from typing import Any


def _encode(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"__bytes__": value.hex()}
    if isinstance(value, dict):
        return {key: _encode(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_encode(item) for item in value]
    return value


def _decode(value: Any) -> Any:
    if isinstance(value, dict) and set(value) == {"__bytes__"}:
        return bytes.fromhex(value["__bytes__"])
    if isinstance(value, dict):
        return {key: _decode(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_decode(item) for item in value]
    return value


class S3ObjectStore:
    def __init__(self, bucket: str, client: Any = None) -> None:
        if not bucket:
            raise ValueError("S3 bucket is required")
        if client is None:
            import boto3
            client = boto3.client("s3")
        self.bucket = bucket
        self.client = client

    def put(self, key: str, value: dict[str, Any]) -> None:
        body = json.dumps(_encode(value)).encode()
        self.client.put_object(Bucket=self.bucket, Key=key, Body=body, ServerSideEncryption="AES256")

    def get(self, key: str) -> dict[str, Any]:
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return _decode(json.loads(response["Body"].read()))

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)


class DynamoMetadataStore:
    def __init__(self, table_name: str, resource: Any = None) -> None:
        if not table_name:
            raise ValueError("DynamoDB table is required")
        if resource is None:
            import boto3
            resource = boto3.resource("dynamodb")
        self.table = resource.Table(table_name)

    def put(self, value: dict[str, Any]) -> None:
        self.table.put_item(Item=value)

    def get(self, file_id: str) -> dict[str, Any] | None:
        return self.table.get_item(Key={"file_id": file_id}).get("Item")

    def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        response = self.table.query(
            IndexName="user_id-index",
            KeyConditionExpression="user_id = :user_id",
            ExpressionAttributeValues={":user_id": user_id},
        )
        return response.get("Items", [])

    def delete(self, file_id: str) -> None:
        self.table.delete_item(Key={"file_id": file_id})


class SecretsManager:
    def __init__(self, client: Any = None) -> None:
        if client is None:
            import boto3
            client = boto3.client("secretsmanager")
        self.client = client

    def get_bytes(self, secret_name: str) -> bytes:
        response = self.client.get_secret_value(SecretId=secret_name)
        value = response.get("SecretString")
        if value is None:
            return response["SecretBinary"]
        parsed = json.loads(value) if value.startswith("{") else {"kseed": value}
        encoded = parsed.get("kseed")
        if not encoded:
            raise ValueError("secret does not contain kseed")
        import base64
        return base64.b64decode(encoded, validate=True)
