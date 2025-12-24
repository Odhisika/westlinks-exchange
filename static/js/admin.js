
const API_URL = window.location.origin + '/api';
const assetsToast = document.getElementById('assetsToast');
let adminAssets = [];

// Auth Check
(function () {
    const sessionToken = localStorage.getItem('admin_session_token');
    if (!sessionToken) {
        window.location.href = '/admin/login';
        return;
    }
    // Verify session
    fetch(`${API_URL}/admin/auth/session-status`, {
        headers: { 'Authorization': `Bearer ${sessionToken}` }
    })
        .then(res => res.json())
        .then(data => {
            if (!data.valid) {
                localStorage.removeItem('admin_session_token');
                window.location.href = '/admin/login';
            }
        })
        .catch(() => {
            localStorage.removeItem('admin_session_token');
            window.location.href = '/admin/login';
        });
})();

async function adminLogout() {
    try {
        const sessionToken = localStorage.getItem('admin_session_token');
        if (sessionToken) {
            await fetch(`${API_URL}/admin/auth/logout`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${sessionToken}` }
            });
        }
    } finally {
        localStorage.removeItem('admin_session_token');
        window.location.href = '/admin/login';
    }
}

function getAdminKeyOrAlert() {
    const key = localStorage.getItem('admin_session_token');
    if (!key) { alert('Please login as admin'); return null; }
    return key;
}

// Navigation
function switchTab(tabId) {
    localStorage.setItem('admin_last_tab', tabId);
    // Update sidebar active state
    document.querySelectorAll('.sidebar-link').forEach(link => {
        if (link.dataset.tab === tabId) link.classList.add('active');
        else link.classList.remove('active');
    });

    // Show/Hide sections
    document.querySelectorAll('.tab-content').forEach(section => {
        if (section.id === `tab-${tabId}`) section.classList.remove('hidden');
        else section.classList.add('hidden');
    });

    // Load data
    if (tabId === 'overview') loadOverview();
    if (tabId === 'vendors') loadVendors();
    if (tabId === 'transactions') loadTransactions();
    if (tabId === 'orders') loadBuyOrders();
    if (tabId === 'sell-orders') loadSellOrders();
    if (tabId === 'exchange-orders') loadExchangeOrders();
    if (tabId === 'logs') loadLogs();
    if (tabId === 'settings') loadSettingsData();
    if (tabId === 'exchanges') { loadExchanges(); loadExchangeRates(); loadExchangePaymentSettings(); }
    if (tabId === 'assets') loadAdminAssets();

    // Mobile: close sidebar
    if (window.innerWidth <= 768) toggleSidebar();
}

function toggleSidebar() {
    document.getElementById('dashboardSidebar').classList.toggle('active');
    const backdrop = document.getElementById('sidebarBackdrop');
    if (backdrop) backdrop.classList.toggle('visible');
}

const backdrop = document.getElementById('sidebarBackdrop');
if (backdrop) backdrop.addEventListener('click', toggleSidebar);

// --- Data Loading Functions ---

async function loadOverview() {
    const key = getAdminKeyOrAlert(); if (!key) return;
    try {
        const res = await fetch(`${API_URL}/admin/overview`, { headers: { 'Authorization': `Bearer ${key}` } });
        const data = await res.json();
        if (!data.success) return;
        const o = data.overview;
        document.getElementById('statVendors').textContent = o.vendors;
        document.getElementById('statTx').textContent = o.transactions;
        document.getElementById('statTxPending').textContent = o.tx_pending;
        document.getElementById('statTxCompleted').textContent = o.tx_completed;
        document.getElementById('statOrders').textContent = o.buy_orders;
    } catch (e) { console.error(e); }
}

async function loadVendors(page = 1) {
    const key = getAdminKeyOrAlert(); if (!key) return;
    const q = document.getElementById('vendorsSearch').value.trim();
    const status = document.getElementById('vendorsStatus').value;
    const params = new URLSearchParams({ page, page_size: 20 });
    if (q) params.append('q', q);
    if (status) params.append('status', status);

    const res = await fetch(`${API_URL}/admin/vendors?${params.toString()}`, { headers: { 'Authorization': `Bearer ${key}` } });
    const data = await res.json();
    if (!data.success) return alert(data.detail);

    document.getElementById('vendorsMeta').textContent = `Showing ${data.vendors.length} of ${data.total}`;

    const rows = data.vendors.map(v => `
                <tr>
                    <td class="font-mono text-xs">${v.id}</td>
                    <td>
                        <div class="font-medium">${v.name}</div>
                        <div class="text-xs text-secondary">${v.email}</div>
                    </td>
                    <td>${v.momo_number || '-'}</td>
                    <td>${v.country}</td>
                    <td>₵${(v.balance ?? 0).toFixed(2)}</td>
                    <td>
                        <span class="badge ${v.is_active ? 'badge-success' : 'badge-danger'}">${v.is_active ? 'Active' : 'Inactive'}</span>
                        <span class="badge ${v.is_verified ? 'badge-info' : 'badge-warning'} ml-1">${v.is_verified ? 'Verified' : 'Unverified'}</span>
                    </td>
                    <td>
                        <button class="btn btn-secondary text-xs py-1 px-2" onclick="vendorAction(${v.id}, '${v.is_active ? 'deactivate' : 'activate'}')">${v.is_active ? 'Deactivate' : 'Activate'}</button>
                        <button class="btn btn-secondary text-xs py-1 px-2 ml-1" onclick="vendorAction(${v.id}, '${v.is_verified ? 'unverify' : 'verify'}')">${v.is_verified ? 'Unverify' : 'Verify'}</button>
                        <button class="btn btn-secondary text-xs py-1 px-2 ml-1" style="color: #ef4444;" onclick="vendorAction(${v.id}, 'delete')" title="Delete Vendor">Delete</button>
                    </td>
                </tr>
            `).join('');

    document.getElementById('vendorsTable').innerHTML = `
                <div class="table-responsive">
                    <table class="dashboard-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Vendor</th>
                                <th>MoMo</th>
                                <th>Country</th>
                                <th>Balance</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>${rows}</tbody>
                    </table>
                </div>`;
}

async function vendorAction(id, action) {
    const key = getAdminKeyOrAlert(); if (!key) return;

    // Stronger confirmation for delete action
    if (action === 'delete') {
        if (!confirm(`⚠️ WARNING: This will permanently delete vendor #${id} and all associated data.\n\nThis action CANNOT be undone!\n\nAre you absolutely sure?`)) return;
    } else {
        if (!confirm(`Confirm ${action} vendor #${id}?`)) return;
    }

    const res = await fetch(`${API_URL}/admin/vendors/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${key}` },
        body: JSON.stringify({ action })
    });
    const data = await res.json();
    if (data.success) {
        if (action === 'delete') {
            alert('Vendor deleted successfully');
        }
        loadVendors();
    } else {
        alert(data.detail);
    }
}

