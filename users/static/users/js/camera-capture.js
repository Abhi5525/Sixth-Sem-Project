/**
 * Camera Capture Module for KYC Profile Photo
 * Handles live camera access and photo capture for professional registration
 */

class CameraCapture {
    constructor() {
        this.video = null;
        this.canvas = null;
        this.stream = null;
        this.capturedImageData = null;
        this.modal = null;
        this.modalInstance = null;
        this.isCapturing = false;

        this.init();
    }

    init() {
        // Ensure DOM is fully ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }

    setup() {
        // Check browser support and secure context
        if (!this.checkCameraSupport()) {
            return;
        }

        this.setupEventListeners();
        console.log('CameraCapture initialized successfully');
    }

    checkCameraSupport() {
        // Check if we're in a secure context (HTTPS or localhost)
        if (!window.isSecureContext) {
            console.error('Camera requires secure context (HTTPS or localhost).');
            this.showInsecureError();
            return false;
        }

        const hasGetUserMedia = !!(
            navigator.mediaDevices &&
            navigator.mediaDevices.getUserMedia
        );

        if (!hasGetUserMedia) {
            console.warn('Camera not supported on this device');
            document.getElementById('cameraBtn')?.setAttribute('disabled', 'disabled');
            this.showCameraFallback('Camera is not supported on this device.');
        }

        return hasGetUserMedia;
    }

    setupEventListeners() {
        // Camera button click
        const cameraBtn = document.getElementById('cameraBtn');
        if (cameraBtn) {
            cameraBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.openCamera();
            });
        } else {
            console.error('Camera button (#cameraBtn) not found in DOM');
        }

        // Capture button
        const captureBtn = document.getElementById('capturePhotoBtn');
        if (captureBtn) {
            captureBtn.addEventListener('click', () => this.capturePhoto());
        }

