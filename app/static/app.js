// Dashboard State Variables
let activeRole = 'Technician'; // 'Technician' or 'Dispatch Manager'
let activeTechId = 'tech_1';
let activeEntity = null; // { type: 'tech'|'job', id: string }
let dbState = null;
let mapSelectedEntity = null;

// DOM Elements
const selectTech = document.getElementById('select-tech');
const techUserContext = document.getElementById('tech-user-context');
const managerUserContext = document.getElementById('manager-user-context');
const techFilters = document.getElementById('tech-filters');
const jobFilters = document.getElementById('job-filters');
const techListWrapper = document.getElementById('tech-list-wrapper');
const jobListWrapper = document.getElementById('job-list-wrapper');
const techList = document.getElementById('tech-list');
const jobList = document.getElementById('job-list');
const approvalsList = document.getElementById('approvals-list');
const approvalsCountBadge = document.getElementById('approvals-count-badge');
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const typingIndicator = document.getElementById('typing-indicator');
const auditLog = document.getElementById('audit-log');
const seedPrompts = document.getElementById('seed-prompts');
const entityDetailsCard = document.getElementById('entity-details-card');
const detailsContent = document.getElementById('details-content');
const currentTimeSpan = document.getElementById('current-time');

// Leaflet Map Variables
let map = null;
let mapLayers = [];
let activeTileLayer = null;
let activeTheme = 'dark';

// Filter states
let activeTechFilter = 'all';
let activeJobFilter = 'all';
let searchQuery = '';

// Seed prompts dataset
const SEED_PROMPTS = {
    'Technician': [
        { label: "Can't do Job J1 (Inaccessible)", text: "I can't complete Job job_1 because the site is inaccessible." },
        { label: "Unassign Job J7 (Traffic)", text: "Remove Job job_7 from my schedule. I'm delayed in traffic." },
        { label: "Request Reassign J3 -> Tech 4", text: "Move Job job_3 from me to Technician tech_4 because I am running late." },
        { label: "Transfer J5 to Priya (tech_6)", text: "Please reassign Job job_5 to tech_6 because she has the right skills." }
    ],
    'Dispatch Manager': [
        { label: "Approve Request req_1", text: "Approve reassignment request req_1." },
        { label: "Reject Request req_1", text: "Reject reassignment request req_1 because tech_4 is already overbooked." },
        { label: "Unassigned Jobs Query", text: "Are there any unassigned jobs in the West territory?" },
        { label: "Show Technician status", text: "List all active technicians and their workloads." }
    ]
};

// Leaflet does not need manual projection helpers

// Initialise Dashboard
window.addEventListener('load', () => {
    // Leaflet Map Setup
    initLeafletMap();

    // Clock
    setInterval(() => {
        const date = new Date();
        currentTimeSpan.textContent = date.toLocaleTimeString() + ' PST';
    }, 1000);

    // Initial load
    fetchState();
    updateApiKeyButtonState();
    
    // Auto-poll state every 5 seconds to keep the operations screen live
    setInterval(fetchState, 5000);
});

function initLeafletMap() {
    const darkTileUrl = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
    const lightTileUrl = 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';
    const attribution = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';

    map = L.map('ops-map', {
        zoomControl: true,
        attributionControl: true
    }).setView([37.765, -122.44], 12);

    activeTheme = localStorage.getItem('theme') || 'dark';
    if (activeTheme === 'light') {
        document.body.classList.add('light-theme');
        const btnTheme = document.getElementById('btn-theme-toggle');
        if (btnTheme) btnTheme.innerHTML = '<i class="fa-solid fa-sun"></i>';
    }

    const tileUrl = activeTheme === 'light' ? lightTileUrl : darkTileUrl;
    activeTileLayer = L.tileLayer(tileUrl, { attribution: attribution, maxZoom: 20 }).addTo(map);
}

