import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import re
import json
import time
import base64
import logging

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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ff_api")

# ============================================================
#  SETTINGS
# ============================================================
AES_KEY = base64.b64decode("WWcmdGMlREV1aDYlWmNeOA==")
AES_IV  = base64.b64decode("Nm95WkRyMjJFM3ljaGpNJQ==")
USERAGENT = "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)"
RELEASEVERSION = "OB55"

LOGIN_URL = "https://loginbp.ggpolarbear.com/MajorLogin"
LOGIN_URL_ALT = "https://loginbp.ppmainecoonghj.com/MajorLogin"
OAUTH_URL = "https://100067.connect.garena.com/api/v2/oauth/guest/token:grant"

HTTP_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
_http_client = httpx.Client(timeout=HTTP_TIMEOUT, follow_redirects=True)

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
    _g["_LOGINREQ"]._serialized_start = 18
    _g["_LOGINREQ"]._serialized_end = 117
    _g["_LOGINRES"]._serialized_start = 319
    _g["_LOGINRES"]._serialized_end = 735

LoginReq = _g["LoginReq"]
LoginRes = _g["LoginRes"]


# ============================================================
#  HELPERS
# ============================================================
def aes_encrypt(key, iv, plaintext: bytes) -> bytes:
    return AES.new(key, AES.MODE_CBC, iv).encrypt(pad(plaintext, AES.block_size))


def extract_login_res(raw: bytes):
    """Try multiple methods to extract LoginRes from response"""
    # Method 1: Parse from start
    try:
        msg = LoginRes()
        msg.ParseFromString(raw)
        if msg.account_id and msg.account_id > 0:
            return json.loads(json_format.MessageToJson(msg))
    except Exception:
        pass

    # Method 2: Scan for \x08 marker
    idx = 0
    while True:
        idx = raw.find(b"\x08", idx)
        if idx == -1:
            break
        try:
            msg = LoginRes()
            msg.ParseFromString(raw[idx:])
            if msg.account_id and msg.account_id > 0:
                return json.loads(json_format.MessageToJson(msg))
        except Exception:
            pass
        idx += 1

    # Method 3: Find JWT marker and go back to 0x42
    jwt_marker = raw.find(b"eyJhbGciOiJIUzI1NiIs")
    if jwt_marker != -1:
        for i in range(jwt_marker - 1, max(jwt_marker - 300, -1), -1):
            if raw[i] == 0x42:
                try:
                    msg = LoginRes()
                    msg.ParseFromString(raw[i:])
                    if msg.account_id and msg.account_id > 0:
                        return json.loads(json_format.MessageToJson(msg))
                except Exception:
                    pass
                break

    return None


def extract_jwt_from_bytes(content: bytes):
    """Extract JWT token using regex"""
    match = re.search(
        rb'eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+',
        content
    )
    if match:
        try:
            return match.group(0).decode('utf-8')
        except Exception:
            pass
    return None


def extract_region(content: bytes) -> str:
    """Extract region from byte stream"""
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
    """Decode JWT payload without verification"""
    try:
        parts = token.split('.')
        if len(parts) >= 2:
            payload_b64 = parts[1]
            payload_b64 += '=' * ((4 - len(payload_b64) % 4) % 4)
            return json.loads(
                base64.urlsafe_b64decode(payload_b64).decode('utf-8')
            )
    except Exception:
        pass
    return {}


