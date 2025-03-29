// Elementos del DOM
const fileInput = document.getElementById('fileInput');
const analyzeBtn = document.getElementById('analyzeBtn');
const fileName = document.getElementById('fileName');
const loading = document.getElementById('loading');
const results = document.getElementById('results');
const diagnosisDiv = document.getElementById('diagnosis');
const originalImg = document.getElementById('originalImg');
const maskImg = document.getElementById('maskImg');
const overlayImg = document.getElementById('overlayImg');
const maskContainer = document.getElementById('maskContainer');
const overlayContainer = document.getElementById('overlayContainer');
const historyContainer = document.getElementById('history-container');
const modal = document.getElementById('analysisModal');
const modalContent = document.getElementById('modal-content');
const closeModalBtn = document.querySelector('.close-modal');
const deleteAnalysisBtn = document.getElementById('deleteAnalysisBtn');

// Variables de estado
let currentAnalysisId = null;

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    // Configurar eventos
    fileInput.addEventListener('change', handleFileSelect);
    analyzeBtn.addEventListener('click', uploadImage);
    closeModalBtn.addEventListener('click', closeModal);
    deleteAnalysisBtn.addEventListener('click', deleteAnalysis);
    
    // Cargar historial
    loadHistory();
    
    // Ocultar contenedores inicialmente
    maskContainer.style.display = 'none';
    overlayContainer.style.display = 'none';
    results.style.display = 'none';
});

// Manejar selección de archivo
function handleFileSelect() {
    if (this.files && this.files[0]) {
        fileName.textContent = this.files[0].name;
        analyzeBtn.disabled = false;
    } else {
        fileName.textContent = '';
        analyzeBtn.disabled = true;
    }
}

// Función para subir y analizar imagen
async function uploadImage() {
    const file = fileInput.files[0];
    
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
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/predict', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        displayResults(data);
        loadHistory(); // Actualizar el historial después de nuevo análisis
    } catch (error) {
        showError(error.message);
    } finally {
        loading.style.display = 'none';
    }
}

// Mostrar resultados del análisis
function displayResults(data) {
    const hasTumor = data.has_tumor === 'true';
    
    // Mostrar diagnóstico
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
}

// Cargar historial de análisis
async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        
        historyContainer.innerHTML = '';
        
        if (data.error) {
            historyContainer.innerHTML = `<p class="error">Error loading history: ${data.error}</p>`;
            return;
        }
        
        if (data.analyses.length === 0) {
            historyContainer.innerHTML = '<p>No analysis history found</p>';
            return;
        }
        
        data.analyses.forEach(analysis => {
            const analysisDiv = document.createElement('div');
            analysisDiv.className = 'image-container history-item';
            analysisDiv.innerHTML = `
                <img src="/static/uploads/${analysis.original}" alt="Analysis ${analysis.id}" 
                     style="width: 100%; height: 150px; object-fit: cover;">
                <p class="image-caption">${analysis.date}</p>
            `;
            analysisDiv.addEventListener('click', () => openAnalysis(analysis.id));
            historyContainer.appendChild(analysisDiv);
        });
    } catch (error) {
        console.error('Error loading history:', error);
        historyContainer.innerHTML = `<p class="error">Error loading history</p>`;
    }
}

// Abrir análisis en modal
async function openAnalysis(analysisId) {
    currentAnalysisId = analysisId;
    modal.style.display = 'block';
    modalContent.innerHTML = '<div class="loader"></div><p>Loading analysis...</p>';
    
    try {
        // Verificar si existe overlay (para saber si hubo tumor)
        const overlayResponse = await fetch(`/static/uploads/${analysisId}/overlay.png`);
        const hasOverlay = overlayResponse.ok;
        
        modalContent.innerHTML = `
            <div class="image-container">
                <h3>Original MRI</h3>
                <img src="/static/uploads/${analysisId}/original.jpg" alt="Original MRI">
            </div>
            ${hasOverlay ? `
            <div class="image-container">
                <h3>Segmentation Mask</h3>
                <div class="mask-display">
                    <img src="/static/uploads/${analysisId}/mask.png" alt="Segmentation Mask">
                </div>
            </div>
            <div class="image-container">
                <h3>Tumor Detection</h3>
                <img src="/static/uploads/${analysisId}/overlay.png" alt="MRI with Tumor Detection">
            </div>
            ` : '<p>No tumor detected in this analysis</p>'}
        `;
    } catch (error) {
        modalContent.innerHTML = `<p class="error">Error loading analysis: ${error.message}</p>`;
    }
}

// Cerrar modal
function closeModal() {
    modal.style.display = 'none';
    currentAnalysisId = null;
}

// Eliminar análisis
async function deleteAnalysis() {
    if (!currentAnalysisId) return;
    
    if (!confirm('Are you sure you want to delete this analysis?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/delete/${currentAnalysisId}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        
        if (data.success) {
            alert('Analysis deleted successfully');
            closeModal();
            loadHistory();
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// Mostrar error
function showError(message) {
    diagnosisDiv.className = 'diagnosis error';
    diagnosisDiv.innerHTML = `❌ <strong>Error:</strong> ${message}`;
    results.style.display = 'block';
}

// Resetear resultados
function resetResults() {
    originalImg.src = '';
    maskImg.src = '';
    overlayImg.src = '';
    maskContainer.style.display = 'none';
    overlayContainer.style.display = 'none';
    diagnosisDiv.className = '';
    diagnosisDiv.innerHTML = '';
    results.style.display = 'none';
}