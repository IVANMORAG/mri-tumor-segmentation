// Manejo del historial
function initHistory() {
    loadHistory();
    
    // Event listeners para el modal
    document.querySelector('.close-modal').addEventListener('click', closeModal);
    document.querySelector('.delete-btn').addEventListener('click', deleteAnalysis);
}

function loadHistory() {
    fetch('/api/history')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('history-container');
            container.innerHTML = '';
            
            if (data.error) {
                container.innerHTML = `<p>Error loading history: ${data.error}</p>`;
                return;
            }
            
            if (data.analyses.length === 0) {
                container.innerHTML = '<p>No analysis history found</p>';
                return;
            }
            
            data.analyses.forEach(analysis => {
                const analysisDiv = document.createElement('div');
                analysisDiv.className = 'image-container history-item';
                analysisDiv.innerHTML = `
                    <img src="/static/uploads/${analysis.original}" alt="Analysis ${analysis.id}" 
                         style="width: 100%; height: 150px; object-fit: cover;">
                    <p style="font-size: 0.8em; color: #7f8c8d;">${analysis.date}</p>
                `;
                analysisDiv.addEventListener('click', () => openAnalysis(analysis.id));
                container.appendChild(analysisDiv);
            });
        })
        .catch(error => {
            console.error('Error loading history:', error);
        });
}

function openAnalysis(analysisId) {
    currentAnalysisId = analysisId;
    const modal = document.getElementById('analysisModal');
    const modalContent = document.getElementById('modal-content');
    
    // Mostrar carga
    modalContent.innerHTML = '<div class="loader"></div><p>Loading analysis...</p>';
    modal.style.display = 'block';
    
    // Cargar contenido del análisis
    fetch(`/static/uploads/${analysisId}/overlay.png`)
        .then(response => {
            const hasOverlay = response.ok;
            
            modalContent.innerHTML = `
                <div class="image-container">
                    <h3>Original MRI</h3>
                    <img src="/static/uploads/${analysisId}/original.jpg" alt="Original MRI" style="max-width: 100%;">
                </div>
                ${hasOverlay ? `
                <div class="image-container">
                    <h3>Segmentation Mask</h3>
                    <div style="background: black; padding: 10px;">
                        <img src="/static/uploads/${analysisId}/mask.png" alt="Segmentation Mask" style="max-width: 100%;">
                    </div>
                </div>
                <div class="image-container">
                    <h3>Tumor Detection</h3>
                    <img src="/static/uploads/${analysisId}/overlay.png" alt="MRI with Tumor Detection" style="max-width: 100%; border: 2px solid red;">
                </div>
                ` : '<p>No tumor detected in this analysis</p>'}
            `;
        })
        .catch(error => {
            modalContent.innerHTML = `<p>Error loading analysis: ${error.message}</p>`;
        });
}

function closeModal() {
    document.getElementById('analysisModal').style.display = 'none';
}

function deleteAnalysis() {
    if (!currentAnalysisId) return;
    
    if (!confirm('Are you sure you want to delete this analysis?')) {
        return;
    }
    
    fetch(`/api/delete/${currentAnalysisId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Analysis deleted successfully');
            closeModal();
            loadHistory();
        } else {
            alert(`Error: ${data.error || 'Unknown error'}`);
        }
    })
    .catch(error => {
        alert(`Error: ${error.message}`);
    });
}