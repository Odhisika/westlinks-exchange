
const API_URL = '/api';
const token = localStorage.getItem('coinvibe_token');
let currentDirection = 'NGN_GHS';
let currentQuote = null;
let currentExchangeId = null;
let debounceTimer;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    setDirection('NGN_GHS');
    loadUserInfo();
});

function setDirection(dir) {
    currentDirection = dir;

    // Update UI toggles
    document.getElementById('btnNgnGhs').className = `toggle-btn ${dir === 'NGN_GHS' ? 'active' : ''}`;
    document.getElementById('btnGhsNgn').className = `toggle-btn ${dir === 'GHS_NGN' ? 'active' : ''}`;

    // Update inputs
    const isNgnToGhs = dir === 'NGN_GHS';
    document.getElementById('sendCurrency').textContent = isNgnToGhs ? 'NGN' : 'GHS';
    document.getElementById('receiveCurrency').textContent = isNgnToGhs ? 'GHS' : 'NGN';
    document.getElementById('sendFlag').src = isNgnToGhs ? 'https://flagcdn.com/w40/ng.png' : 'https://flagcdn.com/w40/gh.png';
    document.getElementById('receiveFlag').src = isNgnToGhs ? 'https://flagcdn.com/w40/gh.png' : 'https://flagcdn.com/w40/ng.png';

    // Update recipient forms
    document.getElementById('ghsRecipientForm').className = isNgnToGhs ? '' : 'hidden';
    document.getElementById('ngnRecipientForm').className = isNgnToGhs ? 'hidden' : '';

    // Reset values
    document.getElementById('sendAmount').value = '';
    document.getElementById('receiveAmount').value = '';
    document.getElementById('feeBreakdown').className = 'fee-breakdown hidden';

    // Fetch rates immediately to show rate display
    fetchQuote(1);
}

function calculateQuote() {
    clearTimeout(debounceTimer);
    const amount = parseFloat(document.getElementById('sendAmount').value);

    if (!amount || amount <= 0) {
        document.getElementById('receiveAmount').value = '';
        document.getElementById('feeBreakdown').className = 'fee-breakdown hidden';
        return;
    }

    debounceTimer = setTimeout(() => fetchQuote(amount), 500);
}

async function fetchQuote(amount) {
    try {
        const isNgnToGhs = currentDirection === 'NGN_GHS';
        const res = await fetch(`${API_URL}/exchange/quote`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                from_currency: isNgnToGhs ? 'NGN' : 'GHS',
                to_currency: isNgnToGhs ? 'GHS' : 'NGN',
                amount: amount
            })
        });

        const data = await res.json();

        if (data.success) {
            currentQuote = data.quote;

            // Clear any error states
            const wrapper = document.getElementById('sendAmountWrapper');
            const errorMsg = document.getElementById('amountError');
            wrapper.classList.remove('error');
            errorMsg.style.display = 'none';

            // Update Rate Display
            const rateText = isNgnToGhs
                ? `1 GHS = ${(1 / data.quote.exchange_rate).toFixed(2)} NGN`
                : `1 GHS = ${data.quote.exchange_rate.toFixed(2)} NGN`;
            document.getElementById('rateDisplay').textContent = rateText;

            if (document.getElementById('sendAmount').value) {
                document.getElementById('receiveAmount').value = data.quote.to_amount.toFixed(2);
                document.getElementById('feePercent').textContent = data.quote.fee_percent;
                document.getElementById('feeAmount').textContent = `${data.quote.fee_amount.toFixed(2)} ${data.quote.to_currency}`;
                document.getElementById('netAmount').textContent = `${data.quote.to_amount.toFixed(2)} ${data.quote.to_currency}`;
                document.getElementById('feeBreakdown').className = 'fee-breakdown';
            }
        } else {
            // Show inline error instead of alert
            const wrapper = document.getElementById('sendAmountWrapper');
            const errorMsg = document.getElementById('amountError');

            if (document.getElementById('sendAmount').value && parseFloat(document.getElementById('sendAmount').value) > 10) {
                wrapper.classList.add('error');
                errorMsg.style.display = 'block';
                errorMsg.textContent = data.detail || 'Invalid amount';

                // Clear the receive amount
                document.getElementById('receiveAmount').value = '';
                document.getElementById('feeBreakdown').className = 'fee-breakdown hidden';
            }
        }
    } catch (e) {
        console.error(e);
    }
}

