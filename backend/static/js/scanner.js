/**
 * Camera Scanner Module for QR Code Scanning
 */

class QRScanner {
    constructor(options = {}) {
        this.options = {
            videoElement: '#camera-preview',
            canvasElement: '#qr-canvas',
            resultElement: '#camera-result-content',
            onScan: null,
            onError: null,
            ...options
        };
        
        this.video = document.querySelector(this.options.videoElement);
        this.canvas = document.querySelector(this.options.canvasElement);
        this.context = this.canvas?.getContext('2d');
        this.stream = null;
        this.scanning = false;
        this.animationFrame = null;
        
        this.init();
    }
    
    /**
     * Initialize scanner
     */
    init() {
        if (!this.video || !this.canvas) {
            console.error('Video or canvas element not found');
            return;
        }
        
        // Set up canvas dimensions
        this.canvas.width = this.video.width || 640;
        this.canvas.height = this.video.height || 480;
    }
    
    /**
     * Start camera and scanning
     */
    async start() {
        try {
            // Request camera access
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: 'environment',
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                },
                audio: false
            });
            
            // Set video source
            this.video.srcObject = this.stream;
            await this.video.play();
            
            // Start scanning loop
            this.scanning = true;
            this.scanLoop();
            
            return true;
            
        } catch (error) {
            console.error('Camera error:', error);
            
            if (this.options.onError) {
                this.options.onError(error);
            }
            
            return false;
        }
    }
    
    /**
     * Stop camera and scanning
     */
    stop() {
        this.scanning = false;
        
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
            this.animationFrame = null;
        }
        
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        
        if (this.video) {
            this.video.srcObject = null;
        }
    }
    
    /**
     * Scanning loop
     */
    scanLoop() {
        if (!this.scanning || !this.video.videoWidth) {
            this.animationFrame = requestAnimationFrame(() => this.scanLoop());
            return;
        }
        
        // Update canvas dimensions
        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;
        
        // Draw video frame to canvas
        this.context.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
        
        // Get image data
        const imageData = this.context.getImageData(0, 0, this.canvas.width, this.canvas.height);
        
        try {
            // Decode QR code
            const code = jsQR(imageData.data, imageData.width, imageData.height);
            
            if (code) {
                // QR code found
                this.onQRDetected(code);
            }
        } catch (error) {
            console.error('QR decoding error:', error);
        }
        
        // Continue scanning
        this.animationFrame = requestAnimationFrame(() => this.scanLoop());
    }
    
    /**
     * Handle QR code detection
     */
    onQRDetected(code) {
        console.log('QR code detected:', code.data);
        
        // Draw bounding box for debugging
        this.drawBoundingBox(code.location);
        
        if (this.options.onScan) {
            this.options.onScan(code.data, code);
        }
        
        // Optional: stop scanning after detection
        // this.stop();
    }
    
    /**
     * Draw bounding box around QR code (for debugging)
     */
    drawBoundingBox(location) {
        const { topLeftCorner, topRightCorner, bottomRightCorner, bottomLeftCorner } = location;
        
        this.context.beginPath();
        this.context.moveTo(topLeftCorner.x, topLeftCorner.y);
        this.context.lineTo(topRightCorner.x, topRightCorner.y);
        this.context.lineTo(bottomRightCorner.x, bottomRightCorner.y);
        this.context.lineTo(bottomLeftCorner.x, bottomLeftCorner.y);
        this.context.closePath();
        
        this.context.lineWidth = 4;
        this.context.strokeStyle = '#00FF00';
        this.context.stroke();
    }
    
    /**
     * Toggle between front and rear cameras
     */
    async toggleCamera() {
        const currentTrack = this.stream?.getVideoTracks()[0];
        if (!currentTrack) return;
        
        const currentFacingMode = currentTrack.getSettings().facingMode;
        const newFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';
        
        // Stop current stream
        this.stop();
        
        // Start with new facing mode
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: newFacingMode,
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                },
                audio: false
            });
            
            this.video.srcObject = this.stream;
            await this.video.play();
            
            this.scanning = true;
            this.scanLoop();
            
        } catch (error) {
            console.error('Camera toggle error:', error);
            
            if (this.options.onError) {
                this.options.onError(error);
            }
        }
    }
    
    /**
     * Capture still image from camera
     */
    captureImage() {
        if (!this.video.videoWidth) return null;
        
        // Create temporary canvas
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = this.video.videoWidth;
        tempCanvas.height = this.video.videoHeight;
        
        const tempContext = tempCanvas.getContext('2d');
        tempContext.drawImage(this.video, 0, 0);
        
        return tempCanvas.toDataURL('image/png');
    }
    
    /**
     * Check if camera is supported
     */
    static isSupported() {
        return !!(
            navigator.mediaDevices &&
            navigator.mediaDevices.getUserMedia &&
            typeof window.jsQR !== 'undefined'
        );
    }
    
    /**
     * Get list of available cameras
     */
    static async getCameras() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            return devices.filter(device => device.kind === 'videoinput');
        } catch (error) {
            console.error('Error getting cameras:', error);
            return [];
        }
    }
}

