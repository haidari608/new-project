const state = { reservations: [], rooms: [], tasks: [], guests: [], movement: 'arrivals' };
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const escapeHtml = (value = '') => String(value).replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#039;', '"': '&quot;' }[char]));
const money = (value) => `$${Number(value || 0).toLocaleString()}`;
const dateLabel = (value) => value ? new Date(`${value}T12:00:00`).toLocaleDateString([], { month: 'short', day: 'numeric' }) : '—';

async function api(path, options = {}) {
    const response = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...options });
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || 'Something went wrong.');
    return body;
}

function toast(message, isError = false) {
    const element = $('#toast');
    element.textContent = message;
    element.className = `toast visible${isError ? ' error' : ''}`;
    window.setTimeout(() => element.className = 'toast', 3200);
}

function renderRooms(rooms, target) {
    target.innerHTML = rooms.map((room) => `<article class="room-card ${room.status.toLowerCase()}" data-room-id="${room.id}"><div class="room-card-top"><strong>${escapeHtml(room.number)}</strong><span class="room-rate">${money(room.rate)} <small>/ night</small></span></div><span>${escapeHtml(room.room_type)} · floor ${room.floor}</span><label class="room-status"><span class="status-dot"></span><select class="room-status-select" data-room-id="${room.id}">${['Clean', 'Inspected', 'Occupied', 'Dirty', 'Checkout', 'Maintenance'].map((status) => `<option ${status === room.status ? 'selected' : ''}>${status}</option>`).join('')}</select></label></article>`).join('');
}

function renderMovement() {
    const rows = state.reservations.filter((reservation) => state.movement === 'arrivals' ? reservation.status === 'Arriving' : ['Departing', 'Checked in'].includes(reservation.status));
    $('#movement-body').innerHTML = rows.length ? rows.map((reservation) => `<tr><td><strong>${escapeHtml(reservation.guest_name)}</strong>${reservation.vip ? '<span class="vip-tag">VIP</span>' : ''}<small>${escapeHtml(reservation.confirmation_code)}</small></td><td>${reservation.room_number || 'Unassigned'}<small>${escapeHtml(reservation.room_type || 'Room pending')}</small></td><td>${state.movement === 'arrivals' ? `in ${dateLabel(reservation.check_in)}` : `out ${dateLabel(reservation.check_out)}`}<small>${reservation.adults} adults${reservation.children ? ` · ${reservation.children} children` : ''}</small></td><td><span class="payment ${reservation.payment_status.toLowerCase()}">${escapeHtml(reservation.payment_status)}</span></td><td><button class="table-action" data-reservation-action="${reservation.id}" data-next-status="${state.movement === 'arrivals' ? 'Checked in' : 'Departed'}">${state.movement === 'arrivals' ? 'Check in' : 'Check out'} →</button></td></tr>`).join('') : '<tr><td colspan="5" class="empty-state">No movement in this queue.</td></tr>';
}

function renderReservations() {
    const rows = state.reservations;
    $('#reservations-body').innerHTML = rows.length ? rows.map((reservation) => `<tr><td><strong>${escapeHtml(reservation.confirmation_code)}</strong><small>${escapeHtml(reservation.source)}</small></td><td><strong>${escapeHtml(reservation.guest_name)}</strong>${reservation.vip ? '<span class="vip-tag">VIP</span>' : ''}<small>${escapeHtml(reservation.email)}</small></td><td>${dateLabel(reservation.check_in)} → ${dateLabel(reservation.check_out)}<small>${reservation.adults} adults</small></td><td>${reservation.room_number || 'Unassigned'}<small>${escapeHtml(reservation.room_type || 'Room pending')}</small></td><td>${money(reservation.total_amount)}<small>${escapeHtml(reservation.payment_status)}</small></td><td><span class="status-badge ${reservation.status.toLowerCase().replaceAll(' ', '-')}">${escapeHtml(reservation.status)}</span></td><td><select class="reservation-status" data-reservation-id="${reservation.id}"><option value="">Update</option>${['Confirmed', 'Arriving', 'Checked in', 'Departing', 'Departed', 'Cancelled'].map((status) => `<option>${status}</option>`).join('')}</select></td></tr>`).join('') : '<tr><td colspan="7" class="empty-state">No reservations match your search.</td></tr>';
}

