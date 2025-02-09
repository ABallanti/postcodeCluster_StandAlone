import os

# Create necessary directories (run before exeucting the flask app)
os.makedirs('static', exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('uploads', exist_ok=True) 

# If you want to recreate the distribution again copy/pase on teh terminal the following line
# pyinstaller --name="Postcode_Clustering" --add-data "templates;templates" --add-data "static;static" --hidden-import="sklearn.metrics" --hidden-import="sklearn.neighbors._partition_nodes" --onefile --noconsole run_app.pyw

