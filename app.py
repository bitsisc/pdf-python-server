import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Enable CORS for all domains on all routes
CORS(app)

@app.route('/api/convert', methods=['POST'])
def convert_pdf():
    # Check if the multipart/form-data request contains the 'document' key
    if 'document' not in request.files:
        return jsonify({"error": "No document provided in the request"}), 400
    
    file = request.files['document']
    
    # Check if a file was actually selected and uploaded
    if file.filename == '':
        return jsonify({"error": "Empty filename provided"}), 400

    # Return the exact mock JSON response required
    return jsonify({"markdown": "Εδώ θα μπει το κείμενο από την Python"}), 200

if __name__ == '__main__':
    # Configure for deployment (e.g., Render.com)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
