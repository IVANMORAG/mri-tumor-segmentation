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
```

