/**
 * Trash Classification Application - Frontend JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const elements = {
        videoContainer: document.getElementById('videoContainer'),
        cameraPlaceholder: document.getElementById('cameraPlaceholder'),
        startCameraBtn: document.getElementById('startCameraBtn'),
        stopCameraBtn: document.getElementById('stopCameraBtn'),
        captureBtn: document.getElementById('captureBtnStatic'),
        cameraFeed: document.getElementById('cameraFeed'),
        className: document.getElementById('className'),
        confidenceValue: document.getElementById('confidenceValue'),
        confidencePercent: document.getElementById('confidencePercent'),
        uploadForm: document.getElementById('uploadForm'),
        uploadArea: document.getElementById('uploadArea'),
        imageUpload: document.getElementById('imageUpload'),
        imagePreview: document.getElementById('imagePreview'),
        uploadPreview: document.getElementById('uploadPreview'),
        removePreview: document.getElementById('removePreview'),
        resultIcon: document.getElementById('resultIcon'),
        resultTips: document.getElementById('resultTips')
    };

    // State variables
    let state = {
        isStreamActive: false,
        predictionInterval: null,
        isCaptureMode: false,
        capturedImageUrl: null,
        capturedClassName: null,
        isProcessingImage: false
    };

    /**
     * Update result display with icons and tips based on waste type
     * @param {string} className - The predicted waste class name
     */
    function updateResultDisplay(className) {
        // Default values
        let iconClass = 'fas fa-question-circle';
        let tipText = 'Unable to identify this type of waste.';
        let categoryGroup = '';
        
        // Classify waste by category
        switch(className.toLowerCase()) {
            case 'battery':
                iconClass = 'fas fa-skull-crossbones';
                tipText = 'Batteries are hazardous waste and should be collected at special collection points.';
                categoryGroup = 'Hazardous waste';
                break;
                
            case 'biological':
                iconClass = 'fas fa-leaf';
                tipText = 'Organic waste can be composted or processed into biogas.';
                categoryGroup = 'Organic waste';
                break;
                
            case 'cardboard':
            case 'paper':
                iconClass = 'fas fa-scroll';
                tipText = 'Paper and cardboard are recyclable. Fold them neatly and sort separately.';
                categoryGroup = 'Recyclable waste';
                break;
                
            case 'plastic':
                iconClass = 'fas fa-wine-bottle';
                tipText = 'Plastic is recyclable. Clean and flatten before disposal.';
                categoryGroup = 'Recyclable waste';
                break;
                
            case 'metal':
                iconClass = 'fas fa-cookie-bite';
                tipText = 'Metals are recyclable and can be recycled multiple times without losing quality.';
                categoryGroup = 'Recyclable waste';
                break;
                
            case 'brown-glass':
            case 'green-glass':
            case 'white-glass':
                iconClass = 'fas fa-glass-martini-alt';
                tipText = 'Glass is non-recyclable. Wrap carefully to avoid injury.';
                categoryGroup = 'Non-recyclable waste';
                break;
                
            case 'trash':
                iconClass = 'fas fa-trash-alt';
                tipText = 'Mixed waste belongs to the non-recyclable category.';
                categoryGroup = 'Non-recyclable waste';
                break;
        }
        
        // Update icon and tips
        elements.resultIcon.innerHTML = `<i class="${iconClass}"></i>`;
        elements.resultTips.innerHTML = `
            <div class="category-badge mb-2">
                <span class="badge ${getCategoryBadgeClass(categoryGroup)}">${categoryGroup || 'Unidentified'}</span>
            </div>
            <p><i class="fas fa-lightbulb me-1"></i>${tipText}</p>
        `;
    }
    
    /**
     * Get CSS class for category badge
     * @param {string} category - Waste category
     * @returns {string} - CSS class name
     */
    function getCategoryBadgeClass(category) {
        switch(category) {
            case 'Organic waste': return 'bg-success';
            case 'Recyclable waste': return 'bg-primary';
            case 'Non-recyclable waste': return 'bg-warning text-dark';
            case 'Hazardous waste': return 'bg-danger';
            default: return 'bg-secondary';
        }
    }

    /**
     * Start camera stream
     */
    function startCamera() {
        elements.videoContainer.classList.remove('hidden');
        elements.cameraPlaceholder.style.display = 'none';
        // Reset src to avoid caching issues
        elements.cameraFeed.src = "video_feed?" + new Date().getTime();
        
        state.isStreamActive = true;
        elements.startCameraBtn.disabled = true;
        elements.stopCameraBtn.disabled = false;
        elements.captureBtn.disabled = false;
        
        // Exit capture view mode if active
        if (state.isCaptureMode) {
            exitCaptureViewMode();
        }
        
        // Start prediction if not processing an image
        if (!state.isProcessingImage) {
            startPredictionUpdates();
        }
    }

    /**
     * Stop camera stream
     */
    function stopCamera() {
        fetch('/stop_camera')
            .then(response => response.json())
            .then(data => {
                elements.videoContainer.classList.add('hidden');
                elements.cameraPlaceholder.style.display = 'flex';
                state.isStreamActive = false;
                elements.startCameraBtn.disabled = false;
                elements.stopCameraBtn.disabled = true;
                elements.captureBtn.disabled = true;
                
                stopPredictionUpdates();
            })
            .catch(error => {
                console.error('Error stopping camera:', error);
                alert('Failed to stop camera. Please try again.');
            });
    }

    /**
     * Update prediction from server
     */
    function updatePrediction() {
        if (!state.isStreamActive || state.isCaptureMode || state.isProcessingImage) return;
        
        fetch('/get_prediction')
            .then(response => response.json())
            .then(data => {
                elements.className.textContent = data.class_name;
                elements.confidenceValue.style.width = data.confidence + '%';
                elements.confidencePercent.textContent = data.confidence + '%';
                updateResultDisplay(data.class_name);
            })
            .catch(error => console.error('Error fetching prediction:', error));
    }

    /**
     * Start periodic prediction updates
     */
    function startPredictionUpdates() {
        updatePrediction();
        state.predictionInterval = setInterval(updatePrediction, 1000);
    }

    /**
     * Stop prediction updates
     */
    function stopPredictionUpdates() {
        clearInterval(state.predictionInterval);
    }

    /**
     * Capture image from camera
     */
    function captureImage() {
        if (!state.isStreamActive) return;
        
        state.isProcessingImage = true;
        stopPredictionUpdates();
        
        // Create flash effect
        const flashOverlay = document.createElement('div');
        flashOverlay.style.position = 'absolute';
        flashOverlay.style.top = '0';
        flashOverlay.style.left = '0';
        flashOverlay.style.right = '0';
        flashOverlay.style.bottom = '0';
        flashOverlay.style.backgroundColor = 'white';
        flashOverlay.style.opacity = '0.8';
        flashOverlay.style.zIndex = '10';
        flashOverlay.style.pointerEvents = 'none';
        
        elements.videoContainer.appendChild(flashOverlay);
        
        // Sound effect
        const shutterSound = new Audio('https://freesound.org/data/previews/202/202044_1038806-lq.mp3');
        shutterSound.play().catch(() => {});
        
        // Animation
        setTimeout(() => {
            flashOverlay.style.opacity = '0';
            setTimeout(() => {
                elements.videoContainer.removeChild(flashOverlay);
            }, 300);
        }, 100);
        
        // Send capture request to server
        fetch('/capture_image', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('Error capturing image: ' + data.error);
                state.isProcessingImage = false;
                return;
            }
            
            // Save classification info
            state.capturedClassName = data.class_name;
            
            // Update UI with results
            elements.className.textContent = data.class_name;
            elements.confidenceValue.style.width = data.confidence + '%';
            elements.confidencePercent.textContent = data.confidence + '%';
            updateResultDisplay(data.class_name);
            
            // Enter capture view mode
            enterCaptureViewMode(data.image_path);
        })
        .catch(error => {
            console.error('Error during image capture:', error);
            alert('An error occurred while capturing the image');
            state.isProcessingImage = false;
        });
    }

    /**
     * Enter capture view mode after taking a photo
     * @param {string} imagePath - Path to the captured image
     */
    function enterCaptureViewMode(imagePath) {
        state.isCaptureMode = true;
        state.capturedImageUrl = imagePath;
        
        stopPredictionUpdates();
        
        // Save current camera feed source
        const originalCameraFeedSrc = elements.cameraFeed.src;
        
        // Change image source to captured image
        elements.cameraFeed.src = imagePath;
        
        // Create return button
        const returnButton = createButton({
            className: 'btn btn-info capture-return-btn',
            innerHTML: '<i class="fas fa-arrow-left me-2"></i>Return to camera',
            style: {
                position: 'absolute',
                bottom: '10px',
                left: '10px',
                zIndex: '15'
            }
        });
        
        // Create download button
        const downloadButton = createButton({
            className: 'btn btn-secondary capture-download-btn',
            innerHTML: '<i class="fas fa-download me-2"></i>Download',
            style: {
                position: 'absolute',
                bottom: '10px',
                right: '10px',
                zIndex: '15'
            }
        });
        
        // Create controls overlay
        const controlsOverlay = document.createElement('div');
        controlsOverlay.className = 'capture-controls-overlay';
        Object.assign(controlsOverlay.style, {
            position: 'absolute',
            top: '0',
            left: '0',
            right: '0',
            bottom: '0',
            backgroundColor: 'rgba(0,0,0,0.2)',
            zIndex: '10',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center'
        });
        
        // Add elements to container
        elements.videoContainer.appendChild(controlsOverlay);
        elements.videoContainer.appendChild(returnButton);
        elements.videoContainer.appendChild(downloadButton);
        
        // Update button state
        elements.captureBtn.disabled = true;
        
        // Return button handler
        returnButton.addEventListener('click', function() {
            elements.cameraFeed.src = originalCameraFeedSrc;
            exitCaptureViewMode();
            
            state.isProcessingImage = false;
            if (state.isStreamActive) {
                startPredictionUpdates();
            }
        });
        
        // Download button handler
        downloadButton.addEventListener('click', function() {
            const fileName = `${state.capturedClassName || elements.className.textContent}_${new Date().getTime()}.jpg`;
            const a = document.createElement('a');
            a.href = imagePath;
            a.download = fileName;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        });
        
        // Create manual class selection UI
        const manualClassContainer = document.createElement('div');
        manualClassContainer.className = 'manual-class-selection';
        Object.assign(manualClassContainer.style, {
            position: 'absolute',
            top: '10px',
            left: '10px',
            right: '10px',
            zIndex: '15',
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            padding: '10px',
            borderRadius: '5px',
            boxShadow: '0 2px 5px rgba(0,0,0,0.2)'
        });
        
        manualClassContainer.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-2">
                <label class="fw-bold mb-0">Manual waste type selection:</label>
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="manualClassSwitch">
                    <label class="form-check-label" for="manualClassSwitch">Select manually</label>
                </div>
            </div>
            <select class="form-select" id="manualClassSelect" disabled>
                <option value="battery">Battery & Accumulators</option>
                <option value="biological">Organic Waste</option>
                <option value="brown-glass">Brown Glass</option>
                <option value="cardboard">Cardboard</option>
                <option value="green-glass">Green Glass</option>
                <option value="metal">Metal</option>
                <option value="paper">Paper</option>
                <option value="plastic">Plastic</option>
                <option value="trash">Other Waste</option>
                <option value="white-glass">White Glass</option>
            </select>
        `;
        
        elements.videoContainer.appendChild(manualClassContainer);
        
        // Manual class selection handlers
        const manualClassSwitch = manualClassContainer.querySelector('#manualClassSwitch');
        const manualClassSelect = manualClassContainer.querySelector('#manualClassSelect');
        
        // Set default selection to detected class
        if (state.capturedClassName) {
            const options = manualClassSelect.options;
            for (let i = 0; i < options.length; i++) {
                if (options[i].value === state.capturedClassName.toLowerCase()) {
                    manualClassSelect.selectedIndex = i;
                    break;
                }
            }
        }
        
        // Toggle manual selection
        manualClassSwitch.addEventListener('change', function() {
            manualClassSelect.disabled = !this.checked;
            
            if (this.checked) {
                const selectedClass = manualClassSelect.options[manualClassSelect.selectedIndex].text;
                elements.className.textContent = selectedClass + " (manually selected)";
                state.capturedClassName = manualClassSelect.value;
                updateResultDisplay(state.capturedClassName);
            } else {
                elements.className.textContent = state.capturedClassName || "Unknown";
                updateResultDisplay(state.capturedClassName);
            }
        });
        
        // Handle selection change
        manualClassSelect.addEventListener('change', function() {
            if (manualClassSwitch.checked) {
                const selectedClass = this.options[this.selectedIndex].text;
                elements.className.textContent = selectedClass + " (manually selected)";
                state.capturedClassName = this.value;
                updateResultDisplay(state.capturedClassName);
            }
        });
    }
    
    /**
     * Exit capture view mode
     */
    function exitCaptureViewMode() {
        state.isCaptureMode = false;
        state.capturedImageUrl = null;
        
        // Remove added UI elements
        const returnBtn = elements.videoContainer.querySelector('.capture-return-btn');
        const downloadBtn = elements.videoContainer.querySelector('.capture-download-btn');
        const overlay = elements.videoContainer.querySelector('.capture-controls-overlay');
        const manualClassContainer = elements.videoContainer.querySelector('.manual-class-selection');
        
        if (returnBtn) elements.videoContainer.removeChild(returnBtn);
        if (downloadBtn) elements.videoContainer.removeChild(downloadBtn);
        if (overlay) elements.videoContainer.removeChild(overlay);
        if (manualClassContainer) elements.videoContainer.removeChild(manualClassContainer);
        
        // Re-enable capture button
        if (state.isStreamActive) {
            elements.captureBtn.disabled = false;
        }
    }

    /**
     * Show manual class selection UI for uploaded images
     */
    function showManualClassForUpload() {
        // Remove existing UI if present
        const existingManualClass = document.querySelector('.upload-manual-class');
        if (existingManualClass) {
            existingManualClass.remove();
        }
        
        // Create new UI
        const manualClassDiv = document.createElement('div');
        manualClassDiv.className = 'upload-manual-class mt-3';
        
        manualClassDiv.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-2">
                <label class="fw-bold mb-0">Manual waste type selection:</label>
                <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="uploadManualSwitch">
                    <label class="form-check-label" for="uploadManualSwitch">Select manually</label>
                </div>
            </div>
            <select class="form-select" id="uploadManualSelect" disabled>
                <option value="battery">Battery & Accumulators</option>
                <option value="biological">Organic Waste</option>
                <option value="brown-glass">Brown Glass</option>
                <option value="cardboard">Cardboard</option>
                <option value="green-glass">Green Glass</option>
                <option value="metal">Metal</option>
                <option value="paper">Paper</option>
                <option value="plastic">Plastic</option>
                <option value="trash">Other Waste</option>
                <option value="white-glass">White Glass</option>
            </select>
            <div class="d-flex justify-content-between mt-3">
                <button type="button" class="btn btn-secondary btn-sm" id="cancelUploadBtn">
                    <i class="fas fa-times me-1"></i>Cancel
                </button>
                <button type="button" class="btn btn-success btn-sm" id="downloadUploadBtn">
                    <i class="fas fa-download me-1"></i>Download
                </button>
            </div>
        `;
        
        // Insert after upload form
        elements.uploadForm.insertAdjacentElement('afterend', manualClassDiv);
        
        // Set default selection
        const uploadManualSelect = document.getElementById('uploadManualSelect');
        if (state.capturedClassName) {
            const options = uploadManualSelect.options;
            for (let i = 0; i < options.length; i++) {
                if (options[i].value === state.capturedClassName.toLowerCase()) {
                    uploadManualSelect.selectedIndex = i;
                    break;
                }
            }
        }
        
        // Setup event handlers
        const uploadManualSwitch = document.getElementById('uploadManualSwitch');
        const cancelUploadBtn = document.getElementById('cancelUploadBtn');
        const downloadUploadBtn = document.getElementById('downloadUploadBtn');
        
        uploadManualSwitch.addEventListener('change', function() {
            uploadManualSelect.disabled = !this.checked;
            
            if (this.checked) {
                const selectedClass = uploadManualSelect.options[uploadManualSelect.selectedIndex].text;
                elements.className.textContent = selectedClass + " (manually selected)";
                state.capturedClassName = uploadManualSelect.value;
                updateResultDisplay(state.capturedClassName);
            } else {
                elements.className.textContent = state.capturedClassName || "Unknown";
                updateResultDisplay(state.capturedClassName);
            }
        });
        
        uploadManualSelect.addEventListener('change', function() {
            if (uploadManualSwitch.checked) {
                const selectedClass = this.options[this.selectedIndex].text;
                elements.className.textContent = selectedClass + " (manually selected)";
                state.capturedClassName = this.value;
                updateResultDisplay(state.capturedClassName);
            }
        });
        
        cancelUploadBtn.addEventListener('click', function() {
            manualClassDiv.remove();
            
            state.isProcessingImage = false;
            if (state.isStreamActive) {
                startPredictionUpdates();
            }
            
            // Reset upload form
            elements.removePreview.click();
        });
        
        downloadUploadBtn.addEventListener('click', function() {
            const file = elements.imageUpload.files[0];
            if (file) {
                const fileExt = file.name.split('.').pop();
                
                const currentClassName = uploadManualSwitch.checked ? 
                    uploadManualSelect.value : state.capturedClassName;
                const fileName = `${currentClassName}_${new Date().getTime()}.${fileExt}`;
                
                const url = URL.createObjectURL(file);
                const a = document.createElement('a');
                a.href = url;
                a.download = fileName;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }
        });
    }

    /**
     * Display image preview after selection/drag-and-drop
     * @param {File} file - Image file to preview
     */
    function displayImagePreview(file) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            elements.uploadPreview.src = e.target.result;
            elements.uploadArea.classList.add('d-none');
            elements.imagePreview.classList.remove('d-none');
        };
        
        reader.readAsDataURL(file);
    }

    /**
     * Create button helper function
     * @param {Object} options - Button options
     * @returns {HTMLButtonElement} - Button element
     */
    function createButton(options) {
        const button = document.createElement('button');
        if (options.className) button.className = options.className;
        if (options.innerHTML) button.innerHTML = options.innerHTML;
        
        if (options.style) {
            Object.keys(options.style).forEach(key => {
                button.style[key] = options.style[key];
            });
        }
        
        return button;
    }

    // Event Listeners
    
    // Camera controls
    elements.startCameraBtn.addEventListener('click', startCamera);
    elements.stopCameraBtn.addEventListener('click', stopCamera);
    elements.captureBtn.addEventListener('click', captureImage);

    // Upload area click/drag-and-drop
    elements.uploadArea.addEventListener('click', function() {
        elements.imageUpload.click();
    });

    elements.uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.classList.add('upload-area-active');
    });

    elements.uploadArea.addEventListener('dragleave', function() {
        this.classList.remove('upload-area-active');
    });

    elements.uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        this.classList.remove('upload-area-active');
        
        if (e.dataTransfer.files.length) {
            elements.imageUpload.files = e.dataTransfer.files;
            displayImagePreview(e.dataTransfer.files[0]);
        }
    });

    // Image upload handling
    elements.imageUpload.addEventListener('change', function() {
        if (this.files.length) {
            displayImagePreview(this.files[0]);
        }
    });

    elements.removePreview.addEventListener('click', function() {
        elements.imageUpload.value = '';
        elements.imagePreview.classList.add('d-none');
        elements.uploadArea.classList.remove('d-none');
        
        if (state.isProcessingImage) {
            state.isProcessingImage = false;
            if (state.isStreamActive) {
                startPredictionUpdates();
            }
        }
    });

    // Upload form submission
    elements.uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const file = elements.imageUpload.files[0];
        
        if (!file) {
            alert('Please select an image to upload');
            return;
        }
        
        state.isProcessingImage = true;
        stopPredictionUpdates();
        
        const formData = new FormData();
        formData.append('file', file);
        
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            state.capturedClassName = data.class_name;
            elements.className.textContent = data.class_name;
            elements.confidenceValue.style.width = data.confidence + '%';
            elements.confidencePercent.textContent = data.confidence + '%';
            updateResultDisplay(data.class_name);
            
            showManualClassForUpload();
        })
        .catch(error => {
            console.error('Error uploading image:', error);
            state.isProcessingImage = false;
            if (state.isStreamActive) {
                startPredictionUpdates();
            }
        });
    });

    // Handle page unload
    window.addEventListener('beforeunload', function() {
        if (state.isStreamActive) {
            fetch('/stop_camera').catch(err => console.log('Error stopping camera on page unload'));
        }
    });
});