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
        
        // Cache frequently accessed DOM elements
        this.cameraBtn = null;
        this.captureBtn = null;
        this.closeBtn = null;
        this.retakeBtn = null;
        this.confirmBtn = null;
        this.viewPhotoBtn = null;
        this.removePhotoBtn = null;
        this.fallback = null;
        this.cameraView = null;
        this.previewView = null;
        this.fileInput = null;
        this.captureButtonContainer = null;
        this.previewSection = null;
        this.uploadedPhotoPreview = null;
        this.statusDiv = null;

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
        
        // Cache all DOM elements on setup
        this.cacheElements();
        this.setupEventListeners();
        console.log('CameraCapture initialized successfully');
    }
    
    cacheElements() {
        this.cameraBtn = document.getElementById('cameraBtn');
        this.captureBtn = document.getElementById('capturePhotoBtn');
        this.closeBtn = document.getElementById('closeCameraBtn');
        this.retakeBtn = document.getElementById('retakePhotoBtn');
        this.confirmBtn = document.getElementById('confirmPhotoBtn');
        this.viewPhotoBtn = document.getElementById('viewPhotoBtn');
        this.removePhotoBtn = document.getElementById('removePhotoBtn');
        this.fallback = document.getElementById('cameraFallback');
        this.cameraView = document.getElementById('cameraView');
        this.previewView = document.getElementById('previewView');
        this.fileInput = document.getElementById('profile_picture');
        this.captureButtonContainer = document.getElementById('captureButtonContainer');
        this.previewSection = document.getElementById('imagePreviewSection');
        this.uploadedPhotoPreview = document.getElementById('uploadedPhotoPreview');
        this.statusDiv = document.getElementById('captureStatus');
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
            if (this.cameraBtn) {
                this.cameraBtn.setAttribute('disabled', 'disabled');
            }
            this.showCameraFallback('Camera is not supported on this device.');
        }

        return hasGetUserMedia;
    }

    setupEventListeners() {
        // Camera button click
        if (this.cameraBtn) {
            this.cameraBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.openCamera();
            });
        } else {
            console.error('Camera button (#cameraBtn) not found in DOM');
        }

        // Capture button
        if (this.captureBtn) {
            this.captureBtn.addEventListener('click', () => this.capturePhoto());
        }

        // Close camera
        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', () => this.closeCamera());
        }

        // Retake photo
        if (this.retakeBtn) {
            this.retakeBtn.addEventListener('click', () => this.retakePhoto());
        }

        // Confirm photo
        if (this.confirmBtn) {
            this.confirmBtn.addEventListener('click', () => this.confirmPhoto());
        }

        // View photo button
        if (this.viewPhotoBtn) {
            this.viewPhotoBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.viewPhoto();
            });
        }

        // Remove photo button
        if (this.removePhotoBtn) {
            this.removePhotoBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.removePhoto();
            });
        }

        // Hide camera fallback if visible
        if (this.fallback) {
            this.fallback.style.display = 'none';
        }
    }

    async openCamera() {
        try {
            // Get DOM elements
            this.modal = document.getElementById('cameraModal');
            this.video = document.getElementById('cameraVideo');
            this.canvas = document.getElementById('photoCanvas');

            if (!this.modal || !this.video || !this.canvas) {
                console.error('Camera UI elements missing:', {
                    modal: !!this.modal,
                    video: !!this.video,
                    canvas: !!this.canvas
                });
                alert('Error: Camera components are missing. Please reload the page.');
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
        if (this.cameraView) {
            this.cameraView.classList.add('active');
            this.cameraView.style.display = '';
        }
        if (this.previewView) {
            this.previewView.classList.remove('active');
            this.previewView.style.display = '';
        }
    }

    showPreview() {
        if (this.uploadedPhotoPreview) {
            this.uploadedPhotoPreview.src = this.capturedImageData;
        }
        if (this.cameraView) {
            this.cameraView.classList.remove('active');
            this.cameraView.style.display = '';
        }
        if (this.previewView) {
            this.previewView.classList.add('active');
            this.previewView.style.display = '';
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

            if (!this.fileInput) {
                console.error('File input #profile_picture not found');
                alert('Error: Profile picture field not found. Please reload the page.');
                return;
            }

            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            this.fileInput.files = dataTransfer.files;

            console.log('File set on input:', this.fileInput.files);

            this.updateCaptureStatus();
            this.showImagePreview();

            this.closeCamera();

            this.showSuccessMessage('Profile photo captured successfully! Click "Submit" to complete registration.');

        } catch (error) {
            console.error('Error processing photo:', error);
            alert('Error processing photo. Please try again.');
        }
    }

    showImagePreview() {
        // Hide capture button container
        if (this.captureButtonContainer) {
            this.captureButtonContainer.style.display = 'none';
        }

        // Show preview section
        if (this.previewSection) {
            this.previewSection.style.display = 'block';
        }

        // Set the preview image
        if (this.uploadedPhotoPreview && this.capturedImageData) {
            this.uploadedPhotoPreview.src = this.capturedImageData;
        }

        // Disable camera button
        if (this.cameraBtn) {
            this.cameraBtn.disabled = true;
            this.cameraBtn.innerHTML = '<i class="fas fa-check"></i> Photo Captured';
        }
    }

    viewPhoto() {
        const previewImg = document.getElementById('uploadedPhotoPreview');
        if (previewImg && previewImg.src) {
            // Create a modal to view the full image
            const modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.id = 'photoViewModal';
            modal.tabIndex = '-1';
            modal.innerHTML = `
                <div class="modal-dialog modal-lg modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-image"></i> Profile Photo Preview
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body text-center">
                            <img src="${previewImg.src}" alt="Profile photo" style="max-width: 100%; max-height: 500px; border-radius: 8px;">
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
            const viewModal = new bootstrap.Modal(modal);
            viewModal.show();

            // Clean up modal after it's hidden
            modal.addEventListener('hidden.bs.modal', () => {
                modal.remove();
            });
        }
    }

    removePhoto() {
        // Confirm removal
        const confirmed = confirm('Are you sure you want to remove this photo? You can capture another one.');
        if (!confirmed) return;

        // Clear file input
        if (this.fileInput) {
            this.fileInput.value = '';
            this.fileInput.files = new DataTransfer().files;
        }

        // Clear captured image data
        this.capturedImageData = null;

        // Hide preview section
        if (this.previewSection) {
            this.previewSection.style.display = 'none';
        }

        // Show capture button container
        if (this.captureButtonContainer) {
            this.captureButtonContainer.style.display = 'block';
        }

        // Re-enable camera button
        if (this.cameraBtn) {
            this.cameraBtn.disabled = false;
            this.cameraBtn.innerHTML = '<i class="fas fa-camera"></i> Capture with Camera';
        }

        this.showSuccessMessage('Photo removed. You can capture a new one.');
    }

    updateCaptureStatus() {
        if (this.statusDiv) {
            this.statusDiv.style.display = 'block';
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
        if (this.cameraView) {
            this.cameraView.classList.remove('active');
            this.cameraView.style.display = 'none';
        }
        if (this.previewView) {
            this.previewView.classList.remove('active');
            this.previewView.style.display = 'none';
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
        const fallback = this.fallback || document.getElementById('cameraFallback');
        if (fallback) {
            fallback.style.display = 'block';
            fallback.innerHTML = `<i class="fas fa-exclamation-triangle"></i> <strong>Camera not available.</strong> ${message}`;
        }
    }

    showInsecureError() {
        const fallback = this.fallback || document.getElementById('cameraFallback');
        if (fallback) {
            fallback.style.display = 'block';
            fallback.innerHTML = `
                <i class="fas fa-exclamation-triangle"></i>
                <strong>Camera requires a secure connection.</strong>
                Camera access only works on HTTPS or localhost (127.0.0.1).
                If you're accessing from another device on the network, please use HTTPS.
            `;
        }

        const cameraBtn = this.cameraBtn || document.getElementById('cameraBtn');
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
