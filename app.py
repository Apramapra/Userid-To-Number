import json
import secrets
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

# ---- Load data from tg_India.json (must be an array of user objects) ----
DATA = {}  # final combined dictionary keyed by UserID

try:
    with open("tg_India.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    if isinstance(raw_data, list):
        for user in raw_data:
            if "UserID" in user:
                DATA[user["UserID"]] = user
            else:
                print("⚠️  Skipping entry missing 'UserID':", user)
        print(f"✅ Loaded {len(DATA)} users from tg_India.json")
    else:
        print("⚠️  tg_India.json is not an array; expected format: [ {UserID: ..., ...}, ... ]")
        DATA = {}

except FileNotFoundError:
    print("⚠️  tg_India.json not found.")
except json.JSONDecodeError:
    print("⚠️  tg_India.json is not valid JSON.")

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
