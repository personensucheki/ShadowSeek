// Persistenz & Restore der Search-Inputs (außer Datei-Upload)

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('search-form');
    const resetBtn = document.getElementById('reset-btn');
    const fields = [
        'query', 'real_name', 'clan_name', 'age', 'postal_code'
    ];
    const platformCheckboxes = () => Array.from(document.querySelectorAll('input[name="platforms"]'));
    const deepSearch = document.querySelector('input[name="deep_search"]');
    const storageKey = 'shadowseek_search_inputs';

    // Restore
    function restoreInputs() {
        const data = JSON.parse(localStorage.getItem(storageKey) || '{}');
        fields.forEach(f => {
            if (data[f] !== undefined && form.elements[f]) {
                form.elements[f].value = data[f];
            }
        });
        if (Array.isArray(data.platforms)) {
            platformCheckboxes().forEach(cb => {
                cb.checked = data.platforms.includes(cb.value);
            });
        }
        if (typeof data.deep_search === 'boolean') {
            deepSearch.checked = data.deep_search;
        }
    }

    // Save
    function saveInputs() {
        const data = {};
        fields.forEach(f => {
            data[f] = form.elements[f]?.value || '';
        });
        data.platforms = platformCheckboxes().filter(cb => cb.checked).map(cb => cb.value);
        data.deep_search = deepSearch.checked;
        localStorage.setItem(storageKey, JSON.stringify(data));
    }

    // Clear
    function clearInputs() {
        localStorage.removeItem(storageKey);
        fields.forEach(f => {
            if (form.elements[f]) form.elements[f].value = '';
        });
        platformCheckboxes().forEach(cb => { cb.checked = true; });
        deepSearch.checked = false;
    }

    // Save on change
    form.addEventListener('input', function (e) {
        if (e.target.name !== 'image') saveInputs();
    });
    form.addEventListener('change', function (e) {
        if (e.target.name !== 'image') saveInputs();
    });

    // Restore on load
    restoreInputs();

    // Reset-Button
    if (resetBtn) {
        resetBtn.addEventListener('click', function () {
            clearInputs();
        });
    }
});
