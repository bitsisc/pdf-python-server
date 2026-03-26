import os
import tempfile
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS

# Conversion Libraries
import fitz  # PyMuPDF
import mammoth
import docx  # python-docx
from markitdown import MarkItDown
from odf.opendocument import load as odf_load
from odf.teletype import extractText

app = Flask(__name__)
# Enable CORS globally
CORS(app)

# Configure basic logging for production visibility
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.odt'}

def extract_pdf(file_path):
    """Extract text from PDF using PyMuPDF (fitz)."""
    text_blocks = []
    with fitz.open(file_path) as doc:
        for page in doc:
            text_blocks.append(page.get_text("text"))
    return "\n".join(text_blocks)

def extract_docx(file_path):
    """Extract Markdown from DOCX using mammoth, fallback to python-docx."""
    try:
        with open(file_path, "rb") as docx_file:
            result = mammoth.convert_to_markdown(docx_file)
            if result.value.strip():
                return result.value
    except Exception as e:
        logger.warning(f"Mammoth conversion failed, falling back to python-docx: {str(e)}")
        
    # Fallback using python-docx
    document = docx.Document(file_path)
    return "\n\n".join([p.text for p in document.paragraphs if p.text.strip()])

def extract_odt(file_path):
    """Extract text from ODT using odfpy."""
    doc = odf_load(file_path)
    return extractText(doc)

def extract_markitdown(file_path):
    """Extract Markdown from legacy .doc or general formats using markitdown."""
    md = MarkItDown()
    result = md.convert(file_path)
    return result.text_content

@app.route('/api/convert', methods=['POST'])
def convert_document():
    # 1. Validate request payload
    if 'document' not in request.files:
        return jsonify({"error": "Missing 'document' key in multipart/form-data payload."}), 400
    
    file = request.files['document']
    
    if file.filename == '':
        return jsonify({"error": "No file selected for uploading."}), 400
        
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": f"Unsupported file extension '{ext}'. Allowed extensions are: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

    temp_path = None
    try:
        # 2. Safely save to an ephemeral temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
            file.save(temp_file)
            temp_path = temp_file.name

        # 3. Intelligent conversion routing based on file extension
        markdown_text = ""
        
        if ext == '.pdf':
            markdown_text = extract_pdf(temp_path)
        elif ext == '.docx':
            markdown_text = extract_docx(temp_path)
        elif ext == '.odt':
            markdown_text = extract_odt(temp_path)
        elif ext == '.doc':
            markdown_text = extract_markitdown(temp_path)
        else:
            return jsonify({"error": "Unhandled file extension during processing."}), 500

        # 4. Return the successfully extracted Markdown
        return jsonify({"markdown": markdown_text}), 200

    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {str(e)}")
        return jsonify({"error": f"Internal server error during conversion: {str(e)}"}), 500

    finally:
        # 5. Guaranteed cleanup of the temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.error(f"Failed to delete temporary file {temp_path}: {str(e)}")

if __name__ == '__main__':
    # Bind to 0.0.0.0 and dynamically assign port for Render deployment
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