function renderTasks() {
    $('#tasks-page-list').innerHTML = state.tasks.length ? state.tasks.map((task) => `<article class="task-card"><div class="task-main"><span class="priority ${task.priority.toLowerCase()}">${escapeHtml(task.priority)}</span><h3>Room ${escapeHtml(task.room_number || '—')} · ${escapeHtml(task.task_type)}</h3><p>${escapeHtml(task.description)}</p></div><div class="task-meta"><strong>${escapeHtml(task.assignee)}</strong><span>Due ${escapeHtml(task.due_time || 'when ready')}</span><select class="task-status" data-task-id="${task.id}"><option>${escapeHtml(task.status)}</option><option>In progress</option><option>Complete</option></select></div></article>`).join('') : '<div class="panel empty-state">All housekeeping tasks are complete.</div>';
    $('#attention-list').innerHTML = state.tasks.slice(0, 4).map((task) => `<div class="attention-item"><span class="priority ${task.priority.toLowerCase()}">${escapeHtml(task.priority)}</span><div><strong>Room ${escapeHtml(task.room_number || '—')}</strong><span>${escapeHtml(task.description)}</span></div><small>${escapeHtml(task.due_time)}</small></div>`).join('') || '<p class="muted empty-state">Nothing urgent right now.</p>';
}

function renderGuests() {
    $('#guest-list').innerHTML = state.guests.map((guest) => `<article class="guest-card"><div class="guest-avatar">${escapeHtml(guest.first_name[0] + guest.last_name[0])}</div><div><h3>${escapeHtml(guest.first_name)} ${escapeHtml(guest.last_name)} ${guest.vip ? '<span class="vip-tag">VIP</span>' : ''}</h3><p>${escapeHtml(guest.email || 'No email on file')}<br>${escapeHtml(guest.phone || 'No phone on file')}</p></div><div class="guest-stats"><strong>${guest.stays}</strong><span>stays</span><small>Last: ${dateLabel(guest.last_stay)}</small></div></article>`).join('') || '<div class="panel empty-state">No guests match your search.</div>';
}

async function refresh() {
    const [summary, reservations, rooms, tasks, guests] = await Promise.all([api('/api/summary'), api('/api/reservations'), api('/api/rooms'), api('/api/tasks'), api('/api/guests')]);
    Object.assign(state, { reservations: reservations.reservations, rooms: rooms.rooms, tasks: tasks.tasks, guests: guests.guests });
    $('#kpi-occupancy').textContent = `${summary.summary.occupancy}%`;
    $('#kpi-occupancy-detail').textContent = `${summary.summary.occupied_rooms} / ${summary.summary.total_rooms} rooms occupied`;
    $('#kpi-arrivals').textContent = summary.summary.arrivals;
    $('#kpi-departures').textContent = summary.summary.departures;
    $('#kpi-ready').textContent = `${summary.summary.rooms_ready} rooms ready now`;
    $('#kpi-revenue').textContent = money(summary.summary.room_revenue);
    $('#kpi-tasks').textContent = `${summary.summary.open_tasks} open tasks`;
    renderMovement(); renderReservations(); renderRooms(state.rooms, $('#overview-rooms')); renderRooms(state.rooms, $('#rooms-page-grid')); renderTasks(); renderGuests();
    $('#reservation-room').innerHTML = '<option value="">Assign later</option>' + state.rooms.filter((room) => ['Clean', 'Inspected'].includes(room.status)).map((room) => `<option value="${room.id}">${room.number} · ${escapeHtml(room.room_type)} · ${money(room.rate)}</option>`).join('');
    $('#sync-status').textContent = `Synced ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
}

async function updateReservation(id, status) { await api(`/api/reservations/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) }); await refresh(); toast(`Reservation marked ${status.toLowerCase()}.`); }
async function updateRoom(id, status) { await api(`/api/rooms/${id}`, { method: 'PATCH', body: JSON.stringify({ status }) }); await refresh(); toast(`Room marked ${status.toLowerCase()}.`); }
async function updateTask(id, status) { await api(`/api/tasks/${id}`, { method: 'PATCH', body: JSON.stringify({ status }) }); await refresh(); toast('Housekeeping task updated.'); }

