import json
import decimal
import boto3
import os
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Attr

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            return int(o)
        return super(DecimalEncoder, self).default(o)


HUMAN_STATUS = {
    "100": "incomplete",
    "110": "payment failed",
    "120": "paid",
    "200": "processed",
    "210": "shipped",
    "300": "delivered",
    "500": "cancelled",
    "600": "rejected",
}


def _to_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_ts(value):
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc).isoformat()
    except (TypeError, ValueError):
        return str(value)


def _normalize_order(item):
    status = json.dumps(item["orderStatus"], cls=DecimalEncoder)
    return {
        "order-id": item["orderId"],
        "date": _to_ts(item["paymentTS"]),
        "total": item["totalAmount"],
        "status": HUMAN_STATUS.get(status, "unknown"),
        "token": item.get("confirmationToken", ""),
    }


def _scan_orders(table, user_id, min_status, limit):
    scan_kwargs = {
        "FilterExpression": Attr("userId").eq(user_id) & Attr("orderStatus").gte(min_status),
        "Limit": limit,
    }
    response = table.scan(**scan_kwargs)
    orders = list(response.get("Items", []))

    while "LastEvaluatedKey" in response and len(orders) < limit:
        scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
        response = table.scan(**scan_kwargs)
        orders.extend(response.get("Items", []))

    return orders[:limit]


def lambda_handler(event, context):
    user_id = event["user"]
    max_results = max(1, min(_to_int(event.get("max_results"), 50), 200))
    min_status = _to_int(event.get("min_status"), 100)

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["ORDERS_TABLE"])
    raw_orders = _scan_orders(table, user_id, min_status, max_results)

    orders = [_normalize_order(item) for item in raw_orders]
    orders.sort(key=lambda x: x["date"], reverse=True)

    return {
        "status": "ok",
        "orders": orders,
        "count": len(orders),
    }
