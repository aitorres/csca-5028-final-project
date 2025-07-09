document.addEventListener('DOMContentLoaded', function() {
  // Initialize DataTable
  const eventsTable = $('#eventsTable').DataTable({
    responsive: true,
    language: {
      search: "_INPUT_",
      searchPlaceholder: "Search content...",
      emptyTable: "No data available",
      info: "Showing _START_ to _END_ of _TOTAL_ entries",
      infoEmpty: "Showing 0 to 0 of 0 entries",
      infoFiltered: "(filtered from _MAX_ total entries)"
    },
    order: [[0, 'desc']], // Sort by date descending by default
    columnDefs: [
      {
        targets: 3, // Sentiment column
        render: function(data, type, row) {
          // Only apply the badge rendering for display
          if (type === 'display') {
            let badgeClass = 'bg-secondary';
            switch(data) {
              case 'Positive': badgeClass = 'bg-success'; break;
              case 'Neutral': badgeClass = 'bg-secondary'; break;
              case 'Negative': badgeClass = 'bg-danger'; break;
            }
            return `<span class="badge ${badgeClass}">${data}</span>`;
          }
          // Return raw data for sorting/filtering
          return data;
        }
      },
      {
        targets: 2, // Content column
        render: function(data, type, row) {
          // Truncate long content for display, but keep full text for search
          if (type === 'display' && data.length > 300) {
            return `<span title="${data.replace(/"/g, '&quot;')}">${data.substr(0, 300)}...</span>`;
          }
          return data;
        }
      },
      {
        targets: 0, // Date column
        render: function(data, type, row) {
          // Format for display but keep ISO for sorting
          if (type === 'display' || type === 'filter') {
            const date = new Date(data);
            return date.toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'long',
              day: 'numeric'
            });
          }
          return data;
        }
      }
    ],
    dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>rtip'
  });

  // Form validation
  const entryForm = document.querySelector('#addEventModal form');
  if (entryForm) {
    const saveButton = document.querySelector('#addEventModal .btn-primary');

    saveButton.addEventListener('click', function() {
      if (!entryForm.checkValidity()) {
        entryForm.classList.add('was-validated');
      } else {
        // Get form values
        const user = document.getElementById('entryUser').value;
        const content = document.getElementById('entryContent').value;

        const currentDate = new Date();
        const formattedDate = currentDate.toISOString().split('T')[0]; // YYYY-MM-DD format

        // TODO: submit to API

        // Create a success alert
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success alert-dismissible fade show';
        alertDiv.setAttribute('role', 'alert');
        alertDiv.innerHTML = `
          <strong>Success!</strong> Your post has been submitted for analysis, it will be added to the table as soon as the analysis completes.
          <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        // Insert the alert before the table
        const tableCard = document.querySelector('.card');
        tableCard.parentNode.insertBefore(alertDiv, tableCard);

        // Reset the form and close the modal
        entryForm.reset();
        const modal = bootstrap.Modal.getInstance(document.querySelector('#addEventModal'));
        modal.hide();

        // Remove the alert after 5 seconds
        setTimeout(() => {
          alertDiv.classList.remove('show');
          setTimeout(() => alertDiv.remove(), 150);
        }, 5000);
      }
    });
  }
});
