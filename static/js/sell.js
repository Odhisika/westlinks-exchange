const API_URL = window.location.origin + '/api';

document.addEventListener('DOMContentLoaded', function () {
    const brand = document.getElementById('cvpBrand');
    const t = localStorage.getItem('coinvibe_token');
    const loggedIn = !!(t && t !== 'null' && t !== 'undefined' && t !== '');
    if (brand) brand.setAttribute('href', loggedIn ? '/dashboard' : '/');
    if (window.lucide && lucide.createIcons) lucide.createIcons();
    initMobileMenu();
});

function initMobileMenu() {
    const toggle = document.getElementById('mobileMenuToggle');
    const mobileNav = document.getElementById('mobileNav');
    if (toggle && mobileNav) {
        toggle.addEventListener('click', function (e) {
            e.stopPropagation();
            mobileNav.classList.toggle('active');
            const icon = toggle.querySelector('i');
            if (icon) {
                const currentIcon = icon.getAttribute('data-lucide');
                icon.setAttribute('data-lucide', currentIcon === 'menu' ? 'x' : 'menu');
                if (window.lucide && lucide.createIcons) lucide.createIcons();
            }
        });
        document.addEventListener('click', function (e) {
            if (!mobileNav.contains(e.target) && !toggle.contains(e.target)) {
                mobileNav.classList.remove('active');
                const icon = toggle.querySelector('i');
                if (icon) {
                    icon.setAttribute('data-lucide', 'menu');
                    if (window.lucide && lucide.createIcons) lucide.createIcons();
                }
            }
        });
    }
}

function logout() {
    localStorage.removeItem('coinvibe_token');
    localStorage.removeItem('coinvibe_user');
    window.location.href = '/';
}

let sellAssets = [];
let selectedSellAsset = null;

async function loadPublicAssets() {
    try {
        const res = await fetch(`${API_URL}/public/assets`);
        const data = await res.json();
        sellAssets = (data.assets || []).filter(a => a.sell_enabled);
        const select = document.getElementById('sellAssetSelect');
        select.innerHTML = '';
        sellAssets.forEach((a, idx) => {
            const opt = document.createElement('option');
            opt.value = String(a.id);
            opt.textContent = `${a.asset_name || a.symbol} • ${a.network}`;
            if (idx === 0) opt.selected = true;
            select.appendChild(opt);
        });
        selectedSellAsset = sellAssets.length ? sellAssets[0] : null;
        updateSelectedSellAssetUI();
        select.addEventListener('change', () => {
            const id = Number(select.value);
            selectedSellAsset = sellAssets.find(a => a.id === id) || null;
            updateSelectedSellAssetUI();
            updateSellCalculator();
        });
    } catch (error) {
        console.error('Error loading assets:', error);
        showToast('Failed to load assets');
    }
}

function updateSelectedSellAssetUI() {
    const rateLabel = document.getElementById('sellRateLabel');
    const rate = selectedSellAsset && selectedSellAsset.sell_rate ? Number(selectedSellAsset.sell_rate) : null;
    rateLabel.textContent = rate ? `₵${rate.toFixed(2)}/${selectedSellAsset.symbol || 'Asset'}` : '₵--/Asset';
    const walletEl = document.getElementById('confirmAdminWallet');
    const wallet = selectedSellAsset && selectedSellAsset.wallet_address ? selectedSellAsset.wallet_address : '';
    walletEl.textContent = wallet || '--';
}

function updateSellCalculator() {
    const amount = parseFloat(document.getElementById('sellAmountUSDT').value) || 0;
    const rate = selectedSellAsset && selectedSellAsset.sell_rate ? Number(selectedSellAsset.sell_rate) : 14.80;
    const ghsAmount = amount * rate;
    const fee = ghsAmount * 0.015;
    const total = ghsAmount - fee;
    document.getElementById('sellFee').textContent = `₵${fee.toFixed(2)}`;
    document.getElementById('sellTotal').textContent = `₵${total.toFixed(2)}`;
}

function showToast(msg) {
    const el = document.getElementById('sellToast');
    const m = document.getElementById('sellToastMsg');
    m.textContent = msg;
    el.style.display = 'block';
    if (window.lucide && lucide.createIcons) lucide.createIcons();
    setTimeout(() => { el.style.display = 'none'; }, 3000);
}

function copyWalletAddress() {
    const wallet = selectedSellAsset && selectedSellAsset.wallet_address ? selectedSellAsset.wallet_address : '';
    if (wallet) {
        // Fallback for non-secure contexts (HTTP)
        if (!navigator.clipboard) {
            const textArea = document.createElement("textarea");
            textArea.value = wallet;
            textArea.style.position = "fixed";  // Avoid scrolling to bottom
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            try {
                const successful = document.execCommand('copy');
                if (successful) {
                    showToast('Wallet address copied to clipboard');
                } else {
                    showToast('Failed to copy address');
                }
            } catch (err) {
                console.error('Fallback copy failed', err);
                showToast('Failed to copy address');
            }
            document.body.removeChild(textArea);
            return;
        }

        navigator.clipboard.writeText(wallet).then(() => {
            showToast('Wallet address copied to clipboard');
        }).catch(err => {
            console.error('Copy failed:', err);
            showToast('Failed to copy address');
        });
    }
}

async function confirmSell() {
    const t = localStorage.getItem('coinvibe_token');
    const u = localStorage.getItem('coinvibe_user');
    const loggedIn = !!(t && t !== 'null' && t !== 'undefined' && t !== '');
    if (!loggedIn || !u) {
        window.location.href = '/login';
        return;
    }
    const amount = parseFloat(document.getElementById('sellAmountUSDT').value) || 0;
    const network = selectedSellAsset ? selectedSellAsset.network : '';
    const walletAddress = document.getElementById('confirmAdminWallet').textContent;
    const momoNumber = document.getElementById('sellMoMoNumber').value.trim();
    const momoNetwork = document.getElementById('sellMoMoNetwork').value;

    if (!amount || amount <= 0) { showToast('Please enter a valid amount'); return; }

    if (!momoNumber) { showToast('Please enter your mobile money number'); return; }

    try {
        const res = await fetch(`${API_URL}/sell/confirm`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${t}` },
            body: JSON.stringify({
                usdt_amount: amount,
                network: network,
                wallet_address: walletAddress,
                vendor_email: localStorage.getItem('coinvibe_user') ? JSON.parse(localStorage.getItem('coinvibe_user')).email : '',
                tx_hash: document.getElementById('sellTxHash').value.trim() || null
            })
        });
        const data = await res.json();
        if (res.ok && (data.success || data.payment_id || data.id)) {
            const pid = data.payment_id || data.id;
            showToast(`Sell order created: ${pid}`);
            window.location.href = `/sell-success?id=${pid}`;
            return;
        }
        else { showToast(data.detail || 'Failed to create sell order'); }
    } catch (err) {
        showToast('Network error, try again');
    }
}

loadPublicAssets();