function toggleTheme() {
    const darkTileUrl = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
    const lightTileUrl = 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';
    const btnTheme = document.getElementById('btn-theme-toggle');

    if (document.body.classList.contains('light-theme')) {
        document.body.classList.remove('light-theme');
        localStorage.setItem('theme', 'dark');
        activeTheme = 'dark';
        if (btnTheme) btnTheme.innerHTML = '<i class="fa-solid fa-moon"></i>';
        activeTileLayer.setUrl(darkTileUrl);
    } else {
        document.body.classList.add('light-theme');
        localStorage.setItem('theme', 'light');
        activeTheme = 'light';
        if (btnTheme) btnTheme.innerHTML = '<i class="fa-solid fa-sun"></i>';
        activeTileLayer.setUrl(lightTileUrl);
    }
}

// State fetching
async function fetchState() {
    try {
        const response = await fetch('/api/state');
        const data = await response.json();
        dbState = data;
        renderDashboard();
    } catch (err) {
        console.error("Error fetching state:", err);
    }
}

// Reset state
async function resetDatabase() {
    if (!confirm("Are you sure you want to reset the simulation state?")) return;
    try {
        addMessage('system', 'System state resetting...');
        const response = await fetch('/api/reset', { method: 'POST' });
        const data = await response.json();
        dbState = data;
        renderDashboard();
        addMessage('system', 'System state successfully restored to initial seed dataset.');
    } catch (err) {
        console.error("Error resetting database:", err);
    }
}

// Switch Left Panel Tabs
function switchLeftTab(tab) {
    const btnTechs = document.getElementById('tab-btn-techs');
    const btnJobs = document.getElementById('tab-btn-jobs');
    
    if (tab === 'techs') {
        btnTechs.classList.add('active');
        btnJobs.classList.remove('active');
        techListWrapper.classList.remove('hidden');
        jobListWrapper.classList.add('hidden');
        techFilters.classList.remove('hidden');
        jobFilters.classList.add('hidden');
    } else {
        btnTechs.classList.remove('active');
        btnJobs.classList.add('active');
        techListWrapper.classList.add('hidden');
        jobListWrapper.classList.remove('hidden');
        techFilters.classList.add('hidden');
        jobFilters.classList.remove('hidden');
    }
}

// Set active role (Technician or Dispatch Manager)
function setRole(role) {
    activeRole = role;
    
    // Toggle UI buttons
    document.getElementById('btn-tech-role').classList.toggle('active', role === 'Technician');
    document.getElementById('btn-manager-role').classList.toggle('active', role === 'Dispatch Manager');
    
    // Toggle active tech contexts
    techUserContext.classList.toggle('hidden', role !== 'Technician');
    managerUserContext.classList.toggle('hidden', role !== 'Dispatch Manager');
    
    // Re-render chat seeds & dashboard elements
    renderSeedPrompts();
    renderApprovals();
    
    clearChat();
}

// Handle Simulated Technician selection
function changeActiveTech() {
    activeTechId = selectTech.value;
    addMessage('system', `Now simulating inputs as Technician: ${selectTech.options[selectTech.selectedIndex].text}`);
    clearChat();
}

function clearChat() {
    chatMessages.innerHTML = `
        <div class="message system">
            <div class="message-content">
                Welcome to Aerocore Field Service Copilot. Use the dropdown/role switcher to toggle permissions. Speak naturally to query status, reassign jobs, or handle exceptions.
            </div>
        </div>
    `;
}

// Filter triggers
function setTechFilter(val) {
    activeTechFilter = val;
    document.querySelectorAll('#tech-filters .pill').forEach(btn => {
        btn.classList.toggle('active', btn.textContent.trim() === val || (val === 'all' && btn.textContent.trim() === 'All'));
    });
    renderTechs();
}

// Set job filter
function setJobFilter(val) {
    activeJobFilter = val;
    document.querySelectorAll('#job-filters .pill').forEach(btn => {
        btn.classList.toggle('active', btn.textContent.trim().startsWith(val) || (val === 'all' && btn.textContent.trim() === 'All'));
    });
    renderJobs();
}

