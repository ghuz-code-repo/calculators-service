// --- Глобальное состояние ---
let itemsPerPageMap = {
    'apartments': 20,
    'calculationHistory': 20
};
let currentPages = {
    'apartments': 1,
    'calculationHistory': 1
};

// --- Логика пагинации ---

function goToPage(page, rows, prefix) {
    console.log(`goToPage called for prefix: ${prefix}, page: ${page}, total rows: ${rows.length}`); // Добавлено логирование
    const itemsPerPage = itemsPerPageMap[prefix];
    if (!itemsPerPage || itemsPerPage <= 0) {
        console.error(`[${prefix}] Invalid itemsPerPage:`, itemsPerPage);
        return;
    }

    const totalRows = rows.length;
    const totalPages = Math.ceil(totalRows / itemsPerPage);

    // Ограничение номера страницы
    page = Math.max(1, Math.min(page, totalPages));
    if (isNaN(page)) page = 1; // Обработка NaN

    const startIndex = (page - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage - 1, totalRows - 1);

    // Обновление информации о пагинации
    const pageStartEl = document.getElementById(`${prefix}_pageStart`);
    const pageEndEl = document.getElementById(`${prefix}_pageEnd`);
    const totalItemsEl = document.getElementById(`${prefix}_totalItems`);

    if (pageStartEl) pageStartEl.textContent = totalRows > 0 ? startIndex + 1 : 0;
    if (pageEndEl) pageEndEl.textContent = totalRows > 0 ? endIndex + 1 : 0;
    if (totalItemsEl) totalItemsEl.textContent = totalRows;

    // Сначала скрыть все строки
    rows.forEach(row => {
        row.style.display = 'none';
    });

    // Показать только строки для текущей страницы
    console.log(`[${prefix}] Displaying rows from index ${startIndex} to ${endIndex}`); // Добавлено логирование
    for (let i = startIndex; i <= endIndex; i++) {
        if (rows[i]) { // Проверка существования строки
            rows[i].style.display = ''; // Использовать стандартное отображение (обычно 'table-row')
        }
    }

    // Обновить глобальное состояние текущей страницы
    currentPages[prefix] = page;

    // Обновить кнопки пагинации
    updatePaginationButtons(totalRows, prefix);
}

function updatePaginationButtons(totalRows, prefix) {
    console.log(`updatePaginationButtons called for prefix: ${prefix}, total rows: ${totalRows}`); // Добавлено логирование
    const itemsPerPage = itemsPerPageMap[prefix];
    if (!itemsPerPage || itemsPerPage <= 0) {
        console.error(`[${prefix}] Invalid itemsPerPage in updatePaginationButtons:`, itemsPerPage);
        return;
    }

    const totalPages = Math.ceil(totalRows / itemsPerPage);
    const currentPage = currentPages[prefix];

    // Обновить состояние кнопок prev/next
    const prevButton = document.getElementById(`${prefix}_prevPage`);
    const nextButton = document.getElementById(`${prefix}_nextPage`);
    if (prevButton) prevButton.disabled = (currentPage <= 1);
    if (nextButton) nextButton.disabled = (currentPage >= totalPages);

    // Получить контейнер для номеров страниц
    const pageNumbersContainer = document.getElementById(`${prefix}_pageNumbers`);
    if (!pageNumbersContainer) {
        console.error(`[${prefix}] Element with ID '${prefix}_pageNumbers' not found.`);
        return;
    }
    pageNumbersContainer.innerHTML = ''; // Очистить существующие кнопки

    // Пагинация не нужна, если всего одна страница или ноль
    if (totalPages <= 1) {
        console.log(`[${prefix}] Total pages (${totalPages}) <= 1, skipping button generation.`); // Добавлено логирование
        return;
    }

    const maxVisibleButtons = 7; // Макс. видимых кнопок (напр., 1 ... 4 5 6 ... 10)

    // --- Вспомогательные функции ---
    function addPageButton(i) {
        const pageButton = document.createElement('button');
        pageButton.textContent = i;
        pageButton.addEventListener('click', (event) => {
            event.preventDefault();
            console.log(`[${prefix}] Page button ${i} clicked.`); // Добавлено логирование
            // Переполучить строки на случай изменения DOM
            const table = document.getElementById(`${prefix}_table`);
            const currentRows = table ? Array.from(table.querySelectorAll('tbody tr')).filter(row => !row.querySelector('td[colspan]')) : [];
            goToPage(i, currentRows, prefix);
        });

        if (i === currentPage) {
            pageButton.classList.add('active');
        }
        pageNumbersContainer.appendChild(pageButton);
    }

    function addEllipsis() {
        const ellipsis = document.createElement('span');
        ellipsis.textContent = '...';
        ellipsis.className = 'pagination-ellipsis';
        pageNumbersContainer.appendChild(ellipsis);
    }
    // --- Конец вспомогательных функций ---

    // Логика отображения кнопок с многоточием
    if (totalPages <= maxVisibleButtons) {
        // Показать все номера страниц, если их мало
        for (let i = 1; i <= totalPages; i++) {
            addPageButton(i);
        }
    } else {
        // Показать первую страницу
        addPageButton(1);

        // Рассчитать видимый диапазон вокруг текущей страницы
        let start = Math.max(2, currentPage - Math.floor((maxVisibleButtons - 3) / 2));
        let end = Math.min(totalPages - 1, currentPage + Math.ceil((maxVisibleButtons - 3) / 2));

        // Корректировка диапазона, если близко к началу
        if (currentPage < maxVisibleButtons - 2) {
            end = maxVisibleButtons - 2;
        }
        // Корректировка диапазона, если близко к концу
        if (currentPage > totalPages - (maxVisibleButtons - 3)) {
            start = totalPages - (maxVisibleButtons - 3);
        }

        // Многоточие после первой страницы?
        if (start > 2) {
            addEllipsis();
        }

        // Кнопки в среднем диапазоне
        for (let i = start; i <= end; i++) {
            addPageButton(i);
        }

        // Многоточие перед последней страницей?
        if (end < totalPages - 1) {
            addEllipsis();
        }

        // Показать последнюю страницу
        addPageButton(totalPages);
    }
    console.log(`[${prefix}] Finished generating pagination buttons.`); // Добавлено логирование
}

