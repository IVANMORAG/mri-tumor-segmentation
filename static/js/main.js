// Variables globales
let currentAnalysisId = null;

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    // Inicializar módulos
    initUpload();
    initHistory();
});

// Función para mostrar error
function showError(message) {
    alert(message);
}

// Función para resetear resultados
function resetResults() {
    const originalImg = document.getElementById('originalImg');
    const maskImg = document.getElementById('maskImg');
    const overlayImg = document.getElementById('overlayImg');
    const maskContainer = document.getElementById('maskContainer');
    const overlayContainer = document.getElementById('overlayContainer');
    const diagnosisDiv = document.getElementById('diagnosis');
    const results = document.getElementById('results');
    
    originalImg.src = '';
    maskImg.src = '';
    overlayImg.src = '';
    maskContainer.style.display = 'none';
    overlayContainer.style.display = 'none';
    diagnosisDiv.className = '';
    diagnosisDiv.innerHTML = '';
    results.style.display = 'none';
}