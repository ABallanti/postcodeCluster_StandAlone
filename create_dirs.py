import os

# Create necessary directories (run before executing the flask app)
os.makedirs('static', exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('uploads', exist_ok=True)

# Updated PyInstaller command with data files included
"""
pyinstaller --name="Postcode_Clustering" ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --add-data "data;data" ^
    --hidden-import="sklearn.metrics" ^
    --hidden-import="sklearn.neighbors._partition_nodes" ^
    --exclude-pattern "*.xlsx" ^
    --onefile ^
    --noconsole ^
    run_app.pyw
"""
#
# pyinstaller --name="Postcode_Clustering" --add-data "templates;templates" --add-data "static;static" --add-data "data;data" --hidden-import="sklearn.metrics" --hidden-import="sklearn.neighbors._partition_nodes" --onefile --noconsole run_app.pyw
