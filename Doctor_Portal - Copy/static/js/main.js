document.addEventListener('DOMContentLoaded', () => {
    // Doctor Portal functionality
    const addSlotForm = document.getElementById('add-slot-form');
    if (addSlotForm) {
        addSlotForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const start_time = document.getElementById('start_time').value;
            const end_time = document.getElementById('end_time').value;
            const location = document.getElementById('location').value;
            const notes = document.getElementById('notes').value;

            const response = await fetch('/api/add_slot', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ start_time, end_time, location, notes })
            });

            const result = await response.json();
            alert(result.message);
            if (result.status === 'success') {
                window.location.reload();
            }
        });
    }

    // Patient Portal functionality
    document.querySelectorAll('.book-btn').forEach(button => {
        button.addEventListener('click', async (event) => {
            const slotId = event.target.dataset.slotId;
            const response = await fetch(`/api/book_slot/${slotId}`, {
                method: 'POST'
            });

            const result = await response.json();
            alert(result.message);
            if (result.status === 'success') {
                window.location.reload();
            }
        });
    });
});