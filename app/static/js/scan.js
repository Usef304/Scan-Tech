// Scanner functionality
let stream = null;
let scanning = false;
let currentFacingMode = 'environment';
let scanInterval = null;

function showCameraScanner() {
  document.getElementById('cameraScanner').style.display = 'block';
  document.getElementById('fileUpload').style.display = 'none';
  document.getElementById('scanResult').innerHTML = 'No QR code detected. Please try again.';
  document.getElementById('scanResult').className = 'result-placeholder';
}

function showFileUpload() {
  document.getElementById('cameraScanner').style.display = 'none';
  document.getElementById('fileUpload').style.display = 'block';
  stopCamera();
}

function showError(message) {
  const errorDiv = document.getElementById('cameraError');
  errorDiv.innerHTML = `<p>${message}</p>`;
  errorDiv.style.display = 'block';
}

async function initCamera() {
  try {
    document.getElementById('scanningOverlay').style.display = 'flex';
    document.getElementById('cameraError').style.display = 'none';
    
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
    
    // Check browser support
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      showError('Camera access is not supported in your browser. Please use Chrome, Firefox, or Edge.');
      document.getElementById('scanningOverlay').style.display = 'none';
      return;
    }
    
    stream = await navigator.mediaDevices.getUserMedia({
      video: { 
        facingMode: currentFacingMode,
        width: { ideal: 1280 },
        height: { ideal: 720 }
      },
      audio: false
    });
    
    const video = document.getElementById('video');
    video.srcObject = stream;
    
    video.onloadedmetadata = function() {
      document.getElementById('scanningOverlay').style.display = 'none';
      document.getElementById('startCamera').style.display = 'none';
      document.getElementById('stopCamera').style.display = 'inline-block';
      document.getElementById('switchCamera').style.display = 'inline-block';
      
      scanning = true;
      startQRScanning();
    };
    
  } catch (error) {
    console.error('Error accessing camera:', error);
    document.getElementById('scanningOverlay').style.display = 'none';
    
    if (error.name === 'NotAllowedError') {
      showError('Camera permission denied. Please allow camera access in your browser settings.');
    } else if (error.name === 'NotFoundError' || error.name === 'OverconstrainedError') {
      showError('No camera found or camera doesn\'t meet requirements. Please try a different device.');
    } else {
      showError(`Unable to access camera: ${error.message}`);
    }
  }
}

function stopCamera() {
  scanning = false;
  
  if (scanInterval) {
    clearInterval(scanInterval);
    scanInterval = null;
  }
  
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
    stream = null;
  }
  
  const video = document.getElementById('video');
  video.srcObject = null;
  
  document.getElementById('startCamera').style.display = 'inline-block';
  document.getElementById('stopCamera').style.display = 'none';
  document.getElementById('switchCamera').style.display = 'none';
  document.getElementById('scanningOverlay').style.display = 'none';
}

async function switchCamera() {
  currentFacingMode = currentFacingMode === 'environment' ? 'user' : 'environment';
  stopCamera();
  setTimeout(initCamera, 300);
}

function startQRScanning() {
  if (scanInterval) {
    clearInterval(scanInterval);
  }
  
  scanInterval = setInterval(scanQRCode, 100);
}

function scanQRCode() {
  if (!scanning) return;
  
  const video = document.getElementById('video');
  const canvas = document.createElement('canvas');
  const context = canvas.getContext('2d');
  
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  context.drawImage(video, 0, 0, canvas.width, canvas.height);
  
  const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
  
  try {
    const code = jsQR(imageData.data, imageData.width, imageData.height, {
      inversionAttempts: 'dontInvert',
    });
    
    if (code) {
      clearInterval(scanInterval);
      scanning = false;
      
      context.strokeStyle = '#4CAF50';
      context.lineWidth = 4;
      context.strokeRect(
        code.location.topLeftCorner.x, 
        code.location.topLeftCorner.y,
        code.location.topRightCorner.x - code.location.topLeftCorner.x,
        code.location.bottomLeftCorner.y - code.location.topLeftCorner.y
      );
      
      document.getElementById('scanResult').innerHTML = 
        `<div class="success-message">✅ QR Code Detected!</div>
         <div style="margin: 15px 0; font-size: 1.1rem;">${code.data}</div>
         <form action="{{ url_for('main.analyze_qr_data') }}" method="post" id="qrDataForm">
           <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
           <input type="hidden" name="qr_data" value="${code.data}">
           <button type="submit" class="btn btn-primary" style="margin-top: 15px;">
             Analyze Security
           </button>
         </form>`;
      document.getElementById('scanResult').className = '';
      
      // Add loading indicator to form submission
      document.getElementById('qrDataForm').addEventListener('submit', function() {
        this.querySelector('button').innerHTML = '<span class="loading"></span> Analyzing...';
        this.querySelector('button').disabled = true;
      });
      
      setTimeout(stopCamera, 3000);
    }
  } catch (error) {
    console.error('Error scanning QR code:', error);
  }
}

// File upload handling
document.addEventListener('DOMContentLoaded', function() {
  const fileInput = document.getElementById('file');
  const uploadArea = document.getElementById('uploadArea');
  const analyzeBtn = document.getElementById('analyzeBtn');
  const uploadText = uploadArea.querySelector('.upload-text');
  
  // Prevent double file dialog by handling the label click properly
  uploadArea.addEventListener('click', function(e) {
    // Only trigger file input if the click is not on a child element that should handle its own clicks
    if (e.target === uploadArea || e.target.classList.contains('upload-icon') || 
        e.target.classList.contains('upload-text') || e.target.classList.contains('upload-subtext')) {
      e.preventDefault();
      fileInput.click();
    }
  });
  
  fileInput.addEventListener('change', function(e) {
    if (this.files && this.files[0]) {
      const fileName = this.files[0].name;
      uploadText.textContent = fileName;
      uploadArea.classList.add('file-selected');
      analyzeBtn.disabled = false;
    }
  });
  
  uploadArea.addEventListener('dragover', function(e) {
    e.preventDefault();
    this.classList.add('dragover');
  });
  
  uploadArea.addEventListener('dragleave', function(e) {
    e.preventDefault();
    this.classList.remove('dragover');
  });
  
  uploadArea.addEventListener('drop', function(e) {
    e.preventDefault();
    this.classList.remove('dragover');
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      fileInput.files = e.dataTransfer.files;
      const fileName = e.dataTransfer.files[0].name;
      uploadText.textContent = fileName;
      this.classList.add('file-selected');
      analyzeBtn.disabled = false;
      
      // Auto-submit the form after file drop
      setTimeout(() => {
        document.getElementById('uploadForm').submit();
      }, 100);
    }
  });
  
  // Show camera not supported message
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    document.querySelector('.scan-method:nth-child(1)').innerHTML += 
      '<div style="color: #f44336; margin-top: 10px; font-size: 0.9rem;">Camera not supported in your browser</div>';
  }
}); 