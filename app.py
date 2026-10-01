import os
import re
import json
import time
import base64
import logging
import asyncio
import urllib.parse
from datetime import datetime, timezone

import aiohttp
import requests
import httpx
from flask import Flask, request, jsonify
from flask_cors import CORS

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
from google.protobuf import json_format
from google.protobuf.message import Message

# ============================================================
#  LOGGING
# ============================================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("werkzeug").setLevel(logging.WARNING)
logger = logging.getLogger("ff_api")

# ============================================================
#  SETTINGS
# ============================================================
AES_KEY = base64.b64decode("WWcmdGMlREV1aDYlWmNeOA==")  # Yg&tc%h6%Zc^8
AES_IV = base64.b64decode("Nm95WkRyMjJFM3ljaGpNJQ==")   # 6oyZDr22chjM%
USERAGENT = "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)"
RELEASEVERSION = "OB55"
REQUEST_DELAY = 0.3

LOGIN_URL = "https://loginbp.ggpolarbear.com/"
LOGIN_URL_ALT = "https://loginbp.ppmainecoonghj.com/"
OAUTH_URL = "https://100067.connect.garena.com/api/v2/oauth/guest/token:grant"

# Fast HTTP client (sync fallback)
HTTP_LIMITS = httpx.Limits(max_keepalive_connections=20, max_connections=50)
HTTP_TIMEOUT = httpx.Timeout(15.0, connect=5.0)
_http_client = httpx.Client(limits=HTTP_LIMITS, timeout=HTTP_TIMEOUT)

# ============================================================
#  PROTOBUF — FreeFire_pb2 (inlined)
# ============================================================
_sym_db = _symbol_database.Default()

DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x0e\x46reeFire.proto"c\n\x08LoginReq\x12\x0f\n\x07open_id\x18\x16 \x01(\t'
    b'\x12\x14\n\x0copen_id_type\x18\x17 \x01(\t\x12\x13\n\x0blogin_token\x18\x1d '
    b'\x01(\t\x12\x1b\n\x13orign_platform_type\x18\x63 \x01(\t"]\n\x10\x42lacklist'
    b'InfoRes\x12\x1e\n\nban_reason\x18\x01 \x01(\x0e\x32\n.BanReason\x12\x17\n'
    b'\x0f\x65xpire_duration\x18\x02 \x01(\r\x12\x10\n\x08\x62\x61n_time\x18\x03 '
    b'\x01(\r"f\n\x0eLoginQueueInfo\x12\r\n\x05\x61llow\x18\x01 \x01(\x08\x12'
    b'\x16\n\x0equeue_position\x18\x02 \x01(\r\x12\x16\n\x0eneed_wait_secs\x18'
    b'\x03 \x01(\r\x12\x15\n\rqueue_is_full\x18\x04 \x01(\x08"\xa0\x03\n\x08'
    b'LoginRes\x12\x12\n\naccount_id\x18\x01 \x01(\x04\x12\x13\n\x0block_region'
    b'\x18\x02 \x01(\t\x12\x13\n\x0bnoti_region\x18\x03 \x01(\t\x12\x11\n\tip_'
    b'region\x18\x04 \x01(\t\x12\x19\n\x11\x61gora_environment\x18\x05 \x01(\t'
    b'\x12\x19\n\x11new_active_region\x18\x06 \x01(\t\x12\x19\n\x11recommend_'
    b'regions\x18\x07 \x03(\t\x12\r\n\x05token\x18\x08 \x01(\t\x12\x0b\n\x03ttl'
    b'\x18\t \x01(\r\x12\x12\n\nserver_url\x18\n \x01(\t\x12\x16\n\x0e\x65mul'
    b'ator_score\x18\x0b \x01(\r\x12$\n\tblacklist\x18\x0c \x01(\x0b\x32\x11.'
    b'BlacklistInfoRes\x12#\n\nqueue_info\x18\r \x01(\x0b\x32\x0f.LoginQueue'
    b'Info\x12\x0e\n\x06tp_url\x18\x0e \x01(\t\x12\x15\n\rapp_server_id\x18'
    b'\x0f \x01(\r\x12\x0f\n\x07\x61no_url\x18\x10 \x01(\t\x12\x0f\n\x07ip_city'
    b'\x18\x11 \x01(\t\x12\x16\n\x0eip_subdivision\x18\x12 \x01(\t*\xa8\x01\n'
    b'\tBanReason\x12\x16\n\x12\x42\x41N_REASON_UNKNOWN\x10\x00\x12\x1b\n\x17'
    b'\x42\x41N_REASON_IN_GAME_AUTO\x10\x01\x12\x15\n\x11\x42\x41N_REASON_'
    b'REFUND\x10\x02\x12\x15\n\x11\x42\x41N_REASON_OTHERS\x10\x03\x12\x16\n'
    b'\x12\x42\x41N_REASON_SKINMOD\x10\x04\x12 \n\x1b\x42\x41N_REASON_IN_GAME'
    b'_AUTO_NEW\x10\xf6\x07\x62\x06proto3'
)

