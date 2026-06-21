import json
import secrets
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

# ---- Load data from both files and merge ----
DATA = {}  # final combined dictionary

# 1. Load tg_India.json
try:
    with open("tg_India.json", "r", encoding="utf-8") as f:
        json_data = json.load(f)
    if isinstance(json_data, dict):
        DATA.update(json_data)
    else:
        print("⚠️  tg_India.json is not a dictionary; skipping.")
except FileNotFoundError:
    print("⚠️  tg_India.json not found.")
except json.JSONDecodeError:
    print("⚠️  tg_India.json is not valid JSON.")

# 2. Load INDIAN_TG_NUMBERS.txt (overwrites duplicates)
try:
    with open("INDIAN_TG_NUMBERS.txt", "r", encoding="utf-8") as f:
        content = f.read().strip()
    # Try to parse as JSON
    try:
        txt_data = json.loads(content)
        if isinstance(txt_data, dict):
            DATA.update(txt_data)          # overwrite with .txt data
        else:
            # If it's a JSON array, convert to dict with array index as key? Not ideal.
            # Better: treat as list of IDs and create simple records.
            raise ValueError("Not a dict")
    except (json.JSONDecodeError, ValueError):
        # Not JSON → treat each line as a user ID
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        for uid in lines:
            DATA[uid] = {"id": uid, "info": "Data from INDIAN_TG_NUMBERS.txt"}
        print(f"✅ Loaded {len(lines)} user IDs from INDIAN_TG_NUMBERS.txt (as simple records).")
except FileNotFoundError:
    print("⚠️  INDIAN_TG_NUMBERS.txt not found.")

# ---- In‑memory code store ----
CODES = {}

# ---- Endpoints ----
@app.route('/code', methods=['GET'])
def generate_codes():
    """
    Generate access codes.
    Query: ?amount=N&days=D
    """
    try:
        amount = int(request.args.get('amount', 1))
        days = int(request.args.get('days', 1))
    except ValueError:
        return jsonify({"error": "amount and days must be integers"}), 400

    if amount < 1 or days < 1:
        return jsonify({"error": "amount and days must be at least 1"}), 400

    expiry = time.time() + (days * 24 * 3600)
    codes = []
    for _ in range(amount):
        code = secrets.token_urlsafe(12)
        CODES[code] = expiry
        codes.append({"code": code, "expires_at": expiry})

    return jsonify({
        "generated": codes,
        "valid_for_days": days,
        "expires_at": expiry
    })

@app.route('/users', methods=['GET'])
def get_user():
    """
    Fetch user details by userid, but only if a valid, non-expired code is provided.
    Query: ?code=<code>&userid=<userid>
    """
    code = request.args.get('code')
    userid = request.args.get('userid')

    if not code or not userid:
        return jsonify({"error": "Missing 'code' or 'userid' query parameter"}), 400

    # Validate code
    expiry = CODES.get(code)
    if expiry is None:
        return jsonify({"error": "Invalid code"}), 401
    if time.time() > expiry:
        del CODES[code]
        return jsonify({"error": "Code has expired"}), 401

    # Look up user in the merged DATA
    user_data = DATA.get(userid)
    if user_data is None:
        return jsonify({"error": f"User with id '{userid}' not found"}), 404

    return jsonify(user_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
