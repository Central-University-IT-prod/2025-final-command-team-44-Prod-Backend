import hashlib
import hmac
from operator import itemgetter
from urllib.parse import parse_qsl

from app.config import TELEGRAM_BOT_TOKEN


def get_secret_key() -> bytes:
    return hmac.new(
        key=b"WebAppData", msg=TELEGRAM_BOT_TOKEN.encode(), digestmod=hashlib.sha256
    ).digest()


def validate_init_data(init_data: str) -> dict:
    try:
        parsed_data = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError:
        return None
    if "hash" not in parsed_data:
        return None

    hash_ = parsed_data.pop("hash")
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed_data.items(), key=itemgetter(0))
    )
    calculated_hash = hmac.new(
        key=get_secret_key(),
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()
    if calculated_hash != hash_:
        return None
    return parsed_data
