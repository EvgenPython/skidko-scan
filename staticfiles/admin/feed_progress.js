(function () {
    // запускаем только на странице списка объектов FeedFile
    if (!window.location.href.includes('/feeds/feedfile/')) {
        return;
    }

    function updateProgress() {
        const rows = document.querySelectorAll('#result_list tbody tr');

        rows.forEach(row => {
            const pk = row.querySelector('th').innerText.trim();

            fetch(`/admin/feeds/feedfile/progress/${pk}/`)
                .then(response => response.json())
                .then(data => {
                    const progressCell = row.querySelector('td.field-progress_display');

                    if (!progressCell) return;

                    // обновляем HTML прогресс-бара
                    progressCell.innerHTML = `
                        <div style="width:100px; border:1px solid #ccc; background:#eee">
                            <div style="width:${data.progress}%; background:${data.progress === 100 ? '#4caf50' : '#2196F3'}; color:white; text-align:center;">
                                ${data.progress}%
                            </div>
                        </div>
                    `;
                });
        });
    }

    setInterval(updateProgress, 2000);
})();
