/**
 * Main JavaScript for QR Security Scanner
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initMethodTabs();
    initFileUpload();
    initCameraScanner();
    initExampleLinks();
    
    // Add global error handler
    window.addEventListener('error', handleGlobalError);
});

/**
 * Initialize method tabs on scan page
 */
function initMethodTabs() {
    const tabs = document.querySelectorAll('.method-tab');
    const methods = document.querySelectorAll('.scan-method');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const method = this.getAttribute('data-method');
            
            // Update active tab
            tabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            // Show selected method
            methods.forEach(m => {
                if (m.id === `${method}-method`) {
                    m.classList.add('active');
                } else {
                    m.classList.remove('active');
                }
            });
        });
    });
}

/**
 * Initialize file upload functionality
 */
function initFileUpload() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('qr-file');
    const browseBtn = document.getElementById('browse-files');
    const previewDiv = document.getElementById('upload-preview');
    const previewImage = document.getElementById('preview-image');
    const removeBtn = document.getElementById('remove-image');
    const resultDiv = document.getElementById('upload-result');
    
    if (!uploadArea) return;
    
    // Click on upload area triggers file input
    uploadArea.addEventListener('click', function() {
        fileInput.click();
    });
    
    // Browse button triggers file input
    browseBtn?.addEventListener('click', function(e) {
        e.stopPropagation();
        fileInput.click();
    });
    
    // Handle file selection
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            handleFileUpload(file);
        }
    });
    
    // Drag and drop support
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.style.borderColor = '#667eea';
        this.style.backgroundColor = '#f7fafc';
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        this.style.borderColor = '#cbd5e0';
        this.style.backgroundColor = 'transparent';
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        this.style.borderColor = '#cbd5e0';
        this.style.backgroundColor = 'transparent';
        
        const file = e.dataTransfer.files[0];
        if (file) {
            handleFileUpload(file);
        }
    });
    
    // Remove image
    removeBtn?.addEventListener('click', function() {
        resetFileUpload();
    });
    
    /**
     * Handle file upload and preview
     */
    function handleFileUpload(file) {
        // Validate file type
        const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/bmp', 'image/gif'];
        if (!validTypes.includes(file.type)) {
            alert('نوع الملف غير مدعوم. الرجاء اختيار صورة (PNG, JPG, JPEG, BMP, GIF)');
            return;
        }
        
        // Validate file size (5MB max)
        if (file.size > 5 * 1024 * 1024) {
            alert('حجم الملف كبير جداً. الحد الأقصى 5MB');
            return;
        }
        
        // Show preview
        const reader = new FileReader();
        reader.onload = function(e) {
            previewImage.src = e.target.result;
            previewDiv.style.display = 'block';
            uploadArea.style.display = 'none';
            
            // Extract QR code
            extractQRFromFile(file);
        };
        reader.readAsDataURL(file);
    }
    
    /**
     * Extract QR code from uploaded file
     */
    function extractQRFromFile(file) {
        const loadingOverlay = document.getElementById('loading-overlay');
        const loadingMessage = document.getElementById('loading-message');
        
        if (loadingOverlay) {
            loadingMessage.textContent = 'جاري استخراج الرابط من صورة QR...';
            loadingOverlay.style.display = 'flex';
        }
        
        const formData = new FormData();
        formData.append('file', file);
        
        fetch('/api/scan_qr', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (loadingOverlay) {
                loadingOverlay.style.display = 'none';
            }
            
            if (data.success) {
                showUploadResult(data);
            } else {
                alert('خطأ: ' + (data.error || 'فشل استخراج QR'));
                resetFileUpload();
            }
        })
        .catch(error => {
            if (loadingOverlay) {
                loadingOverlay.style.display = 'none';
            }
            alert('حدث خطأ في الخادم: ' + error.message);
            resetFileUpload();
        });
    }
    
    /**
     * Show upload result
     */
    function showUploadResult(data) {
        const resultContent = document.getElementById('upload-result-content');
        if (resultContent) {
            resultContent.innerHTML = `
                <div class="result-url">
                    <strong>الرابط:</strong> ${data.content}
                </div>
                <div class="result-type">
                    <strong>النوع:</strong> ${data.type === 'url' ? 'رابط ويب' : data.type}
                </div>
            `;
        }
        
        resultDiv.style.display = 'block';
        
        // Set up scan button
        const scanBtn = document.getElementById('scan-upload-link');
        if (scanBtn) {
            scanBtn.onclick = function() {
                scanURL(data.content);
            };
        }
        
        // Set up clear button
        const clearBtn = document.getElementById('clear-upload-result');
        if (clearBtn) {
            clearBtn.onclick = resetFileUpload;
        }
    }
    
    /**
     * Reset file upload to initial state
     */
    function resetFileUpload() {
        fileInput.value = '';
        previewDiv.style.display = 'none';
        uploadArea.style.display = 'flex';
        resultDiv.style.display = 'none';
    }
}