function handleEntitySearch() {
    searchQuery = document.getElementById('entity-search').value.toLowerCase();
    renderTechs();
    renderJobs();
}

// Render loop for the visual elements
function renderDashboard() {
    if (!dbState) return;
    
    // Render KPIs
    const kpis = dbState.kpis;
    document.querySelector('#kpi-total-jobs .kpi-value').textContent = kpis.total_jobs;
    document.querySelector('#kpi-unassigned-jobs .kpi-value').textContent = kpis.unassigned_jobs;
    document.querySelector('#kpi-pending-approvals .kpi-value').textContent = kpis.pending_approvals;
    document.querySelector('#kpi-active-techs .kpi-value').textContent = kpis.active_techs;
    
    // Add pulsing glow to approvals if there are pending items
    document.querySelector('#kpi-pending-approvals .kpi-icon').classList.toggle('highlight-glow', kpis.pending_approvals > 0);
    
    // Populate select tech dropdown once
    if (selectTech.children.length === 0) {
        dbState.technicians.forEach(t => {
            if (t.role === 'Technician') {
                const opt = document.createElement('option');
                opt.value = t.id;
                opt.textContent = `${t.name} (${t.territory})`;
                selectTech.appendChild(opt);
            }
        });
        activeTechId = selectTech.value;
    }
    
    renderTechs();
    renderJobs();
    renderApprovals();
    renderAuditLog();
    renderSeedPrompts();
    drawMap();
}

function renderTechs() {
    techList.innerHTML = '';
    const filtered = dbState.technicians.filter(t => {
        if (t.role !== 'Technician') return false;
        if (activeTechFilter !== 'all' && t.availability !== activeTechFilter) return false;
        if (searchQuery && !t.name.toLowerCase().includes(searchQuery) && !t.skills.join(',').toLowerCase().includes(searchQuery)) return false;
        return true;
    });

    filtered.forEach(t => {
        const isSelected = activeEntity && activeEntity.type === 'tech' && activeEntity.id === t.id;
        const card = document.createElement('div');
        card.className = `tech-card ${isSelected ? 'selected' : ''}`;
        card.onclick = () => selectEntity('tech', t.id);
        
        card.innerHTML = `
            <div class="tech-card-header">
                <span class="tech-name">${t.name}</span>
                <span class="status-badge ${t.availability.toLowerCase().replace(' ', '_')}">${t.availability}</span>
            </div>
            <div class="tech-card-body">
                <div class="tech-info-row">
                    <span>Territory:</span>
                    <strong style="color: ${dbState.territories[t.territory].color}">${t.territory}</strong>
                </div>
                <div class="tech-info-row">
                    <span>Active Jobs:</span>
                    <span>${t.assigned_job_ids.length} jobs</span>
                </div>
                <div class="skills-wrapper">
                    ${t.skills.map(s => `<span class="skill-tag">${s}</span>`).join('')}
                </div>
            </div>
        `;
        techList.appendChild(card);
    });
}

function renderJobs() {
    jobList.innerHTML = '';
    const filtered = dbState.jobs.filter(j => {
        if (activeJobFilter === 'Assigned' && j.status !== 'Assigned') return false;
        if (activeJobFilter === 'Unassigned' && j.status !== 'Unassigned') return false;
        if (activeJobFilter === 'High' && j.priority !== 'High') return false;
        if (searchQuery && !j.customer_name.toLowerCase().includes(searchQuery) && !j.id.toLowerCase().includes(searchQuery) && !j.required_skill.toLowerCase().includes(searchQuery)) return false;
        return true;
    });

    filtered.forEach(j => {
        const isSelected = activeEntity && activeEntity.type === 'job' && activeEntity.id === j.id;
        const card = document.createElement('div');
        card.className = `job-card ${isSelected ? 'selected' : ''}`;
        card.onclick = () => selectEntity('job', j.id);
        
        const assignedTech = dbState.technicians.find(t => t.id === j.assigned_technician_id);
        const techName = assignedTech ? assignedTech.name : 'None';
        
        card.innerHTML = `
            <div class="job-card-header">
                <span class="job-id">${j.id.toUpperCase()} - ${j.customer_name}</span>
                <span class="status-badge ${j.status.toLowerCase()}">${j.status}</span>
            </div>
            <div class="job-card-body">
                <div class="job-info-row">
                    <span>Assigned To:</span>
                    <span>${techName}</span>
                </div>
                <div class="job-info-row">
                    <span>Skill Needed:</span>
                    <span class="skill-tag">${j.required_skill}</span>
                </div>
                <div class="job-info-row">
                    <span>Time Window:</span>
                    <span>${j.time_window}</span>
                </div>
                <div style="margin-top: 4px; display: flex; justify-content: space-between; align-items: center;">
                    <span class="priority-badge ${j.priority.toLowerCase()}">${j.priority} Priority</span>
                </div>
            </div>
        `;
        jobList.appendChild(card);
    });
}

