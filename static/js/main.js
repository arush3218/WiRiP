// WiRiP - Main JavaScript File

document.addEventListener('DOMContentLoaded', function() {
    // Initialize smooth scrolling for anchor links
    initSmoothScrolling();
    
    // Initialize lazy loading for images
    initLazyLoading();
    
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        initTooltips();
    }
    
    // Initialize mobile navigation
    initMobileNav();
    
    // Initialize search functionality
    initSearch();
    
    // Initialize theme animations
    initAnimations();
});

// Smooth scrolling for anchor links
function initSmoothScrolling() {
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Lazy loading for images
function initLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        images.forEach(img => imageObserver.observe(img));
    } else {
        // Fallback for browsers without IntersectionObserver
        images.forEach(img => {
            img.src = img.dataset.src;
            img.classList.remove('lazy');
        });
    }
}

// Initialize Bootstrap tooltips
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Mobile navigation enhancements
function initMobileNav() {
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggler && navbarCollapse) {
        // Close mobile menu when clicking on a link
        const navLinks = navbarCollapse.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (navbarCollapse.classList.contains('show')) {
                    navbarToggler.click();
                }
            });
        });
        
        // Close mobile menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!navbarToggler.contains(e.target) && !navbarCollapse.contains(e.target)) {
                if (navbarCollapse.classList.contains('show')) {
                    navbarToggler.click();
                }
            }
        });
    }
}

// Search functionality
function initSearch() {
    const searchInput = document.querySelector('#searchInput');
    
    if (searchInput) {
        let searchTimeout;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length >= 3) {
                searchTimeout = setTimeout(() => {
                    performSearch(query);
                }, 300);
            } else {
                clearSearchResults();
            }
        });
    }
}

// Perform search (you can customize this to your needs)
function performSearch(query) {
    // This is a placeholder - in a real app, you'd make an API call
    console.log('Searching for:', query);
    
    // Example: Filter visible blog cards
    const blogCards = document.querySelectorAll('.blog-card');
    blogCards.forEach(card => {
        const title = card.querySelector('.blog-title')?.textContent.toLowerCase() || '';
        const summary = card.querySelector('.blog-summary')?.textContent.toLowerCase() || '';
        
        if (title.includes(query.toLowerCase()) || summary.includes(query.toLowerCase())) {
            card.style.display = 'block';
            card.parentElement.style.display = 'block';
        } else {
            card.style.display = 'none';
            card.parentElement.style.display = 'none';
        }
    });
}

// Clear search results
function clearSearchResults() {
    const blogCards = document.querySelectorAll('.blog-card');
    blogCards.forEach(card => {
        card.style.display = 'block';
        card.parentElement.style.display = 'block';
    });
}

// Animation enhancements
function initAnimations() {
    // Fade in elements on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observe elements with fade-in class
    const elementsToAnimate = document.querySelectorAll('.blog-card, .feature-card, .category-card');
    elementsToAnimate.forEach(el => {
        observer.observe(el);
    });
    
    // Add staggered animation delays
    elementsToAnimate.forEach((el, index) => {
        el.style.animationDelay = `${index * 0.1}s`;
    });
}

// Voting functionality
function initVoting() {
    const voteButtons = document.querySelectorAll('.vote-btn');
    
    voteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const postId = this.dataset.postId;
            const isUpvote = this.dataset.voteType === 'true';
            
            // Disable button temporarily
            this.disabled = true;
            
            fetch('/vote', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    post_id: parseInt(postId),
                    is_upvote: isUpvote
                })
            })
            .then(response => response.json())
            .then(data => {
                // Update vote counts
                const upvoteCount = document.getElementById('upvote-count');
                const downvoteCount = document.getElementById('downvote-count');
                const scoreCount = document.getElementById('score-count');
                
                if (upvoteCount) upvoteCount.textContent = data.upvotes;
                if (downvoteCount) downvoteCount.textContent = data.downvotes;
                if (scoreCount) scoreCount.textContent = data.score;
                
                // Update button states
                const upvoteBtn = document.querySelector('.upvote-btn');
                const downvoteBtn = document.querySelector('.downvote-btn');
                
                upvoteBtn?.classList.remove('active');
                downvoteBtn?.classList.remove('active');
                
                // Add active class based on current vote
                if (isUpvote && !this.classList.contains('active')) {
                    this.classList.add('active');
                } else if (!isUpvote && !this.classList.contains('active')) {
                    this.classList.add('active');
                }
                
                // Show success animation
                showVoteAnimation(this, true);
            })
            .catch(error => {
                console.error('Error:', error);
                showVoteAnimation(this, false);
            })
            .finally(() => {
                this.disabled = false;
            });
        });
    });
}

// Show vote animation
function showVoteAnimation(button, success) {
    const originalHTML = button.innerHTML;
    
    if (success) {
        button.innerHTML = '<i class="fas fa-check"></i>';
        button.classList.add('success-animation');
        
        setTimeout(() => {
            button.innerHTML = originalHTML;
            button.classList.remove('success-animation');
        }, 1000);
    } else {
        button.classList.add('error-animation');
        
        setTimeout(() => {
            button.classList.remove('error-animation');
        }, 1000);
    }
}

// Form validation helpers
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            showFieldError(field, 'This field is required');
            isValid = false;
        } else {
            clearFieldError(field);
        }
    });
    
    return isValid;
}

function showFieldError(field, message) {
    clearFieldError(field);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error text-danger mt-1';
    errorDiv.textContent = message;
    
    field.parentNode.appendChild(errorDiv);
    field.classList.add('is-invalid');
}

function clearFieldError(field) {
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
    field.classList.remove('is-invalid');
}

// Notification system
function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show notification-toast`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    const container = document.querySelector('.container') || document.body;
    container.insertBefore(notification, container.firstChild);
    
    // Auto remove after duration
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, duration);
}

// Loading spinner
function showLoadingSpinner(element) {
    const spinner = document.createElement('div');
    spinner.className = 'loading-spinner';
    spinner.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    
    element.appendChild(spinner);
    element.classList.add('loading');
}

function hideLoadingSpinner(element) {
    const spinner = element.querySelector('.loading-spinner');
    if (spinner) {
        spinner.remove();
    }
    element.classList.remove('loading');
}

// Utility functions
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

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// Copy to clipboard function
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch (err) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            document.body.removeChild(textArea);
            return true;
        } catch (err) {
            document.body.removeChild(textArea);
            return false;
        }
    }
}

// Initialize voting when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initVoting();
});

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .animate-fade-in {
        animation: fadeIn 0.6s ease-out forwards;
    }
    
    .success-animation {
        animation: pulse 0.6s ease-in-out;
        background-color: var(--success) !important;
    }
    
    .error-animation {
        animation: shake 0.6s ease-in-out;
        background-color: var(--danger) !important;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
    
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }
    
    .loading-spinner {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-size: 1.5rem;
        color: var(--pink-primary);
    }
    
    .loading {
        position: relative;
        pointer-events: none;
        opacity: 0.7;
    }
    
    .notification-toast {
        position: fixed;
        top: 100px;
        right: 20px;
        z-index: 1060;
        min-width: 300px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    
    .field-error {
        font-size: 0.875rem;
    }
    
    .is-invalid {
        border-color: var(--danger) !important;
        box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25) !important;
    }
`;

document.head.appendChild(style);