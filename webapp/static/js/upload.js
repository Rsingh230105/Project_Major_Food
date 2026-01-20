// Image Upload Handler - Single Click Fix
document.addEventListener('DOMContentLoaded', function() {
    const uploadSections = document.querySelectorAll('.image-upload-section');
    
    uploadSections.forEach(section => {
        const dropZone = section.querySelector('.drop-zone');
        const fileInput = section.querySelector('input[type="file"]');
        const uploadContent = section.querySelector('.upload-content');
        const previewContainer = section.querySelector('.preview-container');
        const previewImage = section.querySelector('.preview-image');
        const removeBtn = section.querySelector('.remove-image');
        
        // Single click to upload
        dropZone.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            fileInput.click();
        });
        
        // File selection handler
        fileInput.addEventListener('change', function(e) {
            const file = this.files[0];
            if (file && file.type.startsWith('image/')) {
                displayPreview(file);
            }
        });
        
        // Display preview
        function displayPreview(file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                previewImage.src = e.target.result;
                uploadContent.classList.add('hidden');
                previewContainer.classList.remove('hidden');
                dropZone.classList.add('border-green-500', 'bg-green-50');
            };
            reader.readAsDataURL(file);
        }
        
        // Remove image
        removeBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            fileInput.value = '';
            previewImage.src = '';
            uploadContent.classList.remove('hidden');
            previewContainer.classList.add('hidden');
            dropZone.classList.remove('border-green-500', 'bg-green-50');
        });
        
        // Drag and drop
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });
        
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file && file.type.startsWith('image/')) {
                fileInput.files = e.dataTransfer.files;
                displayPreview(file);
            }
        });
    });
    
    // Form submission
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const brandName = document.getElementById('brandName').value.trim();
            
            // Client-side validation
            if (!brandName) {
                alert('Please enter a brand name.');
                document.getElementById('brandName').focus();
                return;
            }
            
            if (brandName.length < 2) {
                alert('Brand name must be at least 2 characters long.');
                document.getElementById('brandName').focus();
                return;
            }
            
            // Check for required images (front and back)
            const frontInput = document.querySelector('input[data-view="front"]');
            const backInput = document.querySelector('input[data-view="back"]');
            
            if (!frontInput.files.length) {
                alert('Please upload a front view image (required).');
                frontInput.click();
                return;
            }
            
            if (!backInput.files.length) {
                alert('Please upload a back view image (required).');
                backInput.click();
                return;
            }
            
            // Validate file types and sizes
            const allInputs = document.querySelectorAll('input[type="file"]');
            for (let input of allInputs) {
                if (input.files.length > 0) {
                    const file = input.files[0];
                    if (!file.type.startsWith('image/')) {
                        alert('Please upload only image files.');
                        return;
                    }
                    if (file.size > 5 * 1024 * 1024) { // 5MB
                        alert('File size must be less than 5MB.');
                        return;
                    }
                }
            }
            
            const formData = new FormData();
            
            formData.append('brand_name', brandName);
            
            // Collect all uploaded images
            const fileInputs = document.querySelectorAll('input[type="file"]');
            const viewTypes = document.querySelectorAll('input[name="view_types[]"]');
            
            let hasImages = false;
            fileInputs.forEach((input, index) => {
                if (input.files.length > 0) {
                    formData.append('images[]', input.files[0]);
                    formData.append('view_types[]', viewTypes[index].value);
                    hasImages = true;
                }
            });
            
            if (!hasImages) {
                alert('Please upload at least front and back view images');
                return;
            }
            
            // Show loading
            const submitBtn = uploadForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Analyzing...';
            
            try {
                const response = await fetch('/api/detect/', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    }
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    // Show success message
                    showNotification('Analysis Complete!', 'success');
                    // Redirect to dashboard or show results
                    setTimeout(() => {
                        window.location.href = '/dashboard/';
                    }, 1500);
                } else {
                    showNotification(result.error || 'Upload failed', 'error');
                }
            } catch (error) {
                showNotification('Network error. Please try again.', 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }
        });
    }
    
    // Notification function
    function showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 px-6 py-4 rounded-lg shadow-lg z-50 ${
            type === 'success' ? 'bg-green-500' : 'bg-red-500'
        } text-white transform transition-all duration-300`;
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} mr-3"></i>
                <span>${message}</span>
            </div>
        `;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.transform = 'translateX(400px)';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
});