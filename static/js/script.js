// Custom JavaScript for Wind Sports Bot dashboard

// Function to format wind speed with appropriate styling
function formatWindSpeed(speed) {
    let badgeClass = 'bg-wind-low';
    let icon = 'fa-wind';
    
    if (speed >= 25) {
        badgeClass = 'bg-wind-extreme';
        icon = 'fa-exclamation-triangle';
    } else if (speed >= 20) {
        badgeClass = 'bg-wind-high';
        icon = 'fa-wind fa-2x';
    } else if (speed >= 15) {
        badgeClass = 'bg-wind-medium';
        icon = 'fa-wind fa-lg';
    }
    
    return `<span class="wind-badge ${badgeClass}"><i class="fas ${icon} wind-icon"></i>${speed.toFixed(1)}</span>`;
}

// Initialize any tooltips
document.addEventListener('DOMContentLoaded', function() {
    // Enable tooltips everywhere
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
