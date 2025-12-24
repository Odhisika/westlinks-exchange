const API_URL = window.location.origin + '/api';
const currentUser = localStorage.getItem('coinvibe_user') ? JSON.parse(localStorage.getItem('coinvibe_user')) : null;
const tokenRaw = localStorage.getItem('coinvibe_token');
const authToken = tokenRaw && tokenRaw !== 'null' && tokenRaw !== 'undefined' && tokenRaw !== '' ? tokenRaw : null;

if (!authToken || !currentUser) {
  window.location.href = '/login';
}

let allTransactions = [];
let currentFilters = { status: '', type: '' };

function initHeader() {
  const name = currentUser && (currentUser.name || currentUser.username || currentUser.full_name) ?
    (currentUser.name || currentUser.username || currentUser.full_name) : '';
  document.getElementById('dashUserName').textContent = name;
  document.getElementById('dashAvatar').textContent = name ? name.charAt(0).toUpperCase() : 'U';
}

function logout() {
  localStorage.removeItem('coinvibe_token');
  localStorage.removeItem('coinvibe_user');
  window.location.href = '/';
}

function toggleSidebar() {
  const sidebar = document.getElementById('dashboardSidebar');
  const backdrop = document.getElementById('sidebarBackdrop');
  sidebar.classList.toggle('open');
  sidebar.classList.toggle('active');
  if (backdrop) {
    backdrop.classList.toggle('visible');
    backdrop.classList.toggle('active');
  }
}

async function loadTransactions() {
  try {
    if (!authToken) {
      console.error('No auth token');
      return;
    }

    const res = await fetch(`${API_URL}/vendors/me/transactions`, {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });

    if (res.status === 401) {
      window.location.href = '/login';
      return;
    }

    const data = await res.json();
    allTransactions = data.transactions || [];

    document.getElementById('transactionCount').textContent = `${allTransactions.length} transaction${allTransactions.length !== 1 ? 's' : ''} found`;

    renderTransactions(allTransactions);
  } catch (e) {
    console.error('Failed to load transactions:', e);

    // Desktop view
    document.getElementById('transactionsTable').innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">
              <i data-lucide="alert-circle" style="width: 40px; height: 40px; color: #ef4444;"></i>
            </div>
            <h4 class="empty-state-title">Error loading transactions</h4>
            <p class="empty-state-desc">${e.message}</p>
          </div>`;

    // Mobile view
    document.getElementById('transactionsMobile').innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">
              <i data-lucide="alert-circle" style="width: 40px; height: 40px; color: #ef4444;"></i>
            </div>
            <h4 class="empty-state-title">Error loading transactions</h4>
            <p class="empty-state-desc">${e.message}</p>
          </div>`;

    if (window.lucide && lucide.createIcons) lucide.createIcons();
  }
}

function applyFilters() {
  currentFilters.status = document.getElementById('filterStatus').value;
  currentFilters.type = document.getElementById('filterType').value;

  let filtered = allTransactions;

  if (currentFilters.status) {
    filtered = filtered.filter(t => t.status === currentFilters.status);
  }

  if (currentFilters.type) {
    filtered = filtered.filter(t => t.type === currentFilters.type);
  }

  document.getElementById('transactionCount').textContent = `${filtered.length} transaction${filtered.length !== 1 ? 's' : ''} found`;
  renderTransactions(filtered);
}

function clearFilters() {
  document.getElementById('filterStatus').value = '';
  document.getElementById('filterType').value = '';
  currentFilters = { status: '', type: '' };
  document.getElementById('transactionCount').textContent = `${allTransactions.length} transaction${allTransactions.length !== 1 ? 's' : ''} found`;
  renderTransactions(allTransactions);
}