async function loadTransactions(page = 1) {
    const key = getAdminKeyOrAlert(); if (!key) return;
    const tx_type = document.getElementById('txType').value;
    const status = document.getElementById('txStatus').value;
    const q = document.getElementById('txSearch').value.trim();
    const params = new URLSearchParams({ page, page_size: 20 });
    if (tx_type) params.append('tx_type', tx_type);
    if (status) params.append('status', status);
    if (q) params.append('q', q);

    const res = await fetch(`${API_URL}/admin/transactions?${params.toString()}`, { headers: { 'Authorization': `Bearer ${key}` } });
    const data = await res.json();
    if (!data.success) return alert(data.detail);

    document.getElementById('txMeta').textContent = `Showing ${data.transactions.length} of ${data.total}`;

    const rows = data.transactions.map(t => `
                <tr>
                    <td class="font-mono text-xs">${t.payment_id}</td>
                    <td>${t.type || '-'}</td>
                    <td>${t.vendor_id || '-'}</td>
                    <td>${t.crypto_amount} ${t.crypto_symbol || 'USDT'}</td>
                    <td>₵${(t.fiat_amount ?? 0).toFixed(2)}</td>
                    <td><span class="badge ${getStatusBadge(t.status)}">${t.status}</span></td>
                    <td class="font-mono text-xs">${t.crypto_tx_hash ? t.crypto_tx_hash.substring(0, 10) + '...' : '-'}</td>
                    <td class="text-xs">${new Date(t.created_at).toLocaleString()}</td>
                </tr>
            `).join('');

    document.getElementById('txTable').innerHTML = `
                <div class="table-responsive">
                    <table class="dashboard-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Type</th>
                                <th>Vendor</th>
                                <th>Crypto</th>
                                <th>Fiat</th>
                                <th>Status</th>
                                <th>Tx Hash</th>
                                <th>Date</th>
                            </tr>
                        </thead>
                        <tbody>${rows}</tbody>
                    </table>
                </div>`;
}