function showView(name) {
    $$('.view').forEach((view) => view.classList.toggle('hidden', view.id !== `${name}-view`));
    $$('.nav-item').forEach((item) => item.classList.toggle('active', item.dataset.view === name));
    const headings = { overview: ['Good morning, Alina.', 'Your property at a glance, with the next decisions in view.'], reservations: ['Reservations', 'Search, check in, and close out every stay.'], rooms: ['Rooms & rates', 'Update room readiness as the property changes.'], housekeeping: ['Housekeeping', 'Prioritized work by room, assignee, and due time.'], guests: ['Guest directory', 'Keep preferences and stay history close to the desk.'] };
    $('#page-heading').textContent = headings[name][0]; $('#page-subtitle').textContent = headings[name][1]; $('#sidebar').classList.remove('open');
}

function openModal() { $('#reservation-modal').classList.remove('hidden'); $('#reservation-form').querySelector('[name="first_name"]').focus(); }
function closeModal() { $('#reservation-modal').classList.add('hidden'); $('#reservation-form').reset(); $('#reservation-error').textContent = ''; }

$$('.nav-item').forEach((item) => item.addEventListener('click', () => showView(item.dataset.view)));
$$('[data-view-target]').forEach((item) => item.addEventListener('click', () => showView(item.dataset.viewTarget)));
$$('[data-open-modal]').forEach((item) => item.addEventListener('click', openModal));
$$('[data-close-modal]').forEach((item) => item.addEventListener('click', closeModal));
$('#menu-toggle').addEventListener('click', () => { const open = $('#sidebar').classList.toggle('open'); $('#menu-toggle').setAttribute('aria-expanded', open); });
$$('[data-movement]').forEach((tab) => tab.addEventListener('click', () => { state.movement = tab.dataset.movement; $$('[data-movement]').forEach((item) => item.classList.toggle('active', item === tab)); renderMovement(); }));
document.addEventListener('click', async (event) => {
    const action = event.target.closest('[data-reservation-action]');
    if (action) { try { await updateReservation(action.dataset.reservationAction, action.dataset.nextStatus); } catch (error) { toast(error.message, true); } }
});
document.addEventListener('change', async (event) => {
    try {
        if (event.target.matches('.room-status-select')) await updateRoom(event.target.dataset.roomId, event.target.value);
        if (event.target.matches('.reservation-status') && event.target.value) await updateReservation(event.target.dataset.reservationId, event.target.value);
        if (event.target.matches('.task-status')) await updateTask(event.target.dataset.taskId, event.target.value);
    } catch (error) { toast(error.message, true); }
});
$('#reservation-search').addEventListener('input', async (event) => { const data = await api(`/api/reservations?search=${encodeURIComponent(event.target.value)}`); state.reservations = data.reservations; renderReservations(); });
$('#reservation-filter').addEventListener('change', async (event) => { const data = await api(`/api/reservations?status=${encodeURIComponent(event.target.value)}`); state.reservations = data.reservations; renderReservations(); });
$('#guest-search').addEventListener('input', async (event) => { const data = await api(`/api/guests?search=${encodeURIComponent(event.target.value)}`); state.guests = data.guests; renderGuests(); });
$('#reservation-form').addEventListener('submit', async (event) => { event.preventDefault(); const payload = Object.fromEntries(new FormData(event.target).entries()); try { await api('/api/reservations', { method: 'POST', body: JSON.stringify(payload) }); closeModal(); await refresh(); toast('Reservation created successfully.'); showView('reservations'); } catch (error) { $('#reservation-error').textContent = error.message; } });

function updateClock() { const now = new Date(); $('#clock').textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }); $('#today-label').textContent = now.toLocaleDateString([], { weekday: 'long', day: 'numeric', month: 'long' }); }
updateClock(); setInterval(updateClock, 1000); refresh().catch((error) => toast(error.message, true));
