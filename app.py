from flask import Flask, render_template, Response, jsonify, request, abort
import cv2
import numpy as np
import os
import time
import threading
import logging
import uuid
from queue import Queue
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
from PIL import Image
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(), 
                              logging.FileHandler("app.log")])
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB upload limit

# Configuration paths
MODEL_PATH = 'model/trash_classification_model.h5'
CLASS_NAMES_PATH = 'model/class_names.txt'
UPLOAD_FOLDER = 'app/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure uploads directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def load_class_names():
    if os.path.exists(CLASS_NAMES_PATH):
        with open(CLASS_NAMES_PATH, 'r') as f:
            return [line.strip() for line in f.readlines()]
    else:
        logger.warning(f"File {CLASS_NAMES_PATH} not found. Using default class list.")
        return ['battery', 'biological', 'brown-glass', 'cardboard', 'green-glass', 
                'metal', 'paper', 'plastic', 'trash', 'white-glass']

# Load class names
TRASH_CATEGORIES = load_class_names()
logger.info(f"Loaded {len(TRASH_CATEGORIES)} trash classification categories")

# Global variables
latest_prediction = {'class_name': 'Unknown', 'confidence': 0.0}
camera = None
is_camera_active = False
current_frame = None
frame_queue = Queue(maxsize=1)  # Only keep the latest frame
prediction_ready = threading.Event()
classification_running = False

# Camera settings
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CLASSIFICATION_INTERVAL = 5

# Load the model once at startup
model = None
try:
    if os.path.exists(MODEL_PATH):
        model = load_model(MODEL_PATH)
        logger.info("Model loaded successfully")
    else:
        logger.warning(f"Model file {MODEL_PATH} not found")
except Exception as e:
    logger.error(f"Error loading model: {e}")

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_camera():
    """Initialize and configure camera"""
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)  # Default camera
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        camera.set(cv2.CAP_PROP_BUFFERSIZE, 2)
        if not camera.isOpened():
            logger.error("Could not open camera")
    return camera

def release_camera():
    """Release camera resources"""
    global camera
    if camera is not None:
        camera.release()
        camera = None
        logger.info("Camera resources released")

def translate_class_name(class_name):
    """Convert class name to standardized English"""
    translations = {
        "battery": "Battery",
        "biological": "Biological Waste",
        "cardboard": "Cardboard",
        "paper": "Paper",
        "plastic": "Plastic",
        "metal": "Metal",
        "brown-glass": "Brown Glass",
        "green-glass": "Green Glass",
        "white-glass": "White Glass",
        "trash": "Other Trash",
        "unknown": "Unknown",
        "error": "Error"
    }
    
    lower_class = class_name.lower()
    return translations.get(lower_class, "Unknown")

def preprocess_image(image, target_size=(224, 224)):
    """Preprocess image for model input"""
    try:
        if image is None:
            logger.error("Input image is empty")
            return None
            
        if len(image.shape) == 3 and image.shape[2] == 4:
            # Convert RGBA to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        
        # Resize image
        image_resized = cv2.resize(image, target_size)
        
        # Convert to model input format
        image_array = img_to_array(image_resized)
        image_array = np.expand_dims(image_array, axis=0)
        # Normalize similar to training
        image_preprocessed = image_array / 127.5 - 1
        
        return image_preprocessed
    except Exception as e:
        logger.error(f"Error preprocessing image: {e}")
        return None

def classify_image_thread():
    """Dedicated thread for image classification from camera stream"""
    global latest_prediction, classification_running
    
    classification_running = True
    logger.info("Classification thread started")
    
    while classification_running:
        try:
            if frame_queue.empty():
                time.sleep(0.01)
                continue
                
            # Get the latest frame from queue
            image = frame_queue.get()
            
            # Classify image
            if model is not None:
                processed_image = preprocess_image(image)
                if processed_image is None:
                    continue
                    
                predictions = model.predict(processed_image, verbose=0)[0]
                class_index = np.argmax(predictions)
                confidence = float(predictions[class_index])
                class_name = TRASH_CATEGORIES[class_index]
            else:
                # Simulate results when model is unavailable (for demo purposes)
                import random
                class_index = random.randint(0, len(TRASH_CATEGORIES) - 1)
                class_name = TRASH_CATEGORIES[class_index]
                confidence = random.uniform(0.7, 0.99)
            
            latest_prediction = {
                'class_name': class_name,
                'confidence': round(confidence * 100, 2)
            }
            
            # Signal new prediction is ready
            prediction_ready.set()
            
        except Exception as e:
            logger.error(f"Error in classification thread: {e}")
            latest_prediction = {
                'class_name': 'Error',
                'confidence': 0.0
            }
        
        # Wait briefly before processing the next frame
        time.sleep(0.05)
    
    logger.info("Classification thread stopped")

