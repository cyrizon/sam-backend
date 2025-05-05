from flask import Flask, jsonify
import os
from dotenv import load_dotenv
from src.config.config import Config

# loading environment variables
load_dotenv()

# declaring flask application
app = Flask(__name__)

# calling the dev configuration
config = Config().dev_config

# making our application to use dev env
app.env = config.ENV

# Reroute for the root URL
@app.route('/')
def index():
    return jsonify({"message": "Welcome to the Flask API!"})

# Example API route
@app.route('/api/hello', methods=['GET'])
def hello_world():
    return jsonify({"message": "Hello, World!"})