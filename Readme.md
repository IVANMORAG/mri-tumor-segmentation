# Brain Tumor Detection System 🧠🔍

![Flask](https://img.shields.io/badge/Flask-2.3.2-lightgrey?logo=flask)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.12.0-orange?logo=tensorflow)
![OpenCV](https://img.shields.io/badge/OpenCV-4.7.0-blue?logo=opencv)
![License](https://img.shields.io/badge/License-MIT-green)

A **Flask-based web application** for detecting and segmenting brain tumors in MRI scans using deep learning models.

## 📌 Table of Contents
- [Brain Tumor Detection System 🧠🔍](#brain-tumor-detection-system-)
  - [📌 Table of Contents](#-table-of-contents)
  - [✨ Features](#-features)
  - [⚙️ Installation](#️-installation)
    - [Prerequisites](#prerequisites)
    - [Steps](#steps)
- [Clone repo](#clone-repo)
- [Create virtual environment](#create-virtual-environment)
- [Install dependencies](#install-dependencies)
- [Run the app](#run-the-app)
  - [📂 Project Structure](#-project-structure)
  - [🔍 How It Works](#-how-it-works)

## ✨ Features
✅ **Tumor Classification**: Detects if an MRI contains a tumor  
✅ **Tumor Segmentation**: Highlights tumor regions with a mask  
✅ **Interactive UI**: Displays original image + segmentation results  
✅ **Analysis History**: Saves and manages previous scans  
✅ **REST API**: Easy integration with other systems  

## ⚙️ Installation

### Prerequisites
- Python 3.8+
- TensorFlow 2.12+
- Flask 2.3.2

### Steps
```bash
# Clone repo
git clone https://github.com/yourusername/Detection-tumor.git
cd Detection-tumor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py

## 📂 Project Structure

Detection-tumor/
├── app.py # Flask entry point
├── requirements.txt # Dependencies
│
├── src/ # Core logic
│ ├── config.py # App settings
│ ├── models/ # ML models
│ │ ├── loader.py # Model loading
│ │ └── custom_metrics.py # Loss functions
│ ├── processing/ # Image processing
│ │ ├── preprocess.py # Image normalization
│ │ ├── postprocess.py # Mask refinement
│ │ └── visualization.py # Overlay generation
│ ├── routes/ # API endpoints
│ │ ├── api.py # Prediction logic
│ │ └── views.py # HTML rendering
│ └── utils/ # Helpers
│ ├── file_handling.py # Upload management
│ └── ngrok.py # Ngrok integration
│
├── static/
│ ├── css/styles.css # Main stylesheet
│ ├── js/
│ │ ├── main.js # Core functions
│ │ ├── upload.js # File handling
│ │ └── history.js # Analysis history
│ └── uploads/ # User uploads storage
│
└── templates/
└── index.html # Main interface
Copy


## 🔍 How It Works

1. **User Flow**:
   ```mermaid
   graph TD
     A[User Uploads MRI] --> B(Preprocess Image)
     B --> C{Classification Model}
     C -->|Tumor Detected| D[Segment Tumor Regions]
     C -->|No Tumor| E[Return Negative Result]
     D --> F[Generate Visualization]
     F --> G[Display Results]

    Backend Process:

        Image resized to 256x256px

        Normalized pixel values (0-1 range)

        Classification confidence threshold: 70%

        Segmentation uses Tversky loss (α=0.7)