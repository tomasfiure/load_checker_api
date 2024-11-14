from flask import Flask, jsonify, request
from database import get_db
from models import APIKey
from functools import wraps
from sqlalchemy import text

app = Flask(__name__)

# Decorator to require an API key for access
def require_api_key(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("X-API-Key") or request.args.get("api_key")
        
        if not api_key:
            return jsonify({"error": "API key is missing"}), 401

        db = next(get_db())
        key_exists = db.query(APIKey).filter_by(key=api_key).first()
        db.close()

        if not key_exists:
            return jsonify({"error": "Invalid API key"}), 403

        return func(*args, **kwargs)
    return decorated_function

# Route to get load details by reference number, accepting both path and query parameter
@app.route("/loads", defaults={"reference_number": None}, methods=["GET"])
@app.route("/loads/<string:reference_number>", methods=["GET"])
@require_api_key
def get_load_details(reference_number):
    # Allow for reference_number as a query parameter if not provided as a path parameter
    reference_number = reference_number or request.args.get("reference_number")

    # Validate that a reference number is provided
    if not reference_number:
        return jsonify({"error": "reference_number is required as a path or query parameter"}), 400

    db = next(get_db())
    
    try:
        # Query the database for the specific reference number
        query = text("SELECT * FROM shipping_rates WHERE reference_number = :reference_number")
        result = db.execute(query, {"reference_number": reference_number}).mappings().fetchone()

        # If no record is found, return a 404 error
        if result is None:
            return jsonify({"error": "Load not found"}), 404

        # Convert the result to a dictionary and return as JSON
        load_details = dict(result)
        return jsonify(load_details)

    finally:
        db.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
    
