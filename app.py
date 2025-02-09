from flask import Flask, render_template, request, send_file, send_from_directory
import os
import sys
import tempfile
from clustering_engine import group_postcodes, create_map
from werkzeug.utils import secure_filename
import pandas as pd

app = Flask(__name__)

# Configure upload folder using temp directory
if getattr(sys, 'frozen', False):
    # If running as executable
    UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'postcode_clustering', 'uploads')
    STATIC_FOLDER = os.path.join(tempfile.gettempdir(), 'postcode_clustering', 'static')
else:
    # If running as script
    UPLOAD_FOLDER = 'uploads'
    STATIC_FOLDER = 'static'

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                return render_template('upload.html', error='No file selected')
            
            file = request.files['file']
            if file.filename == '':
                return render_template('upload.html', error='No file selected')

            if not allowed_file(file.filename):
                return render_template('upload.html', error='Invalid file type. Please upload a CSV file')

            # Get number of groups from form
            num_groups = int(request.form.get('num_groups', 8))
            
            # Save uploaded file
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Process the file
            grouped_postcodes, invalid_postcodes = group_postcodes(filepath, num_groups)
            
            # Create and save the map
            postcode_map = create_map(grouped_postcodes)
            map_file = os.path.join(STATIC_FOLDER, 'map.html')
            postcode_map.save(map_file)

            # Save Excel file with results
            excel_file = os.path.join(STATIC_FOLDER, 'grouped_postcodes.xlsx')
            with pd.ExcelWriter(excel_file) as writer:
                grouped_postcodes.to_excel(writer, sheet_name='Valid Postcodes', index=False)
                invalid_postcodes.to_excel(writer, sheet_name='Invalid Postcodes', index=False)

            # Clean up uploaded file
            os.remove(filepath)

            return render_template(
                'results.html',
                valid_count=len(grouped_postcodes),
                invalid_count=len(invalid_postcodes),
                static_folder=STATIC_FOLDER
            )

        except Exception as e:
            import traceback
            print(f"Error: {str(e)}")
            print(traceback.format_exc())
            return render_template('upload.html', error=f'Error processing file: {str(e)}')

    return render_template('upload.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files from the temporary directory when running as executable"""
    return send_from_directory(STATIC_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True) 