/**
 * Initialize camera scanner
 */
function initCameraScanner() {
    const startBtn = document.getElementById('start-camera');
    const stopBtn = document.getElementById('stop-camera');
    const toggleBtn = document.getElementById('toggle-camera');
    const cameraPlaceholder = document.getElementById('camera-placeholder');
    const cameraPreview = document.getElementById('camera-preview');
    const canvas = document.getElementById('qr-canvas');
    const resultDiv = document.getElementById('camera-result');
    
    if (!startBtn) return;
    
    let stream = null;
    let facingMode = 'environment'; // Default to rear camera
    let scanning = false;
    let animationFrame = null;
    
    // Start camera
    startBtn.addEventListener('click', startCamera);
    
    // Stop camera
    stopBtn?.addEventListener('click', stopCamera);
    
    // Toggle camera
    toggleBtn?.addEventListener('click', toggleCamera);
    
    /**
     * Start camera and begin scanning
     */
    async function startCamera() {
        try {
            const constraints = {
                video: {
                    facingMode: facingMode,
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                }
            };
            
            stream = await navigator.mediaDevices.getUserMedia(constraints);
            cameraPreview.srcObject = stream;
            
            // Show camera preview
            cameraPlaceholder.style.display = 'none';
            cameraPreview.style.display = 'block';
            startBtn.style.display = 'none';
            stopBtn.style.display = 'inline-block';
            toggleBtn.style.display = 'inline-block';
            
            // Start scanning
            scanning = true;
            scanFrame();
            
        } catch (error) {
            console.error('Camera error:', error);
            alert('فشل تشغيل الكاميرا: ' + error.message);
        }
    }
    
    /**
     * Stop camera
     */
    function stopCamera() {
        scanning = false;
        
        if (animationFrame) {
            cancelAnimationFrame(animationFrame);
            animationFrame = null;
        }
        
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
        }
        
        // Reset UI
        cameraPreview.srcObject = null;
        cameraPreview.style.display = 'none';
        cameraPlaceholder.style.display = 'flex';
        startBtn.style.display = 'inline-block';
        stopBtn.style.display = 'none';
        toggleBtn.style.display = 'none';
        resultDiv.style.display = 'none';
    }
    
    /**
     * Toggle between front and rear cameras
     */
    async function toggleCamera() {
        facingMode = facingMode === 'environment' ? 'user' : 'environment';
        
        // Stop current stream
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
        
        // Restart with new facing mode
        await startCamera();
    }
    
    /**
     * Scan camera frame for QR codes
     */
    function scanFrame() {
        if (!scanning || !cameraPreview.videoWidth) {
            animationFrame = requestAnimationFrame(scanFrame);
            return;
        }
        
        // Set canvas dimensions to match video
        canvas.width = cameraPreview.videoWidth;
        canvas.height = cameraPreview.videoHeight;
        
        // Draw video frame to canvas
        const context = canvas.getContext('2d');
        context.drawImage(cameraPreview, 0, 0, canvas.width, canvas.height);
        
        // Get image data
        const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
        
        // Try to decode QR code
        try {
            const code = jsQR(imageData.data, imageData.width, imageData.height);
            
            if (code) {
                // QR code found
                stopCamera();
                showCameraResult(code.data);
            }
        } catch (error) {
            console.error('QR scanning error:', error);
        }
        
        // Continue scanning
        animationFrame = requestAnimationFrame(scanFrame);
    }
    
    /**
     * Show camera scan result
     */
    function showCameraResult(content) {
        const resultContent = document.getElementById('camera-result-content');
        if (resultContent) {
            resultContent.innerHTML = `
                <div class="result-url">
                    <strong>الرابط:</strong> ${content}
                </div>
            `;
        }
        
        resultDiv.style.display = 'block';
        
        // Set up scan button
        const scanBtn = document.getElementById('scan-camera-link');
        if (scanBtn) {
            scanBtn.onclick = function() {
                scanURL(content);
            };
        }
        
        // Set up clear button
        const clearBtn = document.getElementById('clear-camera-result');
        if (clearBtn) {
            clearBtn.onclick = function() {
                resultDiv.style.display = 'none';
                startCamera();
            };
        }
    }
}

