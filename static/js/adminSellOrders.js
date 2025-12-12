
async function loadSellOrders(page = 1) {
    const key = getAdminKeyOrAlert(); if (!key) return;
    const status = document.getElementById('sellOrdersStatus') ? document.getElementById('sellOrdersStatus').value : '';
    const q = document.getElementById('sellOrdersSearch') ? document.getElementById('sellOrdersSearch').value.trim() : '';

    const params = new URLSearchParams({ page, page_size: 20 });
    if (status) params.append('status', status);
    if (q) params.append('q', q);

    try {
        const res = await fetch(`${API_URL}/admin/sell-orders?${params.toString()}`, { headers: { 'Authorization': `Bearer ${key}` } });
        const data = await res.json();

        if (!data.success) {
            console.error(data.detail);
            return;
        }

        const metaEl = document.getElementById('sellOrdersMeta');
        if (metaEl) metaEl.textContent = `Showing ${data.orders.length} of ${data.total}`;

        const rows = data.orders.map(o => `
            <tr>
                <td class="font-mono text-xs">${o.payment_id}</td>
                <td>
                    <div class="font-bold">${o.crypto_amount} ${o.crypto_symbol}</div>
                    <div class="text-xs text-secondary">${o.network}</div>
                </td>
                <td>₵${o.fiat_amount.toFixed(2)}</td>
                <td>
                    <div class="text-xs">${o.wallet_address}</div>
                    ${o.crypto_tx_hash ? `<div class="text-xs text-secondary font-mono" title="${o.crypto_tx_hash}">Tx: ${o.crypto_tx_hash.substring(0, 8)}...</div>` : ''}
                </td>
                <td><span class="badge ${getStatusBadge(o.status)}">${o.status}</span></td>
                <td>
                    <div class="flex gap-1">
                        ${o.status === 'pending' ? `
                            <button class="btn btn-success text-xs py-1 px-2" onclick="openUpdateSellOrderModal('${o.payment_id}', 'paid')">Mark Paid</button>
                        ` : ''}
                        ${o.status === 'paid' ? `
                            <button class="btn btn-primary text-xs py-1 px-2" onclick="openUpdateSellOrderModal('${o.payment_id}', 'completed')">Complete</button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `).join('');

        const tableContainer = document.getElementById('sellOrdersTable');
        if (tableContainer) {
            tableContainer.innerHTML = `
                <div class="table-responsive">
                    <table class="dashboard-table">
                        <thead>
                            <tr>
                                <th>Order ID</th>
                                <th>Crypto</th>
                                <th>Fiat (GHS)</th>
                                <th>Wallet / Tx</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>${rows.length ? rows : '<tr><td colspan="6" class="text-center text-secondary">No sell orders found</td></tr>'}</tbody>
                    </table>
                </div>`;
        }
    } catch (e) {
        console.error('Error loading sell orders:', e);
    }
}

let currentSellOrderId = null;

function openUpdateSellOrderModal(orderId, action) {
    currentSellOrderId = orderId;
    // We can use a simple confirm for now, or a modal if we want to add notes.
    // The user requirement was "admin should be able to mark the transaction as paid".
    // A simple confirm is efficient.

    if (confirm(`Are you sure you want to mark order ${orderId} as ${action.toUpperCase()}?`)) {
        updateSellOrderStatus(orderId, action);
    }
}

async function updateSellOrderStatus(orderId, status) {
    const key = getAdminKeyOrAlert(); if (!key) return;

    try {
        const res = await fetch(`${API_URL}/admin/sell-orders/${orderId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${key}`
            },
            body: JSON.stringify({ status: status })
        });

        const data = await res.json();

        if (data.success) {
            // showToast('Order updated successfully'); // Assuming showToast exists or use alert
            alert('Order updated successfully');
            loadSellOrders();
        } else {
            alert(data.detail || 'Failed to update order');
        }
    } catch (e) {
        console.error(e);
        alert('Network error');
    }
}