_g = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _g)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, "FreeFire_pb2", _g)

if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _g["_BANREASON"]._serialized_start = 738
    _g["_BANREASON"]._serialized_end = 906
    _g["_LOGINREQ"]._serialized_start = 18
    _g["_LOGINREQ"]._serialized_end = 117
    _g["_BLACKLISTINFORES"]._serialized_start = 119
    _g["_BLACKLISTINFORES"]._serialized_end = 212
    _g["_LOGINQUEUEINFO"]._serialized_start = 214
    _g["_LOGINQUEUEINFO"]._serialized_end = 316
    _g["_LOGINRES"]._serialized_start = 319
    _g["_LOGINRES"]._serialized_end = 735

LoginReq = _g["LoginReq"]
LoginRes = _g["LoginRes"]


# ============================================================
#  HELPERS — AES / Proto / Parsing
# ============================================================
def pad_bytes(text: bytes) -> bytes:
    padding_length = AES.block_size - (len(text) % AES.block_size)
    return text + bytes([padding_length] * padding_length)


def aes_cbc_encrypt(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    return AES.new(key, AES.MODE_CBC, iv).encrypt(pad(plaintext, AES.block_size))


def json_to_proto(json_data: str, proto_message: Message) -> bytes:
    json_format.ParseDict(json.loads(json_data), proto_message)
    return proto_message.SerializeToString()


def try_parse_login_res(data: bytes):
    try:
        msg = LoginRes()
        msg.ParseFromString(data)
        if msg.account_id and msg.account_id > 0:
            return json.loads(json_format.MessageToJson(msg))
    except Exception:
        pass
    return None


def extract_login_res(raw: bytes) -> dict:
    # Attempt 1: from index 0
    parsed = try_parse_login_res(raw)
    if parsed:
        return parsed

    # Attempt 2: scan each \x08
    idx = 0
    while True:
        idx = raw.find(b"\x08", idx)
        if idx == -1:
            break
        parsed = try_parse_login_res(raw[idx:])
        if parsed:
            return parsed
        idx += 1

    # Attempt 3: JWT marker prefix
    jwt_marker = raw.find(b"eyJhbGciOiJIUzI1NiIs")
    if jwt_marker != -1:
        for i in range(jwt_marker - 1, max(jwt_marker - 300, -1), -1):
            if raw[i] == 0x42:
                parsed = try_parse_login_res(raw[i:])
                if parsed:
                    return parsed
                break

    return None


def extract_jwt_from_bytes(content: bytes):
    """Regex-based JWT extraction (from app.py)"""
    match = re.search(rb'eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+', content)
    if match:
        try:
            return match.group(0).decode('utf-8')
        except Exception:
            pass

    for i in range(len(content) - 5):
        if content[i] == 0x42:
            if content[i + 1] == 0x80 or (i + 2 < len(content) and content[i + 2:i + 5] == b'eyJ'):
                length = content[i + 1]
                if length & 0x80:
                    length = (length & 0x7f) | (content[i + 2] << 7)
                    token_start = i + 3
                else:
                    token_start = i + 2

                if content[token_start:token_start + 3] == b'eyJ':
                    token_bytes = content[token_start:token_start + length]
                    try:
                        return token_bytes.decode('utf-8')
                    except Exception:
                        pass

    eyj_pos = content.find(b'eyJ')
    if eyj_pos > 0:
        tail = content[eyj_pos:eyj_pos + 2000]
        m = re.match(rb'[A-Za-z0-9_\-\.]+', tail)
        if m:
            try:
                token = m.group(0).decode('utf-8')
                if token.count('.') >= 2:
                    return token
            except Exception:
                pass

    return None


def extract_region_from_bytes(content: bytes) -> str:
    for i in range(len(content) - 6):
        if content[i] == 0x12:
            rlen = content[i + 1]
            if 1 <= rlen <= 5:
                rbytes = content[i + 2:i + 2 + rlen]
                if rbytes.isalpha() and rbytes.isupper():
                    try:
                        return rbytes.decode('utf-8')
                    except Exception:
                        pass
    return "N/A"


def decode_jwt_payload(token: str) -> dict:
    try:
        parts = token.split('.')
        if len(parts) >= 2:
            payload_b64 = parts[1]
            payload_b64 += '=' * ((4 - len(payload_b64) % 4) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))
            return payload
    except Exception:
        pass
    return {}