function renderApprovals() {
    approvalsList.innerHTML = '';
    const pending = dbState.approval_requests.filter(r => r.status === 'Pending');
    approvalsCountBadge.textContent = `${pending.length} Pending`;
    approvalsCountBadge.style.background = pending.length > 0 ? 'var(--color-danger)' : 'var(--color-muted)';

    if (pending.length === 0) {
        approvalsList.innerHTML = `<div class="message system" style="background:transparent; border:none; padding:10px 0;">No pending approval requests.</div>`;
        return;
    }

    pending.forEach(r => {
        const job = dbState.jobs.find(j => j.id === r.job_id);
        const sourceTech = dbState.technicians.find(t => t.id === r.source_technician_id);
        const targetTech = dbState.technicians.find(t => t.id === r.target_technician_id);
        
        const card = document.createElement('div');
        card.className = 'approval-card';
        card.innerHTML = `
            <div class="approval-card-header">
                <span class="approval-req-id">${r.request_id}</span>
                <span>Job: ${r.job_id.toUpperCase()}</span>
            </div>
            <div class="approval-card-body">
                <div>Reassign: <strong>${sourceTech ? sourceTech.name : 'Unassigned'}</strong> &rarr; <strong>${targetTech ? targetTech.name : 'Unknown'}</strong></div>
                <div style="font-style: italic; margin-top: 4px;">Reason: "${r.reason}"</div>
            </div>
            <div class="approval-card-actions">
                ${activeRole === 'Dispatch Manager' 
                    ? `<button class="btn-sm reject" onclick="openApprovalModal('${r.request_id}', 'reject')">Reject</button>
                       <button class="btn-sm approve" onclick="openApprovalModal('${r.request_id}', 'approve')">Approve</button>`
                    : `<span style="color:var(--text-muted); font-size:10px;"><i class="fa-regular fa-clock"></i> Manager Approval Required</span>`
                }
            </div>
        `;
        approvalsList.appendChild(card);
    });
}

function renderAuditLog() {
    auditLog.innerHTML = '';
    dbState.activity_log.slice().reverse().forEach(log => {
        const date = new Date(log.timestamp);
        const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        
        const item = document.createElement('div');
        item.className = 'audit-item';
        item.innerHTML = `
            [<span class="audit-time">${timeStr}</span>] 
            <span class="audit-user">${log.user}</span>: 
            <strong>${log.action}</strong> - ${log.details}
        `;
        auditLog.appendChild(item);
    });
}

function renderSeedPrompts() {
    seedPrompts.innerHTML = '';
    const prompts = SEED_PROMPTS[activeRole] || [];
    prompts.forEach(p => {
        const chip = document.createElement('div');
        chip.className = 'seed-prompt-chip';
        chip.textContent = p.label;
        chip.onclick = () => {
            chatInput.value = p.text;
            chatInput.focus();
        };
        seedPrompts.appendChild(chip);
    });
}

