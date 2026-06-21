import json
import secrets
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load JSON data
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

# In-memory store for generated codes: code -> expiry timestamp (seconds since epoch)
CODES = {}

@app.route('/code', methods=['GET'])
def generate_codes():
    """
    Generate access codes.
    Query parameters:
        amount (int, default=1) – number of codes to generate
        days   (int, default=1) – validity period in days
    Returns JSON with the generated codes and their expiry.
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
        code = secrets.token_urlsafe(12)  # ~16 characters
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
    Fetch user details by userid, but ONLY if a valid, non-expired code is provided.
    Query parameters:
        code   (str) – access code (required)
        userid (str) – user identifier (required)
    Returns user data if code is valid, otherwise an error.
    """
    code = request.args.get('code')
    userid = request.args.get('userid')

    if not code or not userid:
        return jsonify({"error": "Missing 'code' or 'userid' query parameter"}), 400

    # Validate the code
    expiry = CODES.get(code)
    if expiry is None:
        return jsonify({"error": "Invalid code"}), 401

    if time.time() > expiry:
        del CODES[code]  # clean up expired code
        return jsonify({"error": "Code has expired"}), 401

    # Look up the user
    user_data = DATA.get(userid)
    if user_data is None:
        return jsonify({"error": f"User with id '{userid}' not found"}), 404

    return jsonify(user_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
