function openPage(pageName, elmnt) {
  // Hide all elements with class="tabcontent" by default */
  var i, tabcontent, tablinks;
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }

  // Remove the background color of all tablinks/buttons and reset to default
  tablinks = document.getElementsByClassName("tablink");
  for (i = 0; i < tablinks.length; i++) {
    // tablinks[i].style.backgroundColor = "";
    tablinks[i].classList.remove("active");
  }

  // Show the specific tab content
  document.getElementById(pageName).style.display = "flex";

  // Add the specific color to the button used to open the tab content
  // Используем CSS переменную для совместимости с темами
  elmnt.style.borderColor = 'var(--primary-golden)';
  elmnt.classList.add("active");
}

// Инициализация при загрузке DOM
document.addEventListener('DOMContentLoaded', function() {
  // Применяем тему к активной вкладке при загрузке
  const defaultTab = document.getElementById("defaultOpen");
  if (defaultTab) {
    defaultTab.click();
  }
  
  // Обновляем цвета вкладок при смене темы
  document.addEventListener('themeChanged', function(event) {
    const activeTab = document.querySelector('.tablink.active');
    if (activeTab) {
      // Перезапускаем стили для активной вкладки с новой темой
      setTimeout(() => {
        activeTab.style.borderColor = 'var(--primary-golden)';
      }, 50);
    }
  });
});

// Мобильное выпадающее меню для выбора калькулятора
document.addEventListener('DOMContentLoaded', function () {
    const tabMenu = document.querySelector('.tab_menu');
    const dropdownToggle = document.querySelector('.tab-dropdown-toggle');
    const tabLinks = document.querySelectorAll('.tab_menu .tablink');

    function closeDropdown() {
        if (tabMenu) tabMenu.classList.remove('open');
        // Оставляем только активную вкладку видимой на мобильном
        if (window.innerWidth <= 900) {
            tabLinks.forEach(btn => {
                if (btn.classList.contains('active')) {
                    dropdownToggle.textContent =btn.textContent+" | для выбора нажмите"; // Обновляем текст кнопки
                    btn.style.display = 'block';
                } else {
                    btn.style.display = 'none';
                }
            });
        }
    }

    function openDropdown() {
        if (tabMenu) tabMenu.classList.add('open');
        // Показываем все вкладки
        if (window.innerWidth <= 900) {
            tabLinks.forEach(btn => {
                btn.style.display = 'block';
            });
        }
    }

    // Изначально скрываем неактивные вкладки на мобильном
    function initMobileTabs() {
        if (window.innerWidth <= 900) {
            tabLinks.forEach(btn => {
                if (tabMenu.classList.contains('open')) {
                    btn.style.display = 'block';
                } else {
                    if (btn.classList.contains('active')) {
                        dropdownToggle.textContent = btn.textContent+" | для выбора нажмите";  // Обновляем текст кнопки
                        btn.style.display = 'block';
                    } else {
                        btn.style.display = 'none';
                    }
                }
            });
        } else {
            tabLinks.forEach(btn => {
                btn.style.display = '';
            });
        }
    }

    if (dropdownToggle && tabMenu) {
        dropdownToggle.addEventListener('click', function (e) {
            e.stopPropagation();
            if (tabMenu.classList.contains('open')) {
                closeDropdown();
            } else {
                openDropdown();
            }
        });

        // При выборе калькулятора закрываем меню и показываем только активную вкладку
        tabLinks.forEach(btn => {
            btn.addEventListener('click', function () {
                closeDropdown();
            });
        });

        // Клик вне меню — закрыть
        document.addEventListener('click', function (e) {
            if (tabMenu.classList.contains('open') && !tabMenu.contains(e.target)) {
                closeDropdown();
            }
        });

        // При ресайзе окна корректируем отображение вкладок
        window.addEventListener('resize', initMobileTabs);

        // Инициализация при загрузке
        initMobileTabs();
    }
});