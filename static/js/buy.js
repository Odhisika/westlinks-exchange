
const API_URL = window.location.origin + '/api';
let currentOrderId = null;

document.addEventListener('DOMContentLoaded', function () {
    const brand = document.getElementById('cvpBrand');
    const t = localStorage.getItem('coinvibe_token');
    const loggedIn = !!(t && t !== 'null' && t !== 'undefined' && t !== '');
    if (brand) brand.setAttribute('href', loggedIn ? '/dashboard' : '/');
    if (window.lucide && lucide.createIcons) lucide.createIcons();
    initHeader();
});

function initHeader() {
    const currentUser = JSON.parse(localStorage.getItem('coinvibe_user') || '{}');
    const name = currentUser && (currentUser.name || currentUser.username || currentUser.full_name) ? (currentUser.name || currentUser.username || currentUser.full_name) : '';

    const userNameEl = document.getElementById('dashUserName');
    if (userNameEl) userNameEl.textContent = name;

    const avatarEl = document.getElementById('dashAvatar');
    if (avatarEl) avatarEl.textContent = name ? name.charAt(0).toUpperCase() : 'U';
}

function logout() {
    localStorage.removeItem('coinvibe_token');
    localStorage.removeItem('coinvibe_user');
    window.location.href = '/';
}

// Sidebar Logic
(function () {
    const sidebar = document.getElementById('dashboardSidebar');
    const toggleBtn = document.querySelector('.sidebar-toggle');
    const mobileToggle = document.querySelector('.mobile-nav-toggle');
    const body = document.body;

    let backdrop = document.getElementById('sidebarBackdrop');
    if (!backdrop) {
        backdrop = document.createElement('div');
        backdrop.id = 'sidebarBackdrop';
        backdrop.className = 'sidebar-backdrop';
        document.body.appendChild(backdrop);
    }

    function isMobileWidth() {
        return window.innerWidth <= 1024;
    }

    function openSidebar() {
        if (!sidebar) return;
        sidebar.classList.add('active');
        backdrop.classList.add('visible');
        body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        if (!sidebar) return;
        sidebar.classList.remove('active');
        backdrop.classList.remove('visible');
        body.style.overflow = '';
    }

    window.toggleSidebar = function () {
        if (!sidebar) return;
        if (sidebar.classList.contains('active')) closeSidebar();
        else openSidebar();
    }

    if (toggleBtn) toggleBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        toggleSidebar();
    });

    if (mobileToggle) mobileToggle.addEventListener('click', function (e) {
        e.stopPropagation();
        toggleSidebar();
    });

    backdrop.addEventListener('click', closeSidebar);

    window.addEventListener('resize', function () {
        if (!isMobileWidth()) {
            sidebar.classList.remove('open');
        }
    });
})();

function updateAddressPlaceholder() {
    const addr = document.getElementById('buyWalletAddress');
    const val = document.getElementById('buyNetworkSelect') ? document.getElementById('buyNetworkSelect').value : '';
    if (!addr) return;
    switch (val) {
        case 'ERC20':
        case 'BEP20':
        case 'POLYGON':
        case 'ARBITRUM':
        case 'AVALANCHE':
            addr.placeholder = '0x… (42-char hex address)';
            break;
        case 'TRC20':
            addr.placeholder = 'Starts with T… (TRON address)';
            break;
        case 'SOLANA':
            addr.placeholder = 'Solana base58';
            break;
        case 'LITECOIN':
            addr.placeholder = 'Litecoin (ltc1… or L/M…)';
            break;
        default:
            addr.placeholder = 'Enter wallet address';
    }
}

function normalizeNetworkCode(s) {
    s = String(s).toUpperCase();
    if (s.includes('ERC')) return 'ERC20';
    if (s.includes('TRC')) return 'TRC20';
    if (s.includes('BEP')) return 'BEP20';
    if (s.includes('SOL')) return 'SOLANA';
    if (s.includes('AVA')) return 'AVALANCHE';
    if (s.includes('POLY')) return 'POLYGON';
    if (s.includes('ARBI')) return 'ARBITRUM';
    if (s.includes('LTC')) return 'LITECOIN';
    return s;
}

function networkLabelFromCode(code) {
    const m = {
        ERC20: 'Ethereum (ERC-20)',
        TRC20: 'TRON (TRC-20)',
        BEP20: 'Binance Smart Chain (BEP-20)',
        SOLANA: 'Solana',
        AVALANCHE: 'Avalanche',
        POLYGON: 'Polygon',
        ARBITRUM: 'Arbitrum',
        LITECOIN: 'Litecoin'
    };
    return m[code] || code;
}

