const $ = (selector) => document.querySelector(selector);
const state = { token: localStorage.getItem('helpdesk_token'), user: null, tickets: [], categories: [] };
const statusLabel = (status) => ({ OPEN: 'Open', IN_PROGRESS: 'In progress', WAITING_FOR_USER: 'Waiting for user', RESOLVED: 'Resolved', CLOSED: 'Closed' }[status] || status);
const statusClass = (status) => `status-${String(status).toLowerCase().replaceAll('_', '-')}`;
const safe = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
function notify(message, error = false) { const toast = $('#toast'); toast.textContent = message; toast.className = `toast show${error ? ' error' : ''}`; clearTimeout(notify.timer); notify.timer = setTimeout(() => { toast.className = 'toast'; }, 3200); }
async function api(path, options = {}) {
  const headers = { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...(state.token ? { Authorization: `Bearer ${state.token}` } : {}), ...options.headers };
  const response = await fetch(path, { ...options, headers });
  if (response.status === 401) { signOut(); throw new Error('Please sign in again.'); }
  const data = response.status === 204 ? null : await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || data.message || 'Something went wrong. Please try again.');
  return data;
}
function signOut() { state.token = null; state.user = null; localStorage.removeItem('helpdesk_token'); $('#appView').classList.add('hidden'); $('#authView').classList.remove('hidden'); }
function openApp(user) {
  state.user = user;
  $('#authView').classList.add('hidden'); $('#appView').classList.remove('hidden');
  const name = `${user.first_name} ${user.last_name}`.trim();
  $('#userName').textContent = name; $('#userRole').textContent = user.role; $('#userAvatar').textContent = (user.first_name || 'U').slice(0, 1).toUpperCase();
  const hour = new Date().getHours(); $('#greeting').textContent = `${hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'}, ${user.first_name || 'there'}`;
  $('#todayDate').textContent = new Intl.DateTimeFormat(undefined, { weekday: 'short', month: 'short', day: 'numeric' }).format(new Date());
}
async function loadWorkspace() {
  const user = await api('/me'); openApp(user);
  const ticketRequest = user.role === 'admin'
    ? api('/tickets/all')
    : user.role === 'analyst'
      ? Promise.all([api('/tickets/'), api('/tickets/assigned')]).then(([created, assigned]) => [...new Map([...created, ...assigned].map((ticket) => [ticket.id, ticket])).values()].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)))
      : api('/tickets/');
  const [tickets, categories] = await Promise.all([ticketRequest, api('/categories/')]);
  state.tickets = tickets; state.categories = categories;
  const categorySelect = $('#ticketCategory'); categorySelect.innerHTML = '<option value="">Choose a category</option>' + categories.map((category) => `<option value="${category.id}">${safe(category.name)}</option>`).join('');
  renderTickets();
}
function ticketRow(ticket) {
  const category = state.categories.find((item) => item.id === ticket.category_id);
  const date = ticket.created_at ? new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(new Date(ticket.created_at)) : '';
  return `<article class="ticket-row"><div class="ticket-main"><div class="ticket-title">${safe(ticket.title)}</div><div class="ticket-meta">#${ticket.id} · ${date}</div></div><span class="ticket-category">${safe(category?.name || 'Support')}</span><span class="status-pill ${statusClass(ticket.status)}">${safe(statusLabel(ticket.status))}</span><span class="priority-pill priority-${safe(String(ticket.priority).toLowerCase())}">${safe(ticket.priority)}</span></article>`;
}
function emptyMarkup(title, message) { return `<div class="empty-state"><strong>${title}</strong>${message}</div>`; }
function renderTickets() {
  const counts = { total: state.tickets.length, open: 0, progress: 0, resolved: 0 };
  state.tickets.forEach((ticket) => { if (ticket.status === 'OPEN') counts.open++; if (ticket.status === 'IN_PROGRESS' || ticket.status === 'WAITING_FOR_USER') counts.progress++; if (ticket.status === 'RESOLVED') counts.resolved++; });
  $('#statTotal').textContent = counts.total; $('#statOpen').textContent = counts.open; $('#statProgress').textContent = counts.progress; $('#statResolved').textContent = counts.resolved; $('#navTicketCount').textContent = counts.total;
  const recent = state.tickets.slice(0, 5);
  $('#recentTickets').innerHTML = recent.length ? recent.map(ticketRow).join('') : emptyMarkup('Nothing here yet', 'Create a ticket and we’ll take it from there.');
  filterTickets();
}
function filterTickets() {
  const term = ($('#ticketSearch')?.value || '').trim().toLowerCase(); const status = $('#statusFilter')?.value || '';
  const tickets = state.tickets.filter((ticket) => (!status || ticket.status === status) && (!term || `${ticket.title} ${ticket.description} ${ticket.id}`.toLowerCase().includes(term)));
  $('#allTickets').innerHTML = tickets.length ? tickets.map(ticketRow).join('') : emptyMarkup(state.tickets.length ? 'No matching tickets' : 'No tickets yet', state.tickets.length ? 'Try a different search or status.' : 'Your requests will show up here.');
}
function showPage(page) {
  const ticketsPage = page === 'tickets'; $('#overviewPage').classList.toggle('hidden', ticketsPage); $('#ticketsPage').classList.toggle('hidden', !ticketsPage);
  document.querySelectorAll('.nav-link').forEach((link) => link.classList.toggle('active', link.dataset.view === page)); $('#breadcrumbPage').textContent = ticketsPage ? 'My tickets' : 'Overview';
}
function openTicketDialog() { $('#ticketDialog').showModal(); }

