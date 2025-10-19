document.addEventListener('DOMContentLoaded', function() {
    // ===== CSRF Token =====
    function getCsrfToken() {
        return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    }

    // ===== ADD LOCATION =====
    const addLocationForm = document.getElementById('add-location-form');
    const dropZone = document.getElementById('location-image-dropzone');
    const previewContainer = document.getElementById('location-image-preview');
    const fileInput = document.getElementById('location-image');
    let imageFiles = [];

    // Keyword sets management for add location
    const locationKeywordsContainer = document.getElementById('location-keywords-container');
    const addLocationKeywordSetBtn = document.getElementById('add-location-keyword-set');

    function updateLocationKeywordSetButtons() {
        const keywordSets = locationKeywordsContainer.querySelectorAll('.keyword-set');
        keywordSets.forEach((set, index) => {
            const removeBtn = set.querySelector('.remove-keyword-set');
            if (keywordSets.length > 1) {
                removeBtn.style.display = 'inline-block';
            } else {
                removeBtn.style.display = 'none';
            }
        });
    }

    if (addLocationKeywordSetBtn) {
        addLocationKeywordSetBtn.addEventListener('click', () => {
            const newSet = document.createElement('div');
            newSet.className = 'keyword-set d-flex align-items-center mb-2';
            newSet.innerHTML = `
                <input type="text" class="form-control keyword-input" placeholder="e.g. library, main hall" required>
                <button type="button" class="btn btn-danger btn-sm ms-2 remove-keyword-set">×</button>
            `;
            locationKeywordsContainer.appendChild(newSet);
            updateLocationKeywordSetButtons();
        });
    }

    if (locationKeywordsContainer) {
        locationKeywordsContainer.addEventListener('click', (e) => {
            if (e.target.classList.contains('remove-keyword-set')) {
                e.target.closest('.keyword-set').remove();
                updateLocationKeywordSetButtons();
            }
        });
    }

    function updatePreviews(container, filesArray) {
        container.innerHTML = '';
        filesArray.forEach((file, idx) => {
            const wrapper = document.createElement('div');
            wrapper.className = 'image-preview-wrapper position-relative';
            wrapper.style.position = 'relative';
            wrapper.style.width = '100px';
            wrapper.style.height = '100px';
            wrapper.style.margin = '5px';

            const img = document.createElement('img');
            img.src = URL.createObjectURL(file);
            img.style.width = '100%';
            img.style.height = '100%';
            img.style.objectFit = 'cover';
            wrapper.appendChild(img);

            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.textContent = '×';
            removeBtn.className = 'remove-image-btn';
            removeBtn.style.position = 'absolute';
            removeBtn.style.top = '0';
            removeBtn.style.right = '0';
            removeBtn.style.background = 'rgba(255,0,0,0.8)';
            removeBtn.style.color = 'white';
            removeBtn.style.border = 'none';
            removeBtn.style.borderRadius = '50%';
            removeBtn.style.width = '20px';
            removeBtn.style.height = '20px';
            removeBtn.style.cursor = 'pointer';
            removeBtn.addEventListener('click', () => {
                filesArray.splice(idx, 1);
                updatePreviews(container, filesArray);
            });
            wrapper.appendChild(removeBtn);

            container.appendChild(wrapper);
        });
    }

    if (dropZone) {
        dropZone.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('dragover', e => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
        dropZone.addEventListener('drop', e => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            Array.from(e.dataTransfer.files)
                .filter(f => f.type.startsWith('image/'))
                .forEach(f => imageFiles.push(f));
            updatePreviews(previewContainer, imageFiles);
        });

        fileInput.addEventListener('change', e => {
            Array.from(e.target.files).forEach(f => imageFiles.push(f));
            updatePreviews(previewContainer, imageFiles);
            e.target.value = '';
        });
    }

    if (addLocationForm) {
        addLocationForm.addEventListener('submit', async e => {
            e.preventDefault();
            const keywordInputs = locationKeywordsContainer.querySelectorAll('.keyword-input');
            const keywords = Array.from(keywordInputs).map(input => input.value.trim().split(',').map(k => k.trim()).filter(k => k));
            const userType = document.getElementById('location-user-type').value;
            const description = document.getElementById('location-response').value.trim();
            if (keywords.length === 0 || !description) return alert('Please enter keywords and description.');
            if (imageFiles.length === 0) return alert('Please select at least one image.');

            // Note: Skipping category creation for locations to prevent creating files in user/guest databases

            const formData = new FormData();
            formData.append('keywords', JSON.stringify(keywords));
            formData.append('user_type', userType);
            formData.append('description', description);
            imageFiles.forEach(file => formData.append('images', file));

            try {
                const res = await fetch('/add_location', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': getCsrfToken() },
                    body: formData
                });
                const data = await res.json();
                if (data.status === 'success') location.reload();
                else alert(data.message || 'Failed to add location');
            } catch (err) {
                console.error(err);
                alert('Error uploading location.');
            }
        });
    }

    // ===== EDIT LOCATION =====
    function attachLocationEdit() {
        document.querySelectorAll('.edit-location').forEach(button => {
            button.addEventListener('click', () => {
                const locationId = button.dataset.id;
                const card = button.closest('.futuristic-card');

                // Get current data from the card
                let currentKeywords = [];
                try {
                    currentKeywords = JSON.parse(card.dataset.keywords || '[]');
                } catch (e) {
                    console.error('Failed to parse keywords for location edit:', e);
                    currentKeywords = [];
                }
                const descP = Array.from(card.querySelectorAll('p')).find(p => p.textContent.trim().startsWith('Description:'));
                const currentDesc = descP ? descP.textContent.replace('Description:', '').trim() : '';
                const currentUserType = card.dataset.userType || 'both';

                // Get all existing images from the DOM elements
                const existingImages = card.querySelectorAll('.location-images img, img.img-fluid.rounded.mb-3');
                const existingImagesData = Array.from(existingImages).map(img => ({
                    src: img.src || img.dataset.src,
                    type: 'img'
                }));

                // Create popup modal
                const locationModal = document.createElement('div');
                locationModal.className = 'edit-location-modal modal fade show';
                locationModal.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0,0,0,0.5);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 10002;
                `;

                // Create keyword sets container
                const keywordSetsContainer = document.createElement('div');

                // Normalize keywords: if flat array, wrap in array; if nested, use as is
                let keywordSets = [];
                if (currentKeywords.length > 0) {
                    if (Array.isArray(currentKeywords[0])) {
                        keywordSets = currentKeywords;
                    } else {
                        keywordSets = [currentKeywords];
                    }
                }

                if (keywordSets.length > 0) {
                    keywordSets.forEach((set, index) => {
                        const setValue = (Array.isArray(set) ? set.join(', ') : set);
                        const setDiv = document.createElement('div');
                        setDiv.className = 'keyword-set d-flex align-items-center mb-2';

                        const input = document.createElement('input');
                        input.type = 'text';
                        input.className = 'form-control keyword-input';
                        input.placeholder = 'e.g. library, main hall';
                        input.value = setValue;
                        input.required = true;
                        setDiv.appendChild(input);

                        const removeBtn = document.createElement('button');
                        removeBtn.type = 'button';
                        removeBtn.className = 'btn btn-danger btn-sm ms-2 remove-keyword-set';
                        if (keywordSets.length <= 1) {
                            removeBtn.style.display = 'none';
                        }
                        setDiv.appendChild(removeBtn);

                        keywordSetsContainer.appendChild(setDiv);
                    });
                } else {
                    const setDiv = document.createElement('div');
                    setDiv.className = 'keyword-set d-flex align-items-center mb-2';

                    const input = document.createElement('input');
                    input.type = 'text';
                    input.className = 'form-control keyword-input';
                    input.placeholder = 'e.g. library, main hall';
                    input.required = true;
                    setDiv.appendChild(input);

                    const removeBtn = document.createElement('button');
                    removeBtn.type = 'button';
                    removeBtn.className = 'btn btn-danger btn-sm ms-2 remove-keyword-set';
                    removeBtn.style.display = 'none';
                    setDiv.appendChild(removeBtn);

                    keywordSetsContainer.appendChild(setDiv);
                }

                locationModal.innerHTML = `
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Edit Location</h5>
                                <button type="button" class="btn-close" onclick="this.closest('.modal').remove()" style="background: none; border: none; font-size: 24px; color: #6c757d; cursor: pointer; position: absolute; top: 10px; right: 15px; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center;">&times;</button>
                            </div>
                            <div class="modal-body" style="overflow-y: auto; max-height: 70vh;">
                                <form id="edit-location-form-${locationId}">
                                    <div class="mb-3">
                                        <label class="form-label" title="Keyword sets that trigger this location response">Keyword Sets <i class="fas fa-info-circle"></i></label>
                                        <div id="edit-location-keywords-container-${locationId}"></div>
                                        <button type="button" class="btn btn-secondary btn-sm mt-2" id="add-edit-keyword-set-${locationId}">+ Add Keyword Set</button>
                                        <div class="form-text">Each set is comma-separated keywords. Multiple sets allow different combinations to trigger the same response.</div>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">User Type</label>
                                        <select class="form-control" id="edit-user-type-${locationId}" required>
                                            <option value="both" ${currentUserType === 'both' ? 'selected' : ''}>Both Users and Guests</option>
                                            <option value="user" ${currentUserType === 'user' ? 'selected' : ''}>Users Only</option>
                                            <option value="guest" ${currentUserType === 'guest' ? 'selected' : ''}>Guests Only</option>
                                        </select>
                                    </div>
                                    <div class="mb-3">
                                        <label class="form-label">Description</label>
                                        <textarea class="form-control" id="edit-description-${locationId}" rows="3" required>${currentDesc}</textarea>
                                    </div>
                                    ${existingImagesData.length > 0 ? `
                                    <div class="mb-3">
                                        <label class="form-label">Existing Images (Click X to remove)</label>
                                        <div id="existing-images-${locationId}" class="d-flex flex-wrap gap-2"></div>
                                    </div>
                                    ` : ''}
                                    <div class="mb-3">
                                        <label class="form-label">Add New Images</label>
                                        <input type="file" class="form-control" id="edit-images-${locationId}" accept="image/*" multiple>
                                        <div id="edit-images-preview-${locationId}" class="d-flex flex-wrap gap-2 mt-2"></div>
                                    </div>
                                </form>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" onclick="this.closest('.modal').remove()">Cancel</button>
                                <button type="button" class="btn btn-primary" id="save-edit-${locationId}">Save Changes</button>
                            </div>
                        </div>
                    </div>
                `;

                document.body.appendChild(locationModal);

                // Insert the keyword sets container into the modal
                const keywordsContainerPlaceholder = locationModal.querySelector(`#edit-location-keywords-container-${locationId}`);
                keywordsContainerPlaceholder.appendChild(keywordSetsContainer);

                // Allow closing modal by clicking outside
                locationModal.addEventListener('click', (e) => {
                    if (e.target === locationModal) {
                        locationModal.remove();
                    }
                });

                // Attach keyword set management for edit
                const editKeywordsContainer = locationModal.querySelector(`#edit-location-keywords-container-${locationId}`);
                const addEditKeywordSetBtn = locationModal.querySelector(`#add-edit-keyword-set-${locationId}`);

                function updateEditKeywordSetButtons() {
                    const keywordSets = editKeywordsContainer.querySelectorAll('.keyword-set');
                    keywordSets.forEach((set, index) => {
                        const removeBtn = set.querySelector('.remove-keyword-set');
                        if (keywordSets.length > 1) {
                            removeBtn.style.display = 'inline-block';
                        } else {
                            removeBtn.style.display = 'none';
                        }
                    });
                }

                if (addEditKeywordSetBtn) {
                    addEditKeywordSetBtn.addEventListener('click', () => {
                        const newSet = document.createElement('div');
                        newSet.className = 'keyword-set d-flex align-items-center mb-2';
                        newSet.innerHTML = `
                            <input type="text" class="form-control keyword-input" placeholder="e.g. library, main hall" required>
                            <button type="button" class="btn btn-danger btn-sm ms-2 remove-keyword-set">×</button>
                        `;
                        editKeywordsContainer.appendChild(newSet);
                        updateEditKeywordSetButtons();
                    });
                }

                if (editKeywordsContainer) {
                    editKeywordsContainer.addEventListener('click', (e) => {
                        if (e.target.classList.contains('remove-keyword-set')) {
                            e.target.closest('.keyword-set').remove();
                            updateEditKeywordSetButtons();
                        }
                    });
                }

                // Handle existing images display and removal
                const existingImagesContainer = locationModal.querySelector(`#existing-images-${locationId}`);
                const removedImages = new Set();

                if (existingImagesContainer) {
                    existingImagesData.forEach((img, index) => {
                        const wrapper = document.createElement('div');
                        wrapper.className = 'image-preview-wrapper position-relative';
                        wrapper.style.position = 'relative';
                        wrapper.style.width = '100px';
                        wrapper.style.height = '100px';
                        wrapper.style.margin = '5px';

                        const imgElement = document.createElement('img');
                        imgElement.src = img.src;
                        imgElement.style.width = '100%';
                        imgElement.style.height = '100%';
                        imgElement.style.objectFit = 'cover';

                        wrapper.appendChild(imgElement);

                        const removeBtn = document.createElement('button');
                        removeBtn.type = 'button';
                        removeBtn.textContent = '×';
                        removeBtn.className = 'remove-image-btn';
                        removeBtn.style.position = 'absolute';
                        removeBtn.style.top = '0';
                        removeBtn.style.right = '0';
                        removeBtn.style.background = 'rgba(255,0,0,0.8)';
                        removeBtn.style.color = 'white';
                        removeBtn.style.border = 'none';
                        removeBtn.style.borderRadius = '50%';
                        removeBtn.style.width = '20px';
                        removeBtn.style.height = '20px';
                        removeBtn.style.cursor = 'pointer';
                        removeBtn.title = 'Remove this image';

                        removeBtn.addEventListener('click', () => {
                            // Extract the path after '/static/' to match backend storage format
                            const url = new URL(img.src);
                            const relativeSrc = url.pathname.replace('/static/', '');
                            removedImages.add(relativeSrc);
                            wrapper.remove();
                        });

                        wrapper.appendChild(removeBtn);
                        existingImagesContainer.appendChild(wrapper);
                    });
                }

                // Handle new images preview
                const imagesInput = locationModal.querySelector(`#edit-images-${locationId}`);
                const previewContainer = locationModal.querySelector(`#edit-images-preview-${locationId}`);
                let newImageFiles = [];

                imagesInput.addEventListener('change', (e) => {
                    newImageFiles = Array.from(e.target.files);
                    updatePreviews(previewContainer, newImageFiles);
                });

                // Handle save
                locationModal.querySelector(`#save-edit-${locationId}`).addEventListener('click', async () => {
                    const keywordInputs = locationModal.querySelectorAll('.keyword-input');
                    const updatedKeywords = Array.from(keywordInputs).map(input => input.value.trim().split(',').map(k => k.trim()).filter(k => k));
                    const updatedUserType = locationModal.querySelector(`#edit-user-type-${locationId}`).value;
                    const updatedDesc = locationModal.querySelector(`#edit-description-${locationId}`).value.trim();

                    if (updatedKeywords.length === 0 || !updatedDesc) {
                        alert('Keywords and Description are required.');
                        return;
                    }

                    const formData = new FormData();
                    formData.append('keywords', JSON.stringify(updatedKeywords));
                    formData.append('user_type', updatedUserType);
                    formData.append('description', updatedDesc);
                    formData.append('removedImages', JSON.stringify(Array.from(removedImages)));
                    newImageFiles.forEach(file => formData.append('images', file));

                    try {
                        formData.append('csrf_token', getCsrfToken());
                        const res = await fetch(`/edit_location/${locationId}`, {
                            method: 'POST',
                            body: formData
                        });
                        const data = await res.json();
                        if (data.status === 'success') {
                            locationModal.remove();
                            location.reload();
                        } else {
                            alert(data.message || 'Failed to update location');
                        }
                    } catch (err) {
                        console.error(err);
                        alert('Error updating location.');
                    }
                });
            });
        });
    }

    attachLocationEdit();

    // ===== DELETE LOCATION =====
    document.querySelectorAll('.delete-location').forEach(btn => {
        btn.addEventListener('click', async () => {
            const locationId = btn.dataset.id;
            if (!confirm('Are you sure you want to delete this location?')) return;

            try {
                const response = await fetch('/delete_location', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
                    body: JSON.stringify({ id: locationId })
                });
                const data = await response.json();
                if (data.status === 'success') location.reload();
                else alert('Failed to delete location');
            } catch (error) {
                console.error(error);
                alert('Error deleting location');
            }
        });
    });

    // ===== SEARCH LOCATIONS =====
    const locationSearchInput = document.getElementById('location-search');
    const locationsContainer = document.getElementById('locations-container');
    let searchTimeout;

    if (locationSearchInput && locationsContainer) {
        function applyLocationSearch() {
            const searchValue = locationSearchInput.value.toLowerCase().trim();
            const cards = locationsContainer.querySelectorAll('.futuristic-card');

            cards.forEach(card => {
                const keywordsText = card.querySelector('p strong')?.parentElement?.textContent.toLowerCase() || '';
                const descriptionText = card.querySelectorAll('p')[1]?.textContent.toLowerCase() || '';

                const searchMatch = !searchValue ||
                    keywordsText.includes(searchValue) ||
                    descriptionText.includes(searchValue);

                card.style.display = searchMatch ? '' : 'none';
            });
        }

        locationSearchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(applyLocationSearch, 300); // Debounce for 300ms
        });
    }
});

