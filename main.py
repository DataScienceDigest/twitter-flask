from flask import Flask, request, jsonify

# Create Flask app
app = Flask(__name__)

# Home route
@app.route("/")
def home():
    return "Hello, Flask! 🚀"

# About route
@app.route("/about")
def about():
    return "This is a basic Flask application."

# Dynamic route
@app.route("/greet/<name>")
def greet(name):
    return f"Hello, {name}!"

# POST API example
@app.route("/api/data", methods=["POST"])
def receive_data():
    data = request.get_json()
    return jsonify({
        "message": "Data received successfully",
        "your_data": data
    })

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
