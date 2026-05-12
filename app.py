import os
from flask import Flask, render_template, request, redirect, url_for
import pdfplumber

app = Flask(__name__)

# Folder setup
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_pdf():
    if 'file' not in request.files:
        return "No file uploaded"
    
    file = request.files['file']
    if file.filename == '':
        return "No file selected"

    # File save karna
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    extracted_data = []
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    # PDF ki lines ko list mein convert karna
                    extracted_data.extend(text.split('\n'))
    except Exception as e:
        return f"Error processing PDF: {str(e)}"
    finally:
        # File delete kar dena processing ke baad (Safety/Privacy ke liye)
        if os.path.exists(filepath):
            os.remove(filepath)

    return render_template('options.html', lines=extracted_data)

@app.route('/extract', methods=['POST'])
def extract_selected():
    selected_lines = request.form.getlist('selected_data')
    if not selected_lines:
        return "Aapne kuch bhi select nahi kiya!"
    
    return render_template('result.html', data=selected_lines)

if __name__ == '__main__':
    # GitHub Codespaces aur Cloud hosting ke liye zaroori
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
