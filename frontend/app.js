const API_BASE = "https://whatsapp-notifier-4cuw.onrender.com";
let currentUser = null;
let allContacts = [];
let allTemplates = [];
let allGroups = [];

// --- Helpers ---
function escapeHtml(text) {
    if (text == null) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

function toggleModal(id) {
    document.getElementById(id).classList.toggle('hidden');
}

function showToast(msg, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = msg;
    toast.style.background = type === 'success' ? 'var(--primary)' : 'var(--error)';
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), 3000);
}

async function apiFetch(endpoint, method = 'GET', body = null) {
    const token = localStorage.getItem('token');
    const options = {
        method,
        headers: {
            'Authorization': `Bearer ${token}`
        }
    };
    if (body) {
        options.headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(body);
    }

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        if (response.status === 401) {
            handleLogout();
            return null;
        }
        const data = await response.json();
        if (!response.ok) {
            const detail = typeof data.detail === 'string' ? data.detail : 'API Error';
            showToast(detail, 'error');
            return null;
        }
        return data;
    } catch (e) {
        showToast('Network error', 'error');
        return null;
    }
}

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    if (token) {
        showMainView();
    } else {
        showAuthView();
    }
});

// --- Auth Functions ---
function toggleAuth() {
    document.getElementById('loginForm').classList.toggle('hidden');
    document.getElementById('registerForm').classList.toggle('hidden');
}

async function handleLogin() {
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);

    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        if (response.ok) {
            localStorage.setItem('token', data.access_token);
            showToast('Logged in successfully!', 'success');
            showMainView();
        } else {
            showToast(data.detail || 'Login failed', 'error');
        }
    } catch (e) {
        showToast('Server error', 'error');
    }
}

async function handleRegister() {
    const username = document.getElementById('regUsername').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;

    try {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });

        const data = await response.json();
        if (response.ok) {
            localStorage.setItem('token', data.access_token);
            showToast('Account created!', 'success');
            showMainView();
        } else {
            showToast(data.detail || 'Registration failed', 'error');
        }
    } catch (e) {
        showToast('Server error', 'error');
    }
}

function handleLogout() {
    localStorage.removeItem('token');
    if (wsConnection) {
        wsConnection.close();
        wsConnection = null;
    }
    showAuthView();
}

// --- View/Page Management ---
function showAuthView() {
    document.getElementById('authView').classList.remove('hidden');
    document.getElementById('mainView').classList.add('hidden');
}

function showMainView() {
    document.getElementById('authView').classList.add('hidden');
    document.getElementById('mainView').classList.remove('hidden');
    showPage('dashboard');
}

function showPage(pageId) {
    document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
    document.querySelectorAll('.nav-links li').forEach(l => l.classList.remove('active'));

    document.getElementById(`page-${pageId}`).classList.remove('hidden');
    document.getElementById(`nav-${pageId}`).classList.add('active');

    if (pageId === 'dashboard') loadDashboardData();
    if (pageId === 'contacts') {
        loadContacts();
        loadGroups();
    }
    if (pageId === 'templates') loadTemplates();
    if (pageId === 'composer') loadComposerData();
    if (pageId === 'settings') loadSettings();
}

// --- Dashboard Logic ---
let dashboardStats = { total: 0, success: 0, failed: 0, rate: 0 };
let wsConnection = null;

function updateDashboardStats() {
    document.getElementById('stat-total').textContent = dashboardStats.total;
    document.getElementById('stat-success').textContent = dashboardStats.success;
    document.getElementById('stat-failed').textContent = dashboardStats.failed;
    document.getElementById('stat-rate').textContent = `${dashboardStats.rate}%`;
}