// ===== FULL-SCREEN IMAGE MODAL =====
let currentImageIndex = 0;
let allImages = [];

// Create modal elements
const modal = document.createElement('div');
modal.id = 'image-modal';
modal.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.9);
    display: none;
    z-index: 10001;
    cursor: pointer;
`;

const modalImg = document.createElement('img');
modalImg.style.cssText = `
    max-width: 90%;
    max-height: 90%;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    object-fit: contain;
`;

const closeBtn = document.createElement('button');
closeBtn.innerHTML = '×';
closeBtn.style.cssText = `
    position: absolute;
    top: 20px;
    right: 30px;
    color: white;
    font-size: 40px;
    font-weight: bold;
    cursor: pointer;
    background: none;
    border: none;
    z-index: 10000;
`;

const prevBtn = document.createElement('button');
prevBtn.innerHTML = '‹';
prevBtn.style.cssText = `
    position: absolute;
    top: 50%;
    left: 20px;
    color: white;
    font-size: 40px;
    font-weight: bold;
    cursor: pointer;
    background: none;
    border: none;
    transform: translateY(-50%);
    z-index: 10000;
`;

const nextBtn = document.createElement('button');
nextBtn.innerHTML = '›';
nextBtn.style.cssText = `
    position: absolute;
    top: 50%;
    right: 20px;
    color: white;
    font-size: 40px;
    font-weight: bold;
    cursor: pointer;
    background: none;
    border: none;
    transform: translateY(-50%);
    z-index: 10000;
