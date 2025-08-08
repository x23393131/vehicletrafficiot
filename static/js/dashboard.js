// Initialize the map
const map = L.map('map').setView([53.349805, -6.26031], 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

// Store markers to update them instead of creating new ones
const markers = {};

// Connect to Socket.IO
const socket = io({
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000
});

// Connection status handlers
socket.on('connect', () => {
    document.getElementById('connection-status').className = 'badge bg-success';
    document.getElementById('connection-status').textContent = 'Connected';
    console.log('Connected to server');
});

socket.on('disconnect', () => {
    document.getElementById('connection-status').className = 'badge bg-danger';
    document.getElementById('connection-status').textContent = 'Disconnected';
    console.log('Disconnected from server');
});

// Handle incoming data
socket.on('update', (data) => {
    updateDashboard(data);
});

// Function to update the dashboard with new data
function updateDashboard(data) {
    // Update vehicle count
    document.getElementById('vehicle-count').textContent = 
        `${data.vehicle_count} vehicles`;
    
    // Update traffic status
    const trafficElement = document.getElementById('current-traffic');
    let badgeClass = 'badge bg-success';
    if (data.traffic_level === 'MEDIUM') badgeClass = 'badge bg-warning';
    if (data.traffic_level === 'HEAVY') badgeClass = 'badge bg-danger';
    
    trafficElement.innerHTML = 
        `<span class="${badgeClass}">${data.traffic_level} TRAFFIC</span>`;
    
    // Update map marker
    const markerKey = `${data.lat}-${data.lng}`;
    if (!markers[markerKey]) {
        markers[markerKey] = L.marker([data.lat, data.lng]).addTo(map);
    }
    markers[markerKey]
        .setLatLng([data.lat, data.lng])
        .bindPopup(`
            <b>Location:</b> ${data.lat.toFixed(4)}, ${data.lng.toFixed(4)}<br>
            <b>Vehicles:</b> ${data.vehicle_count}<br>
            <b>Status:</b> ${data.traffic_level}<br>
            <b>Gateway:</b> ${data.gateway || 'Unknown'}
        `)
        .openPopup();
    
    // Center map on new data
    map.setView([data.lat, data.lng], 13);
}