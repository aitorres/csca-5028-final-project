document.addEventListener('DOMContentLoaded', function() {
  // Track if user is hovering over the table
  let isHoveringTable = false;

  // Chart instances
  let sourceChart, sentiment24hChart, sentimentOverallChart;

  // Chart color schemes
  const sourceColors = ['#0d6efd', '#fd7e14'];
  const sentimentColors = {
    'positive': '#198754',
    'neutral': '#6c757d',
    'negative': '#dc3545'
  };

  // Function to create or update pie chart
  function createOrUpdateChart(canvasId, chartInstance, data, colors) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    if (chartInstance) {
      chartInstance.destroy();
    }

    const chartColors = colors || data.labels.map((_, index) => sourceColors[index % sourceColors.length]);

    return new Chart(ctx, {
      type: 'pie',
      data: {
        labels: data.labels,
        datasets: [{
          data: data.data,
          backgroundColor: chartColors,
          borderWidth: 2,
          borderColor: '#fff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              padding: 20,
              usePointStyle: true,
              font: {
                size: 12
              }
            }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const label = context.label || '';
                const value = context.parsed;
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const percentage = ((value / total) * 100).toFixed(1);
                return `${label}: ${value} (${percentage}%)`;
              }
            }
          }
        }
      }
    });
  }

  // Function to fetch and update charts
  async function refreshCharts() {
    try {
      // Fetch source data
      const sourceResponse = await fetch('/api/posts/statistics/sources');
      if (sourceResponse.ok) {
        const sourceData = await sourceResponse.json();
        sourceChart = createOrUpdateChart('sourceChart', sourceChart, sourceData, sourceColors);
      }

      // Fetch 24h sentiment data
      const sentiment24hResponse = await fetch('/api/posts/statistiscs/sentiment?hours=24');
      if (sentiment24hResponse.ok) {
        const sentiment24hData = await sentiment24hResponse.json();
        const sentiment24hColors = sentiment24hData.labels.map(label => sentimentColors[label]);
        sentiment24hChart = createOrUpdateChart('sentiment24hChart', sentiment24hChart, sentiment24hData, sentiment24hColors);
      }

      // Fetch overall sentiment data
      const sentimentOverallResponse = await fetch('/api/posts/statistics/sentiment');
      if (sentimentOverallResponse.ok) {
        const sentimentOverallData = await sentimentOverallResponse.json();
        const sentimentOverallColors = sentimentOverallData.labels.map(label => sentimentColors[label]);
        sentimentOverallChart = createOrUpdateChart('sentimentOverallChart', sentimentOverallChart, sentimentOverallData, sentimentOverallColors);
      }

    } catch (error) {
      console.error('Error fetching chart data:', error);
    }
  }

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
        targets: 0, // Date column
        width: "20%"
      },
      {
        targets: 1, // User column
        width: "20%"
      },
      {
        targets: 2, // Content column
        width: "40%"
      },
      {
        targets: 3, // Sentiment column
        width: "20%"
      },
      {
        targets: 3, // Sentiment column
        render: function(data, type, row) {
          // Only apply the badge rendering for display
          if (type === 'display') {
            let badgeClass = 'bg-secondary';
            switch(data) {
              case 'positive': badgeClass = 'bg-success'; break;
              case 'neutral': badgeClass = 'bg-secondary'; break;
              case 'negative': badgeClass = 'bg-danger'; break;
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

  // Track table hover state
  $('#eventsTable').on('mouseenter', function() {
    isHoveringTable = true;
  }).on('mouseleave', function() {
    isHoveringTable = false;
  });

  // Function to show spinner overlay on table
  function showTableSpinner() {
    const tableWrapper = document.querySelector('#eventsTable_wrapper');
    if (!document.querySelector('.table-spinner-overlay')) {
      const spinnerOverlay = document.createElement('div');
      spinnerOverlay.className = 'table-spinner-overlay';
      spinnerOverlay.style.cssText = `
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(255, 255, 255, 0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
      `;
      spinnerOverlay.innerHTML = `
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      `;
      tableWrapper.style.position = 'relative';
      tableWrapper.appendChild(spinnerOverlay);
    }
  }

  // Function to hide spinner overlay
  function hideTableSpinner() {
    const spinnerOverlay = document.querySelector('.table-spinner-overlay');
    if (spinnerOverlay) {
      spinnerOverlay.remove();
    }
  }

  // Function to show confirmation message
  function showConfirmationMessage(message = 'Table data refreshed successfully!') {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-info alert-dismissible fade show';
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
      <i class="fas fa-sync-alt me-2"></i>${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    // Insert the alert before the table card
    const tableCard = document.querySelector('.card');
    tableCard.parentNode.insertBefore(alertDiv, tableCard);

    // Remove the alert after 5 seconds
    setTimeout(() => {
      alertDiv.classList.remove('show');
      setTimeout(() => alertDiv.remove(), 150);
    }, 5000);
  }

  // Function to fetch and update table data
  async function refreshTableData() {
    // Don't refresh if user is hovering over the table
    if (isHoveringTable) {
      return;
    }

    try {
      showTableSpinner();

      const response = await fetch('/api/posts');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const posts = await response.json();

      // Clear existing table data
      eventsTable.clear();

      // Add new data to table
      posts.forEach(post => {
        eventsTable.row.add([
          post.created_at || new Date().toISOString(),
          post.source || 'Unknown',
          post.text || '',
          post.sentiment || 'Unknown'
        ]);
      });

      // Redraw the table
      eventsTable.draw();

      hideTableSpinner();
      showConfirmationMessage();

    } catch (error) {
      console.error('Error fetching posts:', error);
      hideTableSpinner();
      showConfirmationMessage('Failed to refresh table data. Please try again.');
    }
  }

  // Load data on page load
  refreshTableData();
  refreshCharts();

  // Set up auto-refresh every 30 seconds
  setInterval(() => {
    refreshTableData();
    refreshCharts();
  }, 30000);

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
