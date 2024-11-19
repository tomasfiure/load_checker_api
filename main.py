from flask import Flask, jsonify, request
from database import get_db
from models import APIKey
from functools import wraps
from sqlalchemy import text
import requests

app = Flask(__name__)

# Decorator to require an API key for access
def require_api_key(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("X-API-Key") or request.args.get("api_key") or (request.get_json() or {}).get("api_key")
        
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

@app.route("/loads", methods=["POST"])
@require_api_key
def post_load_details():
    """
    Retrieve load details based on a reference number provided in the POST request body.
    """
    # Extract JSON payload
    request_data = request.get_json()

    # Extract the reference number from the payload
    reference_number = request_data.get("reference_number")

    # Validate that a reference number is provided
    if not reference_number:
        return jsonify({"error": "reference_number is required in the request body"}), 400

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


@app.route("/search", methods=["GET"])
@require_api_key
def search_loads():
    """
    Search loads by a single query parameter (e.g., origin, destination, or equipment_type).
    """
    # Get query parameters
    query_params = request.args

    # Exclude `api_key` if it is provided
    query_params = {key: value for key, value in query_params.items() if key != "api_key"}

    # Validate that exactly one query parameter is provided
    if len(query_params) != 1:
        return jsonify({"error": "Exactly one query parameter is required, excluding 'api_key'."}), 400

    # Extract the single parameter and its value
    param_key, param_value = next(iter(query_params.items()))

    db = next(get_db())
    
    try:
        # Build the SQL query dynamically
        query = f"SELECT * FROM shipping_rates WHERE {param_key} = :{param_key}"

        # Execute the query
        results = db.execute(text(query), {param_key: param_value}).mappings().fetchall()

        # If no records are found, return a 404 error
        if not results:
            return jsonify({"error": f"No loads found for {param_key} = {param_value}"}), 404

        # Convert the results to a list of dictionaries and return as JSON
        loads = [dict(result) for result in results]
        return jsonify(loads)

    finally:
        db.close()
        
@app.route("/carrier", methods=["GET"])
def get_carrier_info():
    """
    Makes a GET call to the FMCAS carrier service with the provided API key and MC number.
    """
    # Filter query parameters to include only 'webKey' and 'mc_number'
    query_params = {
        key: value for key, value in request.args.items()
        if key in ["webKey", "mc_number"]
    }

    # Extract the specific query parameters
    webKey = query_params.get('webKey')
    mc_number = query_params.get('mc_number')

    # Validate required query parameters
    if not mc_number or not webKey:
        return jsonify({"error": "Both 'mc_number' and 'webKey' are required."}), 400

    # Base URL for the external service
    base_url = "https://mobile.fmcsa.dot.gov/qc/services/carriers/"
    api_url = f"{base_url}{mc_number}?webKey={webKey}"

    try:
        # Make the external API call
        response = requests.get(api_url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route("/carrier", methods=["POST"])
def post_carrier_info():
    """
    Makes a POST call to the FMCAS carrier service with the provided API key and MC number.
    """
    # Extract JSON payload from the POST request
    request_data = request.get_json()

    # Filter incoming parameters to include only 'webKey' and 'mc_number'
    query_params = {
        key: value for key, value in request_data.items()
        if key in ["webKey", "mc_number"]
    }

    # Extract the specific query parameters
    webKey = query_params.get('webKey')
    mc_number = query_params.get('mc_number')

    # Validate required fields
    if not mc_number or not webKey:
        return jsonify({"error": "Both 'mc_number' and 'webKey' are required."}), 400

    # Base URL for the external service
    base_url = "https://mobile.fmcsa.dot.gov/qc/services/carriers/"
    api_url = f"{base_url}{mc_number}?webKey={webKey}"

    try:
        # Make the external API call
        response = requests.get(api_url)  # External API remains a GET call
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
    
