import azure.functions as func
import gzip, json, base64, hmac, hashlib, datetime, requests

WORKSPACE_ID = "517729f4-6ecd-49d4-9440-64e355ad5a8a"
SHARED_KEY = "PV5jkEIH6K63VsrnG9Q2hfG98Ed23Aumr1E7FkLTHu5GR6/S0h8fHT7t5uzfgpbiOcry43thUNuTmIajMUycJg=="
LOG_TYPE = "KonnectAuditLog"

def build_signature(date, content_length):
    string_to_hash = f"POST\n{content_length}\napplication/json\nx-ms-date:{date}\n/api/logs"
    bytes_to_hash = bytes(string_to_hash, encoding="utf-8")
    decoded_key = base64.b64decode(SHARED_KEY)
    encoded_hash = base64.b64encode(
        hmac.new(decoded_key, bytes_to_hash, digestmod=hashlib.sha256).digest()
    ).decode()
    return f"SharedKey {WORKSPACE_ID}:{encoded_hash}"

def main(req: func.HttpRequest) -> func.HttpResponse:
    compressed_data = req.get_body()
    decompressed_data = gzip.decompress(compressed_data).decode("utf-8")

    logs = [json.loads(line) for line in decompressed_data.strip().split("\n")]
    body = json.dumps(logs)

    date = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    signature = build_signature(date, len(body))

    headers = {
        "Content-Type": "application/json",
        "Authorization": signature,
        "Log-Type": LOG_TYPE,
        "x-ms-date": date,
        "time-generated-field": "timestamp"
    }

    url = f"https://{WORKSPACE_ID}.ods.opinsights.azure.com/api/logs?api-version=2016-04-01"
    response = requests.post(url, data=body, headers=headers)

    return func.HttpResponse(
        f"Status: {response.status_code}, Response: {response.text}",
        status_code=200
    )
