import os
import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify, url_for
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
import ee  # type: ignore
ee.Initialize(project='LANDROVER')



# Initialize Flask application
app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['RESULT_FOLDER'] = 'static/results'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'tif', 'tiff'}

# Create necessary directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)


def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension.
    
    Args:
        filename (str): Name of the uploaded file
        
    Returns:
        bool: True if file extension is allowed, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def fetch_satellite(lat, lng):
    try:
        point = ee.Geometry.Point([float(lng), float(lat)])

        image = (
            ee.ImageCollection('COPERNICUS/S2')
            .filterBounds(point)
            .filterDate('2023-01-01', '2023-12-31')
            .sort('CLOUDY_PIXEL_PERCENTAGE')
            .first()
        )

        url = image.getThumbURL({
            'region': point.buffer(5000).bounds(),
            'dimensions': 512,
            'format': 'png'
        })

        return url
    except Exception as e:
        raise ValueError(f"Failed to fetch satellite image: {str(e)}")

def process_images(old_image_path, new_image_path):
    """
    Process two satellite images to detect land-use changes.
    
    Args:
        old_image_path (str): Path to the older satellite image
        new_image_path (str): Path to the newer satellite image
        
    Returns:
        tuple: (result_image_path, change_percentage, change_level, error_message)
    """
    try:
        # Read both images
        old_img = cv2.imread(old_image_path)
        new_img = cv2.imread(new_image_path)
        
        # Validate that images were read successfully
        if old_img is None:
            return None, 0, "Error", "Failed to read old image. Please check the file format."
        if new_img is None:
            return None, 0, "Error", "Failed to read new image. Please check the file format."
        
        # Get dimensions of both images
        old_h, old_w = old_img.shape[:2]
        new_h, new_w = new_img.shape[:2]
        
        # Resize images to the same dimensions (use the smaller dimensions)
        target_width = min(old_w, new_w)
        target_height = min(old_h, new_h)
        
        # Resize to match dimensions if needed
        if old_img.shape[:2] != (target_height, target_width):
            old_img = cv2.resize(old_img, (target_width, target_height), 
                                interpolation=cv2.INTER_AREA)
        if new_img.shape[:2] != (target_height, target_width):
            new_img = cv2.resize(new_img, (target_width, target_height), 
                                interpolation=cv2.INTER_AREA)
        
        # Convert images to grayscale for processing
        old_gray = cv2.cvtColor(old_img, cv2.COLOR_BGR2GRAY)
        new_gray = cv2.cvtColor(new_img, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise and improve change detection
        old_blur = cv2.GaussianBlur(old_gray, (5, 5), 0)
        new_blur = cv2.GaussianBlur(new_gray, (5, 5), 0)
        
        # Calculate absolute difference between the two images
        diff = cv2.absdiff(old_blur, new_blur)
        
        # Apply thresholding to highlight significant changes
        # Pixels with difference > 30 are considered changed
        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
        
        # Apply morphological operations to remove small noise
        kernel = np.ones((5, 5), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        # Calculate percentage of changed pixels
        total_pixels = thresh.shape[0] * thresh.shape[1]
        changed_pixels = np.count_nonzero(thresh)
        change_percentage = (changed_pixels / total_pixels) * 100
        
        # Determine change level based on percentage
        if change_percentage < 5:
            change_level = "Low Change"
            color = (0, 255, 0)  # Green
        elif change_percentage < 15:
            change_level = "Moderate Change"
            color = (0, 165, 255)  # Orange
        else:
            change_level = "High Change"
            color = (0, 0, 255)  # Red
        
        # Create a colored visualization of changes
        # Start with the new image as base
        result_img = new_img.copy()
        
        # Create a colored mask for changed regions
        change_mask = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
        
        # Highlight changed regions in red on the result image
        result_img[thresh > 0] = [0, 0, 255]  # Red color for changed areas
        
        # Blend the result with original for better visualization
        result_img = cv2.addWeighted(new_img, 0.6, result_img, 0.4, 0)
        
        # Add contours around changed regions for better visibility
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, 
                                      cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(result_img, contours, -1, color, 2)
        
        # Generate unique filename for result image
        result_filename = f"change_detection_{uuid.uuid4().hex[:8]}.png"
        result_path = os.path.join(app.config['RESULT_FOLDER'], result_filename)
        
        # Save the result image
        cv2.imwrite(result_path, result_img)
        
        # Return relative path for web display
        result_url = url_for('static', filename=f'results/{result_filename}')
        
        return result_url, round(change_percentage, 2), change_level, None
        
    except Exception as e:
        return None, 0, "Error", f"Error processing images: {str(e)}"


@app.route('/')
def index():
    """
    Render the home page with the upload form.
    
    Returns:
        HTML template for the main page
    """
    return render_template('index.html')


@app.route('/fetch-satellite', methods=['POST'])
def fetch_satellite_endpoint():
    """
    Fetch satellite image for given coordinates.
    
    Returns:
        JSON response with satellite image URL or error message
    """
    lat = request.form.get('lat')
    lng = request.form.get('lng')
    
    if lat and lng:
        try:
            satellite_url = fetch_satellite(lat, lng)
            return jsonify({
                'success': True,
                'satellite_url': satellite_url
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
    else:
        return jsonify({
            'success': False,
            'error': 'Latitude and longitude are required.'
        }), 400


@app.route('/detect-change', methods=['POST'])
def detect_change():
    """
    Handle image upload and change detection request.
    
    Returns:
        JSON response with detection results or error message
    """
    # Validate that both files are present in the request
    if 'old_image' not in request.files or 'new_image' not in request.files:
        return jsonify({
            'success': False,
            'error': 'Both old and new images are required.'
        }), 400
    
    old_file = request.files['old_image']
    new_file = request.files['new_image']
    
    # Check if files were actually selected
    if old_file.filename == '' or new_file.filename == '':
        return jsonify({
            'success': False,
            'error': 'Please select both images before submitting.'
        }), 400
    
    # Validate file extensions
    if not allowed_file(old_file.filename):
        return jsonify({
            'success': False,
            'error': f'Old image has invalid format. Allowed formats: {", ".join(app.config["ALLOWED_EXTENSIONS"])}'
        }), 400
    
    if not allowed_file(new_file.filename):
        return jsonify({
            'success': False,
            'error': f'New image has invalid format. Allowed formats: {", ".join(app.config["ALLOWED_EXTENSIONS"])}'
        }), 400
    
    try:
        # Generate unique filenames to avoid conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        old_filename = f"old_{timestamp}_{secure_filename(old_file.filename)}"
        new_filename = f"new_{timestamp}_{secure_filename(new_file.filename)}"
        
        # Save uploaded files
        old_path = os.path.join(app.config['UPLOAD_FOLDER'], old_filename)
        new_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        
        old_file.save(old_path)
        new_file.save(new_path)
        
        # Process the images to detect changes
        result_path, change_percentage, change_level, error = process_images(
            old_path, new_path
        )
        
        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 400
        
        # Prepare URLs for displaying images
        old_url = url_for('static', filename=f'uploads/{old_filename}')
        new_url = url_for('static', filename=f'uploads/{new_filename}')
        
        return jsonify({
            'success': True,
            'old_image_url': old_url,
            'new_image_url': new_url,
            'result_image_url': result_path,
            'change_percentage': change_percentage,
            'change_level': change_level
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'An unexpected error occurred: {str(e)}'
        }), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    """
    Handle file size exceeded error.
    
    Returns:
        JSON error response
    """
    return jsonify({
        'success': False,
        'error': 'File size exceeds the maximum limit of 16MB.'
    }), 413


if __name__ == '__main__':
    # Run the Flask application
    # Debug mode is enabled for development (disable in production)
    app.run(debug=True, port=5001)