function filterNetworksForAsset(symbol, networks) {
    symbol = String(symbol).toUpperCase();
    if (symbol === 'USDT') {
        const allowed = new Set(['ERC20', 'TRC20', 'BEP20', 'SOLANA', 'AVALANCHE', 'POLYGON', 'ARBITRUM']);
        return networks.filter(n => allowed.has(String(n).toUpperCase()));
    }
    if (symbol === 'TRX') return ['TRC20'];
    if (symbol === 'LTC') return ['LITECOIN'];
    return networks;
}

let buyAssets = [];
let buySelectedAsset = null;

async function loadBuyAssets() {
    try {
        const res = await fetch(`${API_URL}/public/assets`);
        const data = await res.json();
        if (data.success) {
            // Filter by buy_enabled
            buyAssets = data.assets.filter(a => a.buy_enabled);

            const sel = document.getElementById('buyAssetSelect');
            sel.innerHTML = '';

            // Group by symbol to show unique assets in the first dropdown
            const uniqueSymbols = [...new Set(buyAssets.map(a => a.symbol))];

            uniqueSymbols.forEach(s => {
                const asset = buyAssets.find(a => a.symbol === s); // Get first occurrence for name
                const opt = document.createElement('option');
                opt.value = s;
                opt.textContent = `${asset.asset_name} (${s})`;
                sel.appendChild(opt);
            });

            if (uniqueSymbols.length > 0) {
                // Trigger change to load networks for the first symbol
                sel.value = uniqueSymbols[0];
                updateNetworkDropdown();
            }

            sel.addEventListener('change', () => {
                updateNetworkDropdown();
            });
        }
    } catch (e) { console.error(e); }
}

function updateNetworkDropdown() {
    const assetSel = document.getElementById('buyAssetSelect');
    const networkSel = document.getElementById('buyNetworkSelect');
    const selectedSymbol = assetSel.value;

    networkSel.innerHTML = '';

    // Find all assets matching the selected symbol
    const availableAssets = buyAssets.filter(a => a.symbol === selectedSymbol);

    availableAssets.forEach(a => {
        const opt = document.createElement('option');
        opt.value = a.network; // Use network code as value
        opt.textContent = (typeof networkLabelFromCode === 'function') ? networkLabelFromCode(a.network) : a.network;
        networkSel.appendChild(opt);
    });

    // Select the first network by default and update the global selected asset
    if (availableAssets.length > 0) {
        networkSel.value = availableAssets[0].network;
        buySelectedAsset = availableAssets[0];
        updateBuyCalculator();
        if (typeof updateAddressPlaceholder === 'function') updateAddressPlaceholder();
    }

    networkSel.onchange = function () {
        const selectedNetwork = networkSel.value;
        buySelectedAsset = availableAssets.find(a => a.network === selectedNetwork);
        updateBuyCalculator();
        if (typeof updateAddressPlaceholder === 'function') updateAddressPlaceholder();
    };
}

function updateBuyCalculator() {
    if (!buySelectedAsset) return;

    const title = document.getElementById('buyPageTitle');
    if (title) title.textContent = `Buy ${buySelectedAsset.symbol}`;
    const getLabel = document.getElementById('buyGetLabel');
    if (getLabel) getLabel.textContent = `Value in USD`;

    const amountGhs = parseFloat(document.getElementById('buyAmountGHS').value) || 0;
    const rate = buySelectedAsset.buy_rate || 0;
    const feePercent = 1.5;

    // GHS to USD conversion rate (adjust as needed)
    const ghsToUsdRate = 15; // 1 USD = 15 GHS
    const amountUsd = amountGhs / ghsToUsdRate;

    const serviceFee = amountGhs * (feePercent / 100);
    const networkFeeUsd = buySelectedAsset.network_fee_usd || 1;
    const networkFeeGhs = networkFeeUsd * 15;

    const totalGhs = amountGhs + serviceFee + networkFeeGhs;

    const cryptoAmount = (rate > 0) ? (amountGhs / rate) : 0;

    // Display USD value instead of crypto amount
    const amountUsdtEl = document.getElementById('buyAmountUSDT');
    if (amountUsdtEl) amountUsdtEl.value = `$${amountUsd.toFixed(2)}`;

    document.getElementById('buyRateLabel').textContent = `₵${rate.toFixed(2)}/${buySelectedAsset.symbol}`;
    document.getElementById('buyFeePercent').textContent = feePercent;
    document.getElementById('buyServiceFee').textContent = `₵${serviceFee.toFixed(2)}`;
    document.getElementById('buyNetworkFee').textContent = `₵${networkFeeGhs.toFixed(2)}`;
    document.getElementById('buyTotal').textContent = `₵${totalGhs.toFixed(2)}`;
}


function showToast(msg) {
    const el = document.getElementById('buyToast');
    const m = document.getElementById('buyToastMsg');
    m.textContent = msg;
    el.style.display = 'block';
    if (window.lucide && lucide.createIcons) lucide.createIcons();
    setTimeout(() => { el.style.display = 'none'; }, 3000);
}

