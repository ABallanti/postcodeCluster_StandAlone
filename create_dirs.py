import os

# Create necessary directories (run before exeucting the flask app)
os.makedirs('static', exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('uploads', exist_ok=True) 

# After running the code above run the below script to create the exe file

# Then run PyInstaller with this modified command:
# pyinstaller --name="Postcode_Clustering" --add-data "templates;templates" --add-data "static;static" --hidden-import="sklearn.metrics" --hidden-import="sklearn.neighbors._partition_nodes" --onefile --noconsole run_app.pyw