// Entity focus / details display
function selectEntity(type, id) {
    activeEntity = { type, id };
    
    // Highlight list selection
    if (type === 'tech') {
        switchLeftTab('techs');
        renderTechs();
        renderJobs(); // Redraw selection in jobs if any
    } else {
        switchLeftTab('jobs');
        renderJobs();
        renderTechs();
    }
    
    // Draw map highlights
    drawMap();
    
    // Load detail drawer
    const detailsBody = document.getElementById('entity-details-card');
    detailsBody.classList.remove('hidden');
    
    if (type === 'tech') {
        const t = dbState.technicians.find(x => x.id === id);
        document.getElementById('details-title').textContent = `Technician: ${t.name}`;
        
        // List assigned jobs
        const jobs = dbState.jobs.filter(j => t.assigned_job_ids.includes(j.id));
        const jobsListHtml = jobs.length > 0 
            ? jobs.map(j => `<div>${j.id.toUpperCase()}: ${j.customer_name} (${j.priority})</div>`).join('')
            : 'None';
            
        detailsContent.innerHTML = `
            <div class="details-row"><span class="details-label">ID:</span><span class="details-val">${t.id}</span></div>
            <div class="details-row"><span class="details-label">Zone:</span><span class="details-val">${t.territory}</span></div>
            <div class="details-row"><span class="details-label">Availability:</span><span class="details-val">${t.availability}</span></div>
            <div class="details-row"><span class="details-label">Skills:</span><span class="details-val">${t.skills.join(', ')}</span></div>
            <div style="margin-top: 8px;">
                <span class="details-label" style="font-weight:600; display:block; margin-bottom:4px;">Scheduled Jobs:</span>
                <div style="background:rgba(0,0,0,0.15); padding:8px; border-radius:4px; max-height:80px; overflow-y:auto;">
                    ${jobsListHtml}
                </div>
            </div>
        `;
    } else {
        const j = dbState.jobs.find(x => x.id === id);
        document.getElementById('details-title').textContent = `Job: ${j.id.toUpperCase()}`;
        
        const assignedTech = dbState.technicians.find(t => t.id === j.assigned_technician_id);
        const techName = assignedTech ? assignedTech.name : 'Unassigned';
        
        detailsContent.innerHTML = `
            <div class="details-row"><span class="details-label">Customer:</span><span class="details-val">${j.customer_name}</span></div>
            <div class="details-row"><span class="details-label">Priority:</span><span class="details-val">${j.priority}</span></div>
            <div class="details-row"><span class="details-label">Required Skill:</span><span class="details-val">${j.required_skill}</span></div>
            <div class="details-row"><span class="details-label">Window:</span><span class="details-val">${j.time_window}</span></div>
            <div class="details-row"><span class="details-label">Assigned Tech:</span><span class="details-val">${techName}</span></div>
            <div style="margin-top: 6px;">
                <span class="details-label">Notes:</span>
                <p style="background:rgba(0,0,0,0.15); padding:6px; border-radius:4px; margin-top:2px;">${j.notes}</p>
            </div>
        `;
    }
}

function closeDetails() {
    activeEntity = null;
    document.getElementById('entity-details-card').classList.add('hidden');
    drawMap();
}