function setupWebSocket() {
    if (wsConnection) return;

    const token = localStorage.getItem('token');
    if (!token) return;

    const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsUrl = `${wsProtocol}://${window.location.host}/ws/progress?token=${encodeURIComponent(token)}`;
    wsConnection = new WebSocket(wsUrl);

    wsConnection.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);

            dashboardStats.total += 1;
            if (data.status === 'success') {
                dashboardStats.success += 1;
            } else {
                dashboardStats.failed += 1;
            }
            dashboardStats.rate = dashboardStats.total > 0
                ? Math.round((dashboardStats.success / dashboardStats.total) * 100)
                : 0;

            updateDashboardStats();

            const tbody = document.querySelector('#logsTable tbody');
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${escapeHtml(data.contact_name)}</td>
                <td class="${data.status === 'success' ? 'text-success' : 'text-error'}">${escapeHtml(data.status)}</td>
                <td style="font-size: 0.7rem; color: var(--text-muted)">${new Date(data.timestamp).toLocaleString()}</td>
            `;
            tbody.insertBefore(row, tbody.firstChild);

            if (tbody.children.length > 10) {
                tbody.removeChild(tbody.lastChild);
            }
        } catch (e) {
            console.error('Error processing websocket message', e);
        }
    };

    wsConnection.onclose = () => {
        wsConnection = null;
        if (!document.getElementById('mainView').classList.contains('hidden')) {
            setTimeout(setupWebSocket, 5000);
        }
    };
}

async function loadDashboardData() {
    const stats = await apiFetch('/analytics/stats');
    if (stats) {
        dashboardStats.total = stats.total_messages;
        dashboardStats.success = stats.success_count;
        dashboardStats.failed = stats.failed_count;
        dashboardStats.rate = stats.success_rate;
        updateDashboardStats();
    }

    const logs = await apiFetch('/analytics/logs?limit=10');
    if (logs) {
        const tbody = document.querySelector('#logsTable tbody');
        tbody.innerHTML = logs.map(log => `
            <tr>
                <td>${escapeHtml(log.contact_name)}</td>
                <td class="${log.status === 'success' ? 'text-success' : 'text-error'}">${escapeHtml(log.status)}</td>
                <td style="font-size: 0.7rem; color: var(--text-muted)">${new Date(log.timestamp).toLocaleString()}</td>
            </tr>
        `).join('');
    }

    setupWebSocket();
}

// --- Contacts Logic ---
async function loadContacts() {
    const contacts = await apiFetch('/contacts/');
    if (contacts) {
        allContacts = contacts;
        renderContacts(allContacts);
    }
}

function renderContacts(contacts) {
    const container = document.getElementById('contactsList');
    container.innerHTML = contacts.map(c => `
        <div class="contact-card glass-card">
            <h4>${escapeHtml(c.name)}</h4>
            <p style="color: var(--text-muted)">${escapeHtml(c.phone_number)}</p>
            <div style="margin-top: 10px">${c.tags ? c.tags.split(',').map(t => `<span class="tag">${escapeHtml(t.trim())}</span>`).join(' ') : ''}</div>
            <select onchange="addContactToGroup(this.value, ${c.id})">
                <option value="">Add to Group...</option>
                ${allGroups.map(g => `<option value="${g.id}">${escapeHtml(g.name)}</option>`).join('')}
            </select>
            <div class="card-actions">
                <button class="btn-icon" onclick="openEditContact(${c.id})">Edit</button>
                <button class="btn-danger" onclick="deleteContact(${c.id})">Delete</button>
            </div>
        </div>
    `).join('');
}

function filterContacts() {
    const query = document.getElementById('contactSearch').value.toLowerCase();
    const filtered = allContacts.filter(c =>
        c.name.toLowerCase().includes(query) ||
        c.phone_number.includes(query) ||
        (c.tags && c.tags.toLowerCase().includes(query))
    );
    renderContacts(filtered);
}

function openNewContactModal() {
    document.getElementById('contactModalTitle').textContent = 'Add New Contact';
    document.getElementById('editContactId').value = '';
    document.getElementById('newContactName').value = '';
    document.getElementById('newContactPhone').value = '';
    document.getElementById('newContactTags').value = '';
    document.getElementById('contactSaveBtn').textContent = 'Save';
    toggleModal('contactModal');
}

function openEditContact(id) {
    const contact = allContacts.find(c => c.id === id);
    if (!contact) return;

    document.getElementById('contactModalTitle').textContent = 'Edit Contact';
    document.getElementById('editContactId').value = id;
    document.getElementById('newContactName').value = contact.name;
    document.getElementById('newContactPhone').value = contact.phone_number;
    document.getElementById('newContactTags').value = contact.tags || '';
    document.getElementById('contactSaveBtn').textContent = 'Update';
    toggleModal('contactModal');
}

async function saveContact() {
    const name = document.getElementById('newContactName').value.trim();
    const phone_number = document.getElementById('newContactPhone').value.trim();
    const tags = document.getElementById('newContactTags').value.trim();
    const editId = document.getElementById('editContactId').value;

    if (!name || !phone_number) {
        showToast('Name and phone are required', 'error');
        return;
    }

    let success;
    if (editId) {
        success = await apiFetch(`/contacts/${editId}`, 'PUT', { name, phone_number, tags });
    } else {
        success = await apiFetch('/contacts/', 'POST', { name, phone_number, tags });
    }

    if (success) {
        showToast(editId ? 'Contact updated!' : 'Contact saved!');
        toggleModal('contactModal');
        loadContacts();
    }
}

async function deleteContact(id) {
    if (!confirm('Delete this contact?')) return;
    const success = await apiFetch(`/contacts/${id}`, 'DELETE');
    if (success) {
        showToast('Contact deleted!');
        loadContacts();
    }
}

// --- CSV Import ---
async function uploadCSV(input) {
    if (!input.files || input.files.length === 0) return;
    const file = input.files[0];
    const formData = new FormData();
    formData.append('file', file);

    const token = localStorage.getItem('token');
    try {
        const response = await fetch(`${API_BASE}/contacts/import`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });
        const data = await response.json();
        if (response.ok) {
            showToast(data.detail);
            loadContacts();
        } else {
            showToast(data.detail || 'Import failed', 'error');
        }
    } catch (e) {
        showToast('Upload error', 'error');
    }
    input.value = '';
}

// --- Groups Logic ---
async function loadGroups() {
    const groups = await apiFetch('/contacts/groups');
    if (groups) {
        allGroups = groups;
        const container = document.getElementById('groupsList');
        container.innerHTML = groups.map(g => `
            <div class="group-item">
                <h4 onclick="viewGroupContacts(${g.id})">${escapeHtml(g.name)}</h4>
                <div class="group-item-actions">
                    <span class="tag" onclick="viewGroupContacts(${g.id})">View</span>
                    <button class="btn-danger" onclick="event.stopPropagation(); deleteGroup(${g.id})">Delete</button>
                </div>
            </div>
        `).join('');
        renderContacts(allContacts);
    }
}

async function saveGroup() {
    const name = document.getElementById('newGroupName').value.trim();
    if (!name) {
        showToast('Group name is required', 'error');
        return;
    }
    const success = await apiFetch('/contacts/groups', 'POST', { name });
    if (success) {
        showToast('Group created!');
        toggleModal('groupModal');
        document.getElementById('newGroupName').value = '';
        loadGroups();
    }
}

async function deleteGroup(groupId) {
    if (!confirm('Delete this group? Contacts will not be removed.')) return;
    const success = await apiFetch(`/contacts/groups/${groupId}`, 'DELETE');
    if (success) {
        showToast('Group deleted!');
        loadGroups();
    }
}

async function addContactToGroup(groupId, contactId) {
    if (!groupId) return;
    const success = await apiFetch(`/contacts/groups/${groupId}/add-contact/${contactId}`, 'POST');
    if (success) {
        showToast('Contact added to group!');
    }
}

async function viewGroupContacts(groupId) {
    const group = allGroups.find(g => g.id === groupId);
    const groupName = group ? group.name : 'Group';
    const contacts = await apiFetch(`/contacts/groups/${groupId}/contacts`);
    if (contacts) {
        document.getElementById('groupContactsTitle').textContent = `Contacts in "${groupName}"`;
        const list = document.getElementById('groupContactsList');
        list.innerHTML = contacts.length > 0 ? contacts.map(c => `
            <div class="checklist-item">
                <span>${escapeHtml(c.name)} (${escapeHtml(c.phone_number)})</span>
            </div>
        `).join('') : '<p style="padding: 20px; color: var(--text-muted)">No contacts in this group yet.</p>';
        toggleModal('groupContactsModal');
    }
}

// --- Templates Logic ---
async function loadTemplates() {
    const templates = await apiFetch('/templates/');
    if (templates) {
        allTemplates = templates;
        renderTemplates(allTemplates);
    }
}

function renderTemplates(templates) {
    const container = document.getElementById('templatesList');
    container.innerHTML = templates.map(t => `
        <div class="template-card glass-card">
            <h4>${escapeHtml(t.title)}</h4>
            <p style="font-size: 0.8rem; margin-top: 10px; color: var(--text-muted)">${escapeHtml(t.body)}</p>
            <div class="card-actions">
                <button class="btn-icon" onclick="openEditTemplate(${t.id})">Edit</button>
                <button class="btn-danger" onclick="deleteTemplate(${t.id})">Delete</button>
            </div>
        </div>
    `).join('');
}

function filterTemplates() {
    const query = document.getElementById('templateSearch').value.toLowerCase();
    const filtered = allTemplates.filter(t => t.title.toLowerCase().includes(query));
    renderTemplates(filtered);
}

function openNewTemplateModal() {
    document.getElementById('templateModalTitle').textContent = 'Add New Template';
    document.getElementById('editTemplateId').value = '';
    document.getElementById('newTemplateTitle').value = '';
    document.getElementById('newTemplateBody').value = '';
    document.getElementById('templateSaveBtn').textContent = 'Save';
    toggleModal('templateModal');
}

function openEditTemplate(id) {
    const template = allTemplates.find(t => t.id === id);
    if (!template) return;

    document.getElementById('templateModalTitle').textContent = 'Edit Template';
    document.getElementById('editTemplateId').value = id;
    document.getElementById('newTemplateTitle').value = template.title;
    document.getElementById('newTemplateBody').value = template.body;
    document.getElementById('templateSaveBtn').textContent = 'Update';
    toggleModal('templateModal');
}

async function saveTemplate() {
    const title = document.getElementById('newTemplateTitle').value.trim();
    const body = document.getElementById('newTemplateBody').value.trim();
    const editId = document.getElementById('editTemplateId').value;

    if (!title || !body) {
        showToast('Title and body are required', 'error');
        return;
    }

    let success;
    if (editId) {
        success = await apiFetch(`/templates/${editId}`, 'PUT', { title, body });
    } else {
        success = await apiFetch('/templates/', 'POST', { title, body });
    }

    if (success) {
        showToast(editId ? 'Template updated!' : 'Template saved!');
        toggleModal('templateModal');
        loadTemplates();
    }
}

async function deleteTemplate(id) {
    if (!confirm('Delete this template?')) return;
    const success = await apiFetch(`/templates/${id}`, 'DELETE');
    if (success) {
        showToast('Template deleted!');
        loadTemplates();
    }
}

// --- Composer Logic ---
async function loadComposerData() {
    const templates = await apiFetch('/templates/');
    const select = document.getElementById('composerTemplateSelect');
    select.innerHTML = (templates || []).map(t => `<option value="${t.id}">${escapeHtml(t.title)}</option>`).join('');

    const groups = await apiFetch('/contacts/groups');
    const groupSelect = document.getElementById('composerGroupSelect');
    groupSelect.innerHTML = '<option value="">Select a Group</option>' + (groups || []).map(g => `<option value="${g.id}">${escapeHtml(g.name)}</option>`).join('');

    const contacts = await apiFetch('/contacts/');
    const checklist = document.getElementById('composerContactsChecklist');
    checklist.innerHTML = (contacts || []).map(c => `
        <div class="checklist-item">
            <input type="checkbox" value="${c.id}" class="contact-chk">
            <span>${escapeHtml(c.name)} (${escapeHtml(c.phone_number)})</span>
        </div>
    `).join('');
}

async function handleSendMessage() {
    const template_id = document.getElementById('composerTemplateSelect').value;
    const group_id = document.getElementById('composerGroupSelect').value || null;

    const contact_ids = Array.from(document.querySelectorAll('.contact-chk:checked')).map(cb => parseInt(cb.value));
    const scheduled_at = document.getElementById('composerScheduleTime').value;

    if (!template_id) {
        showToast('Please select a template', 'error');
        return;
    }
    if (!group_id && contact_ids.length === 0) {
        showToast('Select a group or at least one contact', 'error');
        return;
    }

    const payload = {
        template_id: parseInt(template_id),
        group_id: group_id ? parseInt(group_id) : null,
        contact_ids: contact_ids.length > 0 ? contact_ids : null,
        scheduled_at: scheduled_at ? new Date(scheduled_at).toISOString() : null
    };

    const success = await apiFetch('/messages/send', 'POST', payload);

    if (success) {
        showToast(success.detail || 'Messaging campaign started!');
        document.getElementById('composerScheduleTime').value = '';
        showPage('dashboard');
    }
}

// --- Settings Logic ---
async function loadSettings() {
    const user = await apiFetch('/auth/me');
    if (user) {
        document.getElementById('settingsEmail').value = user.email;
    }
}

async function updateProfile() {
    const email = document.getElementById('settingsEmail').value;
    const success = await apiFetch('/auth/profile', 'PUT', { email });
    if (success) {
        showToast('Profile updated!');
    }
}

async function changePassword() {
    const old_password = document.getElementById('oldPassword').value;
    const new_password = document.getElementById('newPassword').value;

    const success = await apiFetch('/auth/change-password', 'PUT', { old_password, new_password });
    if (success) {
        showToast('Password updated!');
        document.getElementById('oldPassword').value = '';
        document.getElementById('newPassword').value = '';
    }
}