        // Close camera
        const closeBtn = document.getElementById('closeCameraBtn');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeCamera());
        }

        // Retake photo
        const retakeBtn = document.getElementById('retakePhotoBtn');
        if (retakeBtn) {
            retakeBtn.addEventListener('click', () => this.retakePhoto());
        }

        // Confirm photo
        const confirmBtn = document.getElementById('confirmPhotoBtn');
        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => this.confirmPhoto());
        }

        // Hide camera fallback if visible
        const fallback = document.getElementById('cameraFallback');
        if (fallback) fallback.style.display = 'none';
    }

    async openCamera() {
        try {
            // Get DOM elements
            this.modal = document.getElementById('cameraModal');
            this.video = document.getElementById('cameraVideo');
            this.canvas = document.getElementById('photoCanvas');

            if (!this.video) {
                console.error('Video element not found');
                alert('Error: Camera modal not found. Please reload the page.');
                return;
            }

            if (typeof bootstrap === 'undefined' || !bootstrap.Modal) {
                console.error('Bootstrap JS not loaded');
                alert('Error: Bootstrap is not loaded. Please reload the page.');
                return;
            }

            // Create modal instance if needed
            this.modalInstance = bootstrap.Modal.getInstance(this.modal);
            if (!this.modalInstance) {
                this.modalInstance = new bootstrap.Modal(this.modal, {
                    backdrop: 'static',
                    keyboard: false
                });
            }

            // Show modal FIRST (before requesting camera — browsers require user gesture on visible element)
            this.modalInstance.show();

            // Wait for modal to be fully shown (Bootstrap transition takes ~150ms)
            await new Promise(resolve => {
                this.modal.addEventListener('shown.bs.modal', resolve, { once: true });
                // Fallback timeout if event doesn't fire
                setTimeout(resolve, 300);
            });

            // Now request camera access
            console.log('Requesting camera access...');
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: 'user',
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                },
                audio: false
            });

            console.log('Camera stream obtained:', this.stream);

            // Display stream
            this.video.srcObject = this.stream;
            await this.video.play();

            console.log('Video playing');

            // Show camera view
            this.showCameraView();

            console.log('Camera opened successfully');
        } catch (error) {
            console.error('Camera error:', error);
            this.handleCameraError(error);
        }
    }

    capturePhoto() {
        if (!this.video) return;

        const context = this.canvas.getContext('2d');

        // Set canvas dimensions to match video
        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;

        // Flip horizontally (mirror effect)
        context.scale(-1, 1);
        context.drawImage(this.video, -this.canvas.width, 0);
        context.scale(-1, 1);

        // Store image data
        this.capturedImageData = this.canvas.toDataURL('image/jpeg', 0.95);

        // Show preview
        this.showPreview();

        console.log('Photo captured');
    }

    showCameraView() {
        const cameraView = document.getElementById('cameraView');
        const previewView = document.getElementById('previewView');
        if (cameraView) {
            cameraView.classList.add('active');
            cameraView.style.display = '';
        }
        if (previewView) {
            previewView.classList.remove('active');
            previewView.style.display = '';
        }
    }

    showPreview() {
        const previewImg = document.getElementById('previewImage');
        if (previewImg) {
            previewImg.src = this.capturedImageData;
        }
        const cameraView = document.getElementById('cameraView');
        const previewView = document.getElementById('previewView');
        if (cameraView) {
            cameraView.classList.remove('active');
            cameraView.style.display = '';
        }
        if (previewView) {
            previewView.classList.add('active');
            previewView.style.display = '';
        }
    }

    retakePhoto() {
        this.capturedImageData = null;
        if (this.video && this.stream) {
            this.video.play();
        }
        this.showCameraView();
    }

    async confirmPhoto() {
        if (!this.capturedImageData) {
            alert('Please capture a photo first');
            return;
        }

        try {
            const blob = await this.dataURLtoBlob(this.capturedImageData);
            const file = new File([blob], 'profile-photo-kyc.jpg', { type: 'image/jpeg' });

            const fileInput = document.getElementById('profile_picture');
            if (!fileInput) {
                console.error('File input #profile_picture not found');
                alert('Error: Profile picture field not found. Please reload the page.');
                return;
            }

            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            fileInput.files = dataTransfer.files;

            console.log('File set on input:', fileInput.files);

            this.updateCaptureStatus();

            const cameraBtn = document.getElementById('cameraBtn');
            if (cameraBtn) {
                cameraBtn.disabled = true;
                cameraBtn.innerHTML = '<i class="fas fa-check"></i> Photo Captured';
            }

            this.closeCamera();

            this.showSuccessMessage('Profile photo captured successfully! Click "Submit" to complete registration.');

        } catch (error) {
            console.error('Error processing photo:', error);
            alert('Error processing photo. Please try again.');
        }
    }

    updateCaptureStatus() {
        const statusDiv = document.getElementById('captureStatus');
        if (statusDiv) {
            statusDiv.style.display = 'block';
        }
    }

    closeCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }

        if (this.video) {
            this.video.srcObject = null;
        }

        if (this.modalInstance) {
            this.modalInstance.hide();
        }

        // Force hide both views
        const cameraView = document.getElementById('cameraView');
        const previewView = document.getElementById('previewView');
        if (cameraView) {
            cameraView.classList.remove('active');
            cameraView.style.display = 'none';
        }
        if (previewView) {
            previewView.classList.remove('active');
            previewView.style.display = 'none';
        }

        this.capturedImageData = null;
    }

    handleCameraError(error) {
        let errorMessage = 'Could not access camera. ';

        if (error.name === 'NotAllowedError') {
            errorMessage += 'Camera access denied. Please allow camera permission in your browser settings and try again.';
        } else if (error.name === 'NotFoundError') {
            errorMessage += 'No camera device found. Please make sure a camera is connected.';
        } else if (error.name === 'NotReadableError') {
            errorMessage += 'Camera is already in use by another application. Please close other apps using the camera.';
        } else if (error.name === 'OverconstrainedError') {
            errorMessage += 'Camera resolution not supported. Please try a different device.';
        } else {
            errorMessage += error.message;
        }

        alert(errorMessage);
        console.error('Camera error details:', error.name, error.message);

        this.showCameraFallback(errorMessage);
        this.closeCamera();
    }

    showCameraFallback(message) {
        const fallback = document.getElementById('cameraFallback');
        if (fallback) {
            fallback.style.display = 'block';
            fallback.innerHTML = `<i class="fas fa-exclamation-triangle"></i> <strong>Camera not available.</strong> ${message}`;
        }
    }

    showInsecureError() {
        const fallback = document.getElementById('cameraFallback');
        if (fallback) {
            fallback.style.display = 'block';
            fallback.innerHTML = `
                <i class="fas fa-exclamation-triangle"></i>
                <strong>Camera requires a secure connection.</strong>
                Camera access only works on HTTPS or localhost (127.0.0.1).
                If you're accessing from another device on the network, please use HTTPS.
            `;
        }

        const cameraBtn = document.getElementById('cameraBtn');
        if (cameraBtn) {
            cameraBtn.disabled = true;
            cameraBtn.innerHTML = '<i class="fas fa-lock"></i> Requires HTTPS';
        }
    }

    async dataURLtoBlob(dataURL) {
        const arr = dataURL.split(',');
        const mime = arr[0].match(/:(.*?);/)[1];
        const bstr = atob(arr[1]);
        let n = bstr.length;
        const u8arr = new Uint8Array(n);
        while (n--) {
            u8arr[n] = bstr.charCodeAt(n);
        }
        return new Blob([u8arr], { type: mime });
    }

    showSuccessMessage(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success alert-dismissible fade show position-fixed';
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; width: auto; max-width: 400px;';
        alertDiv.innerHTML = `
            <i class="fas fa-check-circle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alertDiv);

        setTimeout(() => {
            alertDiv.remove();
        }, 3000);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new CameraCapture();
});

// Expose for manual initialization if needed
if (typeof window.initCamera === 'undefined') {
    window.initCamera = () => new CameraCapture();
}
