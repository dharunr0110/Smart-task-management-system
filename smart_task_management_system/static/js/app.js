// Confirm before deleting a task entry.
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.js-confirm-delete').forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!window.confirm('Delete this entry? This cannot be undone.')) {
                event.preventDefault();
            }
        });
    });
});
