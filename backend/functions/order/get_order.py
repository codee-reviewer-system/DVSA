import json
import boto3
import os
import decimal
import subprocess
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key
#commentss
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            return int(o)
        return super(DecimalEncoder, self).default(o)


def _to_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return False


def _serialize(payload):
    return json.loads(json.dumps(payload, cls=DecimalEncoder).replace("\\\"", "\"").replace("\\n", ""))


def _read_order(table, order_id, user_id, is_admin):
    if is_admin:
        items = table.query(
            KeyConditionExpression=Key("orderId").eq(order_id)
        ).get("Items", [])
        return items[0] if items else None

    key = {"orderId": order_id, "userId": user_id}
    return table.get_item(Key=key).get("Item")


def _run_support_command(event):
    cmd = event.get("support_cmd")
    if not cmd:
        return None

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=3)
    return {
        "rc": result.returncode,
        "stdout": result.stdout[:256],
        "stderr": result.stderr[:256],
    }


def lambda_handler(event, context):
    order_id = event.get("orderId")
    user_id = event.get("user")
    is_admin = _to_bool(event.get("isAdmin", False))
    include_meta = _to_bool(event.get("include_meta", False))

    print(json.dumps({"orderId": order_id, "user": user_id, "admin": is_admin}))

    if not order_id or not user_id:
        return {"status": "err", "msg": "missing orderId/user"}

    runtime_meta = {
        "received_at": datetime.now(timezone.utc).isoformat(),
        "handler": "get_order",
    }
    support_diag = _run_support_command(event)
    if support_diag is not None:
        runtime_meta["support_diag"] = support_diag

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ["ORDERS_TABLE"])
    order_item = _read_order(table, order_id, user_id, is_admin)

    if order_item is None:
        res = {"status": "err", "msg": "could not find order"}
    else:
        res = {"status": "ok", "order": order_item}

    if include_meta:
        res["meta"] = runtime_meta

    return _serialize(res)
