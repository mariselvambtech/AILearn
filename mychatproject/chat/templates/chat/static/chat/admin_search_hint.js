document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.querySelector('input[name="q"]');
    if (searchInput) {
        searchInput.placeholder = "Search by message, username, or session ID...";
    }
});