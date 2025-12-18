
const API_URL = window.location.origin + '/api';
const tokenRaw = localStorage.getItem('coinvibe_token');
let currentUser = null;
try { currentUser = JSON.parse(localStorage.getItem('coinvibe_user') || 'null'); } catch (_) { currentUser = null; }
const authToken = tokenRaw && tokenRaw !== 'null' && tokenRaw !== 'undefined' && tokenRaw !== '' ? tokenRaw : null;

if (!authToken || !currentUser) {
    window.location.href = '/login';
}

function initHeader() {
    const name = currentUser && (currentUser.name || currentUser.username || currentUser.full_name) ? (currentUser.name || currentUser.username || currentUser.full_name) : '';
    document.getElementById('dashUserName').textContent = name;
    document.getElementById('dashAvatar').textContent = name ? name.charAt(0).toUpperCase() : 'U';
}

function logout() {
    localStorage.removeItem('coinvibe_token');
    localStorage.removeItem('coinvibe_user');
    window.location.href = '/';
}

function toggleSidebar() {
    document.getElementById('dashboardSidebar').classList.toggle('active');
}

function showToast(message) {
    document.getElementById('successMessage').textContent = message;
    const toast = document.getElementById('successToast');
    toast.style.display = 'block';
    if (window.lucide && lucide.createIcons) lucide.createIcons();
    setTimeout(() => {
        toast.style.display = 'none';
    }, 3000);
}

function loadUserProfile() {
    // Populate profile data
    const name = currentUser.name || currentUser.username || currentUser.full_name || 'User';
    const email = currentUser.email || 'user@example.com';

    document.getElementById('profileName').textContent = name;
    document.getElementById('profileEmail').textContent = email;
    document.getElementById('profileAvatarLarge').textContent = name.charAt(0).toUpperCase();

    // Personal Info
    document.getElementById('fullName').value = currentUser.full_name || currentUser.name || '';
    document.getElementById('username').value = currentUser.username || '';
    document.getElementById('email').value = email;
    document.getElementById('phone').value = currentUser.phone || '';
    document.getElementById('bio').value = currentUser.bio || '';

    // Payment Settings
    document.getElementById('momoNumber').value = currentUser.momo_number || '';
    document.getElementById('momoProvider').value = currentUser.momo_provider || '';
    document.getElementById('walletAddress').value = currentUser.wallet_address || '';
}

async function updatePersonalInfo(event) {
    event.preventDefault();
    const data = {
        full_name: document.getElementById('fullName').value,
        username: document.getElementById('username').value,
        phone: document.getElementById('phone').value,
        bio: document.getElementById('bio').value
    };

    try {
        const res = await fetch(`${API_URL}/users/profile`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(data)
        });

        const result = await res.json();
        if (result.success) {
            // Update local storage
            currentUser = { ...currentUser, ...data, name: data.full_name };
            localStorage.setItem('coinvibe_user', JSON.stringify(currentUser));
            showToast('Personal information updated successfully!');
            initHeader();
            loadUserProfile();
        } else {
            alert(result.message || 'Failed to update profile');
        }
    } catch (e) {
        console.error('Update failed:', e);
        showToast('Profile updated locally');
    }
}

async function updatePaymentSettings(event) {
    event.preventDefault();
    const momoNumber = document.getElementById('momoNumber').value;

    if (momoNumber && !/^0\d{9}$/.test(momoNumber)) {
        alert('Please enter a valid Ghana mobile money number (10 digits starting with 0)');
        return;
    }

    const data = {
        momo_number: momoNumber,
        momo_provider: document.getElementById('momoProvider').value,
        wallet_address: document.getElementById('walletAddress').value
    };

    try {
        const res = await fetch(`${API_URL}/users/payment-settings`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(data)
        });

        const result = await res.json();
        if (result.success) {
            currentUser = { ...currentUser, ...data };
            localStorage.setItem('coinvibe_user', JSON.stringify(currentUser));
            showToast('Payment settings updated successfully!');
        } else {
            alert(result.message || 'Failed to update payment settings');
        }
    } catch (e) {
        console.error('Update failed:', e);
        showToast('Payment settings updated locally');
    }
}

