class DynamoLicenseRepository:
  def __init__(self, table_name):
    import boto3

    self._table = boto3.resource("dynamodb").Table(table_name)

  def put(self, item):
    self._table.put_item(
      Item=item,
      ConditionExpression="attribute_not_exists(license_id)",
    )

  def get(self, license_id):
    response = self._table.get_item(
      Key={"license_id": license_id},
      ConsistentRead=True,
    )

    return response.get("Item")

  def mark_validated(self, license_id, validated_at):
    self._table.update_item(
      Key={"license_id": license_id},
      UpdateExpression="SET last_validated_at = :validated_at",
      ExpressionAttributeValues={":validated_at": validated_at},
      ConditionExpression="attribute_exists(license_id)",
    )

  def delete(self, license_id):
    self._table.delete_item(
      Key={"license_id": license_id},
      ConditionExpression="attribute_exists(license_id)",
    )
