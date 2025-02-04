from flask import Flask, render_template, request, send_file
import os
from clustering_engine import group_postcodes, create_map
from werkzeug.utils import secure_filename
import pandas as pd

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'file' not in request.files:
            return render_template('upload.html', error='No file selected')
        
        file = request.files['file']
        if file.filename == '':
            return render_template('upload.html', error='No file selected')

        if not allowed_file(file.filename):
            return render_template('upload.html', error='Invalid file type. Please upload a CSV file')

        try:
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
            map_file = os.path.join('static', 'map.html')
            os.makedirs('static', exist_ok=True)
            postcode_map.save(map_file)

            # Save Excel file with results
            excel_file = os.path.join('static', 'grouped_postcodes.xlsx')
            with pd.ExcelWriter(excel_file) as writer:
                grouped_postcodes.to_excel(writer, sheet_name='Valid Postcodes', index=False)
                invalid_postcodes.to_excel(writer, sheet_name='Invalid Postcodes', index=False)

            # Clean up uploaded file
            os.remove(filepath)

            return render_template(
                'results.html',
                valid_count=len(grouped_postcodes),
                invalid_count=len(invalid_postcodes)
            )

        except Exception as e:
            return render_template('upload.html', error=f'Error processing file: {str(e)}')

    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True) 