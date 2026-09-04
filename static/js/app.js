const movementData = {
    arrivals: [
        ['09:30', 'Maya Chen', 'Deluxe King', '2 nights', 'Pre-paid'],
        ['11:15', 'Oliver Grant', 'Garden Suite', '4 nights', 'Due today'],
        ['13:40', 'Sofia Alvarez', 'Twin Room', '1 night', 'Pre-paid'],
        ['16:00', 'Liam Brooks', 'Executive Suite', '3 nights', 'Pre-paid']
    ],
    departures: [
        ['104', 'Amelia James', '—', '11:00 checkout', 'Express'],
        ['216', 'Noah Wilson', '—', '11:00 checkout', 'Standard'],
        ['305', 'Emma Davis', '—', '12:00 checkout', 'Late checkout']
    ]
};

const tableBody = document.querySelector('#movement-table tbody');
const confirmation = document.querySelector('#confirmation');

function renderMovement(view = 'arrivals') {
    tableBody.innerHTML = movementData[view].map(row => `<tr>${row.map((cell, index) => `<td class="${index === 4 ? 'table-status' : ''}">${cell}</td>`).join('')}</tr>`).join('');
}

document.querySelectorAll('.tab').forEach(tab => tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(item => item.classList.remove('active'));
    tab.classList.add('active');
    renderMovement(tab.dataset.tab);
    confirmation.hidden = true;
}));

document.querySelector('#confirm-arrival').addEventListener('click', () => {
    confirmation.textContent = 'Next arrival for Maya Chen is confirmed and front desk has been notified.';
    confirmation.hidden = false;
});

document.querySelectorAll('.nav-item').forEach(item => item.addEventListener('click', event => {
    event.preventDefault();
    document.querySelectorAll('.nav-item').forEach(link => link.classList.remove('active'));
    item.classList.add('active');
    document.querySelectorAll('.nav-item span').forEach(dot => { dot.textContent = '○'; });
    item.querySelector('span').textContent = '●';
}));

const sidebar = document.querySelector('#sidebar');
const menuToggle = document.querySelector('#menu-toggle');
menuToggle.addEventListener('click', () => {
    const open = sidebar.classList.toggle('open');
    menuToggle.setAttribute('aria-expanded', open);
});

function updateClock() {
    const clock = document.querySelector('#clock');
    const now = new Date();
    clock.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    clock.dateTime = now.toISOString();
}

renderMovement();
updateClock();
setInterval(updateClock, 1000);
