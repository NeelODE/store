const themeToggle = document.getElementById('themeToggle');
const htmlElement = document.documentElement; // Target the <html> element
const currentTheme = localStorage.getItem('theme') ? localStorage.getItem('theme') : null;

// Apply the saved theme on initial load
if (currentTheme) {
    htmlElement.setAttribute('data-theme', currentTheme);
}

// Toggle theme on button click
themeToggle.addEventListener('click', () => {
    let currentTheme = htmlElement.getAttribute('data-theme');
    if (currentTheme === 'dark') {
        htmlElement.setAttribute('data-theme', 'light');
        localStorage.setItem('theme', 'light');
    } else {
        htmlElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
    }
});