// Export for use in browser
if (typeof window !== 'undefined') {
    window.QRScanner = QRScanner;
}

/**
 * File-based QR Scanner
 */
class FileQRScanner {
    constructor(options = {}) {
        this.options = {
            fileInput: '#qr-file',
            previewElement: '#preview-image',
            resultElement: '#upload-result-content',
            onScan: null,
            onError: null,
            ...options
        };
        
        this.fileInput = document.querySelector(this.options.fileInput);
        this.preview = document.querySelector(this.options.previewElement);
        
        this.init();
    }
    
    /**
     * Initialize file scanner
     */
    init() {
        if (this.fileInput) {
            this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        }
    }
    
    /**
     * Handle file selection
     */
    handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        // Validate file
        if (!this.validateFile(file)) {
            if (this.options.onError) {
                this.options.onError('نوع الملف غير مدعوم أو الحجم كبير جداً');
            }
            return;
        }
        
        // Show preview
        this.showPreview(file);
        
        // Scan QR code
        this.scanFile(file);
    }
    
    /**
     * Validate file
     */
    validateFile(file) {
        // Check file type
        const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/bmp', 'image/gif'];
        if (!validTypes.includes(file.type)) {
            return false;
        }
        
        // Check file size (5MB max)
        if (file.size > 5 * 1024 * 1024) {
            return false;
        }
        
        return true;
    }
    
    /**
     * Show image preview
     */
    showPreview(file) {
        const reader = new FileReader();
        
        reader.onload = (e) => {
            if (this.preview) {
                this.preview.src = e.target.result;
                this.preview.style.display = 'block';
            }
        };
        
        reader.readAsDataURL(file);
    }
    
    /**
     * Scan QR code from file
     */
    async scanFile(file) {
        try {
            // Create image element
            const image = await this.loadImage(file);
            
            // Create canvas
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            
            // Set canvas dimensions
            canvas.width = image.width;
            canvas.height = image.height;
            
            // Draw image to canvas
            context.drawImage(image, 0, 0);
            
            // Get image data
            const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
            
            // Decode QR code
            const code = jsQR(imageData.data, imageData.width, imageData.height);
            
            if (code) {
                if (this.options.onScan) {
                    this.options.onScan(code.data, code);
                }
            } else {
                if (this.options.onError) {
                    this.options.onError('لم يتم العثور على رمز QR في الصورة');
                }
            }
            
        } catch (error) {
            console.error('File scanning error:', error);
            
            if (this.options.onError) {
                this.options.onError('خطأ في معالجة الصورة');
            }
        }
    }
    
    /**
     * Load image from file
     */
    loadImage(file) {
        return new Promise((resolve, reject) => {
            const image = new Image();
            const reader = new FileReader();
            
            reader.onload = (e) => {
                image.onload = () => resolve(image);
                image.onerror = reject;
                image.src = e.target.result;
            };
            
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }
    
    /**
     * Clear scanner
     */
    clear() {
        if (this.fileInput) {
            this.fileInput.value = '';
        }
        
        if (this.preview) {
            this.preview.src = '';
            this.preview.style.display = 'none';
        }
    }
}

// Export for use in browser
if (typeof window !== 'undefined') {
    window.FileQRScanner = FileQRScanner;
}

/**
 * URL Validation Utility
 */
const URLValidator = {
    /**
     * Validate URL format
     */
    isValidURL(url) {
        try {
            const urlObj = new URL(url);
            return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
        } catch {
            return false;
        }
    },
    
    /**
     * Normalize URL (add https:// if missing)
     */
    normalizeURL(url) {
        if (!url) return '';
        
        let normalized = url.trim();
        
        // Remove any leading/trailing whitespace
        normalized = normalized.trim();
        
        // Add protocol if missing
        if (!normalized.startsWith('http://') && !normalized.startsWith('https://')) {
            normalized = 'https://' + normalized;
        }
        
        return normalized;
    },
    
    /**
     * Extract domain from URL
     */
    extractDomain(url) {
        try {
            const urlObj = new URL(this.normalizeURL(url));
            return urlObj.hostname;
        } catch {
            return '';
        }
    },
    
    /**
     * Check if URL is shortened
     */
    isShortenedURL(url) {
        const shorteners = [
            'bit.ly', 'tinyurl.com', 'goo.gl', 'ow.ly', 'is.gd',
            'buff.ly', 'adf.ly', 'shorte.st', 'cutt.ly', 'shorturl.at',
            'tiny.cc', 'bit.do', 'rebrand.ly', 'bl.ink', 'clickmeter.com'
        ];
        
        const domain = this.extractDomain(url);
        return shorteners.some(shortener => domain.includes(shortener));
    },
    
    /**
     * Check if URL contains suspicious patterns
     */
    hasSuspiciousPatterns(url) {
        const patterns = [
            /login/i,
            /signin/i,
            /verify/i,
            /account/i,
            /banking/i,
            /paypal/i,
            /password/i,
            /secure/i,
            /update/i,
            /confirm/i,
            /admin/i,
            /php/i,
            /wp-/i,
            /jquery/i,
            /free/i,
            /win/i,
            /prize/i,
            /reward/i,
            /urgent/i,
            /immediate/i
        ];
        
        return patterns.some(pattern => pattern.test(url));
    }
};

// Export for use in browser
if (typeof window !== 'undefined') {
    window.URLValidator = URLValidator;
}

/**
 * Scan Result Formatter
 */
const ResultFormatter = {
    /**
     * Format security score with color
     */
    formatScore(score) {
        let className = 'critical';
        let label = 'حرج';
        
        if (score >= 80) {
            className = 'high';
            label = 'عالي';
        } else if (score >= 60) {
            className = 'medium';
            label = 'متوسط';
        } else if (score >= 40) {
            className = 'low';
            label = 'منخفض';
        }
        
        return {
            className,
            label,
            value: score
        };
    },
    
    /**
     * Format risk level
     */
    formatRiskLevel(riskLevel) {
        const levels = {
            'low': { className: 'low', label: 'منخفض', icon: 'check-circle' },
            'medium': { className: 'medium', label: 'متوسط', icon: 'exclamation-circle' },
            'high': { className: 'high', label: 'عالي', icon: 'exclamation-triangle' },
            'critical': { className: 'critical', label: 'حرج', icon: 'skull-crossbones' }
        };
        
        return levels[riskLevel.toLowerCase()] || levels.medium;
    },
    
    /**
     * Format timestamp
     */
    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        
        if (isNaN(date.getTime())) {
            return 'غير معروف';
        }
        
        return date.toLocaleDateString('ar-SA', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    },
    
    /**
     * Format URL for display
     */
    formatURL(url, maxLength = 50) {
        if (!url) return '';
        
        if (url.length <= maxLength) {
            return url;
        }
        
        const start = url.substring(0, maxLength / 2);
        const end = url.substring(url.length - maxLength / 2);
        return start + '...' + end;
    },
    
    /**
     * Create HTML for scan result
     */
    createResultHTML(data) {
        const score = this.formatScore(data.security_score);
        const risk = this.formatRiskLevel(data.risk_level);
        
        return `
            <div class="scan-result-card">
                <div class="result-header">
                    <div class="score-badge score-${score.className}">
                        ${score.value}%
                    </div>
                    <div class="result-info">
                        <h4>${this.formatURL(data.url)}</h4>
                        <div class="risk-level risk-${risk.className}">
                            <i class="fas fa-${risk.icon}"></i>
                            مستوى الخطورة: ${risk.label}
                        </div>
                    </div>
                </div>
                
                <div class="result-body">
                    ${this.createThreatsHTML(data.threats)}
                    ${this.createWarningsHTML(data.warnings)}
                    ${this.createRecommendationsHTML(data.recommendations)}
                </div>
                
                <div class="result-footer">
                    <div class="scan-time">
                        <i class="fas fa-clock"></i>
                        ${this.formatTimestamp(data.timestamp)}
                    </div>
                </div>
            </div>
        `;
    },
    
    /**
     * Create threats HTML
     */
    createThreatsHTML(threats) {
        if (!threats || threats.length === 0) {
            return '';
        }
        
        const items = threats.map(threat => `<li>${threat}</li>`).join('');
        
        return `
            <div class="result-section threats-section">
                <h5><i class="fas fa-exclamation-triangle"></i> التهديدات</h5>
                <ul class="threats-list">${items}</ul>
            </div>
        `;
    },
    
    /**
     * Create warnings HTML
     */
    createWarningsHTML(warnings) {
        if (!warnings || warnings.length === 0) {
            return '';
        }
        
        const items = warnings.map(warning => `<li>${warning}</li>`).join('');
        
        return `
            <div class="result-section warnings-section">
                <h5><i class="fas fa-exclamation-circle"></i> التحذيرات</h5>
                <ul class="warnings-list">${items}</ul>
            </div>
        `;
    },
    
    /**
     * Create recommendations HTML
     */
    createRecommendationsHTML(recommendations) {
        if (!recommendations || recommendations.length === 0) {
            return '';
        }
        
        const items = recommendations.map(rec => `<li>${rec}</li>`).join('');
        
        return `
            <div class="result-section recommendations-section">
                <h5><i class="fas fa-lightbulb"></i> التوصيات</h5>
                <ul class="recommendations-list">${items}</ul>
            </div>
        `;
    }
};

// Export for use in browser
if (typeof window !== 'undefined') {
    window.ResultFormatter = ResultFormatter;
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check for camera support
    const cameraSupport = QRScanner.isSupported();
    
    // Update UI based on camera support
    const cameraMethod = document.querySelector('#camera-method');
    if (cameraMethod && !cameraSupport) {
        const methodContent = cameraMethod.querySelector('.method-content');
        if (methodContent) {
            methodContent.innerHTML = `
                <div class="camera-not-supported">
                    <i class="fas fa-video-slash fa-3x"></i>
                    <h3>الكاميرا غير مدعومة</h3>
                    <p>المتصفح أو الجهاز لا يدعم الوصول إلى الكاميرا.</p>
                    <p>يرجى استخدام ميزة رفع الصورة بدلاً من ذلك.</p>
                </div>
            `;
        }
    }
    
    // Initialize file scanner
    if (document.querySelector('#upload-method')) {
        window.fileScanner = new FileQRScanner({
            fileInput: '#qr-file',
            previewElement: '#preview-image',
            resultElement: '#upload-result-content',
            onScan: function(data, code) {
                console.log('QR detected from file:', data);
                
                const resultDiv = document.getElementById('upload-result');
                const resultContent = document.getElementById('upload-result-content');
                
                if (resultContent) {
                    resultContent.innerHTML = `
                        <div class="result-url">
                            <strong>الرابط:</strong> ${data}
                        </div>
                        <div class="result-type">
                            <strong>النوع:</strong> ${URLValidator.isValidURL(data) ? 'رابط ويب' : 'نص'}
                        </div>
                    `;
                }
                
                if (resultDiv) {
                    resultDiv.style.display = 'block';
                }
                
                // Set up scan button
                const scanBtn = document.getElementById('scan-upload-link');
                if (scanBtn) {
                    scanBtn.onclick = function() {
                        window.scanURL(data);
                    };
                }
            },
            onError: function(error) {
                alert('خطأ في المسح: ' + error);
            }
        });
    }
});