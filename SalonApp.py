import os
import asyncio
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import openai
import requests
from flask_cors import CORS

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RETELL_API_KEY = os.getenv("RETELL_API_KEY")
OPENAI_LLM_MODEL = os.getenv("OPENAI_LLM_MODEL", "gpt-4")

# Initialize Flask app and WebSocket server
app = Flask(__name__)
CORS(app, origins="http://localhost:3000")
socketio = SocketIO(app, cors_allowed_origins="*")

openai.api_key = OPENAI_API_KEY

# Retell API base URL
RETELL_API_BASE = "https://api.retellai.com"

# Static business info
BUSINESS_INFO = {
    "services": {
        "haircut": "500 PHP",
        "coloring": "1500 PHP",
        "styling": "1000 PHP",
    },
    "location": "123 Salon Street, Manila, Philippines",
    "hours": {
        "Monday-Friday": "9:00 AM - 7:00 PM",
        "Saturday-Sunday": "10:00 AM - 5:00 PM",
    },
}

# Helper function: Get Retell AI response
def get_retell_response(conversation_id, message):
    url = f"{RETELL_API_BASE}/conversations/{conversation_id}/messages"
    headers = {"Authorization": f"Bearer {RETELL_API_KEY}"}
    data = {"content": message}
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

# Helper function: Get OpenAI response
def get_openai_response(prompt):
    response = openai.ChatCompletion.create(
        model=OPENAI_LLM_MODEL,
        messages=[{"role": "system", "content": "You are a helpful salon assistant."},
                  {"role": "user", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"]

# Route: Web page to initiate the call
@app.route("/", methods=["GET"])
def index():
    return "<h1>The Color Bar Salon AI Agent</h1><button onclick=\"startCall()\">Start Call</button>", 200

# Route: Booking handler
@app.route("/book", methods=["POST"])
def book_appointment():
    data = request.json
    name = data.get("name")
    contact = data.get("contact")
    service = data.get("service")
    date = data.get("date")
    time = data.get("time")

    if not all([name, contact, service, date, time]):
        return jsonify({"error": "All fields are required."}), 400

    # Confirm the booking
    confirmation = (
        f"Thank you, {name}. Your appointment for {service} is booked on {date} at {time}. "
        "We will contact you at {contact} for any updates."
    )
    return jsonify({"message": confirmation}), 200

# Route: Start Call (Integrating with Express)
@app.route("/start-call", methods=["POST"])
def start_call():
    data = request.json
    agent_id = data.get("agent_id")
    metadata = data.get("metadata")
    retell_llm_dynamic_variables = data.get("retell_llm_dynamic_variables")

    if not agent_id:
        return jsonify({"error": "Agent ID is required."}), 400

    # Prepare payload
    payload = {"agent_id": agent_id}

    if metadata:
        payload["metadata"] = metadata

    if retell_llm_dynamic_variables:
        payload["retell_llm_dynamic_variables"] = retell_llm_dynamic_variables

    # Send data to the Express server
    try:
        response = requests.post(
            "http://localhost:8080/create-web-call",
            json=payload
        )
        response.raise_for_status()

        # Emit agent's first message to the WebSocket client (after starting the call)
        socketio.emit("response", {"message": "Welcome to Color Bar Salon! How can I assist you today?"})

        return jsonify(response.json()), 200
    except requests.RequestException as e:
        app.logger.error(f"Error in /start-call: {e}")
        return jsonify({"error": "Failed to create web call."}), 500

# Route: Dynamic WebSocket call handler
@app.route("/llm-websocket/<call_id>", methods=["GET"])
def websocket_call(call_id):
    # Placeholder for handling WebSocket calls with dynamic call_id
    return jsonify({"message": f"WebSocket call initiated for ID: {call_id}"}), 200

@socketio.on('llm-websocket-call')
def handle_llm_websocket_call(data):
    call_id = data.get('call_id')
    if not call_id:
        emit('response', {'error': 'call_id is missing'})
        return

    # Process call_id and interact with OpenAI or Retell AI API
    emit('response', {'message': f"WebSocket call initiated for ID: {call_id}"})

# WebSocket handler: Manage live conversation
@socketio.on("message")
def handle_message(data):
    user_message = data.get("message")
    print(user_message)

    if not user_message:
        emit("response", {"error": "Message cannot be empty."})
        return

    # Process user message
    if "services" in user_message.lower():
        response = f"We offer the following services: {', '.join(BUSINESS_INFO['services'].keys())}."
    elif "location" in user_message.lower():
        response = f"Our salon is located at {BUSINESS_INFO['location']}"
    elif "hours" in user_message.lower():
        response = (
            f"Our hours are: Monday to Friday: {BUSINESS_INFO['hours']['Monday-Friday']}, "
            f"Saturday and Sunday: {BUSINESS_INFO['hours']['Saturday-Sunday']}."
        )
    else:
        response = get_openai_response(user_message)

    emit("response", {"message": response})

# Main execution
if __name__ == "__main__":
    socketio.run(app, debug=True)
