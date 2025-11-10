document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('uploadForm');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const dropZones = document.querySelectorAll('.drop-zone');
    const resultSection = document.getElementById('resultSection');
    let uploadedFiles = new Map();

    // Initialize the button state
    function updateSubmitButton() {
        const requiredInputs = document.querySelectorAll('input[required]');
        const allFilled = Array.from(requiredInputs).every(input => {
            if (input.type === 'file') {
                return uploadedFiles.has(input.dataset.view);
            }
            return input.value.trim() !== '';
        });
        analyzeBtn.disabled = !allFilled;
    }

    // Handle drag and drop
    dropZones.forEach(zone => {
        const fileInput = zone.querySelector('input[type="file"]');
        const previewContainer = zone.querySelector('.preview-container');
        const previewImage = previewContainer?.querySelector('.preview-image');
        const uploadContent = zone.querySelector('.upload-content');
        const removeButton = zone.querySelector('.remove-image');
        const view = fileInput.dataset.view;

        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('dragover');
        });

        zone.addEventListener('dragleave', () => {
            zone.classList.remove('dragover');
        });

        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file && file.type.startsWith('image/')) {
                handleFile(file, view);
            }
        });

        // Click to upload
        zone.addEventListener('click', () => {
            if (!uploadedFiles.has(view)) {
                fileInput.click();
            }
        });

        // File input change
        fileInput.addEventListener('change', () => {
            const file = fileInput.files[0];
            if (file) {
                handleFile(file, view);
            }
        });

        // Remove image
        if (removeButton) {
            removeButton.addEventListener('click', (e) => {
                e.stopPropagation();
                uploadedFiles.delete(view);
                fileInput.value = '';
                previewContainer.classList.add('hidden');
                uploadContent.classList.remove('hidden');
                updateSubmitButton();
            });
        }

        function handleFile(file, view) {
            if (file && file.type.startsWith('image/')) {
                uploadedFiles.set(view, file);
                const reader = new FileReader();
                reader.onload = (e) => {
                    previewImage.src = e.target.result;
                    previewContainer.classList.remove('hidden');
                    uploadContent.classList.add('hidden');
                };
                reader.readAsDataURL(file);
                updateSubmitButton();
            }
        }
    });

    // Form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Show loading state
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Analyzing...';
        
        const formData = new FormData();
        formData.append('brand_name', document.getElementById('brandName').value);
        
        // Append files with their view types
        uploadedFiles.forEach((file, view) => {
            formData.append('images', file);
            formData.append('view_types', view);
        });

        try {
            const response = await fetch('/detect/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });

            const result = await response.json();
            
            // Show results section
            resultSection.classList.remove('hidden');
            const resultContent = document.createElement('div');
            resultContent.innerHTML = `
                <div class="bg-white p-6 rounded-lg shadow-lg">
                    <h4 class="text-lg font-semibold mb-4">Analysis Complete</h4>
                    <div class="space-y-4">
                        <div class="flex items-center">
                            <span class="text-${result.is_fake ? 'red' : 'green'}-500 font-bold text-xl mr-2">
                                ${result.is_fake ? 'FAKE' : 'AUTHENTIC'}
                            </span>
                            <p class="text-gray-700">${result.message}</p>
                        </div>
                        <div class="text-sm text-gray-600">
                            <p>Confidence Score: ${(result.confidence * 100).toFixed(2)}%</p>
                            <p>Processing Time: ${result.processing_time.toFixed(2)}s</p>
                        </div>
                    </div>
                </div>
            `;
            
            resultSection.appendChild(resultContent);
            
            // Scroll to results
            resultSection.scrollIntoView({ behavior: 'smooth' });

        } catch (error) {
            console.error('Error:', error);
            // Show error message
            const errorDiv = document.createElement('div');
            errorDiv.className = 'text-red-500 mt-4';
            errorDiv.textContent = 'An error occurred during analysis. Please try again.';
            form.appendChild(errorDiv);
        } finally {
            // Reset button state
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = 'Analyze All Images';
        }
    });

    // Initial button state check
    updateSubmitButton();
});