# ============================================================
#  OAUTH — Get Access Token
# ============================================================
async def get_tokens_async(session: aiohttp.ClientSession, uid: str, password: str):
    await asyncio.sleep(REQUEST_DELAY)

    payload = {
        "client_id": 100067,
        "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f71e54715b7d1e3",
        "client_type": 2,
        "password": password,
        "response_type": "token",
        "uid": int(uid)
    }
    headers = {
        "Content-Type": "application/json",
        "User-Agent": USERAGENT
    }

    try:
        async with session.post(OAUTH_URL, json=payload, headers=headers, timeout=30) as r:
            if r.status == 200:
                data = (await r.json()).get('data', {})
                at = data.get('access_token')
                oid = data.get('open_id')
                if at and oid:
                    logger.info(f"OAuth OK for UID: {uid}")
                    return {"open_id": oid, "access_token": at}
            return None
    except Exception as e:
        logger.error(f"OAuth exception {uid}: {e}")
        return None


def get_access_token_sync(account: str):
    """Sync fallback — uses httpx"""
    url = "https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant"
    payload = (
        account
        + "&response_type=token&client_type=2"
        + "&client_secret=2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
        + "&client_id=100067"
    )
    headers = {
        "User-Agent": USERAGENT,
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    try:
        resp = _http_client.post(url, data=payload, headers=headers)
        data = resp.json()
        return data.get("access_token", "0"), data.get("open_id", "0")
    except Exception as e:
        logger.error(f"Sync OAuth error: {e}")
        return "0", "0"


# ============================================================
#  MAJOR LOGIN — Get JWT Token
# ============================================================
async def major_login_async(session: aiohttp.ClientSession, access_token: str, open_id: str):
    await asyncio.sleep(REQUEST_DELAY / 2)
    logger.info(f"MajorLogin for OpenID: {open_id}")

    try:
        req = LoginReq()
        req.open_id = open_id
        req.open_id_type = "4"
        req.login_token = access_token
        req.orign_platform_type = "4"

        serialized = req.SerializeToString()
        encrypted = aes_cbc_encrypt(AES_KEY, AES_IV, serialized)

        url = f"{LOGIN_URL}MajorLogin"
        headers = {
            'User-Agent': USERAGENT,
            'Accept': "*/*",
            'Accept-Encoding': "deflate, gzip",
            'X-GA-SV': "1789568421",
            'Authorization': f"Bearer {access_token}",
            'X-GA': "v1 1",
            'ReleaseVersion': RELEASEVERSION,
            'Content-Type': "application/x-www-form-urlencoded",
            'X-Unity-Version': "2018.4.12f1",
            'PlAy_VeR': "1.132.1",
            'Ob_VeR': RELEASEVERSION,
        }

        async with session.post(url, data=encrypted, headers=headers, timeout=30) as r:
            logger.info(f"MajorLogin HTTP: {r.status}")

            if r.status != 200:
                return None

            content = await r.read()
            logger.info(f"Response: {len(content)} bytes")

            # Method 1: Proto parse
            proto_msg = extract_login_res(content)
            if proto_msg and proto_msg.get('token'):
                return {
                    "token": proto_msg.get('token', ''),
                    "region": proto_msg.get('lockRegion', proto_msg.get('notiRegion', 'N/A')),
                    "account_id": proto_msg.get('accountId'),
                    "nickname": proto_msg.get('nickname', ''),
                    "ttl": proto_msg.get('ttl', 86400),
                    "server_url": proto_msg.get('serverUrl'),
                }

            # Method 2: JWT regex
            token = extract_jwt_from_bytes(content)
            if token and len(token) > 50:
                region = extract_region_from_bytes(content)
                payload = decode_jwt_payload(token)
                return {
                    "token": token,
                    "region": region,
                    "account_id": payload.get('account_id'),
                    "nickname": payload.get('nickname', ''),
                    "ttl": 86400,
                    "server_url": None
                }

            # Method 3: Decrypt then parse
            try:
                dec = AES.new(AES_KEY, AES.MODE_CBC, AES_IV).decrypt(content)
                proto_msg = extract_login_res(dec)
                if proto_msg and proto_msg.get('token'):
                    return {
                        "token": proto_msg.get('token', ''),
                        "region": proto_msg.get('lockRegion', proto_msg.get('notiRegion', 'N/A')),
                        "account_id": proto_msg.get('accountId'),
                        "nickname": proto_msg.get('nickname', ''),
                        "ttl": proto_msg.get('ttl', 86400),
                        "server_url": proto_msg.get('serverUrl'),
                    }
                token = extract_jwt_from_bytes(dec)
                if token and len(token) > 50:
                    region = extract_region_from_bytes(dec)
                    payload = decode_jwt_payload(token)
                    return {
                        "token": token,
                        "region": region,
                        "account_id": payload.get('account_id'),
                        "nickname": payload.get('nickname', ''),
                        "ttl": 86400,
                        "server_url": None
                    }
            except Exception:
                pass

            return None

    except asyncio.TimeoutError:
        return None
    except Exception as e:
        logger.error(f"MajorLogin exception: {e}", exc_info=True)
        return None


# ============================================================
#  GENERATE JWT — Main async pipeline
# ============================================================
async def generate_jwt_async(uid: str, password: str) -> dict:
    start = time.time()
    result = {
        "success": False,
        "uid": uid,
        "token": None,
        "region": None,
        "account_id": None,
        "nickname": None,
        "ttl": None,
        "server_url": None,
        "error": None,
        "elapsed_ms": 0
    }

    try:
        connector = aiohttp.TCPConnector(limit=10, ssl=False)
        timeout = aiohttp.ClientTimeout(total=60)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tokens = await get_tokens_async(session, uid, password)
            if not tokens:
                result["error"] = "Failed to get access token"
                result["elapsed_ms"] = int((time.time() - start) * 1000)
                return result

            login_data = await major_login_async(session, tokens["access_token"], tokens["open_id"])
            if not login_data:
                result["error"] = "MajorLogin failed"
                result["elapsed_ms"] = int((time.time() - start) * 1000)
                return result

            result.update({
                "success": True,
                "token": login_data["token"],
                "region": login_data["region"],
                "account_id": login_data.get("account_id"),
                "nickname": login_data.get("nickname"),
                "ttl": login_data.get("ttl"),
                "server_url": login_data.get("server_url"),
                "access_token": tokens["access_token"],
                "open_id": tokens["open_id"],
            })

    except Exception as e:
        logger.error(f"generate_jwt error: {e}", exc_info=True)
        result["error"] = str(e)

    result["elapsed_ms"] = int((time.time() - start) * 1000)
    return result


def generate_jwt_sync(uid: str, password: str) -> dict:
    """Sync wrapper using httpx (from file 1)"""
    start_time = time.time()

    token_val, open_id = get_access_token_sync(f"uid={uid}&password={password}")
    if token_val == "0" or open_id == "0":
        raise Exception("Invalid UID or Password — access token not received")

    body = json.dumps({
        "open_id": open_id,
        "open_id_type": "4",
        "login_token": token_val,
        "orign_platform_type": "4",
    })
    proto_bytes = json_to_proto(body, LoginReq())
    payload = aes_cbc_encrypt(AES_KEY, AES_IV, proto_bytes)

    headers = {
        "User-Agent": USERAGENT,
        "Accept": "*/*",
        "Accept-Encoding": "deflate, gzip",
        "X-Ga-Sv": "1789534056",
        "Authorization": "Bearer",
        "X-Ga": "v1 1",
        "Releaseversion": RELEASEVERSION,
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Unity-Version": "2018.4.12f1",
        "PlAy_VeR": "1.132.1",
        "Ob_VeR": RELEASEVERSION,
    }

    resp = _http_client.post(f"{LOGIN_URL_ALT}MajorLogin", data=payload, headers=headers)
    msg = extract_login_res(resp.content)
    if not msg:
        raise Exception("Could not parse LoginRes")

    elapsed = time.time() - start_time

    return {
        "access_token": token_val,
        "open_id": open_id,
        "real_uid": str(msg.get("accountId", "")),
        "status": "success",
        "time": f"{elapsed:.2f}s",
        "token": f"{msg.get('token', '')}",
        "region": msg.get('lockRegion', msg.get('notiRegion', 'N/A')),
        "account_id": msg.get("accountId"),
        "nickname": msg.get("nickname", ""),
    }


# ============================================================
#  FLASK APP
# ============================================================
app = Flask(__name__)
CORS(app)


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "name": "FreeFire Token API",
        "status": "online",
        "endpoints": {
            "/token": "GET /token?uid=UID&password=PASS (sync)",
            "/generate": "GET /generate?uid=UID&password=PASS (async)",
        },
        "example": "/token?uid=18097039025&password=yourpass"
    }), 200