function showStep1() {
    document.getElementById('buyStep1').style.display = 'block';
    document.getElementById('buyStep2').style.display = 'none';
}

function showStep2() {
    document.getElementById('buyStep1').style.display = 'none';
    document.getElementById('buyStep2').style.display = 'block';
}

function togglePaymentMethod(method) {
    const btnMomo = document.getElementById('btnMomo');
    const btnBank = document.getElementById('btnBank');
    const momoDetails = document.getElementById('momoDetails');
    const bankDetails = document.getElementById('bankDetails');

    if (method === 'momo') {
        btnMomo.style.background = 'var(--highlight-yellow)';
        btnMomo.style.color = '#000';
        btnBank.style.background = 'transparent';
        btnBank.style.color = 'var(--text-secondary)';
        momoDetails.style.display = 'block';
        bankDetails.style.display = 'none';
    } else {
        btnBank.style.background = 'var(--highlight-yellow)';
        btnBank.style.color = '#000';
        btnMomo.style.background = 'transparent';
        btnMomo.style.color = 'var(--text-secondary)';
        momoDetails.style.display = 'none';
        bankDetails.style.display = 'block';
    }
}

function copyText(elementId) {
    const text = document.getElementById(elementId).innerText;
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard');
    });
}

async function createBuyOrder() {
    const t = localStorage.getItem('coinvibe_token');
    const uRaw = localStorage.getItem('coinvibe_user');
    const loggedIn = !!(t && t !== 'null' && t !== 'undefined' && t !== '');
    if (!loggedIn || !uRaw) { window.location.href = '/login'; return; }
    let u = null; try { u = JSON.parse(uRaw); } catch (_) { }
    const amount = parseFloat(document.getElementById('buyAmountGHS').value) || 0;
    const addr = document.getElementById('buyWalletAddress').value.trim();
    if (!amount || amount <= 0) { showToast('Enter a valid GHS amount'); return; }
    if (!addr) { showToast('Enter your wallet address'); return; }
    if (!buySelectedAsset || !buySelectedAsset.id) { showToast('Please select an asset'); return; }

    try {
        showToast('Creating order...');
        const confirmRes = await fetch(`${API_URL}/buy/confirm`, {
            method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${t}` },
            body: JSON.stringify({
                asset_id: buySelectedAsset.id,
                amount_ghs: amount,
                recipient_address: addr,
                vendor_email: (u && u.email) ? u.email : ''
            })
        });
        const confirmData = await confirmRes.json();
        if (!confirmRes.ok || !confirmData.success) { showToast(confirmData.detail || 'Failed to create order'); return; }

        currentOrderId = confirmData.order_id;
        await loadPaymentInstructions(currentOrderId);
        showStep2();

    } catch (e) {
        showToast('Network error, try again');
    }
}

async function loadPaymentInstructions(orderId) {
    const t = localStorage.getItem('coinvibe_token');
    try {
        const res = await fetch(`${API_URL}/buy/${orderId}/payment-instructions`, {
            headers: { 'Authorization': `Bearer ${t}` }
        });
        const data = await res.json();

        if (data.success) {
            const inst = data.instructions;
            document.getElementById('payAmountDisplay').textContent = `₵${inst.amount_ghs.toFixed(2)}`;
            document.getElementById('payOrderId').textContent = inst.reference;
            document.getElementById('payRefCopy').textContent = inst.reference;

            // MoMo
            document.getElementById('payMomoNumber').textContent = inst.mobile_money.number;
            document.getElementById('payMomoName').textContent = inst.mobile_money.name;
            document.getElementById('payMomoNetwork').textContent = inst.mobile_money.network;

            // Bank
            document.getElementById('payBankName').textContent = inst.bank_transfer.bank_name;
            document.getElementById('payAccountNumber').textContent = inst.bank_transfer.account_number;
            document.getElementById('payAccountName').textContent = inst.bank_transfer.account_name;
        }
    } catch (e) {
        console.error(e);
        showToast('Failed to load payment instructions');
    }
}

async function confirmBuyPayment() {
    if (!currentOrderId) return;

    const ref = document.getElementById('userPayRef').value.trim();
    if (!ref) {
        showToast('Please enter the payment reference');
        return;
    }

    const t = localStorage.getItem('coinvibe_token');
    try {
        showToast('Confirming payment...');
        const res = await fetch(`${API_URL}/buy/${currentOrderId}/confirm-payment`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${t}`
            },
            body: JSON.stringify({ payment_reference: ref })
        });

        const data = await res.json();
        if (data.success) {
            showToast('Payment confirmed successfully!');
            setTimeout(() => {
                window.location.href = `/buy/success?reference=${currentOrderId}`;
            }, 1500);
        } else {
            showToast(data.detail || 'Failed to confirm payment');
        }
    } catch (e) {
        showToast('Network error');
    }
}

loadBuyAssets();
updateBuyCalculator();
