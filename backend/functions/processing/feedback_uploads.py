import json
import time
import boto3
import os
from botocore.exceptions import ClientError
from botocore.client import Config
import uuid
from urllib import parse

DEFAULT_EXPIRES_SECONDS = 120
MAX_EXPIRES_SECONDS = 600

try:
    from .limits import parse_int_expr
except Exception:
    parse_int_expr = None


def lambda_handler(event, context):
    print(json.dumps(event))

    if "file" in event:
        s3 = boto3.client(
            "s3",
            region_name=os.environ["AWS_REGION"],
            endpoint_url=f'https://s3.{os.environ["AWS_REGION"]}.amazonaws.com',
            config=Config(s3={"addressing_style": "virtual"}),
        )

        uuidv4 = str(uuid.uuid4())

        expires = DEFAULT_EXPIRES_SECONDS
        if parse_int_expr is not None:
            expires = parse_int_expr(event.get("expires"), DEFAULT_EXPIRES_SECONDS)
        expires = max(30, min(int(expires), MAX_EXPIRES_SECONDS))

        try:
            response = s3.generate_presigned_post(
                os.environ["FEEDBACK_BUCKET"],
                uuidv4 + "_" + event["file"],
                ExpiresIn=expires,
            )
            print(response)
        except ClientError as e:
            print(str(e))
            return json.dumps({"status": "err", "msg": "could not get signed url"})

        return response

    if "Records" in event:
        filename = parse.unquote_plus(event["Records"][0]["s3"]["object"]["key"])
        if not is_safe(filename) or "/" in filename or ".." in filename:
            return {"status": "error", "message": "invalid filename"}

        # Create marker files without invoking a shell.
        open("/tmp/{}".format(filename), "a").close()
        open("/tmp/{}.txt".format(filename), "a").close()

    return {"status": "ok", "message": "Thank you."}


def is_safe(s):
    if not isinstance(s, str) or not s:
        return False
    return parse.quote(s, safe="._-").replace("%", "") == s

