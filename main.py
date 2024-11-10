# main.py
from flask import Flask, jsonify
import os
from database import get_db

app = Flask(__name__)

# @app.route("/")
# def hello():
#     return jsonify({"message": "Hello, world!"})
@app.route("/fetch-data")
def fetch_data():
    # Use get_db to create a session
    with get_db() as session:
        # Example query
        result = session.execute("SELECT * FROM shipping_rates")  # Replace with your actual table name
        data = [dict(row) for row in result]

    return jsonify(data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