function renderTransactions(transactions) {
  if (transactions.length === 0) {
    // Desktop view
    document.getElementById('transactionsTable').innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">
              <i data-lucide="receipt" style="width: 40px; height: 40px;"></i>
            </div>
            <h4 class="empty-state-title">No transactions found</h4>
            <p class="empty-state-desc">Try adjusting your filters or create a new transaction</p>
          </div>`;

    // Mobile view
    document.getElementById('transactionsMobile').innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">
              <i data-lucide="receipt" style="width: 40px; height: 40px;"></i>
            </div>
            <h4 class="empty-state-title">No transactions found</h4>
            <p class="empty-state-desc">Try adjusting your filters or create a new transaction</p>
          </div>`;

    if (window.lucide && lucide.createIcons) lucide.createIcons();
    return;
  }

  // Render Desktop Table View
  const rows = transactions.map(t => `
        <tr>
          <td class="font-mono" style="font-size: 0.875rem;">
            <a href="/transactions/${t.payment_id}" class="text-primary" style="text-decoration:none; font-weight:600;">${t.payment_id}</a>
          </td>
          <td>${t.type}</td>
          <td>${t.fiat_amount ? `₵${Number(t.fiat_amount).toFixed(2)}` : `${t.crypto_amount} ${t.crypto_symbol || 'USDT'}`}</td>
          <td>
            <span class="badge ${getStatusBadge(t.status)}">${t.status}</span>
            ${t.delivery_status && t.delivery_status !== 'pending' ? `<br><span class="badge ${getStatusBadge(t.delivery_status)}" style="margin-top:4px; font-size:0.7rem;">${t.delivery_status}</span>` : ''}
          </td>
          <td class="hide-mobile font-mono" style="font-size: 0.75rem; max-width: 150px; overflow: hidden; text-overflow: ellipsis;">${t.wallet_address || '-'}</td>
          <td class="hide-mobile">${t.network || '-'}</td>
          <td class="hide-mobile">${t.crypto_tx_hash ? `<span class="font-mono" style="font-size: 0.75rem;">${t.crypto_tx_hash.substring(0, 10)}...</span>` : '-'}</td>
          <td style="font-size: 0.875rem;">${new Date(t.created_at).toLocaleString()}</td>
          <td>
            <a href="/transactions/${t.payment_id}" class="btn btn-sm btn-secondary" style="padding: 6px 12px; font-size: 0.75rem; text-decoration: none;">View</a>
          </td>
        </tr>
      `).join('');

  document.getElementById('transactionsTable').innerHTML = `
        <div class="table-responsive">
          <table class="dashboard-table">
            <thead>
              <tr>
                <th>Payment ID</th>
                <th>Type</th>
                <th>Amount</th>
                <th>Status</th>
                <th class="hide-mobile">Wallet Address</th>
                <th class="hide-mobile">Network</th>
                <th class="hide-mobile">TX Hash</th>
                <th>Date</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>`;

  // Render Mobile Card View
  const cards = transactions.map(t => `
        <div class="transaction-card">
          <div class="transaction-card-header">
            <div>
              <div class="transaction-card-id">${t.payment_id}</div>
              <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 4px;">
                ${new Date(t.created_at).toLocaleString()}
              </div>
            </div>
            <span class="badge ${getStatusBadge(t.status)}">${t.status}</span>
          </div>
          <div class="transaction-card-body">
            <div class="transaction-card-row">
              <span class="transaction-card-label">Type</span>
              <span class="transaction-card-value">${t.type}</span>
            </div>
            <div class="transaction-card-row">
              <span class="transaction-card-label">Amount</span>
              <span class="transaction-card-value">${t.fiat_amount ? `₵${Number(t.fiat_amount).toFixed(2)}` : `${t.crypto_amount} ${t.crypto_symbol || 'USDT'}`}</span>
            </div>
            ${t.wallet_address ? `
            <div class="transaction-card-row">
              <span class="transaction-card-label">Wallet</span>
              <span class="transaction-card-value font-mono" style="font-size: 0.75rem; max-width: 150px; overflow: hidden; text-overflow: ellipsis;">${t.wallet_address}</span>
            </div>` : ''}
            ${t.network ? `
            <div class="transaction-card-row">
              <span class="transaction-card-label">Network</span>
              <span class="transaction-card-value">${t.network}</span>
            </div>` : ''}
            ${t.delivery_status && t.delivery_status !== 'pending' ? `
            <div class="transaction-card-row">
              <span class="transaction-card-label">Delivery Status</span>
              <span class="badge ${getStatusBadge(t.delivery_status)}">${t.delivery_status}</span>
            </div>` : ''}
          </div>
          <div class="transaction-card-footer">
            <a href="/transactions/${t.payment_id}" class="btn btn-secondary" style="width: 100%; text-decoration: none; text-align: center;">View Details</a>
          </div>
        </div>
      `).join('');

  document.getElementById('transactionsMobile').innerHTML = cards;

  if (window.lucide && lucide.createIcons) lucide.createIcons();
}

function getStatusBadge(status) {
  const badges = {
    pending: 'badge-warning',
    paid: 'badge-info',
    sent: 'badge-primary',
    confirmed: 'badge-success',
    completed: 'badge-success',
    failed: 'badge-danger',
    processing: 'badge-info'
  };
  return badges[status] || 'badge-secondary';
}

function exportTransactions() {
  // Convert to CSV format
  const headers = ['Payment ID', 'Type', 'Amount', 'Status', 'Wallet', 'Network', 'TX Hash', 'Date'];
  const rows = allTransactions.map(t => [
    t.payment_id,
    t.type,
    t.fiat_amount || t.crypto_amount,
    t.status,
    t.wallet_address || '',
    t.network || '',
    t.crypto_tx_hash || '',
    new Date(t.created_at).toLocaleString()
  ]);

  let csv = headers.join(',') + '\n';
  rows.forEach(row => {
    csv += row.map(cell => `"${cell}"`).join(',') + '\n';
  });

  const blob = new Blob([csv], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `transactions_${new Date().toISOString().split('T')[0]}.csv`;
  a.click();
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
  initHeader();
  loadTransactions();

  // Initialize Lucide icons
  if (window.lucide && lucide.createIcons) {
    lucide.createIcons();
  }

  // Filter button
  const filterBtn = document.getElementById('filterBtn');
  if (filterBtn) {
    filterBtn.addEventListener('click', function () {
      const panel = document.getElementById('filterPanel');
      panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    });
  }

  // Export button
  const exportBtn = document.getElementById('exportBtn');
  if (exportBtn) {
    exportBtn.addEventListener('click', exportTransactions);
  }

  // Sidebar backdrop
  const backdrop = document.getElementById('sidebarBackdrop');
  if (backdrop) {
    backdrop.addEventListener('click', toggleSidebar);
  }

  // Close sidebar when clicking outside on mobile
  document.addEventListener('click', function (e) {
    const sidebar = document.getElementById('dashboardSidebar');
    const toggle = document.querySelector('.mobile-nav-toggle');
    const backdrop = document.getElementById('sidebarBackdrop');

    if (sidebar && sidebar.classList.contains('active') &&
      !sidebar.contains(e.target) &&
      toggle && !toggle.contains(e.target)) {
      sidebar.classList.remove('active');
      sidebar.classList.remove('open');
      if (backdrop) {
        backdrop.classList.remove('active');
        backdrop.classList.remove('visible');
      }
    }
  });
});