# ============================================================
#  OAUTH — Get Access Token
# ============================================================
def get_access_token(uid: str, password: str):
    """Get access_token and open_id from Garena OAuth"""
    # Method 1: New JSON endpoint
    payload = {
        "client_id": 100067,
        "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f71e54715b7d1e3",
        "client_type": 2,
        "password": password,
        "response_type": "token",
        "uid": int(uid) if uid.isdigit() else uid,
    }
    headers = {
        "Content-Type": "application/json",
        "User-Agent": USERAGENT,
    }
    try:
        r = _http_client.post(OAUTH_URL, json=payload, headers=headers)
        logger.info(f"OAuth (JSON) status: {r.status_code}")
        if r.status_code == 200:
            data = r.json().get("data", {})
            at = data.get("access_token")
            oid = data.get("open_id")
            if at and oid:
                return at, oid
    except Exception as e:
        logger.error(f"OAuth JSON error: {e}")

    # Method 2: Old form endpoint (fallback)
    try:
        url = "https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant"
        body = (
            f"uid={uid}&password={password}"
            "&response_type=token&client_type=2"
            "&client_secret=2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
            "&client_id=100067"
        )
        headers2 = {
            "User-Agent": USERAGENT,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        r = _http_client.post(url, data=body, headers=headers2)
        logger.info(f"OAuth (form) status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            return data.get("access_token"), data.get("open_id")
    except Exception as e:
        logger.error(f"OAuth form error: {e}")

    return None, None


# ============================================================
#  MAJOR LOGIN — Get JWT Token
# ============================================================
def major_login(access_token: str, open_id: str):
    """Send MajorLogin request and parse response"""
    # Build LoginReq protobuf
    req = LoginReq()
    req.open_id = open_id
    req.open_id_type = "4"
    req.login_token = access_token
    req.orign_platform_type = "4"

    serialized = req.SerializeToString()
    encrypted = aes_encrypt(AES_KEY, AES_IV, serialized)

    headers = {
        "User-Agent": USERAGENT,
        "Accept": "*/*",
        "Accept-Encoding": "deflate, gzip",
        "X-GA-SV": "1789568421",
        "Authorization": f"Bearer {access_token}",
        "X-GA": "v1 1",
        "ReleaseVersion": RELEASEVERSION,
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Unity-Version": "2018.4.12f1",
        "PlAy_VeR": "1.132.1",
        "Ob_VeR": RELEASEVERSION,
    }

    for url in (LOGIN_URL, LOGIN_URL_ALT):
        try:
            logger.info(f"MajorLogin trying: {url}")
            r = _http_client.post(url, data=encrypted, headers=headers)
            logger.info(f"MajorLogin status: {r.status_code}, size: {len(r.content)}")

            if r.status_code != 200:
                continue

            content = r.content

            # Try 1: Proto parse
            msg = extract_login_res(content)
            if msg and msg.get("token"):
                logger.info("Token extracted via proto parse")
                return {
                    "token": msg.get("token", ""),
                    "region": (
                        msg.get("lockRegion")
                        or msg.get("notiRegion")
                        or msg.get("ipRegion")
                        or "N/A"
                    ),
                    "account_id": msg.get("accountId"),
                    "nickname": msg.get("nickname", ""),
                    "ttl": msg.get("ttl", 86400),
                    "server_url": msg.get("serverUrl"),
                }

            # Try 2: JWT regex extraction
            token = extract_jwt_from_bytes(content)
            if token and len(token) > 50:
                logger.info("Token extracted via JWT regex")
                payload = decode_jwt_payload(token)
                return {
                    "token": token,
                    "region": extract_region(content),
                    "account_id": payload.get("account_id"),
                    "nickname": payload.get("nickname", ""),
                    "ttl": 86400,
                    "server_url": None,
                }

            # Try 3: Decrypt then parse
            try:
                decrypted = AES.new(
                    AES_KEY, AES.MODE_CBC, AES_IV
                ).decrypt(content)

                msg = extract_login_res(decrypted)
                if msg and msg.get("token"):
                    logger.info("Token extracted via decrypt+proto")
                    return {
                        "token": msg.get("token", ""),
                        "region": msg.get("lockRegion") or "N/A",
                        "account_id": msg.get("accountId"),
                        "nickname": msg.get("nickname", ""),
                        "ttl": msg.get("ttl", 86400),
                        "server_url": msg.get("serverUrl"),
                    }

                token = extract_jwt_from_bytes(decrypted)
                if token and len(token) > 50:
                    logger.info("Token extracted via decrypt+regex")
                    payload = decode_jwt_payload(token)
                    return {
                        "token": token,
                        "region": extract_region(decrypted),
                        "account_id": payload.get("account_id"),
                        "nickname": payload.get("nickname", ""),
                        "ttl": 86400,
                        "server_url": None,
                    }
            except Exception as e:
                logger.error(f"Decrypt attempt failed: {e}")

        except Exception as e:
            logger.error(f"MajorLogin error on {url}: {e}")
            continue

    return None


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
            "/token": "GET /token?uid=UID&password=PASS",
            "/generate": "GET /generate?uid=UID&password=PASS",
        },
        "example": "/token?uid=18097039025&password=yourpass"
    }), 200


@app.route("/token", methods=["GET"])
@app.route("/generate", methods=["GET"])
def api_token():
    uid = request.args.get("uid", "").strip()
    password = request.args.get("password", "").strip()

    if not uid or not password:
        return jsonify({
            "success": False,
            "error": "Both 'uid' and 'password' are required"
        }), 400

    start = time.time()
    logger.info(f"Request: uid={uid}")

    try:
        # Step 1: OAuth
        access_token, open_id = get_access_token(uid, password)
        if not access_token or not open_id:
            return jsonify({
                "success": False,
                "error": "Failed to get access token (check uid/password)"
            }), 401

        # Step 2: MajorLogin
        login_data = major_login(access_token, open_id)
        if not login_data:
            return jsonify({
                "success": False,
                "error": "MajorLogin failed (server rejected or parse error)"
            }), 500

        elapsed = int((time.time() - start) * 1000)

        return jsonify({
            "success": True,
            "uid": uid,
            "token": login_data["token"],
            "region": login_data["region"],
            "account_id": login_data.get("account_id"),
            "nickname": login_data.get("nickname"),
            "ttl": login_data.get("ttl"),
            "server_url": login_data.get("server_url"),
            "access_token": access_token,
            "open_id": open_id,
            "elapsed_ms": elapsed,
        }), 200

    except Exception as e:
        logger.error(f"API error: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
#  ENTRY POINT
# ============================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)