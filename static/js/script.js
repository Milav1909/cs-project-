document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const fileInput = document.getElementById('fileInput');
    const browseBtn = document.getElementById('browseBtn');
    const dropZone = document.getElementById('dropZone');
    const uploadArea = document.getElementById('uploadArea');
    const uploadProgress = document.getElementById('uploadProgress');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const uploadSuccess = document.getElementById('uploadSuccess');
    const shareLink = document.getElementById('shareLink');
    const copyBtn = document.getElementById('copyBtn');
    const newUploadBtn = document.getElementById('newUploadBtn');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const qrCodeContainer = document.getElementById('qrCodeContainer');

    // Initial setup
    uploadProgress.style.display = 'none';
    uploadSuccess.style.display = 'none';
    loadingOverlay.classList.remove('active');

    // Single button for browse and upload
    browseBtn.addEventListener('click', function() {
        fileInput.click();
    });

    // File input change
    fileInput.addEventListener('change', function(event) {
        if (this.files && this.files.length > 0) {
            console.log('Files selected:', this.files.length);
            handleFiles(this.files);
        }
    });

    // Drag and drop events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
        dropZone.classList.add('active');
    }

    function unhighlight() {
        dropZone.classList.remove('active');
    }

    dropZone.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    // Handle files
    function handleFiles(files) {
        if (files.length === 0) return;

        const formData = new FormData();
        formData.append('file', files[0]);

        // Show upload progress
        uploadProgress.style.display = 'block';
        dropZone.style.display = 'none';
        progressBar.style.width = '0%';
        progressText.textContent = '0%';

        // Create XMLHttpRequest
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/upload', true);

        // Progress tracking
        xhr.upload.onprogress = function(e) {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                progressBar.style.width = percentComplete + '%';
                progressText.textContent = Math.round(percentComplete) + '%';
            }
        };

        xhr.onload = function() {
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        handleUploadSuccess(response);
                    } else {
                        handleUploadError(response.error || 'Upload failed');
                    }
                } catch (e) {
                    handleUploadError('Invalid server response');
                }
            } else {
                try {
                    const response = JSON.parse(xhr.responseText);
                    handleUploadError(response.error || 'Upload failed');
                } catch (e) {
                    handleUploadError('Upload failed');
                }
            }
        };

        xhr.onerror = function() {
            handleUploadError('Network error occurred');
        };

        xhr.send(formData);
    }

    function handleUploadSuccess(response) {
        // Hide progress, show success
        uploadProgress.style.display = 'none';
        uploadSuccess.style.display = 'block';

        // Update share link
        shareLink.value = response.share_url;

        // Display QR code
        if (response.qr_code) {
            const qrCodeImg = document.createElement('img');
            qrCodeImg.src = 'data:image/png;base64,' + response.qr_code;
            qrCodeContainer.innerHTML = '';
            qrCodeContainer.appendChild(qrCodeImg);
        }
    }

    function handleUploadError(message) {
        uploadProgress.style.display = 'none';
        dropZone.style.display = 'block';
        alert(message || 'Upload failed. Please try again.');
    }

    // Copy share link
    copyBtn.addEventListener('click', function() {
        shareLink.select();
        document.execCommand('copy');
        
        // Show copied feedback
        const originalText = this.textContent;
        this.textContent = 'Copied!';
        setTimeout(() => {
            this.textContent = originalText;
        }, 2000);
    });

    // New upload button
    newUploadBtn.addEventListener('click', function() {
        // Reset the form
        fileInput.value = '';
        uploadSuccess.style.display = 'none';
        dropZone.style.display = 'block';
        qrCodeContainer.innerHTML = '';
    });
});