/**
 * Initialize example links
 */
function initExampleLinks() {
    document.querySelectorAll('.example-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const url = this.getAttribute('data-url');
            
            // Fill URL input if exists
            const urlInput = document.getElementById('url-input');
            if (urlInput) {
                urlInput.value = url;
                urlInput.focus();
            }
            
            // Trigger scan if on manual page
            const scanBtn = document.getElementById('scan-url');
            if (scanBtn) {
                setTimeout(() => scanBtn.click(), 500);
            }
        });
    });
}

/**
 * Scan URL and display results
 */
function scanURL(url) {
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingMessage = document.getElementById('loading-message');
    const resultsDiv = document.getElementById('scan-results');
    const resultsContent = document.getElementById('results-content');
    
    if (!url) {
        alert('الرجاء إدخال رابط للفحص');
        return;
    }
    
    // Show loading
    if (loadingOverlay) {
        loadingMessage.textContent = 'جاري فحص الرابط وتحليل الأمان...';
        loadingOverlay.style.display = 'flex';
    }
    
    if (resultsDiv) {
        resultsDiv.style.display = 'none';
    }
    
    // Send scan request
    fetch('/api/check_url', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url: url })
    })
    .then(response => response.json())
    .then(data => {
        // Hide loading
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
        }
        
        if (data.success) {
            displayScanResults(data);
            if (resultsDiv) {
                resultsDiv.style.display = 'block';
            }
            
            // Scroll to results
            setTimeout(() => {
                resultsDiv?.scrollIntoView({ behavior: 'smooth' });
            }, 100);
        } else {
            alert('خطأ: ' + data.error);
        }
    })
    .catch(error => {
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
        }
        alert('حدث خطأ في الخادم: ' + error.message);
    });
}

/**
 * Display scan results
 */
