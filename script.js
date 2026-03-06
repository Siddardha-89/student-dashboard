const API_BASE = "http://localhost:8001";

// Notification Helper
function showNotification(msg) {
    const area = document.getElementById('notificationArea');
    if (!area) return;
    const toast = document.createElement('div');
    toast.className = 'notification';
    toast.innerText = msg;
    area.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// Auth Logic
async function handleLogin(e) {
    e.preventDefault();
    const btn = e.target.querySelector('button');
    btn.innerText = "Authenticating...";

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, role: 'admin' })
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('token', data.access_token);
            const decoded = JSON.parse(atob(data.access_token.split('.')[1]));
            localStorage.setItem('role', decoded.role);
            localStorage.setItem('username', decoded.sub);

            showNotification(`Welcome back, ${decoded.sub}`);
            setTimeout(() => {
                if (decoded.role === 'admin') window.location.href = 'admin.html';
                else window.location.href = 'dashboard.html';
            }, 500);
        } else {
            showNotification("Access Denied: Invalid Credentials");
            btn.innerText = "Sign In to Portal";
        }
    } catch (err) {
        showNotification("Critical: Backend Server Offline");
        btn.innerText = "Sign In to Portal";
    }
}

function checkAuth(requiredRole = null) {
    const token = localStorage.getItem('token');
    const role = localStorage.getItem('role');

    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    if (requiredRole && role !== requiredRole) {
        window.location.href = 'login.html';
    }
}

function logout() {
    localStorage.clear();
    window.location.href = 'login.html';
}

// Student Dashboard Logic
async function loadStudentDashboard() {
    const username = localStorage.getItem('username') || "Student";
    document.getElementById('welcomeText').innerHTML = `Welcome, <span class="gold-gradient-text">${username}</span>`;

    try {
        const res = await fetch(`${API_BASE}/students`);
        const students = await res.json();
        const me = students.find(s => s.name.toLowerCase() === username.toLowerCase()) || students[0];

        if (me) {
            updateDashboardUI(me);
            initCharts(me);
            loadSuggestions(me.marks);
        }
    } catch (e) {
        // Fallback for demo
        const demoData = {
            name: username,
            marks: { "Maths": 88, "Physics": 75, "Coding": 92, "English": 85 },
            attendance: 88,
            prev_gpa: 8.4,
            coding_score: 9.0,
            communication_score: 8.0,
            projects_count: 3
        };
        updateDashboardUI(demoData);
        initCharts(demoData);
        loadSuggestions(demoData.marks);
    }
}

async function updateDashboardUI(data) {
    // Update GPA
    const gpaEl = document.querySelector('.score-value');
    if (gpaEl) gpaEl.innerText = data.prev_gpa.toFixed(1);

    const bar = document.getElementById('gpaProgressBar');
    if (bar) bar.style.width = `${(data.prev_gpa * 10)}%`;

    // Update Risk
    const riskEl = document.getElementById('riskLevel');
    const probEl = document.getElementById('riskProb');

    try {
        const riskRes = await fetch(`${API_BASE}/predict-risk`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ gpa: data.prev_gpa, attendance: data.attendance })
        });
        const riskData = await riskRes.json();
        if (riskEl) {
            riskEl.innerText = riskData.risk.toUpperCase();
            riskEl.className = `status-badge status-${riskData.color}`;
        }
        if (probEl) probEl.innerText = `${riskData.probability}%`;
    } catch (err) {
        if (riskEl) riskEl.innerText = "LOW RISK";
        if (probEl) probEl.innerText = "12%";
    }

    // Update Placement
    const placeEl = document.getElementById('placementChance');
    try {
        const placeRes = await fetch(`${API_BASE}/predict-placement`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                gpa: data.prev_gpa,
                coding_score: data.coding_score || 8,
                communication_score: data.communication_score || 8,
                projects_count: data.projects_count || 2
            })
        });
        const placeData = await placeRes.json();
        if (placeEl) placeEl.innerText = `${placeData.placement_probability}%`;
    } catch (err) {
        if (placeEl) placeEl.innerText = "85%";
    }
}