async function loadOrders(page = 1) {
    const key = getAdminKeyOrAlert(); if (!key) return;
    const status = document.getElementById('ordersStatus').value;
    const q = document.getElementById('ordersSearch').value.trim();
    const params = new URLSearchParams({ page, page_size: 20 });
    if (status) params.append('status', status);
    if (q) params.append('q', q);

    const res = await fetch(`${API_URL}/admin/buy-orders?${params.toString()}`, { headers: { 'Authorization': `Bearer ${key}` } });
    const data = await res.json();
    if (!data.success) return alert(data.detail);

    document.getElementById('ordersMeta').textContent = `Showing ${data.orders.length} of ${data.total}`;

    const rows = data.orders.map(o => `
                <tr>
                    <td class="font-mono text-xs">${o.order_id}</td>
                    <td>₵${o.amount_ghs}</td>
                    <td>${o.usdt_amount} USDT</td>
                    <td>${o.rate_usd_to_ghs}</td>
                    <td>${o.network}</td>
                    <td><span class="badge ${getStatusBadge(o.status)}">${o.status}</span></td>
                    <td class="text-xs">${new Date(o.created_at).toLocaleString()}</td>
                </tr>
            `).join('');

    document.getElementById('ordersTable').innerHTML = `
                <div class="table-responsive">
                    <table class="dashboard-table">
                        <thead>
                            <tr>
                                <th>Order ID</th>
                                <th>GHS</th>
                                <th>USDT</th>
                                <th>Rate</th>
                                <th>Network</th>
                                <th>Status</th>
                                <th>Date</th>
                            </tr>
                        </thead>
                        <tbody>${rows}</tbody>
                    </table>
                </div>`;
}

async function loadLogs(page = 1) {
    const key = getAdminKeyOrAlert(); if (!key) return;
    const action = document.getElementById('logsAction').value.trim();
    const vendor_id = document.getElementById('logsVendorId').value.trim();
    const params = new URLSearchParams({ page, page_size: 30 });
    if (action) params.append('action', action);
    if (vendor_id) params.append('vendor_id', vendor_id);

    const res = await fetch(`${API_URL}/admin/audit-logs?${params.toString()}`, { headers: { 'Authorization': `Bearer ${key}` } });
    const data = await res.json();
    if (!data.success) return alert(data.detail);

    document.getElementById('logsMeta').textContent = `Showing ${data.logs.length} of ${data.total}`;

    const rows = data.logs.map(l => `
                <tr>
                    <td class="font-mono text-xs">${l.id}</td>
                    <td>${l.vendor_id ?? '-'}</td>
                    <td>${l.action}</td>
                    <td class="text-xs">${l.details ?? '-'}</td>
                    <td class="text-xs">${new Date(l.created_at).toLocaleString()}</td>
                </tr>
            `).join('');

    document.getElementById('logsTable').innerHTML = `
                <div class="table-responsive">
                    <table class="dashboard-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Vendor</th>
                                <th>Action</th>
                                <th>Details</th>
                                <th>Date</th>
                            </tr>
                        </thead>
                        <tbody>${rows}</tbody>
                    </table>
                </div>`;
}

// --- Exchange Functions ---

