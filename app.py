import json
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

@app.route('/users', methods=['GET'])
def get_user():
    """Fetch user details by userid (exact match on JSON keys)."""
    userid = request.args.get('userid')
    if not userid:
        return jsonify({"error": "Missing 'userid' query parameter"}), 400

    # Lookup the key as a string (keys in the file are strings)
    user_data = DATA.get(userid)
    if user_data is None:
        return jsonify({"error": f"User with id '{userid}' not found"}), 404

    return jsonify(user_data)

if __name__ == '__main__':
    # Run on all interfaces, port 5000, with debug mode on for development
    app.run(host='0.0.0.0', port=5000, debug=True)
