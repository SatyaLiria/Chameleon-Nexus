// ============================================================
// CHAMELEON NEXUS - JavaScript
// ============================================================

// ============================================================
// PHOTO UPLOAD
// ============================================================
function uploadPhoto() {
    const fileInput = document.getElementById('photoFile');
    const rollNumber = document.getElementById('rollNumber');
    const statusDiv = document.getElementById('uploadStatus');
    
    if (!fileInput || !fileInput.files || !fileInput.files[0]) {
        showStatus(statusDiv, 'Please select a photo.', 'warning');
        return;
    }
    
    if (!rollNumber || !rollNumber.value.trim()) {
        showStatus(statusDiv, 'Please enter roll number.', 'warning');
        return;
    }
    
    const formData = new FormData();
    formData.append('photo', fileInput.files[0]);
    formData.append('roll_number', rollNumber.value.trim());
    
    showStatus(statusDiv, 'Uploading... Please wait.', 'info');
    
    fetch('/upload-photo', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showStatus(statusDiv, `
                ✅ Photo uploaded successfully!
                <br>
                <img src="${data.url}" style="max-width: 200px; border-radius: 10px; margin-top: 10px; border: 2px solid #1a237e;">
            `, 'success');
            
            if (fileInput) fileInput.value = '';
            if (rollNumber) rollNumber.value = '';
        } else {
            showStatus(statusDiv, `❌ ${data.error}`, 'danger');
        }
    })
    .catch(error => {
        showStatus(statusDiv, `❌ Error: ${error.message}`, 'danger');
    });
}

function showStatus(element, message, type) {
    if (!element) return;
    
    const icons = {
        success: 'check-circle',
        danger: 'x-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    
    element.innerHTML = `
        <div class="alert alert-${type} mt-2" role="alert">
            <i class="bi bi-${icons[type] || 'info-circle'}"></i>
            ${message}
        </div>
    `;
}

// ============================================================
// SEARCH STUDENTS
// ============================================================
let searchTimeout;

function searchStudents(query) {
    clearTimeout(searchTimeout);
    
    if (!query || query.length < 2) {
        document.getElementById('searchResults').innerHTML = '';
        return;
    }
    
    searchTimeout = setTimeout(() => {
        fetch(`/api/search-students?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                displaySearchResults(data);
            })
            .catch(error => {
                console.error('Search error:', error);
            });
    }, 300);
}

function displaySearchResults(results) {
    const container = document.getElementById('searchResults');
    
    if (!results || results.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-3">
                <i class="bi bi-search"></i> No students found
            </div>
        `;
        return;
    }
    
    let html = '<ul class="list-group">';
    results.forEach(student => {
        html += `
            <li class="list-group-item list-group-item-action">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${student.student_name}</strong>
                        <br>
                        <small class="text-muted">${student.roll_number}</small>
                    </div>
                    <a href="/student-verification/${student.roll_number}" class="btn btn-sm btn-primary">
                        <i class="bi bi-eye"></i> View
                    </a>
                </div>
            </li>
        `;
    });
    html += '</ul>';
    
    container.innerHTML = html;
}

// ============================================================
// TABLE SEARCH
// ============================================================
function filterTable(searchInput, tableId) {
    const filter = searchInput.value.toLowerCase();
    const table = document.getElementById(tableId);
    const rows = table.getElementsByTagName('tr');
    
    for (let i = 1; i < rows.length; i++) {
        const row = rows[i];
        const cells = row.getElementsByTagName('td');
        let found = false;
        
        for (let j = 0; j < cells.length; j++) {
            const cell = cells[j];
            if (cell) {
                const text = cell.textContent || cell.innerText;
                if (text.toLowerCase().indexOf(filter) > -1) {
                    found = true;
                    break;
                }
            }
        }
        
        row.style.display = found ? '' : 'none';
    }
}

// ============================================================
// CONFIRM DELETE
// ============================================================
function confirmDelete(message) {
    return confirm(message || 'Are you sure you want to delete this item?');
}

// ============================================================
// TOAST NOTIFICATIONS
// ============================================================
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) return;
    
    const icons = {
        success: 'check-circle',
        danger: 'x-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.role = 'alert';
    toast.ariaLive = 'assertive';
    toast.ariaAtomic = 'true';
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="bi bi-${icons[type] || 'info-circle'} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// ============================================================
// FILE UPLOAD PREVIEW
// ============================================================
function previewFile(input, previewId) {
    const preview = document.getElementById(previewId);
    if (!preview) return;
    
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.innerHTML = `
                <img src="${e.target.result}" class="img-fluid rounded-3" style="max-height: 200px;">
            `;
        };
        reader.readAsDataURL(input.files[0]);
    } else {
        preview.innerHTML = '';
    }
}

// ============================================================
// COPY TO CLIPBOARD
// ============================================================
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text)
            .then(() => {
                showToast('Copied to clipboard!', 'success');
            })
            .catch(() => {
                fallbackCopy(text);
            });
    } else {
        fallbackCopy(text);
    }
}

function fallbackCopy(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    showToast('Copied to clipboard!', 'success');
}

// ============================================================
// TABLE EXPORT TO CSV
// ============================================================
function exportTableToCSV(tableId, filename = 'export.csv') {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    for (const row of rows) {
        const rowData = [];
        const cells = row.querySelectorAll('th, td');
        for (const cell of cells) {
            rowData.push(cell.textContent.trim());
        }
        csv.push(rowData.join(','));
    }
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

// ============================================================
// DATE FORMATTER
// ============================================================
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-IN', {
            day: '2-digit',
            month: 'short',
            year: 'numeric'
        });
    } catch {
        return dateString;
    }
}

function formatDateTime(dateString) {
    if (!dateString) return 'N/A';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-IN', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return dateString;
    }
}

// ============================================================
// INITIALIZATION
// ============================================================
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5 seconds
    document.querySelectorAll('.alert-dismissible').forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Enable tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggerList.forEach(el => {
        new bootstrap.Tooltip(el);
    });
    
    // Enable popovers
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    popoverTriggerList.forEach(el => {
        new bootstrap.Popover(el);
    });
});

// ============================================================
// KEYBOARD SHORTCUTS
// ============================================================
document.addEventListener('keydown', function(e) {
    // Ctrl + K = Focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.getElementById('globalSearch');
        if (searchInput) {
            searchInput.focus();
        }
    }
});