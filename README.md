🌍 Cloud-Native Land-Use Change Detection System
A production-ready Flask web application that detects and visualizes land-use changes between two satellite images using advanced computer vision techniques with OpenCV.

📋 Features
Image Upload Interface: User-friendly form to upload before/after satellite images
Automated Change Detection: Advanced image processing pipeline using OpenCV
Visual Results: Color-coded visualization of detected changes
Change Metrics: Quantitative analysis with percentage and severity levels
Error Handling: Comprehensive validation and user-friendly error messages
Responsive Design: Works seamlessly on desktop and mobile devices
Production Ready: Includes deployment configurations for cloud platforms
🛠️ Technology Stack
Backend: Flask (Python 3.8+)
Image Processing: OpenCV, NumPy
Frontend: HTML5, CSS3, JavaScript (ES6)
Server: Gunicorn (for production)
📁 Project Structure
land-use-detection/
├── app.py                  # Flask application with routes and processing logic
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── static/
│   ├── uploads/           # Uploaded images storage
│   ├── results/           # Processed results storage
│   └── style.css          # Frontend styling
└── templates/
    └── index.html         # Main web interface
🚀 Local Installation & Setup
Prerequisites
Python 3.8 or higher
pip (Python package manager)
Virtual environment (recommended)
Step-by-Step Installation
Clone or Download the Project
bash
   mkdir land-use-detection
   cd land-use-detection
   # Copy all project files to this directory
Create Virtual Environment
bash
   python -m venv venv
Activate Virtual Environment On Windows:
bash
   venv\Scripts\activate
On macOS/Linux:

bash
   source venv/bin/activate
Install Dependencies
bash
   pip install -r requirements.txt
Create Required Directories
bash
   mkdir -p static/uploads static/results
Run the Application
bash
   python app.py
Access the Application Open your browser and navigate to:
   http://localhost:5000
📖 Usage Guide
Upload Images
Click on "Old Image (Before)" to upload the earlier satellite image
Click on "New Image (After)" to upload the recent satellite image
Supported formats: PNG, JPG, JPEG, TIF, TIFF (max 16MB each)
Process Images
Click the "🔍 Detect Changes" button
Wait for the processing to complete (usually 2-5 seconds)
View Results
See the change percentage and severity level
Compare the original images side-by-side
View the change detection visualization with highlighted regions
Red areas indicate detected changes
Green contours = Low change
Orange contours = Moderate change
Red contours = High change
Analyze New Images
Click "🔄 Analyze New Images" to start over
🔬 Image Processing Pipeline
The application uses a sophisticated multi-step process:

Image Loading: Reads both satellite images
Normalization: Resizes images to matching dimensions
Grayscale Conversion: Converts to single-channel for processing
Noise Reduction: Applies Gaussian blur (5x5 kernel)
Difference Calculation: Computes absolute pixel differences
Thresholding: Identifies significant changes (threshold: 30)
Morphological Operations: Removes noise using open/close operations
Change Quantification: Calculates percentage of changed pixels
Visualization: Generates color-coded result image with contours
Change Classification
Low Change (0-5%): Minimal land-use changes detected
Moderate Change (5-15%): Notable changes in land use
High Change (>15%): Significant land transformation
☁️ Cloud Deployment
AWS EC2 Deployment
Launch EC2 Instance
Choose Ubuntu Server 22.04 LTS
Instance type: t2.medium or higher (recommended)
Configure security group to allow HTTP (80) and SSH (22)
Connect to Instance
bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
Install System Dependencies
bash
   sudo apt update
   sudo apt install python3-pip python3-venv -y
   sudo apt install libgl1-mesa-glx libglib2.0-0 -y
Setup Application
bash
   cd /home/ubuntu
   git clone your-repo-url land-use-detection
   cd land-use-detection
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   mkdir -p static/uploads static/results
Configure Gunicorn Create gunicorn_config.py:
python
   bind = "0.0.0.0:8000"
   workers = 4
   threads = 2
   timeout = 120
   accesslog = "/var/log/gunicorn/access.log"
   errorlog = "/var/log/gunicorn/error.log"
Create Systemd Service Create /etc/systemd/system/landuse.service:
ini
   [Unit]
   Description=Land-Use Change Detection System
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/land-use-detection
   Environment="PATH=/home/ubuntu/land-use-detection/venv/bin"
   ExecStart=/home/ubuntu/land-use-detection/venv/bin/gunicorn -c gunicorn_config.py app:app

   [Install]
   WantedBy=multi-user.target
Start Service
bash
   sudo systemctl daemon-reload
   sudo systemctl start landuse
   sudo systemctl enable landuse
Configure Nginx (Optional) Install Nginx:
bash
   sudo apt install nginx -y
Create /etc/nginx/sites-available/landuse:

nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }

       client_max_body_size 20M;
   }
Enable site:

bash
   sudo ln -s /etc/nginx/sites-available/landuse /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
Alternative: Docker Deployment
Create Dockerfile:

dockerfile
FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p static/uploads static/results

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "4", "app:app"]
Build and run:

bash
docker build -t land-use-detection .
docker run -p 5000:5000 land-use-detection
🔒 Security Considerations
File size limits enforced (16MB per image)
File type validation (only image formats allowed)
Secure filename handling with Werkzeug
Input sanitization for all user inputs
No execution of user-provided code
🐛 Troubleshooting
Issue: OpenCV Import Error
bash
pip install opencv-python-headless
Issue: Permission Denied on Directories
bash
chmod -R 755 static/
Issue: Port Already in Use
Change the port in app.py:

python
app.run(debug=True, host='0.0.0.0', port=5001)
Issue: Large Image Processing Takes Too Long
Reduce image size before upload or adjust timeout:

python
app.config['TIMEOUT'] = 300  # 5 minutes
📊 Performance Optimization
Images are automatically resized to optimize processing
Morphological operations reduce noise efficiently
Gunicorn workers handle concurrent requests
Static files cached by browser
🧪 Testing
Test with sample satellite images:

Google Earth Historical Imagery
Sentinel-2 satellite data
Landsat imagery
Any before/after comparison images
📝 License
This project is provided as-is for educational and commercial use.

🤝 Contributing
Suggestions for improvements:

Machine learning-based change detection
Support for multi-band satellite imagery
Batch processing capabilities
Export results as PDF reports
Integration with GIS systems
📧 Support
For issues or questions, please refer to the error messages displayed in the application or check the logs.

Built with ❤️ using Flask and OpenCV