async function createExchange() {
    if (!currentQuote) return;

    const isNgnToGhs = currentDirection === 'NGN_GHS';
    let recipientDetails = {};

    if (isNgnToGhs) {
        const momo = document.getElementById('momoNumber').value;
        const name = document.getElementById('momoName').value;
        if (!momo || !name) return alert('Please fill in recipient details');
        recipientDetails = { momo_number: momo, account_name: name };
    } else {
        const bank = document.getElementById('bankName').value;
        const acc = document.getElementById('accountNumber').value;
        const name = document.getElementById('accountName').value;
        if (!bank || !acc || !name) return alert('Please fill in recipient details');
        recipientDetails = { bank_name: bank, account_number: acc, account_name: name };
    }

    const btn = document.getElementById('exchangeBtn');
    btn.disabled = true;
    btn.textContent = 'Processing...';

    try {
        const res = await fetch(`${API_URL}/exchange/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                from_currency: currentQuote.from_currency,
                to_currency: currentQuote.to_currency,
                from_amount: currentQuote.from_amount,
                recipient_details: recipientDetails
            })
        });

        const data = await res.json();

        if (data.success) {
            currentExchangeId = data.exchange.exchange_id;
            showPaymentStep(data.exchange);
        } else {
            alert(data.detail || 'Failed to create exchange');
            btn.disabled = false;
            btn.textContent = 'Proceed to Exchange';
        }
    } catch (e) {
        console.error(e);
        alert('Network error');
        btn.disabled = false;
        btn.textContent = 'Proceed to Exchange';
    }
}

async function showPaymentStep(exchange) {
    document.getElementById('step1').className = 'hidden';
    document.getElementById('step2').className = '';

    document.getElementById('payAmount').textContent = `${exchange.from_amount.toFixed(2)} ${exchange.from_currency}`;
    document.getElementById('payRef').textContent = exchange.exchange_id;

    // Fetch payment instructions from backend
    try {
        const res = await fetch(`${API_URL}/exchange/${exchange.exchange_id}/payment-instructions`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();

        if (data.success && data.payment_instructions) {
            const instructions = data.payment_instructions;

            if (exchange.from_currency === 'NGN') {
                // Show NGN payment section
                document.getElementById('ngnPayment').className = '';
                document.getElementById('ghsPayment').className = 'hidden';

                // Fill NGN bank details with copy buttons
                const bankName = instructions.bank_name || 'Not configured';
                const accountNumber = instructions.account_number || 'Not configured';
                const accountName = instructions.account_name || 'Not configured';
                document.getElementById('ngnBankName').innerHTML = ` ${bankName}
            <button id="copyBankName" class="copy-btn" onclick="copyToClipboard('${bankName}', 'copyBankName')">
                <i data-lucide="copy" style="width:14px;height:14px;"></i>
            </button> `;
                document.getElementById('ngnAccountNumber').innerHTML = ` ${accountNumber}
                <button id="copyAccountNumber" class="copy-btn" onclick="copyToClipboard('${accountNumber}', 'copyAccountNumber')">
                    <i data-lucide="copy" style="width:14px;height:14px;"></i>
                </button> `;
                document.getElementById('ngnAccountName').innerHTML = ` ${accountName}
                    <button id="copyAccountName" class="copy-btn" onclick="copyToClipboard('${accountName}', 'copyAccountName')">
                        <i data-lucide="copy" style="width:14px;height:14px;"></i>
                    </button> `;
                const refId = exchange.exchange_id;
                document.getElementById('payRefCopy').innerHTML = ` ${refId}
                        <button id="copyRefNgn" class="copy-btn" onclick="copyToClipboard('${refId}', 'copyRefNgn')">
                            <i data-lucide="copy" style="width:14px;height:14px;"></i>
                        </button> `;
                // Refresh icons
                lucide.createIcons();
            } else {
                // Show GHS payment section
                document.getElementById('ngnPayment').className = 'hidden';
                document.getElementById('ghsPayment').className = '';

                // Fill GHS MoMo details with copy buttons
                const momoNumber = instructions.momo_number || 'Not configured';
                const momoName = instructions.momo_name || 'Not configured';
                const momoNetwork = instructions.momo_network || 'MTN';
                document.getElementById('ghsMomoNumber').innerHTML = `${momoNumber}<button id="copyMomoNumber" class="copy-btn" onclick="copyToClipboard('${momoNumber}', 'copyMomoNumber')">
                      <i data-lucide="copy" style="width:14px;height:14px;"></i>
                      </button> `;
                document.getElementById('ghsMomoName').innerHTML = `${momoName} <button id="copyMomoName" class="copy-btn" onclick="copyToClipboard('${momoName}', 'copyMomoName')">
                                <i data-lucide="copy" style="width:14px;height:14px;"></i>
                            </button> `;
                document.getElementById('ghsMomoNetwork').textContent = momoNetwork;
                document.getElementById('ghsPayAmountDisplay').textContent = `GH₵ ${exchange.from_amount.toFixed(2)}`;
                const refIdGhs = exchange.exchange_id;
                document.getElementById('payRefCopyGhs').innerHTML = ` ${refIdGhs}
                    <button id="copyRefGhs" class="copy-btn" onclick="copyToClipboard('${refIdGhs}', 'copyRefGhs')">
                        <i data-lucide="copy" style="width:14px;height:14px;"></i>
                    </button> `;
                // Refresh icons
                lucide.createIcons();
            }
        } else {
            alert('Failed to load payment instructions');
        }
    } catch (e) {
        console.error('Error loading payment instructions:', e);
        alert('Network error loading payment details');
    }
}

async function confirmPayment(currency) {
    let paymentRef;
    let proofFile;

    if (currency === 'NGN') {
        paymentRef = document.getElementById('ngnTxId').value;
        proofFile = document.getElementById('ngnProof').files[0];
    } else {
        paymentRef = document.getElementById('momoTxId').value;
        proofFile = document.getElementById('ghsProof').files[0];
    }

    if (!paymentRef) {
        return alert('Please enter the payment reference/transaction ID');
    }

    if (!proofFile) {
        return alert('Please upload proof of payment (screenshot)');
    }

    // Note: For now we'll just confirm with reference
    // In production, you'd want to upload the proof file to your server
    try {
        const res = await fetch(`${API_URL}/exchange/${currentExchangeId}/confirm-payment`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                exchange_id: currentExchangeId,
                payment_reference: paymentRef
            })
        });

        const data = await res.json();
        if (data.success) {
            alert('✅ Payment confirmed! We will verify and process your exchange shortly.');
            window.location.href = '/dashboard';
        } else {
            alert(data.detail || 'Confirmation failed');
        }
    } catch (e) {
        console.error(e);
        alert('Network error');
    }
}


function copyToClipboard(text, buttonId) {
    navigator.clipboard.writeText(text).then(() => {
        // Show toast
        showToast(`✅ Copied: ${text}`);

        // Update button state
        const btn = document.getElementById(buttonId);
        if (btn) {
            btn.classList.add('copied');
            btn.innerHTML = '<i data-lucide="check" style="width:14px;height:14px;"></i> Copied';
            lucide.createIcons();

            // Reset after 2 seconds
            setTimeout(() => {
                btn.classList.remove('copied');
                btn.innerHTML = '<i data-lucide="copy" style="width:14px;height:14px;"></i>';
                lucide.createIcons();
            }, 2000);
        }
    }).catch(err => {
        console.error('Copy failed:', err);
        alert('Failed to copy');
    });
}
function showToast(message) {
    // Remove existing toast if any
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    // Create toast
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);

    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function logout() {
    localStorage.removeItem('coinvibe_token');
    localStorage.removeItem('coinvibe_user');
    window.location.href = '/login';
}
function toggleSidebar() {
    const sidebar = document.getElementById('dashboardSidebar');
    const backdrop = document.querySelector('.sidebar-backdrop');
    sidebar.classList.toggle('active');
    backdrop.classList.toggle('active');
}

function loadUserInfo() {
    const user = JSON.parse(localStorage.getItem('coinvibe_user') || '{}');
    if (user.username) {
        document.getElementById('dashUserName').textContent = user.username;
        document.getElementById('dashAvatar').textContent = user.username.charAt(0).toUpperCase();
    }
}