function drawMap() {
    if (!dbState || !map) return;
    
    // Clear old layers
    mapLayers.forEach(layer => map.removeLayer(layer));
    mapLayers = [];
    
    // 1. Draw territories
    Object.keys(dbState.territories).forEach(key => {
        const territory = dbState.territories[key];
        const circle = L.circle(territory.center, {
            color: territory.color,
            fillColor: territory.color,
            fillOpacity: 0.05,
            radius: 1400,
            weight: 1.5,
            dashArray: '4,4'
        }).addTo(map);
        
        circle.bindTooltip(key.toUpperCase() + " ZONE", {
            permanent: true,
            direction: 'center',
            className: 'zone-tooltip'
        });
        mapLayers.push(circle);
    });

    // 2. Draw assignment routes (draw lines between technicians and their assigned jobs)
    dbState.jobs.forEach(j => {
        if (j.assigned_technician_id && j.status === 'Assigned') {
            const tech = dbState.technicians.find(t => t.id === j.assigned_technician_id);
            if (tech) {
                const tCenter = dbState.territories[tech.territory].center;
                const techIdx = parseInt(tech.id.replace('tech_', '')) || 1;
                const offsetLat = Math.sin(techIdx * 12) * 0.003;
                const offsetLng = Math.cos(techIdx * 12) * 0.003;
                const techPos = [tCenter[0] + offsetLat, tCenter[1] + offsetLng];
                const jobPos = [j.coordinates.lat, j.coordinates.lng];
                
                const isFocused = activeEntity && (
                    (activeEntity.type === 'tech' && activeEntity.id === tech.id) ||
                    (activeEntity.type === 'job' && activeEntity.id === j.id)
                );
                
                const line = L.polyline([techPos, jobPos], {
                    color: isFocused ? '#6366f1' : 'rgba(99, 102, 241, 0.15)',
                    weight: isFocused ? 3 : 1.5,
                    dashArray: isFocused ? '6,6' : '3,3'
                }).addTo(map);
                mapLayers.push(line);
            }
        }
    });

    // 3. Draw Job Markers
    dbState.jobs.forEach(j => {
        const isSelected = activeEntity && activeEntity.type === 'job' && activeEntity.id === j.id;
        
        let color = '#f59e0b'; // Amber (Unassigned)
        if (j.status === 'Assigned') color = '#10b981'; // Green
        if (j.status === 'In Progress') color = '#06b6d4'; // Cyan
        if (j.status === 'Completed') color = '#6b7280'; // Grey
        
        const priorityIcon = j.priority === 'High' ? '<span class="priority-bang">!</span>' : '';
        const markerHtml = `
            <div class="job-marker-pin ${isSelected ? 'selected' : ''}" style="--pin-color: ${color}">
                <div class="pin-dot"></div>
                ${priorityIcon}
            </div>
        `;
        
        const icon = L.divIcon({
            html: markerHtml,
            className: 'custom-leaflet-icon',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        });
        
        const marker = L.marker([j.coordinates.lat, j.coordinates.lng], { icon: icon })
            .addTo(map)
            .bindPopup(`
                <div class="map-popup">
                    <h4>Job: ${j.id.toUpperCase()}</h4>
                    <p><strong>Customer:</strong> ${j.customer_name}</p>
                    <p><strong>Status:</strong> <span class="popup-badge" style="background: ${color}20; color: ${color}">${j.status}</span></p>
                    <p><strong>Priority:</strong> ${j.priority}</p>
                    <button class="popup-action-btn" onclick="selectEntity('job', '${j.id}')">View Details</button>
                </div>
            `);
        
        if (isSelected && mapSelectedEntity !== j.id) {
            map.panTo([j.coordinates.lat, j.coordinates.lng]);
            mapSelectedEntity = j.id;
        }
        
        marker.on('click', () => {
            selectEntity('job', j.id);
        });
        
        mapLayers.push(marker);
    });

    // 4. Draw Technician Locations
    dbState.technicians.forEach(t => {
        if (t.role !== 'Technician') return;
        const tCenter = dbState.territories[t.territory].center;
        const techIdx = parseInt(t.id.replace('tech_', '')) || 1;
        const offsetLat = Math.sin(techIdx * 12) * 0.003;
        const offsetLng = Math.cos(techIdx * 12) * 0.003;
        const techPos = [tCenter[0] + offsetLat, tCenter[1] + offsetLng];
        
        const isSelected = activeEntity && activeEntity.type === 'tech' && activeEntity.id === t.id;
        
        let color = '#10b981'; // Green (Available)
        if (t.availability === 'On Job') color = '#6366f1'; // Blue/Indigo
        if (t.availability === 'Delayed') color = '#ef4444'; // Red
        if (t.availability === 'Offline') color = '#6b7280'; // Grey
        
        const initials = t.name.split(' ').map(n => n[0]).join('');
        const markerHtml = `
            <div class="tech-marker-pin ${isSelected ? 'selected' : ''}" style="--tech-color: ${color}">
                <div class="tech-initials">${initials}</div>
            </div>
        `;
        
        const icon = L.divIcon({
            html: markerHtml,
            className: 'custom-leaflet-icon',
            iconSize: [28, 28],
            iconAnchor: [14, 14]
        });
        
        const marker = L.marker(techPos, { icon: icon })
            .addTo(map)
            .bindPopup(`
                <div class="map-popup">
                    <h4>Tech: ${t.name}</h4>
                    <p><strong>Territory:</strong> ${t.territory}</p>
                    <p><strong>Availability:</strong> <span class="popup-badge" style="background: ${color}20; color: ${color}">${t.availability}</span></p>
                    <button class="popup-action-btn" onclick="selectEntity('tech', '${t.id}')">View Workload</button>
                </div>
            `);
        
        if (isSelected && mapSelectedEntity !== t.id) {
            map.panTo(techPos);
            mapSelectedEntity = t.id;
        }
        
        marker.on('click', () => {
            selectEntity('tech', t.id);
        });
        
        mapLayers.push(marker);
    });
}