// --- Функция инициализации ---

function setupTablePagination(tableId) {
    console.log(`Setting up pagination for table: ${tableId}`);
    const table = document.getElementById(tableId);
    if (!table) {
        console.error(`Setup Error: Table with ID '${tableId}' not found.`);
        return;
    }

    const tbody = table.querySelector('tbody');
    if (!tbody) {
        console.error(`Setup Error: Tbody not found in table '${tableId}'.`);
        return;
    }

    const prefix = tableId.split('_')[0]; // Original line
    // const prefix = 'calculationHistory';    // Modified line
    if (!prefix) {
        console.error(`Setup Error: Could not determine prefix for table '${tableId}'.`);
        return;
    }
    // ...
    console.log(`[${prefix}] Determined prefix.`); // Добавлено логирование


    // Получить начальные строки (отфильтровать строки "нет данных")
    const initialRows = Array.from(tbody.querySelectorAll('tr')).filter(row => !row.querySelector('td[colspan]'));
    console.log(`[${prefix}] Found ${initialRows.length} initial data rows.`); // Добавлено логирование

    // --- Проверка наличия обязательных элементов ---
    const requiredElements = [
        `${prefix}_totalItems`, `${prefix}_pageStart`, `${prefix}_pageEnd`,
        `${prefix}_prevPage`, `${prefix}_nextPage`, `${prefix}_pageNumbers`,
        `${prefix}_itemsPerPage`, `${prefix}_pageJump`, `${prefix}_pageJumpBtn`
    ];
    let elementsMissing = false;
    requiredElements.forEach(elId => {
        if (!document.getElementById(elId)) {
            console.error(`Setup Error (${prefix}): Element with ID '${elId}' not found.`);
            elementsMissing = true;
        }
    });
    if (elementsMissing) {
        console.error(`[${prefix}] Stopping setup due to missing elements.`);
        return; // Остановить настройку для этой таблицы, если элементы отсутствуют
    }
    console.log(`[${prefix}] All required elements found.`); // Добавлено логирование
    // --- Конец проверки элементов ---


    // --- Настройка обработчиков событий (с клонированием для предотвращения дубликатов) ---

    // Кнопка Prev
    const prevButton = document.getElementById(`${prefix}_prevPage`);
    const newPrevButton = prevButton.cloneNode(true);
    prevButton.parentNode.replaceChild(newPrevButton, prevButton);
    newPrevButton.addEventListener('click', (event) => {
        event.preventDefault();
        console.log(`[${prefix}] Prev button clicked.`); // Добавлено логирование
        const currentRows = Array.from(tbody.querySelectorAll('tr')).filter(row => !row.querySelector('td[colspan]'));
        if (currentPages[prefix] > 1) {
            goToPage(currentPages[prefix] - 1, currentRows, prefix);
        }
    });

    // Кнопка Next
    const nextButton = document.getElementById(`${prefix}_nextPage`);
    const newNextButton = nextButton.cloneNode(true);
    nextButton.parentNode.replaceChild(newNextButton, nextButton);
    newNextButton.addEventListener('click', (event) => {
        event.preventDefault();
        console.log(`[${prefix}] Next button clicked.`); // Добавлено логирование
        const currentRows = Array.from(tbody.querySelectorAll('tr')).filter(row => !row.querySelector('td[colspan]'));
        const currentTotalPages = Math.ceil(currentRows.length / itemsPerPageMap[prefix]);
        if (currentPages[prefix] < currentTotalPages) {
            goToPage(currentPages[prefix] + 1, currentRows, prefix);
        }
    });

    // Селектор Items Per Page
    const itemsPerPageSelect = document.getElementById(`${prefix}_itemsPerPage`);
    const newItemsPerPageSelect = itemsPerPageSelect.cloneNode(true);
    itemsPerPageSelect.parentNode.replaceChild(newItemsPerPageSelect, itemsPerPageSelect);
    newItemsPerPageSelect.value = itemsPerPageMap[prefix]; // Установить начальное значение
    newItemsPerPageSelect.addEventListener('change', function (event) {
        const newItemsPerPage = parseInt(event.target.value);
        console.log(`[${prefix}] Items per page changed to ${newItemsPerPage}.`); // Добавлено логирование
        if (!isNaN(newItemsPerPage) && newItemsPerPage > 0) {
            itemsPerPageMap[prefix] = newItemsPerPage;
            const currentRows = Array.from(tbody.querySelectorAll('tr')).filter(row => !row.querySelector('td[colspan]'));
            goToPage(1, currentRows, prefix); // Сбросить на первую страницу
        }
    });

    // Поле и кнопка Page Jump
    const pageJumpInput = document.getElementById(`${prefix}_pageJump`);
    const pageJumpBtn = document.getElementById(`${prefix}_pageJumpBtn`);
    const newPageJumpInput = pageJumpInput.cloneNode(true);
    const newPageJumpBtn = pageJumpBtn.cloneNode(true);
    pageJumpInput.parentNode.replaceChild(newPageJumpInput, pageJumpInput);
    pageJumpBtn.parentNode.replaceChild(newPageJumpBtn, pageJumpBtn);

    newPageJumpBtn.addEventListener('click', function (event) {
        event.preventDefault();
        const inputEl = newPageJumpInput; // Использовать клонированное поле
        let pageNum = parseInt(inputEl.value);
        console.log(`[${prefix}] Page jump button clicked, value: ${pageNum}.`); // Добавлено логирование
        const currentRows = Array.from(tbody.querySelectorAll('tr')).filter(row => !row.querySelector('td[colspan]'));
        const currentTotalPages = Math.ceil(currentRows.length / itemsPerPageMap[prefix]);

        if (isNaN(pageNum)) pageNum = 1; // По умолчанию 1 при неверном вводе
        pageNum = Math.max(1, Math.min(pageNum, currentTotalPages)); // Ограничить значение

        goToPage(pageNum, currentRows, prefix);
        inputEl.value = pageNum; // Обновить поле ввода ограниченным значением
    });

    newPageJumpInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault(); // Предотвратить отправку формы
            console.log(`[${prefix}] Enter pressed in page jump input.`); // Добавлено логирование
            newPageJumpBtn.click(); // Вызвать событие click клонированной кнопки
        }
    });

    // --- Начальное отображение ---
    // Вызвать goToPage для корректного отображения первой страницы
    goToPage(1, initialRows, prefix);
    console.log(`Pagination setup complete for ${prefix}`);
}

// --- DOM Ready ---
document.addEventListener('DOMContentLoaded', function () {
    console.log("DOM Loaded. Setting up pagination..."); // Это сообщение должно появиться в консоли ПЕРЕД ошибками
    setupTablePagination('apartments_table');
    setupTablePagination('calculationHistory_table'); // Убедитесь, что этот вызов ЗДЕСЬ
});