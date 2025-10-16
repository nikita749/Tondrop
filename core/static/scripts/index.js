document.querySelectorAll('.category-card').forEach(btn => {
  btn.addEventListener('click', function(e) {
    const ripple = document.createElement('span');
    ripple.classList.add('ripple');
    
    // Позиция волны — где кликнули
    const rect = btn.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.left = `${e.clientX - rect.left - size/2}px`;
    ripple.style.top = `${e.clientY - rect.top - size/2}px`;


    
    btn.appendChild(ripple);
    
    // Удаляем элемент после анимации
    setTimeout(() => ripple.remove(), 600);
  });
});