$('#loginForm').addEventListener('submit', async (event) => {
  event.preventDefault(); const button = event.currentTarget.querySelector('button'); button.disabled = true; button.textContent = 'Signing in…';
  try {
    const form = new URLSearchParams(new FormData(event.currentTarget));
    const response = await fetch('/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: form });
    const data = await response.json(); if (!response.ok) throw new Error(data.detail || 'Unable to sign in. Check your details and try again.');
    state.token = data.access_token; localStorage.setItem('helpdesk_token', state.token); await loadWorkspace();
  } catch (error) { notify(error.message, true); }
  finally { button.disabled = false; button.innerHTML = 'Sign in <span>→</span>'; }
});
document.querySelectorAll('.nav-link').forEach((link) => link.addEventListener('click', () => showPage(link.dataset.view)));
document.querySelectorAll('[data-go="tickets"]').forEach((button) => button.addEventListener('click', () => showPage('tickets')));
['#newTicketTop', '#newTicketPage', '#helpNewTicket'].forEach((selector) => $(selector).addEventListener('click', openTicketDialog));
document.querySelectorAll('.close-dialog').forEach((button) => button.addEventListener('click', () => $('#ticketDialog').close()));
$('#ticketSearch').addEventListener('input', filterTickets); $('#statusFilter').addEventListener('change', filterTickets); $('#logoutBtn').addEventListener('click', signOut);
$('#ticketForm').addEventListener('submit', async (event) => {
  event.preventDefault(); const button = event.currentTarget.querySelector('[type="submit"]'); button.disabled = true;
  const payload = { title: $('#ticketTitle').value.trim(), description: $('#ticketDescription').value.trim(), category_id: Number($('#ticketCategory').value), priority: $('#ticketPriority').value };
  try { await api('/tickets/', { method: 'POST', body: JSON.stringify(payload) }); $('#ticketDialog').close(); event.currentTarget.reset(); $('#ticketPriority').value = 'MEDIUM'; await loadWorkspace(); notify('Your ticket was submitted successfully.'); showPage('tickets'); }
  catch (error) { notify(error.message, true); }
  finally { button.disabled = false; }
});

if (state.token) loadWorkspace().catch((error) => { signOut(); notify(error.message, true); });