// Chat Console Submission
function handleChatSubmit(e) {
    if (e.key === 'Enter') {
        submitMessage();
    }
}

async function submitMessage() {
    const text = chatInput.value.trim();
    if (!text) return;
    
    chatInput.value = '';
    addMessage('user', text);
    
    // Show typing state
    typingIndicator.classList.remove('hidden');
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    try {
        const sessionId = activeRole === 'Technician' ? `session_${activeTechId}` : 'session_manager';
        const headers = { 'Content-Type': 'application/json' };
        const customApiKey = localStorage.getItem('GEMINI_API_KEY');
        if (customApiKey) {
            headers['X-Gemini-API-Key'] = customApiKey;
        }

        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                message: text,
                role: activeRole,
                technician_id: activeTechId,
                session_id: sessionId,
                user_id: activeRole === 'Technician' ? `user_${activeTechId}` : 'user_manager'
            })
        });
        
        const data = await response.json();
        
        // Hide typing state
        typingIndicator.classList.add('hidden');
        
        if (data.error === 'API_KEY_INVALID') {
            addMessage('system', 'System warning: The Gemini API Key is invalid or not working.');
            openApiKeyModal(text);
            return;
        }

        if (data.error === 'CHAT_ERROR') {
            addMessage('system', 'Error running agent: ' + data.message);
            return;
        }

        addMessage('agent', data.response);
        
        // Refresh state in case agent tools changed data
        await fetchState();
        
    } catch (err) {
        typingIndicator.classList.add('hidden');
        addMessage('system', 'Error communicating with the Copilot server.');
        console.error(err);
    }
}

