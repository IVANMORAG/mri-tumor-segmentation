// Manejo de subida de archivos
function initUpload() {
    const fileInput = document.getElementById('fileInput');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const fileName = document.getElementById('fileName');
    
    fileInput.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            fileName.textContent = this.files[0].name;
            analyzeBtn.disabled = false;
        } else {
            fileName.textContent = '';
            analyzeBtn.disabled = true;
        }
    });
    
    analyzeBtn.addEventListener('click', uploadImage);
}

// Función para subir imagen
function uploadImage() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    const loading = document.getElementById('loading');
    
    if (!file) {
        showError('Please select an image first');
        return;
    }
    
    if (!['image/png', 'image/jpeg', 'image/jpg'].includes(file.type)) {
        showError('Only PNG, JPEG or JPG images are allowed');
        return;
    }
    
    resetResults();
    loading.style.display = 'block';
    
    const formData = new FormData();
    formData.append('file', file);
    
    // Cambiado a /api/predict para coincidir con el backend
    fetch('/api/predict', {
        method: 'POST',
        body: formData
    })
    .then(handleResponse)
    .then(displayResults)
    .catch(handleError)
    .finally(() => {
        loading.style.display = 'none';
    });
}

function handleResponse(response) {
    if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
    }
    return response.json();
}

function displayResults(data) {
    const diagnosisDiv = document.getElementById('diagnosis');
    const originalImg = document.getElementById('originalImg');
    const maskImg = document.getElementById('maskImg');
    const overlayImg = document.getElementById('overlayImg');
    const maskContainer = document.getElementById('maskContainer');
    const overlayContainer = document.getElementById('overlayContainer');
    const results = document.getElementById('results');
    
    if (data.error) {
        throw new Error(data.error);
    }
    
    // Mostrar diagnóstico
    const hasTumor = data.has_tumor === 'true';
    diagnosisDiv.className = hasTumor ? 'diagnosis tumor' : 'diagnosis no-tumor';
    diagnosisDiv.innerHTML = hasTumor 
        ? `✅ <strong>Tumor detected</strong> (confidence: <span class="accuracy">${(data.accuracy * 100).toFixed(2)}%</span>)`
        : `✅ <strong>No tumor detected</strong> (confidence: <span class="accuracy">${(data.accuracy * 100).toFixed(2)}%</span>)`;
    
    // Mostrar imágenes
    originalImg.src = `/static/uploads/${data.images.original}?t=${Date.now()}`;
    
    // Mostrar máscara y overlay si hay tumor
    if (hasTumor) {
        if (data.images.mask) {
            maskImg.src = `/static/uploads/${data.images.mask}?t=${Date.now()}`;
            maskContainer.style.display = 'block';
        }
        if (data.images.overlay) {
            overlayImg.src = `/static/uploads/${data.images.overlay}?t=${Date.now()}`;
            overlayContainer.style.display = 'block';
        }
    } else {
        maskContainer.style.display = 'none';
        overlayContainer.style.display = 'none';
    }
    
    results.style.display = 'block';
    setTimeout(() => {
        results.scrollIntoView({ behavior: 'smooth' });
    }, 100);
    
    // Recargar historial después de un nuevo análisis
    loadHistory();
}

function handleError(error) {
    console.error('Error:', error);
    const diagnosisDiv = document.getElementById('diagnosis');
    diagnosisDiv.className = 'diagnosis error';
    diagnosisDiv.innerHTML = `❌ <strong>Error:</strong> ${error.message}`;
    document.getElementById('results').style.display = 'block';
}