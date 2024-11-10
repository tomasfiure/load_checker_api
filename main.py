# main.py
from flask import Flask, jsonify
import os
from database import get_db
from sqlalchemy import text 

app = Flask(__name__)

@app.route("/loads/<string:reference_number>", methods=["GET"])
def get_load_details(reference_number):
    # Create a new database session
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
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