function addMessage(sender, text) {
    const msg = document.createElement('div');
    msg.className = `message ${sender}`;
    msg.innerHTML = `<div class="message-content">${text}</div>`;
    chatMessages.appendChild(msg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Modal approval queues
let currentReviewReqId = null;
let currentReviewAction = null;

function openApprovalModal(reqId, action) {
    currentReviewReqId = reqId;
    currentReviewAction = action;
    
    const modal = document.getElementById('approval-modal');
    const req = dbState.approval_requests.find(r => r.request_id === reqId);
    const job = dbState.jobs.find(j => j.id === req.job_id);
    const sourceTech = dbState.technicians.find(t => t.id === req.source_technician_id);
    const targetTech = dbState.technicians.find(t => t.id === req.target_technician_id);
    
    document.getElementById('modal-title').textContent = `${action === 'approve' ? 'Approve' : 'Reject'} Reassignment Request`;
    document.getElementById('modal-manager-comments').value = '';
    
    document.getElementById('modal-body-content').innerHTML = `
        <div class="details-row"><span class="details-label">Request ID:</span><span class="details-val">${req.request_id}</span></div>
        <div class="details-row"><span class="details-label">Service Job:</span><span class="details-val">${req.job_id.toUpperCase()} - ${job.customer_name}</span></div>
        <div class="details-row"><span class="details-label">Current Tech:</span><span class="details-val">${sourceTech ? sourceTech.name : 'None'}</span></div>
        <div class="details-row"><span class="details-label">Target Tech:</span><span class="details-val">${targetTech ? targetTech.name : 'Unknown'}</span></div>
        <div style="margin-top:8px;">
            <span class="details-label" style="font-weight:600;">Requester Reason:</span>
            <p style="background:rgba(0,0,0,0.15); padding:6px; border-radius:4px; margin-top:2px; font-style:italic;">"${req.reason}"</p>
        </div>
    `;
    
    // Configure buttons
    const btnApprove = document.getElementById('modal-btn-approve');
    const btnReject = document.getElementById('modal-btn-reject');
    
    if (action === 'approve') {
        btnApprove.classList.remove('hidden');
        btnReject.classList.add('hidden');
        btnApprove.onclick = handleApprovalSubmit;
    } else {
        btnApprove.classList.add('hidden');
        btnReject.classList.remove('hidden');
        btnReject.onclick = handleApprovalSubmit;
    }
    
    modal.classList.remove('hidden');
}

function closeModal() {
    document.getElementById('approval-modal').classList.add('hidden');
    currentReviewReqId = null;
    currentReviewAction = null;
}

async function handleApprovalSubmit() {
    const comments = document.getElementById('modal-manager-comments').value.trim();
    const action = currentReviewAction;
    const reqId = currentReviewReqId;
    const endpoint = action === 'approve' ? '/api/approve_direct' : '/api/reject_direct';
    
    try {
        closeModal();
        addMessage('system', `${action === 'approve' ? 'Approving' : 'Rejecting'} request ${reqId}...`);
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                request_id: reqId,
                manager_comments: comments
            })
        });
        
        const result = await response.json();
        if (result.status === 'success') {
            addMessage('system', result.message);
        } else {
            addMessage('system', 'Error: ' + result.message);
        }
        
        await fetchState();
    } catch (err) {
        console.error(err);
        addMessage('system', 'Failed to submit manager approval action.');
    }
}

// Gemini API Key Management
let pendingMessageToRetry = null;

function openApiKeyModal(retryText = null) {
    pendingMessageToRetry = retryText;
    const modal = document.getElementById('api-key-modal');
    const input = document.getElementById('modal-gemini-key-input');
    
    // Pre-fill input if there's already a key in localStorage
    const existingKey = localStorage.getItem('GEMINI_API_KEY');
    if (existingKey) {
        input.value = existingKey;
    } else {
        input.value = '';
    }
    
    modal.classList.remove('hidden');
    input.focus();
}

function closeApiKeyModal() {
    document.getElementById('api-key-modal').classList.add('hidden');
    pendingMessageToRetry = null;
}

function saveApiKey() {
    const input = document.getElementById('modal-gemini-key-input');
    const key = input.value.trim();
    
    if (key) {
        localStorage.setItem('GEMINI_API_KEY', key);
        addMessage('system', 'Gemini API Key saved to browser cache.');
    } else {
        localStorage.removeItem('GEMINI_API_KEY');
        addMessage('system', 'Custom Gemini API Key removed. Using default.');
    }
    
    closeApiKeyModal();
    updateApiKeyButtonState();
    
    // Retry the pending message if there was one
    if (pendingMessageToRetry) {
        const textToRetry = pendingMessageToRetry;
        pendingMessageToRetry = null;
        // Put the message back in the chat input and submit
        chatInput.value = textToRetry;
        submitMessage();
    }
}

function updateApiKeyButtonState() {
    const btn = document.getElementById('btn-api-key');
    if (!btn) return;
    const key = localStorage.getItem('GEMINI_API_KEY');
    if (key) {
        btn.classList.add('key-active');
        btn.title = "Gemini API Key Configured (Custom)";
    } else {
        btn.classList.remove('key-active');
        btn.title = "Configure Gemini API Key";
    }
}
