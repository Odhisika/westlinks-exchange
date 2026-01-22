let currentUpdateExchangeId = null;
async function loadExchangeOrders() {
    const key = getAdminKeyOrAlert();
    if (!key) return;

    const status = document.getElementById('filterExchangeStatus')?.value || '';
    const direction = document.getElementById('filterExchangeDirection')?.value || '';
    const search = document.getElementById('filterExchangeSearch')?.value || '';

    let url = `${API_URL}/admin/exchanges`;
    const params = [];
    if (status) params.push(`status=${status}`);
    if (direction) params.push(`direction=${direction}`);
    if (search) params.push(`q=${encodeURIComponent(search)}`);
    if (params.length) url += '?' + params.join('&');

    try {
        const res = await fetch(url, {
            headers: { 'Authorization': `Bearer ${key}` }
        });
        const data = await res.json();

        if (!data.success) {
            document.getElementById('exchangeOrdersTableBody').innerHTML =
                '<tr><td colspan="10" class="text-center text-danger">Failed to load orders</td></tr>';
            return;
        }

        renderExchangeOrders(data.exchanges || []);
    } catch (e) {
        console.error('Error loading exchanges:', e);
        document.getElementById('exchangeOrdersTableBody').innerHTML =
            '<tr><td colspan="10" class="text-center text-danger">Network error</td></tr>';
    }
}
function renderExchangeOrders(exchanges) {
    const tbody = document.getElementById('exchangeOrdersTableBody');

    if (exchanges.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="text-center text-secondary">No exchange orders found</td></tr>';
        return;
    }

    tbody.innerHTML = exchanges.map(ex => {
        const statusBadge = getExchangeStatusBadge(ex.status);
        const directionBadge = getDirectionBadge(ex.from_currency, ex.to_currency);
        const createdDate = formatShortDate(ex.created_at);
        const recipientPreview = getRecipientPreview(ex.recipient_details, ex.to_currency);

        let actionButton = '';
        if (ex.status === 'pending_payment') {
            actionButton = `<button onclick='openUpdateExchangeModal("${ex.exchange_id}", ${JSON.stringify(ex).replace(/'/g, "\\'")})'  class="action-btn btn-update">Confirm Payment</button>`;
        } else if (ex.status === 'paid') {
            actionButton = `<button onclick='openUpdateExchangeModal("${ex.exchange_id}", ${JSON.stringify(ex).replace(/'/g, "\\'")})'  class="action-btn btn-update">Start Processing</button>`;
        } else if (ex.status === 'processing') {
            actionButton = `<button onclick='openUpdateExchangeModal("${ex.exchange_id}", ${JSON.stringify(ex).replace(/'/g, "\\'")})'  class="action-btn btn-update">Mark Complete</button>`;
        } else {
            actionButton = `<button onclick='openUpdateExchangeModal("${ex.exchange_id}", ${JSON.stringify(ex).replace(/'/g, "\\'")})'  class="action-btn btn-view">View/Update</button>`;
        }

        return `
            <tr>
                <td data-label="Exchange ID"><div class="exchange-id">${ex.exchange_id}</div></td>
                <td data-label="User">
                    <div style="font-weight: 600; font-size: 0.9rem;">${ex.vendor_name || ex.vendor_email}</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem;">${ex.vendor_email}</div>
                </td>
                <td data-label="Direction">${directionBadge}</td>
                <td data-label="Sending">
                    <div class="currency-display">
                        <div class="currency-amount">${formatCurrency(ex.from_amount)}</div>
                        <div class="currency-code">${ex.from_currency}</div>
                    </div>
                </td>
                <td data-label="Receiving">
                    <div class="currency-display">
                        <div class="currency-amount">${formatCurrency(ex.to_amount)}</div>
                        <div class="currency-code">${ex.to_currency}</div>
                    </div>
                </td>
                <td data-label="Rate & Fee">
                    <div class="rate-display">1:${ex.exchange_rate.toFixed(4)}</div>
                    <div class="fee-display">Fee: ${formatCurrency(ex.fee_amount)}</div>
                </td>
                <td data-label="Recipient">
                    <div class="recipient-preview">${recipientPreview}</div>
                    <button onclick='showRecipientDetails(${JSON.stringify(ex.recipient_details).replace(/'/g, "\\'")}  , "${ex.to_currency}")' 
                            class="view-details-btn">View Details</button>
                </td>
                <td data-label="Status">
                    <span class="badge ${statusBadge.class}">${statusBadge.text}</span>
                    ${ex.paid_at ? `<div style="font-size: 0.7rem; color: var(--text-muted); margin-top: 0.5rem;">Paid: ${formatShortDate(ex.paid_at)}</div>` : ''}
                </td>
                <td data-label="Date"><div class="date-display">${createdDate}</div></td>
                <td data-label="Actions">${actionButton}</td>
            </tr>
        `;
    }).join('');
}
function getExchangeStatusBadge(status) {
    const badges = {
        'pending_payment': { text: 'Pending Payment', class: 'status-badge-pending_payment' },
        'paid': { text: 'Paid', class: 'status-badge-paid' },
        'processing': { text: 'Processing', class: 'status-badge-processing' },
        'completed': { text: 'Completed', class: 'status-badge-completed' },
        'failed': { text: 'Failed', class: 'status-badge-failed' }
    };
    return badges[status] || { text: status, class: 'badge-secondary' };
}
function getDirectionBadge(from, to) {
    if (from === 'NGN' && to === 'GHS') {
        return '<div class="direction-badge direction-badge-ngn-ghs">🇳🇬 NGN → GHS 🇬🇭</div>';
    } else if (from === 'GHS' && to === 'NGN') {
        return '<div class="direction-badge direction-badge-ghs-ngn">🇬🇭 GHS → NGN 🇳🇬</div>';
    }
    return `<div class="direction-badge">${from} → ${to}</div>`;
}
function getRecipientPreview(details, toCurrency) {
    if (!details || Object.keys(details).length === 0) {
        return '<em style="color: var(--text-muted);">No details</em>';
    }

    if (toCurrency === 'GHS') {
        return details.phone || details.momo_number || 'Mobile Money';
    } else {
        return details.bank_account || details.account_name || 'Bank Transfer';
    }
}
function showRecipientDetails(details, toCurrency) {
    const display = document.getElementById('recipientDetailsDisplay');

    if (!details || Object.keys(details).length === 0) {
        display.innerHTML = '<p style="color: var(--text-muted); text-align: center;">No recipient details available</p>';
    } else if (toCurrency === 'GHS') {
        display.innerHTML = `
            <div class="recipient-detail-item">
                <span class="recipient-detail-label">Phone Number:</span>
                <span class="recipient-detail-value">${details.phone || details.momo_number || 'N/A'}</span>
            </div>
            <div class="recipient-detail-item">
                <span class="recipient-detail-label">Account Name:</span>
                <span class="recipient-detail-value">${details.momo_name || details.account_name || 'N/A'}</span>
            </div>
            <div class="recipient-detail-item">
                <span class="recipient-detail-label">Network:</span>
                <span class="recipient-detail-value">${details.momo_network || 'N/A'}</span>
            </div>
        `;
    } else {
        display.innerHTML = `
            <div class="recipient-detail-item">
                <span class="recipient-detail-label">Bank Name:</span>
                <span class="recipient-detail-value">${details.bank_name || 'N/A'}</span>
            </div>
            <div class="recipient-detail-item">
                <span class="recipient-detail-label">Account Number:</span>
                <span class="recipient-detail-value">${details.bank_account || details.account_number || 'N/A'}</span>
            </div>
            <div class="recipient-detail-item">
                <span class="recipient-detail-label">Account Name:</span>
                <span class="recipient-detail-value">${details.account_name || 'N/A'}</span>
            </div>
        `;
    }

    document.getElementById('recipientDetailsModal').style.display = 'flex';
}
function closeRecipientDetailsModal() {
    document.getElementById('recipientDetailsModal').style.display = 'none';
}
function openUpdateExchangeModal(exchangeId, exchangeData) {
    currentUpdateExchangeId = exchangeId;

    document.getElementById('updateExchangeModalTitle').textContent = `Update Exchange: ${exchangeId}`;
    document.getElementById('updateExchangeId').value = exchangeId;

    const detailsHtml = `
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div>
                <strong style="color: var(--text-muted); font-size: 0.8rem;">Direction:</strong>
                <div style="margin-top: 0.25rem;">${exchangeData.from_currency} → ${exchangeData.to_currency}</div>
            </div>
            <div>
                <strong style="color: var(--text-muted); font-size: 0.8rem;">Status:</strong>
                <div style="margin-top: 0.25rem;">${exchangeData.status}</div>
            </div>
            <div>
                <strong style="color: var(--text-muted); font-size: 0.8rem;">Sending:</strong>
                <div style="margin-top: 0.25rem;">${formatCurrency(exchangeData.from_amount)} ${exchangeData.from_currency}</div>
            </div>
            <div>
                <strong style="color: var(--text-muted); font-size: 0.8rem;">Receiving:</strong>
                <div style="margin-top: 0.25rem;">${formatCurrency(exchangeData.to_amount)} ${exchangeData.to_currency}</div>
            </div>
        </div>
    `;
    document.getElementById('exchangeDetailsDisplay').innerHTML = detailsHtml;

    const actionSelect = document.getElementById('updateExchangeAction');
    if (exchangeData.status === 'pending_payment') {
        actionSelect.value = 'confirm_payment';
    } else if (exchangeData.status === 'paid') {
        actionSelect.value = 'start_processing';
    } else if (exchangeData.status === 'processing') {
        actionSelect.value = 'complete';
    } else {
        actionSelect.value = '';
    }

    document.getElementById('updateExchangeAdminNotes').value = exchangeData.admin_notes || '';
    document.getElementById('updateExchangePaymentRef').value = exchangeData.payment_reference || '';

    toggleExchangeActionFields();
    document.getElementById('updateExchangeModal').style.display = 'flex';
}
function closeUpdateExchangeModal() {
    document.getElementById('updateExchangeModal').style.display = 'none';
    currentUpdateExchangeId = null;
}
function toggleExchangeActionFields() {
    const action = document.getElementById('updateExchangeAction').value;
    const paymentRefField = document.getElementById('paymentRefField');

    if (action === 'confirm_payment') {
        paymentRefField.style.display = 'block';
    } else {
        paymentRefField.style.display = 'none';
    }
}
async function saveExchangeUpdate(e) {
    e.preventDefault();
    const key = getAdminKeyOrAlert();
    if (!key) return;

    const exchangeId = document.getElementById('updateExchangeId').value;
    const action = document.getElementById('updateExchangeAction').value;
    const adminNotes = document.getElementById('updateExchangeAdminNotes').value.trim();
    const paymentRef = document.getElementById('updateExchangePaymentRef').value.trim();

    if (!action) {
        alert('Please select an action');
        return;
    }

    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span style="opacity: 0.7;">⏳ Updating...</span>';

    try {
        const res = await fetch(`${API_URL}/admin/exchanges/${exchangeId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${key}`
            },
            body: JSON.stringify({
                action: action,
                admin_notes: adminNotes,
                payment_reference: paymentRef
            })
        });

        const data = await res.json();

        if (data.success) {
            closeUpdateExchangeModal();
            await loadExchangeOrders();
            showSuccessToast('✓ Exchange updated successfully!');
        } else {
            alert(data.detail || 'Failed to update exchange');
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    } catch (e) {
        console.error('Error updating exchange:', e);
        alert('Network error');
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}
function formatCurrency(amount) {
    return parseFloat(amount).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}
function formatShortDate(isoString) {
    const date = new Date(isoString);
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}