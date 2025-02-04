import webbrowser
import threading
import time
from app import app

def open_browser():
    # Wait a bit for the server to start
    time.sleep(1.5)
    webbrowser.open('http://127.0.0.1:5000/')

if __name__ == '__main__':
    # Start the browser in a new thread
    threading.Thread(target=open_browser).start()
    
    # Run the Flask app
    app.run(port=5000) 