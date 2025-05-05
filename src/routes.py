# filepath: c:\Users\pecni\Desktop\SAM\sam-backend\src\routes.py
from flask import jsonify

def register_routes(app):
    @app.route('/')
    def index():
        return jsonify({"message": "Welcome to the Flask API!"})

    @app.route('/api/hello', methods=['GET'])
    def hello_world():
        return jsonify({"message": "Hello, World!"})