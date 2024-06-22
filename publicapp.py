import os
import cv2
import time
import logging
from flask import Flask, render_template, Response
from flask_cors import CORS

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Get the absolute path of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Specify the path to the templates folder
template_dir = os.path.join(script_dir, 'templates')

app = Flask(__name__, template_folder=template_dir)
CORS(app)  # Enable CORS for all routes

# IP camera URL
camera_url = "rtsp://admin:Admin123@10.100.82.156:554/"

def gen_frames():
    try:
        camera = cv2.VideoCapture(camera_url, cv2.CAP_FFMPEG)
        if not camera.isOpened():
            app.logger.error("Failed to connect to the camera.")
            return

        while True:
            # Discard all but the latest frame
            for _ in range(1):  # Adjust the range to control the frame rate
                camera.grab()
            ret, frame = camera.read()
            if not ret:
                app.logger.error("Failed to read frame from camera.")
                break

            # Resize the frame to a smaller size
            frame = cv2.resize(frame, (640, 480))  # Adjust the size as needed

            # Convert the frame to JPEG format
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])  # Adjust the quality value (0-100)
            if not ret:
                app.logger.error("Failed to encode frame.")
                break

            frame = buffer.tobytes()

            # Yield the frame as an HTTP response
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

            # Introduce a delay to limit the frame rate
            time.sleep(0.05)  # Adjust the delay as needed

    except Exception as e:
        app.logger.error(f"Error in gen_frames: {str(e)}")

@app.route('/video_feed')
def video_feed():
    try:
        return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    except Exception as e:
        app.logger.error(f"Error in video_feed: {str(e)}")
        return "Error occurred", 500

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        app.logger.error(f"Error rendering template: {str(e)}")
        return f"Error rendering template: {str(e)}", 500

if __name__ == '__main__':
    # Print debug information
    print("Current working directory:", os.getcwd())
    print("Template directory:", template_dir)
    try:
        print("Contents of templates folder:", os.listdir(template_dir))
    except Exception as e:
        print(f"Error listing templates folder: {str(e)}")

    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)