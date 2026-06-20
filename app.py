import json
import secrets
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load the JSON data once at startup
JSON_FILE = "tg_India.json"
try:
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        DATA = json.load(f)
except FileNotFoundError:
    DATA = {}
    print(f"⚠️  Warning: {JSON_FILE} not found. Starting with empty data.")
except json.JSONDecodeError:
    DATA = {}
    print(f"⚠️  Warning: {JSON_FILE} is not valid JSON. Starting with empty data.")

# In‑memory store for generated codes: code -> expiry_timestamp (seconds since epoch)
CODES = {}

@app.route('/users', methods=['GET'])
def get_user():
    """Fetch user details by userid (exact match on JSON keys)."""
    userid = request.args.get('userid')
    if not userid:
        return jsonify({"error": "Missing 'userid' query parameter"}), 400

    user_data = DATA.get(userid)
    if user_data is None:
        return jsonify({"error": f"User with id '{userid}' not found"}), 404

    return jsonify(user_data)

@app.route('/code', methods=['GET'])
def generate_codes():
    """
    Generate access codes.
    Query parameters:
        amount (int, default=1) – number of codes to generate
        days   (int, default=1) – validity period in days
    Returns:
        JSON with a list of generated codes and their expiry timestamps.
    """
    try:
        amount = int(request.args.get('amount', 1))
        days = int(request.args.get('days', 1))
    except ValueError:
        return jsonify({"error": "amount and days must be integers"}), 400

    if amount < 1:
        return jsonify({"error": "amount must be at least 1"}), 400
    if days < 1:
        return jsonify({"error": "days must be at least 1"}), 400

    expiry = time.time() + (days * 24 * 3600)
    codes = []
    for _ in range(amount):
        # Generate a secure random alphanumeric code (length 16)
        code = secrets.token_urlsafe(12)  # 12 bytes -> about 16 characters
        CODES[code] = expiry
        codes.append({"code": code, "expires_at": expiry})

    return jsonify({
        "generated": codes,
        "valid_for_days": days,
        "expires_at": expiry  # all codes share the same expiry for simplicity
    })

@app.route('/access', methods=['GET'])
def access_user():
    """
    Validate an access code and return user data.
    Query parameters:
        code   (str) – the access code
        userid (str) – the user identifier
    Returns:
        User data if the code is valid and not expired, otherwise an error.
    """
    code = request.args.get('code')
    userid = request.args.get('userid')

    if not code or not userid:
        return jsonify({"error": "Missing 'code' or 'userid' query parameter"}), 400

    # Check if the code exists
    expiry = CODES.get(code)
    if expiry is None:
        return jsonify({"error": "Invalid code"}), 401

    # Check if the code has expired
    if time.time() > expiry:
        # Optional: remove expired code to keep store clean
        del CODES[code]
        return jsonify({"error": "Code has expired"}), 401

    # Look up the user
    user_data = DATA.get(userid)
    if user_data is None:
        return jsonify({"error": f"User with id '{userid}' not found"}), 404

    return jsonify(user_data)

if __name__ == '__main__':
    # Run on all interfaces, port 5000, with debug mode on for development
    app.run(host='0.0.0.0', port=5000, debug=True)
