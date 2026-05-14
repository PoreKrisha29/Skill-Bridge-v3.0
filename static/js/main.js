/**
 * SkillBridge Main JavaScript
 * 
 * This file contains all client-side JavaScript functionality including:
 * - Search autocomplete
 * - Form validation
 * - Dynamic content loading
 * - Favorite toggling
 * - Smooth scrolling
 * - Interactive elements
 * 
 * Author: SkillBridge Team
 * Purpose: Client-side interactivity and AJAX operations
 */

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Debounce function to limit API calls
 * 
 * Purpose: Prevents excessive API calls during rapid user input
 * Algorithm: Delays function execution until user stops typing
 * 
 * @param {Function} func - Function to debounce
 * @param {Number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Show toast notification
 * 
 * @param {String} message - Message to display
 * @param {String} type - Type of alert (success, danger, warning, info)
 */
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();

    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show`;
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    toastContainer.appendChild(toast);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

/**
 * Create toast container if it doesn't exist
 */
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.style.cssText = 'position: fixed; top: 100px; right: 20px; z-index: 9999; max-width: 350px;';
    document.body.appendChild(container);
    return container;
}

// ============================================================================
// SEARCH FUNCTIONALITY
// ============================================================================

/**
 * Initialize search autocomplete
 * 
 * Features:
 * - Real-time suggestions as user types
 * - Debounced API calls to reduce server load
 * - Keyboard navigation support
 * - Click outside to close
 */
function initializeSearch() {
    const searchInput = document.getElementById('searchInput');
    const searchSuggestions = document.getElementById('searchSuggestions');

    if (!searchInput || !searchSuggestions) return;

    // Debounced search function
    const performSearch = debounce(async (query) => {
        if (query.length < 2) {
            searchSuggestions.innerHTML = '';
            searchSuggestions.classList.remove('show');
            return;
        }

        try {
            // Fetch autocomplete suggestions from API
            const response = await fetch(`/api/search/autocomplete?q=${encodeURIComponent(query)}`);
            const data = await response.json();

            if (data.suggestions && data.suggestions.length > 0) {
                // Display suggestions
                searchSuggestions.innerHTML = data.suggestions
                    .map(s => `<div class="suggestion-item">${escapeHtml(s)}</div>`)
                    .join('');
                searchSuggestions.classList.add('show');

                // Add click handlers to suggestions
                document.querySelectorAll('.suggestion-item').forEach(item => {
                    item.addEventListener('click', function () {
                        searchInput.value = this.textContent;
                        searchSuggestions.classList.remove('show');
                        // Submit search form
                        searchInput.closest('form').submit();
                    });
                });
            } else {
                searchSuggestions.classList.remove('show');
            }
        } catch (error) {
            console.error('Search error:', error);
        }
    }, 300);

    // Listen for input events
    searchInput.addEventListener('input', function () {
        performSearch(this.value.trim());
    });

    // Close suggestions when clicking outside
    document.addEventListener('click', function (e) {
        if (!searchInput.contains(e.target) && !searchSuggestions.contains(e.target)) {
            searchSuggestions.classList.remove('show');
        }
    });

    // Keyboard navigation (optional enhancement)
    searchInput.addEventListener('keydown', function (e) {
        const suggestions = searchSuggestions.querySelectorAll('.suggestion-item');
        if (suggestions.length === 0) return;

        // Arrow down
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            suggestions[0].focus();
        }
    });
}

/**
 * Escape HTML to prevent XSS attacks
 * 
 * @param {String} text - Text to escape
 * @returns {String} Escaped text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================================
// FAVORITE FUNCTIONALITY
// ============================================================================

/**
 * Toggle favorite status for a service
 * 
 * Purpose: Add/remove service from user's favorites
 * Uses: AJAX POST request to backend
 * 
 * @param {Number} serviceId - Service ID
 * @param {HTMLElement} button - Button element (optional)
 */
async function toggleFavorite(serviceId, button) {
    try {
        const response = await fetch(`/service/${serviceId}/favorite`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const data = await response.json();

        // if (response.ok) {
        //     // Update button state
        //     if (button) {
        //         const icon = button.querySelector('i');
        //         if (data.status === 'added') {
        //             button.classList.add('active');
        //             icon.classList.remove('bi-heart');
        //             icon.classList.add('bi-heart-fill');
        //             showToast('Added to favorites!', 'success');
        //         } else {
        //             button.classList.remove('active');
        //             icon.classList.remove('bi-heart-fill');
        //             icon.classList.add('bi-heart');
        //             showToast('Removed from favorites', 'info');
        //         }
        //     }
        // } else {
        //     // User not logged in
        //     showToast('Please log in to add favorites', 'warning');
        //     setTimeout(() => {
        //         window.location.href = '/auth/login';
        //     }, 1500);
        // }
    } catch (error) {
        console.error('Favorite error:', error);
        showToast('An error occurred. Please try again.', 'danger');
    }
}

// ============================================================================
// FORM VALIDATION
// ============================================================================

/**
 * Initialize form validation
 * 
 * Features:
 * - Real-time validation
 * - Custom error messages
 * - Bootstrap validation styles
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');

    forms.forEach(form => {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }

            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * Validate email format
 * 
 * @param {String} email - Email address
 * @returns {Boolean} True if valid
 */
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Validate password strength
 * 
 * Requirements:
 * - Minimum 8 characters
 * - At least one letter
 * - At least one number
 * 
 * @param {String} password - Password
 * @returns {Object} Validation result
 */
function validatePassword(password) {
    const result = {
        valid: true,
        errors: []
    };

    if (password.length < 8) {
        result.valid = false;
        result.errors.push('Password must be at least 8 characters long');
    }

    if (!/[a-zA-Z]/.test(password)) {
        result.valid = false;
        result.errors.push('Password must contain at least one letter');
    }

    if (!/[0-9]/.test(password)) {
        result.valid = false;
        result.errors.push('Password must contain at least one number');
    }

    return result;
}

// ============================================================================
// SMOOTH SCROLLING
// ============================================================================

/**
 * Initialize smooth scrolling for anchor links
 */
function initializeSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href === '#') return;

            const target = document.querySelector(href);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// ============================================================================
// DYNAMIC CONTENT LOADING
// ============================================================================

/**
 * Load more services (pagination)
 * 
 * Purpose: Infinite scroll or "Load More" button functionality
 * 
 * @param {Number} page - Page number
 * @param {String} category - Category filter (optional)
 */
async function loadMoreServices(page, category = null) {
    const container = document.getElementById('servicesContainer');
    const loadMoreBtn = document.getElementById('loadMoreBtn');

    if (!container) return;

    try {
        // Show loading state
        if (loadMoreBtn) {
            loadMoreBtn.disabled = true;
            loadMoreBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
        }

        // Build URL with parameters
        let url = `/api/services/featured?limit=12&page=${page}`;
        if (category) {
            url += `&category=${category}`;
        }

        const response = await fetch(url);
        const data = await response.json();

        if (data.services && data.services.length > 0) {
            // Append services to container
            data.services.forEach(service => {
                const serviceCard = createServiceCard(service);
                container.appendChild(serviceCard);
            });

            // Reset button
            if (loadMoreBtn) {
                loadMoreBtn.disabled = false;
                loadMoreBtn.innerHTML = 'Load More';
            }
        } else {
            // No more services
            if (loadMoreBtn) {
                loadMoreBtn.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Load more error:', error);
        if (loadMoreBtn) {
            loadMoreBtn.disabled = false;
            loadMoreBtn.innerHTML = 'Load More';
        }
    }
}

/**
 * Create service card HTML element
 * 
 * @param {Object} service - Service data
 * @returns {HTMLElement} Service card element
 */
function createServiceCard(service) {
    const col = document.createElement('div');
    col.className = 'col-md-6 col-lg-3';

    col.innerHTML = `
        <div class="service-card h-100">
            <div class="service-image">
                <img src="/static/images/${service.image_url}" alt="${service.title}">
                <button class="favorite-btn" onclick="toggleFavorite(${service.id}, this)">
                    <i class="bi bi-heart"></i>
                </button>
            </div>
            <div class="service-content">
                <div class="d-flex align-items-center mb-3">
                    <img src="/static/images/default-avatar.png" class="provider-avatar me-2">
                    <span class="small fw-medium">${service.provider}</span>
                </div>
                <h5 class="service-title mb-3">
                    <a href="/service/${service.id}">${service.title}</a>
                </h5>
                <div class="service-footer">
                    <div>
                        <i class="bi bi-star-fill text-warning"></i>
                        <span class="fw-medium">${service.rating}</span>
                    </div>
                    <span class="service-price">$${service.price}</span>
                </div>
            </div>
        </div>
    `;

    return col;
}

// ============================================================================
// NEWSLETTER SUBSCRIPTION
// ============================================================================

/**
 * Handle newsletter subscription
 */
function initializeNewsletter() {
    const form = document.getElementById('newsletterForm');

    if (!form) return;

    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        const emailInput = this.querySelector('input[type="email"]');
        const email = emailInput.value.trim();

        if (!validateEmail(email)) {
            showToast('Please enter a valid email address', 'danger');
            return;
        }

        // In a real application, this would send to backend
        // For now, just show success message
        showToast('Thank you for subscribing!', 'success');
        emailInput.value = '';
    });
}

// ============================================================================
// IMAGE LAZY LOADING
// ============================================================================

/**
 * Initialize lazy loading for images
 * 
 * Purpose: Improve page load performance
 * Uses: Intersection Observer API
 */
function initializeLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');

    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    imageObserver.unobserve(img);
                }
            });
        });

        images.forEach(img => imageObserver.observe(img));
    } else {
        // Fallback for older browsers
        images.forEach(img => {
            img.src = img.dataset.src;
        });
    }
}

// ============================================================================
// INITIALIZATION
// ============================================================================

/**
 * Initialize all functionality when DOM is ready
 * 
 * This is the main entry point for the JavaScript
 */
document.addEventListener('DOMContentLoaded', function () {
    // Initialize all features
    initializeSearch();
    initializeFormValidation();
    initializeSmoothScroll();
    initializeNewsletter();
    initializeLazyLoading();

    // Log initialization (for debugging)
    console.log('SkillBridge initialized successfully');
});

// ============================================================================
// GLOBAL FUNCTIONS (accessible from HTML onclick attributes)
// ============================================================================

// Make functions available globally
window.toggleFavorite = toggleFavorite;
window.loadMoreServices = loadMoreServices;
window.showToast = showToast;
