
// Load Buy Orders
async function loadBuyOrders(page = 1) {
    console.log('loadBuyOrders called');
    const key = getAdminKeyOrAlert(); if (!key) return;
    const paymentStatus = document.getElementById('filterPaymentStatus').value;
    const deliveryStatus = document.getElementById('filterDeliveryStatus').value;
    const params = new URLSearchParams({ page, page_size: 20 });

    if (paymentStatus) params.append('payment_status', paymentStatus);
    if (deliveryStatus) params.append('delivery_status', deliveryStatus);

    try {
        const res = await fetch(`${API_URL}/admin/buy-orders?${params.toString()}`, {
            headers: { 'Authorization': `Bearer ${key}` }
        });
        const data = await res.json();

        if (!data.success) {
            alert(data.detail || 'Failed to load orders');
            return;
        }

        const tbody = document.getElementById('buyOrdersTableBody');
        tbody.innerHTML = '';
        console.log(`Loaded ${data.orders.length} orders`);

        if (data.orders.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center text-secondary">No buy orders found.</td></tr>';
            return;
        }

        data.orders.forEach(order => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="font-mono text-xs">#${order.order_id}</td>
                <td>
                    <div class="font-bold">${order.asset_symbol}</div>
                    <div class="text-xs text-secondary">${order.network}</div>
                </td>
                <td>
                    <div>${parseFloat(order.amount_ghs).toFixed(2)} GHS</div>
                    <div class="text-xs text-secondary">$${parseFloat(order.usdt_amount).toFixed(2)}</div>
                </td>
                <td>₵${parseFloat(order.amount_ghs).toFixed(2)}</td>
                <td class="font-mono text-xs" title="${order.recipient_address}">
                    ${order.recipient_address.substring(0, 8)}...${order.recipient_address.substring(order.recipient_address.length - 6)}
                    <button onclick="copyText('${order.recipient_address}')" class="btn-icon" title="Copy">
                        <i data-lucide="copy" style="width:12px;"></i>
                    </button>
                </td>
                <td><span class="badge ${getPaymentStatusBadge(order.payment_status)}">${formatStatus(order.payment_status)}</span></td>
                <td><span class="badge ${getDeliveryStatusBadge(order.delivery_status)}">${formatStatus(order.delivery_status)}</span></td>
                <td class="text-xs">${new Date(order.created_at).toLocaleString()}</td>
                <td>
                    <button onclick="openUpdateOrderModal('${order.order_id}')" class="btn btn-sm btn-primary">Update</button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        if (window.lucide) lucide.createIcons();

    } catch (e) {
        console.error(e);
        alert('Network error loading orders');
    }
}

// Open Update Modal
async function openUpdateOrderModal(orderId) {
    const key = getAdminKeyOrAlert(); if (!key) return;

    try {
        const res = await fetch(`${API_URL}/admin/buy-orders?q=${orderId}`, {
            headers: { 'Authorization': `Bearer ${key}` }
        });
        const data = await res.json();

        if (!data.success || !data.orders || data.orders.length === 0) {
            alert('Order not found');
            return;
        }

        const order = data.orders.find(o => o.order_id == orderId);
        if (!order) {
            alert('Order not found');
            return;
        }

        document.getElementById('updateOrderId').value = order.id;
        document.getElementById('updateTxHash').value = order.tx_hash || '';
        document.getElementById('updatePaymentStatus').value = order.payment_status;
        document.getElementById('updateDeliveryStatus').value = order.delivery_status;
        document.getElementById('updateAdminNotes').value = order.admin_notes || '';
        document.getElementById('updateOrderModalTitle').textContent = `Update Order #${order.order_id}`;

        document.getElementById('updateOrderModal').style.display = 'flex';

    } catch (e) {
        console.error(e);
        alert('Failed to load order details');
    }
}

function closeUpdateOrderModal() {
    document.getElementById('updateOrderModal').style.display = 'none';
}

// Save Order Update
async function saveOrderUpdate(event) {
    event.preventDefault();
    const key = getAdminKeyOrAlert(); if (!key) return;

    const orderId = document.getElementById('updateOrderId').value;
    const payload = {
        tx_hash: document.getElementById('updateTxHash').value.trim(),
        payment_status: document.getElementById('updatePaymentStatus').value,
        delivery_status: document.getElementById('updateDeliveryStatus').value,
        admin_notes: document.getElementById('updateAdminNotes').value.trim()
    };

    try {
        const res = await fetch(`${API_URL}/admin/buy-orders/${orderId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${key}`
            },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (data.success) {
            alert('Order updated successfully');
            closeUpdateOrderModal();
            loadBuyOrders(); // Refresh list
        } else {
            alert(data.detail || 'Failed to update order');
        }
    } catch (e) {
        console.error(e);
        alert('Network error updating order');
    }
}

// Helper functions
function getPaymentStatusBadge(status) {
    switch (status) {
        case 'paid': return 'badge-success';
        case 'pending': return 'badge-warning';
        case 'verification_pending': return 'badge-info';
        case 'failed': return 'badge-danger';
        case 'refunded': return 'badge-secondary';
        default: return 'badge-secondary';
    }
}

function getDeliveryStatusBadge(status) {
    switch (status) {
        case 'confirmed': return 'badge-success';
        case 'sent': return 'badge-info';
        case 'pending': return 'badge-warning';
        case 'failed': return 'badge-danger';
        default: return 'badge-secondary';
    }
}

function formatStatus(status) {
    if (!status) return '-';
    return status.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
}

function copyText(text) {
    navigator.clipboard.writeText(text).then(() => {
        alert('Copied to clipboard!');
    }).catch(() => {
        alert('Failed to copy');
    });
}