def classify_image(image):
    """Classify uploaded image (synchronous)"""
    try:
        if model is not None:
            processed_image = preprocess_image(image)
            if processed_image is None:
                return {'class_name': 'Error', 'confidence': 0.0}
                
            predictions = model.predict(processed_image, verbose=0)[0]
            class_index = np.argmax(predictions)
            confidence = float(predictions[class_index])
            class_name = TRASH_CATEGORIES[class_index]
        else:
            # Simulate results when model is unavailable
            import random
            class_index = random.randint(0, len(TRASH_CATEGORIES) - 1)
            class_name = TRASH_CATEGORIES[class_index]
            confidence = random.uniform(0.7, 0.99)
        
        return {
            'class_name': class_name,
            'confidence': round(confidence * 100, 2)
        }
        
    except Exception as e:
        logger.error(f"Error classifying image: {e}")
        return {
            'class_name': 'Error',
            'confidence': 0.0
        }

def generate_frames():
    """Generator for video streaming"""
    global is_camera_active, current_frame
    is_camera_active = True
    
    cam = get_camera()
    
    if not cam or not cam.isOpened():
        yield (b'--frame\r\n'
               b'Content-Type: text/plain\r\n\r\n'
               b'Camera not available\r\n')
        is_camera_active = False
        return
    
    # Start classification thread if not running
    if not classification_running:
        classification_thread = threading.Thread(target=classify_image_thread)
        classification_thread.daemon = True
        classification_thread.start()
    
    frame_count = 0
    
    while is_camera_active:
        try:
            success, frame = cam.read()
            
            if not success:
                logger.error("Couldn't read frame from camera")
                break
            
            # Flip camera horizontally (mirror effect)
            frame = cv2.flip(frame, 1)
            
            # Save current frame for capture function
            current_frame = frame.copy()
            
            # Only send some frames for classification
            frame_count += 1
            if frame_count % CLASSIFICATION_INTERVAL == 0:
                if not frame_queue.full():
                    frame_queue.put(frame.copy())
                else:
                    try:
                        # Remove old frame and add new one
                        frame_queue.get_nowait()
                        frame_queue.put(frame.copy())
                    except:
                        pass
            
            # Convert class name to display format
            display_class = translate_class_name(latest_prediction['class_name'])
            
            # Draw results on frame
            label = f"{display_class}: {latest_prediction['confidence']}%"
            cv2.putText(frame, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
            # Convert frame to JPEG for streaming
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            # Send frame as multipart/x-mixed-replace
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        except Exception as e:
            logger.error(f"Error generating frame: {e}")
            time.sleep(0.1)
    
# Routes
@app.route('/')
def index():
    """Application homepage"""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Endpoint for video streaming from camera"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_prediction')
def get_prediction():
    """API for getting latest classification result"""
    return jsonify(latest_prediction)

@app.route('/stop_camera')
def stop_camera():
    """API for stopping camera"""
    global is_camera_active, classification_running
    is_camera_active = False
    classification_running = False
    release_camera()
    return jsonify({'status': 'Camera stopped'})

@app.route('/upload', methods=['POST'])
def upload_file():
    """API for uploading and classifying images"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file found'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File format not supported'}), 400
        
    try:
        # Create safe filename
        filename = secure_filename(file.filename)
        unique_filename = f"upload_{uuid.uuid4().hex}.jpg"
        upload_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # Read image file
        img = Image.open(file.stream)
        img_array = np.array(img)
        
        # Save uploaded image
        img.save(upload_path)
        
        # Classify image
        result = classify_image(img_array)
        result['image_path'] = f'/static/uploads/{unique_filename}'
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error processing upload file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/capture_image', methods=['POST'])
def capture_image():
    """API for capturing and classifying image from camera stream"""
    global current_frame
    
    if current_frame is None:
        return jsonify({'error': 'No camera frame available'}), 400
    
    try:
        # Create unique filename with timestamp
        unique_filename = f"capture_{int(time.time())}.jpg"
        capture_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # Save captured image
        cv2.imwrite(capture_path, current_frame)
        
        # Classify captured image
        result = classify_image(current_frame)
        
        # Add image path to result for UI display
        result['image_path'] = f'/static/uploads/{unique_filename}'
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error capturing image: {e}")
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({'error': 'Page not found'}), 404

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Ensure directory exists
    os.makedirs('model', exist_ok=True)
    
    logger.info("Starting trash classification application")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)