function initCharts(data) {
    const marksCtx = document.getElementById('marksChart');
    if (marksCtx) {
        new Chart(marksCtx, {
            type: 'bar',
            data: {
                labels: Object.keys(data.marks),
                datasets: [{
                    label: 'Score',
                    data: Object.values(data.marks),
                    backgroundColor: '#D4AF37',
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#B0B0B0' } },
                    x: { ticks: { color: '#B0B0B0' } }
                }
            }
        });
    }

    const progCtx = document.getElementById('progressChart');
    if (progCtx) {
        new Chart(progCtx, {
            type: 'line',
            data: {
                labels: ['SEM 1', 'SEM 2', 'SEM 3', 'CURRENT'],
                datasets: [{
                    data: [7.2, 7.8, 8.1, data.prev_gpa],
                    borderColor: '#D4AF37',
                    tension: 0.4,
                    fill: false
                }]
            },
            options: {
                plugins: { legend: { display: false } },
                scales: {
                    y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#B0B0B0' } },
                    x: { ticks: { color: '#B0B0B0' } }
                }
            }
        });
    }

    const distCtx = document.getElementById('distributionChart');
    if (distCtx) {
        new Chart(distCtx, {
            type: 'doughnut',
            data: {
                labels: ['Coding', 'Communication', 'Aptitude', 'Soft Skills'],
                datasets: [{
                    data: [data.coding_score * 10, data.communication_score * 10, 85, 78],
                    backgroundColor: ['#D4AF37', '#C5A028', '#F9E29C', '#B0B0B0'],
                    borderWidth: 0,
                    hoverOffset: 15
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#B0B0B0', padding: 25, font: { family: 'Inter', size: 14, weight: 'bold' } }
                    }
                },
                cutout: '60%'
            }
        });
    }
}

function loadSuggestions(marks) {
    const list = document.getElementById('suggestionsList');
    if (!list) return;
    list.innerHTML = '';
    const items = Object.entries(marks).filter(([s, m]) => m < 85);

    if (items.length === 0) {
        list.innerHTML = `<div class="glass-card p-2 small-text">Elite academic standing maintained. Recommendation: Focus on Advanced Research & Global Certifications.</div>`;
    } else {
        items.forEach(([sub, score]) => {
            list.innerHTML += `
                <div class="glass-card" style="padding: 1rem; border-left: 3px solid var(--primary-gold);">
                    <div class="font-bold m-b-1">Improve ${sub}</div>
                    <div class="gray-text">Current Score: ${score}%</div>
                    <div class="m-t-1"><i class="fas fa-lightbulb"></i> Recommended: ${sub} Mastery Course</div>
                </div>
            `;
        });
    }
}

// Admin Dashboard Initialization
async function initializeDashboard() {
    checkAuth('admin');
    await loadAdminDashboard();
}

// Admin Dashboard Logic
async function loadAdminDashboard() {
    try {
        const res = await fetch(`${API_BASE}/students`);
        const students = await res.json();

        students.sort((a, b) => b.prev_gpa - a.prev_gpa);

        const tbody = document.getElementById('studentTableBody');
        const countEl = document.getElementById('studentCount');
        const emptyEl = document.getElementById('noDataMessage');

        if (tbody) tbody.innerHTML = '';
        if (countEl) countEl.innerText = students.length;

        if (students.length === 0) {
            if (emptyEl) emptyEl.style.display = 'block';
            return;
        }

        if (emptyEl) emptyEl.style.display = 'none';

        students.forEach((s, index) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><span class="rank-badge">#${index + 1}</span> <b>${s.roll_no}</b></td>
                <td>${s.name}</td>
                <td class="gray-text">${s.department}</td>
                <td class="font-bold gold-gradient-text">${s.prev_gpa.toFixed(2)}</td>
                <td>${s.attendance}%</td>
                <td>
                    <div class="flex-row gap-1">
                        <button type="button" onclick="viewReport('${s.roll_no}')" class="btn-outline-gold" style="padding: 5px 12px; font-size: 0.7rem;">ANALYZE</button>
                        <button type="button" onclick="deleteStudent('${s.roll_no}')" class="btn-outline-gold" style="padding: 5px 12px; font-size: 0.7rem; border-color: var(--danger-red); color: var(--danger-red);">REMOVE</button>
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (err) {
        showNotification("Database Synchronization Failed");
    }
}

function viewReport(roll) {
    localStorage.setItem('targetRoll', roll);
    window.location.href = 'report.html';
}

async function deleteStudent(roll) {
    if (confirm(`Permanent removal of record ${roll}?`)) {
        const res = await fetch(`${API_BASE}/student/${roll}`, { method: 'DELETE' });
        if (res.ok) {
            showNotification("Record Purged Successfully");
            loadAdminDashboard();
        }
    }
}

function showAddModal() {
    const modal = document.getElementById('studentModal');
    modal.style.display = 'flex';
    setTimeout(() => modal.classList.add('active'), 10);
}

function hideAddModal() {
    const modal = document.getElementById('studentModal');
    modal.classList.remove('active');
    setTimeout(() => modal.style.display = 'none', 500); // Wait for transition
}

async function handleAddStudent(e) {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    btn.innerText = "Encrypting & Storing...";

    const student = {
        name: document.getElementById('sName').value,
        roll_no: document.getElementById('sRoll').value,
        department: document.getElementById('sDept').value,
        marks: { "Mathematics": 85, "Physics": 80, "Coding": 90 },
        attendance: parseFloat(document.getElementById('sAttendance').value),
        internal_marks: 42,
        prev_gpa: parseFloat(document.getElementById('sGPA').value),
        backlog_history: 0,
        coding_score: parseFloat(document.getElementById('sCoding').value),
        communication_score: parseFloat(document.getElementById('sComm').value),
        projects_count: 3
    };

    try {
        const res = await fetch(`${API_BASE}/add-student`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(student)
        });

        if (res.ok) {
            showNotification("Student Enrollment Completed");
            hideAddModal();
            loadAdminDashboard();
        } else {
            showNotification("Error: Roll No already exists");
        }
    } catch (err) {
        showNotification("Server Rejected Operation");
    } finally {
        btn.innerText = "Commit Record";
    }
}

// Report Logic
async function loadReport() {
    const roll = localStorage.getItem('targetRoll') || 'DEMO-01';
    document.getElementById('reportDate').innerText = new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });

    try {
        const res = await fetch(`${API_BASE}/student/${roll}`);
        if (res.ok) {
            const s = await res.json();
            document.getElementById('reportName').innerText = s.name.toUpperCase();
            document.getElementById('reportDeptRoll').innerText = `${s.department} | ID: ${s.roll_no}`;
            document.getElementById('repGPA').innerText = `${s.prev_gpa.toFixed(2)}/10`;
            document.getElementById('repAtt').innerText = `${s.attendance}%`;

            const riskRes = await fetch(`${API_BASE}/predict-risk`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ gpa: s.prev_gpa, attendance: s.attendance })
            });
            const risk = await riskRes.json();
            const rEl = document.getElementById('repRisk');
            rEl.innerText = risk.risk.toUpperCase();
            rEl.style.color = risk.color === 'green' ? '#00FF7F' : (risk.color === 'yellow' ? '#FFD700' : '#FF4D4D');

            const placeRes = await fetch(`${API_BASE}/predict-placement`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ gpa: s.prev_gpa, coding_score: s.coding_score, communication_score: s.communication_score, projects_count: s.projects_count })
            });
            const place = await placeRes.json();
            document.getElementById('repPlace').innerText = `${place.placement_probability}%`;
            document.getElementById('repTier').innerText = place.eligible_tier;
            document.getElementById('repSalary').innerText = place.expected_salary;
        }
    } catch (e) {
        showNotification("Running in Simulation Mode");
    }
}

// PDF Export Logic
function downloadPDF() {
    const element = document.getElementById("pdf-content");
    const actionButtons = document.getElementById("action-buttons");
    
    // Temporarily hide buttons
    if (actionButtons) actionButtons.style.display = "none";
    
    // Add temporary class to adjust styling for PDF
    element.classList.add("pdf-exporting");

    const studentName = document.getElementById("reportName").innerText || "Student";
    
    const opt = {
        margin:       0.5,
        filename:     `Elite-Report-${studentName}.pdf`,
        image:        { type: "jpeg", quality: 1.0 },
        html2canvas:  { 
            scale: 2, 
            useCORS: true, 
            backgroundColor: "#0A0A0A", // Match the dark background
            windowWidth: 1200
        },
        jsPDF:        { unit: "in", format: "a4", orientation: "portrait" }
    };

    html2pdf().set(opt).from(element).save().then(() => {
        // Restore buttons and styles
        if (actionButtons) actionButtons.style.display = "flex";
        element.classList.remove("pdf-exporting");
        showNotification("PDF Export Completed Successfully");
    }).catch(err => {
        if (actionButtons) actionButtons.style.display = "flex";
        element.classList.remove("pdf-exporting");
        showNotification("Error Exporting PDF");
    });
}

