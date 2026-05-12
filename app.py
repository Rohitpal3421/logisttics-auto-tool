from flask import Flask, render_template, request, redirect, url_for
import pdfplumber
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Upload folder banana agar nahi hai toh
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

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

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    extracted_data = []
    
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            # Har page ka text nikalna
            text = page.extract_text()
            if text:
                # Text ko lines mein todna taaki user select kar sake
                extracted_data.extend(text.split('\n'))

    return render_template('options.html', lines=extracted_data)

@app.route('/extract', methods=['POST'])
def extract_selected():
    selected_lines = request.form.getlist('selected_data')
    # Yahan aap data ko excel ya text file mein save kar sakte hain
    return f"<h3>Aapne ye data select kiya hai:</h3><br>" + "<br>".join(selected_lines)

if __name__ == '__main__':
    app.run(debug=True)
