from flask import Flask, render_template, request, send_file, send_from_directory
import os
import sys
import tempfile
import uuid
from datetime import datetime
from clustering_engine import group_postcodes, create_map
from werkzeug.utils import secure_filename
import pandas as pd
import glob
import logging
import traceback
import subprocess
import platform

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

def clean_old_files():
    """Clean up all files in static and upload folders"""
    for folder in [STATIC_FOLDER, UPLOAD_FOLDER]:
        files = glob.glob(os.path.join(folder, '*'))
        for f in files:
            try:
                os.remove(f)
            except Exception as e:
                print(f"Error deleting {f}: {e}")

# Clean files when app starts
clean_old_files()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Update the logging setup
def setup_logging():
    log_path = 'app.log'
    if getattr(sys, 'frozen', False):
        # If running as executable
        log_path = os.path.join(os.path.dirname(sys.executable), 'app.log')
    
    # Configure logging with more detailed format
    logging.basicConfig(
        filename=log_path,
        level=logging.DEBUG,  # Set to DEBUG to capture all logs
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add console handler to see logs in console too
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logging.getLogger('').addHandler(console_handler)
    
    # Log startup information
    logging.info("=== Application Starting ===")
    logging.info(f"Static folder path: {STATIC_FOLDER}")
    logging.info(f"Upload folder path: {UPLOAD_FOLDER}")
    logging.info(f"Log file location: {log_path}")

# Call setup_logging() at startup
setup_logging()

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'GET':
        # Clean up old files when starting new session
        clean_old_files()
        return render_template('upload.html')

    if request.method == 'POST':
        try:
            logging.info("Starting file processing...")
            if 'file' not in request.files:
                logging.error("No file in request")
                return render_template('upload.html', error='No file selected')
            
            file = request.files['file']
            logging.info(f"Received file: {file.filename}")
            
            if file.filename == '':
                logging.error("Empty filename")
                return render_template('upload.html', error='No file selected')

            if not allowed_file(file.filename):
                logging.error("Invalid file type")
                return render_template('upload.html', error='Invalid file type. Please upload a CSV file')

            # Clean up old files before processing new ones
            clean_old_files()

            # Get number of groups from form
            num_groups = int(request.form.get('num_groups', 4))
            logging.info(f"Number of groups: {num_groups}")
            
            # Generate timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save uploaded file with timestamp
            filename = f"{timestamp}_{secure_filename(file.filename)}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            logging.info(f"Saved file to: {filepath}")

            # Process the file
            logging.info("Processing postcodes...")
            grouped_postcodes, invalid_postcodes = group_postcodes(filepath, num_groups)
            logging.info(f"Processed {len(grouped_postcodes)} valid postcodes and {len(invalid_postcodes)} invalid postcodes")
            
            # Create and save the map
            logging.info("Creating map...")
            postcode_map = create_map(grouped_postcodes)
            map_file = os.path.join(STATIC_FOLDER, 'map.html')
            postcode_map.save(map_file)
            logging.info(f"Saved map to: {map_file}")

            # Save Excel file with results - add logging
            excel_file = os.path.join(STATIC_FOLDER, 'grouped_postcodes.xlsx')
            logging.info(f"Attempting to save Excel file to: {excel_file}")
            with pd.ExcelWriter(excel_file) as writer:
                grouped_postcodes.to_excel(writer, sheet_name='Valid Postcodes', index=False)
                invalid_postcodes.to_excel(writer, sheet_name='Invalid Postcodes', index=False)
            logging.info(f"Successfully saved Excel file to: {excel_file}")

            # Verify file exists after saving
            if os.path.exists(excel_file):
                logging.info("Excel file verified to exist after saving")
            else:
                logging.error("Excel file not found after saving!")

            # Clean up uploaded file
            os.remove(filepath)
            logging.info("Cleaned up uploaded file")

            return render_template(
                'results.html',
                valid_count=len(grouped_postcodes),
                invalid_count=len(invalid_postcodes)
            )

        except Exception as e:
            logging.error(f"Error processing file: {str(e)}")
            logging.error(traceback.format_exc())
            return render_template('upload.html', error=f'Error processing file: {str(e)}')

@app.route('/static/<path:filename>')
def serve_static(filename):
    try:
        logging.info("\n=== Download Request Details ===")
        logging.info(f"Time of request: {datetime.now()}")
        logging.info(f"Requested URL: {request.url}")
        logging.info(f"Looking for file: {filename}")
        logging.info(f"Static folder configured as: {STATIC_FOLDER}")
        
        file_path = os.path.join(STATIC_FOLDER, filename)
        logging.info(f"Full file path being checked: {file_path}")
        
        # Check if the directory exists
        if not os.path.exists(STATIC_FOLDER):
            logging.error(f"Static folder does not exist: {STATIC_FOLDER}")
            return "Static folder not found", 404
            
        # List directory contents
        try:
            files_in_static = os.listdir(STATIC_FOLDER)
            logging.info(f"Files currently in static folder: {files_in_static}")
        except Exception as e:
            logging.error(f"Error listing directory: {str(e)}")
        
        # Check file existence
        if os.path.exists(file_path):
            logging.info(f"File found at: {file_path}")
            logging.info(f"File size: {os.path.getsize(file_path)} bytes")
            try:
                return send_file(
                    file_path,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True,
                    download_name='grouped_postcodes.xlsx'
                )
            except Exception as e:
                logging.error(f"Error sending file: {str(e)}")
                logging.error(traceback.format_exc())
                raise
        else:
            logging.error(f"File not found at: {file_path}")
            return "File not found", 404

    except Exception as e:
        logging.error("=== Error in serve_static ===")
        logging.error(f"Error type: {type(e).__name__}")
        logging.error(f"Error message: {str(e)}")
        logging.error(traceback.format_exc())
        return f"Error: {str(e)}", 500

@app.route('/open_folder')
def open_folder():
    """Opens the static folder in the system's file explorer"""
    try:
        logging.info(f"Attempting to open folder: {STATIC_FOLDER}")
        
        # Handle different operating systems
        if platform.system() == "Windows":
            os.startfile(STATIC_FOLDER)
        elif platform.system() == "Darwin":  # macOS
            subprocess.Popen(["open", STATIC_FOLDER])
        else:  # Linux
            subprocess.Popen(["xdg-open", STATIC_FOLDER])
            
        return "", 204  # Return no content success status
    except Exception as e:
        logging.error(f"Error opening folder: {str(e)}")
        return "Error opening folder", 500

if __name__ == '__main__':
    app.run(debug=True) 