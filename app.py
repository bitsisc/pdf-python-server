import os
import tempfile
import logging
import re
from flask import Flask, request, jsonify
from flask_cors import CORS

# Conversion Libraries
import fitz  # PyMuPDF
import pypandoc

# --- 1. Αυτόματη εγκατάσταση του Pandoc στον server (Render.com) ---
# Ελέγχει αν υπάρχει το pandoc binary στο σύστημα, και αν όχι το κατεβάζει!
try:
    pypandoc.get_pandoc_version()
except OSError:
    print("Το Pandoc δεν βρέθηκε. Γίνεται λήψη και εγκατάσταση...")
    pypandoc.download_pandoc()

app = Flask(__name__)

# --- 2. Διπλή Κλειδαριά: Ασφάλεια και Domain Restriction ---
# Επιτρέπει μόνο τα kidmedia.gr, kidmedia.net, kidmedia.eu και τα subdomains τους.
ALLOWED_ORIGINS_PATTERN = re.compile(r"^https?://([a-zA-Z0-9-]+\.)*kidmedia\.(gr|net|eu)(:\d+)?$")

# Κλειδαριά 1: CORS για τους Browsers
CORS(app, resources={
    r"/api/*": {
        "origins": ALLOWED_ORIGINS_PATTERN,
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Κλειδαριά 2: Backend Middleware (Μπλοκάρει Postman, cURL, Python scripts κλπ)
@app.before_request
def restrict_access():
    if request.method == 'OPTIONS':
        return  # Αφήνουμε τις Preflight κλήσεις να περάσουν
    
    origin = request.headers.get('Origin')
    
    # Αν έχει Origin αλλά είναι άγνωστο domain -> Πόρτα!
    if origin and not ALLOWED_ORIGINS_PATTERN.match(origin):
        return jsonify({"error": "Unauthorized Domain: Access Denied. Κλειδωμένο στο kidmedia."}), 403
        
    # Αν ΔΕΝ έχει Origin (άρα κάποιος χτυπάει το API απευθείας, όχι από browser) -> Πόρτα!
    if not origin:
        return jsonify({"error": "Direct API access not allowed. Only browser requests from kidmedia accepted."}), 403

# Configure basic logging for production visibility
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Αφαιρέσαμε το .doc - Το Pandoc απαιτεί .docx
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.odt'}

def extract_pdf(file_path):
    """Extract text from PDF using PyMuPDF (fitz)."""
    text_blocks = []
    with fitz.open(file_path) as doc:
        for page in doc:
            text_blocks.append(page.get_text("text"))
    return "\n".join(text_blocks)

def extract_with_pandoc(file_path):
    """Extract Markdown from DOCX and ODT using the powerful Pandoc engine."""
    # Το 'gfm' (GitHub Flavored Markdown) βγάζει εξαιρετικούς πίνακες
    return pypandoc.convert_file(file_path, 'gfm')

@app.route('/api/convert', methods=['POST'])
def convert_document():
    # Validate request payload
    if 'document' not in request.files:
        return jsonify({"error": "Missing 'document' key in multipart/form-data payload."}), 400
    
    file = request.files['document']
    
    if file.filename == '':
        return jsonify({"error": "No file selected for uploading."}), 400
        
    ext = os.path.splitext(file.filename)[1].lower()
    
    # Ειδικό μήνυμα για τα παλιά .doc αρχεία
    if ext == '.doc':
        return jsonify({"error": "Τα παλιά αρχεία .doc δεν υποστηρίζονται για λόγους σωστής μετατροπής. Παρακαλώ αποθηκεύστε το αρχείο ως .docx (Word) και προσπαθήστε ξανά."}), 400

    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": f"Μη υποστηριζόμενο αρχείο '{ext}'. Επιτρέπονται: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

    temp_path = None
    try:
        # Safely save to an ephemeral temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
            file.save(temp_file)
            temp_path = temp_file.name

        # Intelligent conversion routing
        markdown_text = ""
        
        if ext == '.pdf':
            markdown_text = extract_pdf(temp_path)
        elif ext in ['.docx', '.odt']:
            markdown_text = extract_with_pandoc(temp_path)
        else:
            return jsonify({"error": "Unhandled file extension during processing."}), 500

        # Return the successfully extracted Markdown
        return jsonify({"markdown": markdown_text}), 200

    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {str(e)}")
        return jsonify({"error": f"Internal server error during conversion: {str(e)}"}), 500

    finally:
        # Guaranteed cleanup of the temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.error(f"Failed to delete temporary file {temp_path}: {str(e)}")

if __name__ == '__main__':
    # Bind to 0.0.0.0 and dynamically assign port for Render deployment
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
