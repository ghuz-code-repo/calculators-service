function toggleDiscountFields() {
    var discountFields = document.getElementById('discountFields');
    if (discountFields.style.display === 'none' || discountFields.style.display === '') {
        discountFields.style.display = 'block';
    } else {
        discountFields.style.display = 'none';
    }
}

function toggleSection(id) {
    const section = document.getElementById(id);
    if (section) {
        if (section.style.display === 'none' || section.style.display === '') {
            section.style.display = 'flex'; // Или 'block' в зависимости от CSS
        } else {
            section.style.display = 'none';
        }
    }
}