@app.route("/token", methods=["GET"])
def api_token():
    """Sync endpoint (from file 1)"""
    uid = request.args.get("uid")
    password = request.args.get("password")

    if not uid or not password:
        return jsonify({
            "status": "error",
            "error": "Both uid and password parameters are required"
        }), 400

    try:
        token_data = generate_jwt_sync(uid, password)
        return jsonify(token_data), 200
    except Exception as e:
        logger.error(f"Token error: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": f"Failed to generate token: {str(e)}"
        }), 500


@app.route("/generate", methods=["GET"])
def api_generate():
    """Async endpoint (from file 2)"""
    uid = request.args.get("uid", "").strip()
    password = request.args.get("password", "").strip()

    if not uid or not password:
        return jsonify({
            "success": False,
            "error": "Missing 'uid' or 'password' query parameter"
        }), 400

    logger.info(f"Request: uid={uid}")

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(generate_jwt_async(uid, password))
        loop.close()

        if not result["success"]:
            return jsonify(result), 500

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"API error: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
#  ENTRY POINT
# ============================================================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5002))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info("=" * 60)
    logger.info("FreeFire Token API (Merged)")
    logger.info("=" * 60)
    logger.info(f"Running:  http://{host}:{port}")
    logger.info(f"Sync:     http://127.0.0.1:{port}/token?uid=XXX&password=YYY")
    logger.info(f"Async:    http://127.0.0.1:{port}/generate?uid=XXX&password=YYY")
    logger.info("=" * 60)

    app.run(host=host, port=port, debug=False, threaded=True)