`;

modal.appendChild(modalImg);
modal.appendChild(closeBtn);
modal.appendChild(prevBtn);
modal.appendChild(nextBtn);
document.body.appendChild(modal);

// Modal event listeners
closeBtn.addEventListener('click', closeModal);
prevBtn.addEventListener('click', showPrevImage);
nextBtn.addEventListener('click', showNextImage);
modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
});

document.addEventListener('keydown', (e) => {
    if (modal.style.display === 'block') {
        if (e.key === 'Escape') closeModal();
        else if (e.key === 'ArrowLeft') showPrevImage();
        else if (e.key === 'ArrowRight') showNextImage();
    }
});

// Media item click handler
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('media-item')) {
        e.preventDefault();
        const mediaItem = e.target;
        const container = mediaItem.closest('.location-images') || mediaItem.closest('.futuristic-card');
        if (container) {
            allImages = Array.from(container.querySelectorAll('.media-item')).map(item => ({
                src: item.dataset.src || item.src,
                type: item.dataset.type || 'img'
            }));
            currentImageIndex = allImages.findIndex(img => img.src === (mediaItem.dataset.src || mediaItem.src));
            showImage(currentImageIndex);
        }
    }
});

// Functions
function showImage(index) {
    if (index < 0 || index >= allImages.length) return;

    const image = allImages[index];
    modalImg.src = image.src;
    modal.style.display = 'block';
    updateNavigationButtons();
}

function closeModal() {
    modal.style.display = 'none';
}

function showPrevImage() {
    if (currentImageIndex > 0) {
        currentImageIndex--;
        showImage(currentImageIndex);
    }
}

function showNextImage() {
    if (currentImageIndex < allImages.length - 1) {
        currentImageIndex++;
        showImage(currentImageIndex);
    }
}

function updateNavigationButtons() {
    prevBtn.style.display = currentImageIndex > 0 ? 'block' : 'none';
    nextBtn.style.display = currentImageIndex < allImages.length - 1 ? 'block' : 'none';
}
