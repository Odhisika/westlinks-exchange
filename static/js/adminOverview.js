// ========================================
// ADMIN OVERVIEW DASHBOARD
// ========================================

async function loadOverviewData() {
    const key = getAdminKeyOrAlert();
    if (!key) return;

    try {
        const res = await fetch(`${API_URL}/admin/overview`, {
            headers: { 'Authorization': `Bearer ${key}` }
        });

        const data = await res.json();

        if (!data.success) {
            console.error('Failed to load overview');
            return;
        }

        const stats = data.overview;
        renderOverviewStats(stats);

        // Refresh icons
        if (window.lucide) lucide.createIcons();

    } catch (e) {
        console.error('Error loading overview:', e);
    }
}

function renderOverviewStats(stats) {
    // Revenue
    document.getElementById('totalRevenueToday').textContent = formatCurrency(stats.total_revenue_today_ghs) + ' GHS';
    document.getElementById('revenueWeek').textContent = formatCurrency(stats.total_revenue_week_ghs) + ' GHS this week';

    // Buy Orders  
    document.getElementById('buyOrdersToday').textContent = stats.buy_orders_today;
    document.getElementById('buyOrdersPending').textContent = stats.buy_orders_pending;
    document.getElementById('buyOrdersWeek').textContent = stats.buy_orders_week;

    // Exchanges
    document.getElementById('exchangesToday').textContent = stats.exchanges_today;
    document.getElementById('exchangesProcessing').textContent = stats.exchanges_processing;
    document.getElementById('exchangesWeek').textContent = stats.exchanges_week;

    // Vendors
    document.getElementById('vendorsActive').textContent = stats.vendors_active;
    document.getElementById('vendorsTotal').textContent = stats.vendors_total;

    // Daily Volume
    document.getElementById('buyVolumeToday').textContent = '₵' + formatCurrency(stats.buy_volume_today_ghs);
    document.getElementById('exchangeVolumeToday').textContent = formatCurrency(stats.exchange_volume_today);
    document.getElementById('txVolumeToday').textContent = '₵' + formatCurrency(stats.tx_volume_today_ghs);

    const totalToday = stats.buy_volume_today_ghs + stats.exchange_volume_today + stats.tx_volume_today_ghs;
    document.getElementById('totalVolumeToday').textContent = '₵' + formatCurrency(totalToday);

    // Weekly Volume
    document.getElementById('buyVolumeWeek').textContent = '₵' + formatCurrency(stats.buy_volume_week_ghs);
    document.getElementById('exchangeVolumeWeek').textContent = formatCurrency(stats.exchange_volume_week);
    document.getElementById('txVolumeWeek').textContent = '₵' + formatCurrency(stats.tx_volume_week_ghs);

    const totalWeek = stats.buy_volume_week_ghs + stats.exchange_volume_week + stats.tx_volume_week_ghs;
    document.getElementById('totalVolumeWeek').textContent = '₵' + formatCurrency(totalWeek);

    // Status Breakdowns
    // Buy Orders
    document.getElementById('buyPending').textContent = stats.buy_orders_pending;
    document.getElementById('buyPaid').textContent = stats.buy_orders_paid;
    document.getElementById('buyTotal').textContent = stats.buy_orders_total;

    // Exchanges
    document.getElementById('exchangePending').textContent = stats.exchanges_pending;
    document.getElementById('exchangePaid').textContent = stats.exchanges_paid;
    document.getElementById('exchangeProcessing').textContent = stats.exchanges_processing;

    // Transactions
    document.getElementById('txPending').textContent = stats.transactions_pending;
    document.getElementById('txCompleted').textContent = stats.transactions_completed;
    document.getElementById('txTotal').textContent = stats.transactions_total;
}

function formatCurrency(amount) {
    return parseFloat(amount).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}
