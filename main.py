# main.py
from flask import Flask, jsonify
import os
from database import get_db
from sqlalchemy import text 

app = Flask(__name__)

# @app.route("/")
# def hello():
#     return jsonify({"message": "Hello, world!"})
@app.route("/fetch-data")
def fetch_data():
    # Get a session from the generator
    db = next(get_db())
    
    try:
        # Execute the query
        result = db.execute(text("SELECT * FROM shipping_rates"))  # Replace with your actual table name
        data = [dict(row) for row in result]
    finally:
        # Close the session after the query
        db.close()

    return jsonify(data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
