// Theme toggle functionality
document.addEventListener('DOMContentLoaded', function() {
  const toggleBtn = document.getElementById('themeToggle');
  const themeIcon = toggleBtn.querySelector('.theme-icon');
  const body = document.body;
  
  // Check for saved theme preference or respect OS preference
  const savedTheme = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  
  if (savedTheme === 'light' || (!savedTheme && !prefersDark)) {
    body.classList.add('light-theme');
    themeIcon.textContent = '☀️';
    toggleBtn.setAttribute('aria-pressed', 'false');
  } else {
    body.classList.remove('light-theme');
    themeIcon.textContent = '🌙';
    toggleBtn.setAttribute('aria-pressed', 'true');
  }
  
  // Toggle theme on button click
  toggleBtn.addEventListener('click', () => {
    body.classList.toggle('light-theme');
    const isLight = body.classList.contains('light-theme');
    themeIcon.textContent = isLight ? '☀️' : '🌙';
    toggleBtn.setAttribute('aria-pressed', isLight ? 'false' : 'true');
    localStorage.setItem('theme', isLight ? 'light' : 'dark');
  });
  
  // Animate stats counting
  const animateStats = function() {
    const statElements = document.querySelectorAll('.stat-number');
    
    statElements.forEach(stat => {
      const target = parseInt(stat.getAttribute('data-count'));
      if (isNaN(target)) return;
      
      let count = 0;
      const duration = 2000;
      const frameDuration = 1000 / 60;
      const totalFrames = Math.round(duration / frameDuration);
      const increment = target / totalFrames;
      
      const counter = setInterval(() => {
        count += increment;
        if (count >= target) {
          stat.textContent = target.toLocaleString() + '+';
          clearInterval(counter);
        } else {
          stat.textContent = Math.floor(count).toLocaleString();
        }
      }, frameDuration);
    });
  };
  
  // Initialize stats animation when in viewport
  const statsSection = document.querySelector('.stats');
  if (statsSection) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateStats();
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });
    
    observer.observe(statsSection);
  }
});