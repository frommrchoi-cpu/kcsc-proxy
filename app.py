import os
import re
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

KCSC_OPENAPI_KEY = os.environ.get("KCSC_OPENAPI_KEY", "")
PROXY_API_KEY = os.environ.get("PROXY_API_KEY", "")  # 프록시 보호용(선택)

ALLOWED_CODE_TYPES = {"KDS", "KCS", "KWCS"}

def require_proxy_auth():
    """PROXY_API_KEY가 설정된 경우에만 X-Api-Key 헤더 인증 강제"""
    if not PROXY_API_KEY:
        return None  # 인증 체크 안 함
    got = request.headers.get("X-Api-Key", "")
    if got != PROXY_API_KEY:
        return jsonify({"message": "Unauthorized"}), 401
    return None

def assert_kcsc_key():
    if not KCSC_OPENAPI_KEY:
        return jsonify({"message": "Missing KCSC_OPENAPI_KEY env var"}), 500
    return None

@app.get("/health")
def health():
    return jsonify({"ok": True})

@app.get("/codelist")
def codelist():
    auth = require_proxy_auth()
    if auth: return auth

    missing = assert_kcsc_key()
    if missing: return missing

    url = "https://kcsc.re.kr/OpenApi/CodeList"
    r = requests.get(url, params={"key": KCSC_OPENAPI_KEY}, timeout=30)
    # KCSC가 JSON 반환한다고 가정
    try:
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({"raw": r.text}), r.status_code

@app.get("/codeviewer/<codeType>/<code>")
def codeviewer(codeType, code):
    auth = require_proxy_auth()
    if auth: return auth

    missing = assert_kcsc_key()
    if missing: return missing

    codeType = codeType.upper()
    if codeType not in ALLOWED_CODE_TYPES:
        return jsonify({"message": "Invalid codeType. Use KDS, KCS, or KWCS."}), 400

    if not re.match(r"^\d+$", code):
        return jsonify({"message": "Invalid code. Use numeric string like 111000."}), 400

    url = f"https://kcsc.re.kr/OpenApi/CodeViewer/{codeType}/{code}"
    r = requests.get(url, params={"key": KCSC_OPENAPI_KEY}, timeout=30)
    try:
        return jsonify(r.json()), r.status_code
    except Exception:
        return jsonify({"raw": r.text}), r.status_code

if __name__ == "__main__":
    # Render는 PORT 환경변수를 줌
    port = int(os.environ.get("PORT", "3000"))
    app.run(host="0.0.0.0", port=port)