async function loadExchangeRates() {
    const key = getAdminKeyOrAlert(); if (!key) return;
    const res = await fetch(`${API_URL}/admin/exchange-rates`, { headers: { 'Authorization': `Bearer ${key}` } });
    const data = await res.json();
    if (data.success && data.rates) {
        document.getElementById('ngnGhsRate').value = data.rates.ngn_to_ghs_rate;
        document.getElementById('ghsNgnRate').value = data.rates.ghs_to_ngn_rate;
        document.getElementById('exchangeFee').value = data.rates.fee_percent;
        document.getElementById('minGhs').value = data.rates.min_exchange_ghs;
        document.getElementById('maxGhs').value = data.rates.max_exchange_ghs;
        document.getElementById('minNgn').value = data.rates.min_exchange_ngn;
        document.getElementById('maxNgn').value = data.rates.max_exchange_ngn;
    }
}

async function updateExchangeRates(e) {
    e.preventDefault();
    const key = getAdminKeyOrAlert(); if (!key) return;
    const payload = {
        ngn_to_ghs_rate: parseFloat(document.getElementById('ngnGhsRate').value),
        ghs_to_ngn_rate: parseFloat(document.getElementById('ghsNgnRate').value),
        fee_percent: parseFloat(document.getElementById('exchangeFee').value),
        min_exchange_ghs: parseFloat(document.getElementById('minGhs').value),
        max_exchange_ghs: parseFloat(document.getElementById('maxGhs').value),
        min_exchange_ngn: parseFloat(document.getElementById('minNgn').value),
        max_exchange_ngn: parseFloat(document.getElementById('maxNgn').value),
    };

    const res = await fetch(`${API_URL}/admin/exchange-rates`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${key}` },
        body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success) alert('Rates updated successfully');
    else alert('Failed to update rates');
}

async function loadExchanges(page = 1) {
    const key = getAdminKeyOrAlert(); if (!key) return;
    const status = document.getElementById('exchangesStatus').value;
    const q = document.getElementById('exchangesSearch').value.trim();
    const params = new URLSearchParams({ page, page_size: 20 });
    if (status) params.append('status', status);
    if (q) params.append('q', q);

    const res = await fetch(`${API_URL}/admin/exchanges?${params.toString()}`, { headers: { 'Authorization': `Bearer ${key}` } });
    const data = await res.json();
    if (!data.success) return alert(data.detail);

    document.getElementById('exchangesMeta').textContent = `Showing ${data.exchanges.length} of ${data.total}`;

    const rows = data.exchanges.map(e => {
        let actions = '';
        if (e.status === 'paid') {
            actions = `<button class="btn btn-primary text-xs py-1 px-2" onclick="exchangeAction('${e.exchange_id}', 'approve')">Approve</button>`;
        } else if (e.status === 'processing') {
            actions = `<button class="btn btn-success text-xs py-1 px-2" onclick="exchangeAction('${e.exchange_id}', 'complete')">Complete</button>`;
        }

        let recipient = '';
        if (e.recipient_details.momo_number) {
            recipient = `MoMo: ${e.recipient_details.momo_number} (${e.recipient_details.recipient_name})`;
        } else if (e.recipient_details.bank_name) {
            recipient = `${e.recipient_details.bank_name}: ${e.recipient_details.account_number}`;
        }

        return `
                <tr>
                    <td class="font-mono text-xs">${e.exchange_id}</td>
                    <td>
                        <div>${e.from_amount} ${e.from_currency}</div>
                        <div class="text-xs text-secondary">Rate: ${e.exchange_rate}</div>
                    </td>
                    <td>
                        <div class="font-bold">${e.to_amount} ${e.to_currency}</div>
                        <div class="text-xs text-secondary">Fee: ${e.fee_amount}</div>
                    </td>
                    <td class="text-xs">${recipient}</td>
                    <td><span class="badge ${getStatusBadge(e.status)}">${e.status}</span></td>
                    <td>
                        <div class="flex gap-1">
                            ${actions}
                        </div>
                    </td>
                </tr>
            `}).join('');

    document.getElementById('exchangesTable').innerHTML = `
                <div class="table-responsive">
                    <table class="dashboard-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>From</th>
                                <th>To</th>
                                <th>Recipient</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>${rows}</tbody>
                    </table>
                </div>`;
}

async function exchangeAction(id, action) {
    const key = getAdminKeyOrAlert(); if (!key) return;
    let notes = '';
    if (action === 'complete') {
        notes = prompt('Enter transaction reference/notes (optional):');
    }

    if (!confirm(`Confirm ${action} exchange ${id}?`)) return;

    const res = await fetch(`${API_URL}/admin/exchanges/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${key}` },
        body: JSON.stringify({ action, admin_notes: notes })
    });
    const data = await res.json();
    if (data.success) loadExchanges();
    else alert(data.detail || 'Action failed');
}

// --- Settings Functions ---

async function loadSettingsData() {
    const key = getAdminKeyOrAlert(); if (!key) return;
    const res = await fetch(`${API_URL}/admin/settings`, { headers: { 'Authorization': `Bearer ${key}` } });
    const data = await res.json();
    if (data.success) {
        const s = data.settings;
        document.getElementById('buyRate').value = s.buy_rate ?? '';
        document.getElementById('sellRate').value = s.sell_rate ?? '';
        document.getElementById('walletAddress').value = s.usdt_wallet_address ?? '';
        document.getElementById('settingsLastUpdated').textContent = s.last_updated ? new Date(s.last_updated).toLocaleString() : 'Never';
    }
    await loadAdminAssets(key);
}

async function updateSettings(e) {
    e.preventDefault();
    const key = getAdminKeyOrAlert(); if (!key) return;
    const payload = {
        buy_rate: parseFloat(document.getElementById('buyRate').value),
        sell_rate: parseFloat(document.getElementById('sellRate').value),
        usdt_wallet_address: document.getElementById('walletAddress').value.trim()
    };

    const res = await fetch(`${API_URL}/admin/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${key}` },
        body: JSON.stringify(payload)
    });
    const data = await res.json();
    const statusBox = document.getElementById('settingsStatusBox');
    statusBox.classList.remove('hidden');
    if (data.success) {
        statusBox.textContent = 'Settings updated successfully.';
        statusBox.className = 'mt-4 p-3 rounded text-sm bg-green-500/10 text-green-500 border border-green-500/20';
        document.getElementById('settingsLastUpdated').textContent = new Date().toLocaleString();
    } else {
        statusBox.textContent = data.detail || 'Failed to update';
        statusBox.className = 'mt-4 p-3 rounded text-sm bg-red-500/10 text-red-500 border border-red-500/20';
    }
    setTimeout(() => statusBox.classList.add('hidden'), 5000);
}

async function loadAdminAssets(key) {
    const res = await fetch(`${API_URL}/admin/assets`, { headers: { 'Authorization': `Bearer ${key}` } });
    const data = await res.json();
    if (!data.success) return;
    adminAssets = data.assets || [];
    renderAdminAssets();
}

function renderAdminAssets() {
    const container = document.getElementById('adminAssetsTable');
    if (!adminAssets.length) {
        container.innerHTML = '<div class="p-4 text-sm text-secondary">No sellable assets configured yet.</div>';
        return;
    }
    const rows = adminAssets.map(asset => `
                <tr>
                    <td>
                        <div class="font-semibold text-primary">${asset.symbol}</div>
                        <div class="text-xs text-secondary">${asset.network}</div>
                    </td>
                    <td>
                        <input id="assetAddress-${asset.id}" value="${(asset.wallet_address || '').replace(/"/g, '&quot;')}" class="form-control text-xs" style="background:transparent;">
                    </td>
                    <td>
                        <input id="assetMemo-${asset.id}" value="${(asset.memo || '').replace(/"/g, '&quot;')}" class="form-control text-xs" style="background:transparent;">
                    </td>
                    <td>
                        <input id="assetRate-${asset.id}" type="number" step="0.0001" value="${asset.sell_rate ?? ''}" class="form-control text-xs" style="background:transparent;">
                    </td>
                    <td class="text-center">
                        <input id="assetEnabled-${asset.id}" type="checkbox" ${asset.sell_enabled ? 'checked' : ''}>
                    </td>
                    <td>
                        <div class="flex gap-1 justify-end">
                            <button class="btn btn-secondary text-xs py-1 px-2" onclick="saveAdminAsset(${asset.id})">Save</button>
                            <button class="btn btn-secondary text-xs py-1 px-2 text-red-500" onclick="deleteAdminAsset(${asset.id})">Del</button>
                        </div>
                    </td>
                </tr>
            `).join('');

    container.innerHTML = `
                <div class="table-responsive">
                    <table class="dashboard-table">
                        <thead>
                            <tr>
                                <th>Asset</th>
                                <th>Wallet</th>
                                <th>Memo</th>
                                <th>Rate</th>
                                <th>Enabled</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>${rows}</tbody>
                    </table>
                </div>`;
}

async function createAdminAsset(event) {
    event.preventDefault();
    const key = getAdminKeyOrAlert(); if (!key) return;

    const payload = {
        symbol: document.getElementById('newAssetSymbol').value.trim().toUpperCase(),
        asset_name: document.getElementById('newAssetName').value.trim(),
        network: document.getElementById('newAssetNetwork').value,
        wallet_address: document.getElementById('newAssetAddress').value.trim(),
        memo: document.getElementById('newAssetMemo').value.trim() || null,
        sell_rate: document.getElementById('newAssetRate').value ? parseFloat(document.getElementById('newAssetRate').value) : null,
        sell_enabled: document.getElementById('newAssetEnabled').checked
    };

    const res = await fetch(`${API_URL}/admin/assets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${key}` },
        body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (data.success) {
        event.target.reset();
        loadAdminAssets(key);
        alert('Asset added successfully');
    } else {
        alert(data.detail || 'Failed to add asset');
    }
}

async function saveAdminAsset(assetId) {
    const key = getAdminKeyOrAlert(); if (!key) return;
    const addressEl = document.getElementById(`assetAddress-${assetId}`);
    const memoEl = document.getElementById(`assetMemo-${assetId}`);
    const rateEl = document.getElementById(`assetRate-${assetId}`);
    const enabledEl = document.getElementById(`assetEnabled-${assetId}`);

    const payload = {
        wallet_address: addressEl.value.trim() || null,
        memo: memoEl.value.trim() || null,
        sell_enabled: enabledEl.checked,
        sell_rate: rateEl.value ? parseFloat(rateEl.value) : null
    };

    const res = await fetch(`${API_URL}/admin/assets/${assetId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${key}` },
        body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success) {
        loadAdminAssets(key);
        alert('Asset updated');
    } else alert(data.detail);
}

async function deleteAdminAsset(assetId) {
    if (!confirm('Remove this asset?')) return;
    const key = getAdminKeyOrAlert(); if (!key) return;
    const res = await fetch(`${API_URL}/admin/assets/${assetId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${key}` }
    });
    const data = await res.json();
    if (data.success) loadAdminAssets(key);
    else alert(data.detail);
}

function getStatusBadge(status) {
    const badges = {
        pending: 'badge-warning',
        completed: 'badge-success',
        failed: 'badge-danger',
        paid: 'badge-info',
        crypto_confirmed: 'badge-info',
        processing: 'badge-warning'
    };
    return badges[status] || 'badge-info';
}

// Initialize
document.addEventListener('DOMContentLoaded', function () {
    // Restore last active tab or default to overview
    const lastTab = localStorage.getItem('admin_last_tab') || 'overview';
    switchTab(lastTab);

    if (window.lucide) lucide.createIcons();
});


let currentEditingAssetId = null;
// Load Assets
async function loadAdminAssets() {
    const key = getAdminKeyOrAlert(); if (!key) return;

    try {
        const res = await fetch(`${API_URL}/admin/assets`, {
            headers: { 'Authorization': `Bearer ${key}` }
        });
        const data = await res.json();

        if (!data.success) {
            alert('Failed to load assets');
            return;
        }

        const tbody = document.getElementById('assetsTableBody');
        tbody.innerHTML = '';

        if (data.assets.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-secondary">No assets found. Add your first asset!</td></tr>';
            return;
        }

        data.assets.forEach(asset => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>
                    <div style="font-weight:600;">${asset.symbol}</div>
                    <div class="text-sm text-muted">${asset.asset_name}</div>
                </td>
                <td><span class="badge badge-info">${asset.network}</span></td>
                <td>${asset.buy_rate ? '₵' + parseFloat(asset.buy_rate).toFixed(2) : '-'}</td>
                <td>${asset.buy_fee_percent}%</td>
                <td>$${parseFloat(asset.network_fee_usd).toFixed(2)}</td>
                <td>${asset.sell_rate ? '₵' + parseFloat(asset.sell_rate).toFixed(2) : '-'}</td>
                <td>
                    <span class="badge ${asset.buy_enabled ? 'badge-success' : 'badge-secondary'}">
                        ${asset.buy_enabled ? 'Buy' : 'No Buy'}
                    </span>
                    <span class="badge ${asset.sell_enabled ? 'badge-success' : 'badge-secondary'}">
                        ${asset.sell_enabled ? 'Sell' : 'No Sell'}
                    </span>
                </td>
                <td>
                    <button onclick="editAsset(${asset.id})" class="btn btn-sm btn-primary" style="margin-right:0.5rem;">Edit</button>
                    <button onclick="deleteAsset(${asset.id})" class="btn btn-sm btn-danger">Delete</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        alert('Network error');
    }
}
// Open Add Asset Modal
function openAddAssetModal() {
    currentEditingAssetId = null;
    document.getElementById('assetModalTitle').textContent = 'Add Asset';
    document.getElementById('assetForm').reset();
    document.getElementById('assetModal').style.display = 'flex';
}
// Edit Asset
async function editAsset(assetId) {
    const key = getAdminKeyOrAlert(); if (!key) return;

    try {
        const res = await fetch(`${API_URL}/admin/assets`, {
            headers: { 'Authorization': `Bearer ${key}` }
        });
        const data = await res.json();

        const asset = data.assets.find(a => a.id === assetId);
        if (!asset) return;

        currentEditingAssetId = assetId;
        document.getElementById('assetModalTitle').textContent = 'Edit Asset';

        // Populate form
        document.getElementById('assetSymbol').value = asset.symbol;
        document.getElementById('assetName').value = asset.asset_name;
        document.getElementById('assetNetwork').value = asset.network;
        document.getElementById('assetWallet').value = asset.wallet_address;
        document.getElementById('assetMemo').value = asset.memo || '';

        document.getElementById('assetBuyRate').value = asset.buy_rate || '';
        document.getElementById('assetBuyFeePercent').value = asset.buy_fee_percent;
        document.getElementById('assetNetworkFeeUsd').value = asset.network_fee_usd;
        document.getElementById('assetMinBuyAmountUsd').value = asset.min_buy_amount_usd;
        document.getElementById('assetBuyEnabled').checked = asset.buy_enabled;

        document.getElementById('assetSellRate').value = asset.sell_rate || '';
        document.getElementById('assetSellEnabled').checked = asset.sell_enabled;

        document.getElementById('assetModal').style.display = 'flex';
    } catch (e) {
        alert('Failed to load asset');
    }
}
// Save Asset
async function saveAsset(e) {
    e.preventDefault();
    const key = getAdminKeyOrAlert(); if (!key) return;

    const payload = {
        symbol: document.getElementById('assetSymbol').value.trim(),
        asset_name: document.getElementById('assetName').value.trim(),
        network: document.getElementById('assetNetwork').value,
        wallet_address: document.getElementById('assetWallet').value.trim(),
        memo: document.getElementById('assetMemo').value.trim(),

        buy_rate: parseFloat(document.getElementById('assetBuyRate').value) || null,
        buy_fee_percent: parseFloat(document.getElementById('assetBuyFeePercent').value),
        network_fee_usd: parseFloat(document.getElementById('assetNetworkFeeUsd').value),
        min_buy_amount_usd: parseFloat(document.getElementById('assetMinBuyAmountUsd').value),
        buy_enabled: document.getElementById('assetBuyEnabled').checked,

        sell_rate: parseFloat(document.getElementById('assetSellRate').value) || null,
        sell_enabled: document.getElementById('assetSellEnabled').checked,
    };

    const url = currentEditingAssetId
        ? `${API_URL}/admin/assets/${currentEditingAssetId}`
        : `${API_URL}/admin/assets`;
    const method = currentEditingAssetId ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${key}`
            },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (data.success) {
            alert(currentEditingAssetId ? 'Asset updated successfully' : 'Asset created successfully');
            closeAssetModal();
            loadAdminAssets();
        } else {
            alert(data.detail || 'Failed to save asset');
        }
    } catch (e) {
        alert('Network error');
    }
}
// Delete Asset
async function deleteAsset(assetId) {
    if (!confirm('Are you sure you want to delete this asset? This action cannot be undone.')) return;

    const key = getAdminKeyOrAlert(); if (!key) return;

    try {
        const res = await fetch(`${API_URL}/admin/assets/${assetId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${key}` }
        });

        const data = await res.json();

        if (data.success) {
            alert('Asset deleted successfully');
            loadAdminAssets();
        } else {
            alert(data.detail || 'Failed to delete asset');
        }
    } catch (e) {
        alert('Network error');
    }
}
// Close Asset Modal
function closeAssetModal() {
    document.getElementById('assetModal').style.display = 'none';
    currentEditingAssetId = null;
}


