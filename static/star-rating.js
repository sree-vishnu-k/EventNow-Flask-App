document.addEventListener('DOMContentLoaded', () => {
    // Interactive star rating input
    const starContainers = document.querySelectorAll('.star-rating-input');
    starContainers.forEach(container => {
        const stars = container.querySelectorAll('.star');
        const hiddenInput = container.nextElementSibling;

        stars.forEach(star => {
            star.addEventListener('click', () => {
                const value = star.getAttribute('data-value');
                hiddenInput.value = value;
                stars.forEach(s => {
                    s.classList.toggle('active', s.getAttribute('data-value') <= value);
                });
            });
        });
    });

    // Display star ratings
    const ratingDisplays = document.querySelectorAll('.star-rating');
    ratingDisplays.forEach(display => {
        const rating = parseInt(display.getAttribute('data-rating'));
        display.innerHTML = '★'.repeat(rating) + '☆'.repeat(5 - rating);
    });
});