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

// function toggleCalculator() {
//     const calculator = document.getElementById('calculator');
//     const admin = document.getElementById('admin_panel');
    
//     if (calculator) {
//         if (calculator.style.display === 'none' || calculator.style.display === '') {
//             calculator.style.display = 'flex'; // Или 'block' в зависимости от CSS
//             admin.style.display = 'none'; // Скрыть админ панель при открытии калькулятора
//         } else {
//             calculator.style.display = 'none';
//             admin.style.display = 'flex'; // Показать админ панель при закрытии калькулятора
//         }
//     }

//     console.log('calculator:', calculator.style.display);
//     console.log('admin:', admin.style.display);
// }

// function toggleAdminPanel() {
//     const calculator = document.getElementById('calculator');
//     const admin = document.getElementById('admin_panel');

//     if (admin) {
//         if (admin.style.display === 'none' || admin.style.display === '') {
//             admin.style.display = 'flex'; // Или 'block' в зависимости от CSS
//             calculator.style.display = 'none'; // Скрыть калькулятор при открытии админ панели
//         } else {
//             calculator.style.display = 'flex'; // Показать калькулятор при закрытии админ панели
//             admin.style.display = 'none';
//         }
//     }

//     console.log('calculator:', calculator.style.display);
//     console.log('admin:', admin.style.display);
// }