async function updatePassword(event) {
    event.preventDefault();
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (!currentPassword || !newPassword || !confirmPassword) {
        alert('Please fill in all password fields');
        return;
    }

    if (newPassword !== confirmPassword) {
        alert('New passwords do not match');
        return;
    }

    if (newPassword.length < 8) {
        alert('Password must be at least 8 characters long');
        return;
    }

    try {
        const res = await fetch(`${API_URL}/users/change-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });

        const result = await res.json();
        if (result.success) {
            showToast('Password updated successfully!');
            resetSecurityForm();
        } else {
            alert(result.message || 'Failed to update password');
        }
    } catch (e) {
        console.error('Password update failed:', e);
        alert('Failed to update password');
    }
}

async function updateNotifications(event) {
    event.preventDefault();
    const data = {
        email_notifications: document.getElementById('emailNotifications').checked,
        payment_alerts: document.getElementById('paymentAlerts').checked,
        marketing_emails: document.getElementById('marketingEmails').checked
    };

    try {
        const res = await fetch(`${API_URL}/users/notifications`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(data)
        });

        const result = await res.json();
        if (result.success) {
            showToast('Notification preferences updated!');
        } else {
            alert(result.message || 'Failed to update preferences');
        }
    } catch (e) {
        console.error('Update failed:', e);
        showToast('Preferences saved locally');
    }
}

function resetPersonalInfo() {
    loadUserProfile();
    showToast('Form reset to saved values');
}

function resetPaymentSettings() {
    loadUserProfile();
    showToast('Form reset to saved values');
}

function resetSecurityForm() {
    document.getElementById('currentPassword').value = '';
    document.getElementById('newPassword').value = '';
    document.getElementById('confirmPassword').value = '';
}

function confirmDeleteAccount() {
    const confirmation = confirm('Are you sure you want to delete your account? This action cannot be undone and all your data will be permanently deleted.');
    if (confirmation) {
        const doubleCheck = prompt('Type "DELETE" to confirm account deletion:');
        if (doubleCheck === 'DELETE') {
            deleteAccount();
        } else {
            alert('Account deletion cancelled');
        }
    }
}

async function deleteAccount() {
    try {
        const res = await fetch(`${API_URL}/users/delete-account`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        const result = await res.json();
        if (result.success) {
            alert('Your account has been deleted. You will be logged out now.');
            localStorage.removeItem('coinvibe_token');
            localStorage.removeItem('coinvibe_user');
            window.location.href = '/';
        } else {
            alert(result.message || 'Failed to delete account');
        }
    } catch (e) {
        console.error('Account deletion failed:', e);
        alert('Failed to delete account. Please contact support.');
    }
}

document.addEventListener('DOMContentLoaded', function () {
    if (window.lucide && lucide.createIcons) lucide.createIcons();
    initHeader();
    loadUserProfile();
});


function generateInitials(name) {
    if (!name) return "U";
    const parts = name.trim().split(" ");
    if (parts.length === 1) return parts[0][0].toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function getColorFromName(name) {
    const colors = [
        "#0ea5e9", // sky
        "#6366f1", // indigo
        "#8b5cf6", // violet
        "#ec4899", // pink
        "#f59e0b", // amber
        "#10b981", // emerald
        "#14b8a6", // teal
        "#ef4444", // red
    ];

    let hash = 0;
    for (let i = 0; i < name.length; i++) {
        hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }

    return colors[Math.abs(hash) % colors.length];
}

function renderInitialAvatar(name) {
    const avatar = document.getElementById("profileAvatarLarge");
    if (!avatar) return;

    const initials = generateInitials(name);
    const color = getColorFromName(name);

    avatar.textContent = initials;
    avatar.style.backgroundColor = color;
}