// Load payment settings
async function loadExchangePaymentSettings() {
    const key = getAdminKeyOrAlert();
    if (!key) return;
    try {
        const res = await fetch(`${API_URL}/admin/exchange-payment-settings`, {
            headers: { 'Authorization': `Bearer ${key}` }
        });
        const data = await res.json();
        if (data.success) {
            const s = data.settings;
            // NGN Settings
            document.getElementById('ngnBankName').value = s.ngn_bank_name || '';
            document.getElementById('ngnAccountNumber').value = s.ngn_account_number || '';
            document.getElementById('ngnAccountName').value = s.ngn_account_name || '';
            // GHS Settings
            document.getElementById('ghsMomoNumber').value = s.ghs_momo_number || '';
            document.getElementById('ghsMomoName').value = s.ghs_momo_name || '';
            document.getElementById('ghsMomoNetwork').value = s.ghs_momo_network || 'MTN';
        }
    } catch (e) {
        console.error('Error loading payment settings:', e);
    }
}
// Update payment settings
async function updateExchangePaymentSettings(event) {
    event.preventDefault();
    const key = getAdminKeyOrAlert();
    if (!key) return;
    const payload = {
        ngn_bank_name: document.getElementById('ngnBankName').value.trim(),
        ngn_account_number: document.getElementById('ngnAccountNumber').value.trim(),
        ngn_account_name: document.getElementById('ngnAccountName').value.trim(),
        ghs_momo_number: document.getElementById('ghsMomoNumber').value.trim(),
        ghs_momo_name: document.getElementById('ghsMomoName').value.trim(),
        ghs_momo_network: document.getElementById('ghsMomoNetwork').value
    };
    try {
        const res = await fetch(`${API_URL}/admin/exchange-payment-settings`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${key}`
            },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        const statusBox = document.getElementById('paymentSettingsStatus');
        statusBox.classList.remove('hidden');
        if (data.success) {
            statusBox.textContent = '✅ Payment settings updated successfully';
            statusBox.className = 'mt-3 p-3 rounded bg-green-500/10 text-green-500 border border-green-500/20';
            setTimeout(() => statusBox.classList.add('hidden'), 5000);
        } else {
            statusBox.textContent = '❌ Failed to update settings';
            statusBox.className = 'mt-3 p-3 rounded bg-red-500/10 text-red-500 border border-red-500/20';
        }
    } catch (e) {
        console.error('Error updating payment settings:', e);
        alert('Network error');
    }
}
