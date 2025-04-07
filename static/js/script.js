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

    // Load QR Code library
    loadQRCodeLibrary();

    // Show loading overlay initially
    loadingOverlay.classList.add('active');
    
    // Simulate page loading
    setTimeout(() => {
        loadingOverlay.classList.remove('active');
    }, 1500);

    // Single button for browse and upload
    browseBtn.addEventListener('click', function() {
        fileInput.click();
    });

    // File input change - This is the critical event handler
    fileInput.addEventListener('change', function(event) {
        // Ensure we have files selected
        if (this.files && this.files.length > 0) {
            console.log('Files selected:', this.files.length);
            // Validate file size before proceeding
            if (validateFileSize(this.files)) {
                handleFiles(this.files);
            } else {
                // Reset the file input if validation fails
                this.value = '';
            }
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
        if (validateFileSize(files)) {
            handleFiles(files);
        }
    }

    // Handle files
    function handleFiles(files) {
        if (files.length === 0) return;

        const formData = new FormData();
        formData.append('file', files[0]);

        // Show loading overlay
        loadingOverlay.classList.add('active');

        // Show upload progress
        uploadProgress.style.display = 'block';
        dropZone.style.display = 'none';

        // Create XMLHttpRequest
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/upload', true);

        // Progress tracking
        xhr.upload.onprogress = function(e) {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                progressBar.style.width = `${percentComplete}%`;
                progressText.textContent = `${Math.round(percentComplete)}%`;
            }
        };

        xhr.onload = function() {
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                handleUploadSuccess(response);
            } else {
                handleUploadError();
            }
        };

        xhr.onerror = handleUploadError;
        xhr.send(formData);
    }

    function handleUploadSuccess(response) {
        // Hide loading overlay
        loadingOverlay.classList.remove('active');

        // Hide progress, show success
        uploadProgress.style.display = 'none';
        uploadSuccess.style.display = 'block';

        // Update share link
        shareLink.value = response.share_url;

        // Display QR code
        const qrCodeImg = document.createElement('img');
        qrCodeImg.src = 'data:image/png;base64,' + response.qr_code;
        qrCodeContainer.innerHTML = '';
        qrCodeContainer.appendChild(qrCodeImg);
    }

    function handleUploadError() {
        loadingOverlay.classList.remove('active');
        uploadProgress.style.display = 'none';
        alert('Upload failed. Please try again.');
        dropZone.style.display = 'block';
    }

    // Generate QR Code
    function generateQRCode(url) {
        if (typeof QRCode !== 'undefined' && qrCodeContainer) {
            // Clear previous QR code
            qrCodeContainer.innerHTML = '';
            
            // Generate new QR code
            new QRCode(qrCodeContainer, {
                text: url,
                width: 128,
                height: 128,
                colorDark: "#000000",
                colorLight: "#ffffff",
                correctLevel: QRCode.CorrectLevel.H
            });
            
            qrCodeContainer.style.display = 'block';
        } else {
            console.error('QR Code library not loaded or container not found');
        }
    }

    // Load QR Code library dynamically
    function loadQRCodeLibrary() {
        if (!window.QRCode) {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/qrcodejs@1.0.0/qrcode.min.js';
            script.async = true;
            script.onload = function() {
                console.log('QR Code library loaded');
            };
            script.onerror = function() {
                console.error('Failed to load QR Code library');
            };
            document.head.appendChild(script);
        }
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
        uploadSuccess.style.display = 'none';
        dropZone.style.display = 'block';
        qrCodeContainer.style.display = 'none';
        fileInput.value = '';
    });

    // Language selector
    const languageSelector = document.getElementById('language');
    if (languageSelector) {
        languageSelector.addEventListener('change', function() {
            // Simulate language change
            loadingOverlay.classList.add('active');
            setTimeout(() => {
                loadingOverlay.classList.remove('active');
            }, 1000);
        });
    }

    // Simulate file size validation
    function validateFileSize(files) {
        const maxSize = 2 * 1024 * 1024 * 1024; // 2GB
        for (let i = 0; i < files.length; i++) {
            if (files[i].size > maxSize) {
                alert(`File ${files[i].name} exceeds the 2GB limit.`);
                return false;
            }
        }
        return true;
    }
});