function displayScanResults(data) {
    const resultsContent = document.getElementById('results-content');
    if (!resultsContent) return;
    
    const result = data.result;
    const score = result.security_score || 0;
    const riskLevel = result.risk_level || 'Unknown';
    const isSafe = result.is_safe;
    
    // Determine score class
    let scoreClass = 'critical';
    if (score >= 80) scoreClass = 'high';
    else if (score >= 60) scoreClass = 'medium';
    else if (score >= 40) scoreClass = 'low';
    
    // Create results HTML
    let html = `
        <div class="result-summary">
            <div class="score-circle score-${scoreClass}">
                <span class="score-value">${score}%</span>
                <span class="score-label">درجة الأمان</span>
            </div>
            <div class="result-details">
                <h4>${data.url}</h4>
                <div class="risk-level risk-${riskLevel.toLowerCase()}">
                    مستوى الخطورة: ${riskLevel}
                </div>
                <div class="result-status ${isSafe ? 'safe' : 'danger'}">
                    <i class="fas fa-${isSafe ? 'check-circle' : 'exclamation-triangle'}"></i>
                    ${isSafe ? 'الرابط آمن' : 'تم اكتشاف تهديدات'}
                </div>
                <p class="scan-time">
                    <i class="fas fa-clock"></i>
                    تم الفحص في: ${new Date().toLocaleTimeString()}
                </p>
            </div>
        </div>
    `;
    
    // Add threats if any
    if (result.threats && result.threats.length > 0) {
        html += `
            <div class="threats-section">
                <h4><i class="fas fa-exclamation-triangle"></i> التهديدات المكتشفة:</h4>
                <ul class="threats-list">
                    ${result.threats.map(threat => `<li>${threat}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    // Add warnings if any
    if (result.warnings && result.warnings.length > 0) {
        html += `
            <div class="warnings-section">
                <h4><i class="fas fa-exclamation-circle"></i> التحذيرات:</h4>
                <ul class="warnings-list">
                    ${result.warnings.map(warning => `<li>${warning}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    // Add recommendations if any
    if (result.recommendations && result.recommendations.length > 0) {
        html += `
            <div class="recommendations-section">
                <h4><i class="fas fa-lightbulb"></i> التوصيات:</h4>
                <ul class="recommendations-list">
                    ${result.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    // Add detailed report link
    html += `
        <div class="report-link">
            <a href="/report/${data.scan_id}" class="btn btn-primary">
                <i class="fas fa-file-alt"></i> عرض التقرير التفصيلي
            </a>
            <button onclick="scanNew()" class="btn btn-secondary">
                <i class="fas fa-redo"></i> فحص جديد
            </button>
        </div>
    `;
    
    resultsContent.innerHTML = html;
}

/**
 * Start a new scan
 */
function scanNew() {
    const resultsDiv = document.getElementById('scan-results');
    const resultsContent = document.getElementById('results-content');
    
    if (resultsDiv) {
        resultsDiv.style.display = 'none';
    }
    
    if (resultsContent) {
        resultsContent.innerHTML = '';
    }
    
    // Reset camera if active
    const stopBtn = document.getElementById('stop-camera');
    if (stopBtn && stopBtn.style.display !== 'none') {
        stopBtn.click();
    }
    
    // Reset file upload
    const removeBtn = document.getElementById('remove-image');
    if (removeBtn && removeBtn.style.display !== 'none') {
        removeBtn.click();
    }
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Handle global errors
 */
function handleGlobalError(event) {
    console.error('Global error:', event.error);
    
    // Don't show alert for network errors
    if (event.error && event.error.name === 'TypeError' && event.error.message.includes('fetch')) {
        return;
    }
    
    // Show user-friendly error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'global-error';
    errorDiv.innerHTML = `
        <div style="position: fixed; top: 20px; right: 20px; left: 20px; 
                    background: #fed7d7; color: #742a2a; padding: 15px; 
                    border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                    z-index: 3000; display: flex; justify-content: space-between;
                    align-items: center;">
            <div>
                <i class="fas fa-exclamation-triangle"></i>
                <strong>حدث خطأ:</strong> ${event.message || 'خطأ غير معروف'}
            </div>
            <button onclick="this.parentElement.remove()" 
                    style="background: none; border: none; color: #742a2a; 
                           cursor: pointer; font-size: 1.2rem;">
                ×
            </button>
        </div>
    `;
    
    document.body.appendChild(errorDiv);
    
    // Auto-remove after 10 seconds
    setTimeout(() => {
        if (errorDiv.parentElement) {
            errorDiv.remove();
        }
    }, 10000);
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        // Show success message
        showToast('تم نسخ النص إلى الحافظة');
    }).catch(err => {
        console.error('Copy failed:', err);
        showToast('فشل النسخ إلى الحافظة');
    });
}

/**
 * Show toast notification
 */
function showToast(message, type = 'success') {
    // Remove existing toasts
    document.querySelectorAll('.toast').forEach(toast => toast.remove());
    
    // Create new toast
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div style="position: fixed; bottom: 20px; left: 20px; right: 20px;
                    background: ${type === 'success' ? '#c6f6d5' : '#fed7d7'};
                    color: ${type === 'success' ? '#22543d' : '#742a2a'};
                    padding: 15px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                    z-index: 3000; text-align: center; font-weight: 500;">
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'}"></i>
            ${message}
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, 3000);
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ar-SA', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Validate URL format
 */
function isValidURL(url) {
    try {
        const urlObj = new URL(url);
        return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
    } catch {
        return false;
    }
}

// Make functions available globally
window.scanURL = scanURL;
window.scanNew = scanNew;
window.copyToClipboard = copyToClipboard;
window.formatDate = formatDate;
window.isValidURL = isValidURL;