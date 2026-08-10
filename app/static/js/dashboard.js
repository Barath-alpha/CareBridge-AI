// dashboard.js

document.addEventListener('DOMContentLoaded', () => {

    // ---- Display Current Date ----
    const dateEl = document.getElementById('currentDate');
    if (dateEl) {
        const now = new Date();
        dateEl.textContent = now.toLocaleDateString('en-US', {
            weekday: 'short', year: 'numeric', month: 'short', day: 'numeric'
        });
    }

    // ---- Load User Info from localStorage ----
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    if (user.full_name) {
        const nameEl = document.getElementById('userName');
        if (nameEl) nameEl.textContent = user.full_name.split(' ')[0];
        const avatarEl = document.getElementById('userAvatar');
        if (avatarEl) avatarEl.querySelector('span').textContent = user.full_name.charAt(0).toUpperCase();
    }

    // ---- Sidebar Toggle ----
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const mobileToggle = document.getElementById('mobileToggle');
    const mainContent = document.getElementById('mainContent');

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('expanded');
        });
    }

    if (mobileToggle) {
        mobileToggle.addEventListener('click', () => {
            sidebar.classList.toggle('mobile-open');
        });
    }

    // ---- Notification Drawer ----
    const notifBtn = document.getElementById('notifBtn');
    const notifDrawer = document.getElementById('notifDrawer');
    const drawerOverlay = document.getElementById('drawerOverlay');

    if (notifBtn) {
        notifBtn.addEventListener('click', () => {
            notifDrawer.classList.add('open');
            drawerOverlay.classList.add('active');
        });
    }

    if (drawerOverlay) {
        drawerOverlay.addEventListener('click', () => {
            notifDrawer.classList.remove('open');
            drawerOverlay.classList.remove('active');
        });
    }

    // ---- Animate Recovery Score Ring ----
    const ringFill = document.getElementById('ringFill');
    const scoreNum = document.getElementById('scoreNum');
    if (ringFill) {
        const score = parseInt(scoreNum.textContent);
        const circumference = 2 * Math.PI * 52; // r=52
        const offset = circumference - (score / 100) * circumference;
        setTimeout(() => {
            ringFill.style.strokeDasharray = circumference;
            ringFill.style.strokeDashoffset = offset;
        }, 300);
    }

    // ---- Pain Scale Selection ----
    const painBtns = document.querySelectorAll('.pain-btn');
    painBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            painBtns.forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
        });
    });

    // ---- Mood Selection ----
    const moodBtns = document.querySelectorAll('.mood-btn');
    moodBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            moodBtns.forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
        });
    });

    // ---- Submit Check-In ----
    const submitCheckin = document.getElementById('submitCheckin');
    if (submitCheckin) {
        submitCheckin.addEventListener('click', () => {
            const selectedPain = document.querySelector('.pain-btn.selected');
            const selectedMood = document.querySelector('.mood-btn.selected');
            if (!selectedPain || !selectedMood) {
                alert('Please select your pain level and mood before submitting.');
                return;
            }
            submitCheckin.innerHTML = '<i class="fa-solid fa-check"></i> Submitted!';
            submitCheckin.style.background = '#16a34a';
            setTimeout(() => {
                submitCheckin.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Submit Check-In';
                submitCheckin.style.background = '';
            }, 2500);
        });
    }

    // ---- Quick Chat Send ----
    const quickChatInput = document.getElementById('quickChatInput');
    const quickChatSend = document.getElementById('quickChatSend');
    const quickChatResponse = document.getElementById('quickChatResponse');
    const aiTyping = document.getElementById('aiTyping');
    const aiResponseText = document.getElementById('aiResponseText');

    const sendMessage = async (message) => {
        if (!message.trim()) return;
        quickChatResponse.style.display = 'block';
        aiTyping.style.display = 'flex';
        aiResponseText.textContent = '';

        try {
            const res = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`
                },
                body: JSON.stringify({ message })
            });
            const data = await res.json();
            aiTyping.style.display = 'none';
            aiResponseText.textContent = data.response || data.error || 'Unable to get a response.';
        } catch (err) {
            aiTyping.style.display = 'none';
            aiResponseText.textContent = 'Error communicating with AI. Please try again.';
        }
    };

    if (quickChatSend) {
        quickChatSend.addEventListener('click', () => {
            sendMessage(quickChatInput.value);
            quickChatInput.value = '';
        });
    }

    if (quickChatInput) {
        quickChatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage(quickChatInput.value);
                quickChatInput.value = '';
            }
        });
    }

    // ---- AI Analyze Discharge Summary ----
    const analyzeBtn = document.getElementById('analyzeBtn');
    const analysisResult = document.getElementById('analysisResult');
    const analysisContent = document.getElementById('analysisContent');

    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', async () => {
            const text = document.getElementById('dischargeText').value.trim();
            if (!text) {
                alert('Please paste your discharge summary text first.');
                return;
            }
            analyzeBtn.innerHTML = '<div class="btn-spinner"></div> Analyzing...';
            analyzeBtn.disabled = true;

            try {
                const res = await fetch('/api/ai/analyze-discharge', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text })
                });
                const data = await res.json();

                if (data.success) {
                    const d = data.data;
                    let html = '<div class="analysis-data">';
                    if (d.diagnosis) html += `<div class="analysis-row"><strong>Diagnosis:</strong> <span>${d.diagnosis}</span></div>`;
                    if (d.medications && d.medications.length > 0) {
                        html += `<div class="analysis-row"><strong>Medications:</strong><ul>`;
                        d.medications.forEach(m => {
                            html += `<li><b>${m.name}</b> – ${m.dosage}, ${m.frequency} (${m.instructions})</li>`;
                        });
                        html += '</ul></div>';
                    }
                    if (d.follow_up_appointments && d.follow_up_appointments.length > 0) {
                        html += `<div class="analysis-row"><strong>Follow-ups:</strong><ul>`;
                        d.follow_up_appointments.forEach(a => {
                            html += `<li>${a.doctor} – ${a.specialty} on ${a.date}</li>`;
                        });
                        html += '</ul></div>';
                    }
                    if (d.dietary_recommendations && d.dietary_recommendations.length > 0) {
                        html += `<div class="analysis-row"><strong>Diet:</strong> ${d.dietary_recommendations.join(', ')}</div>`;
                    }
                    if (d.warning_signs && d.warning_signs.length > 0) {
                        html += `<div class="analysis-row warning-signs"><strong>⚠️ Warning Signs:</strong><ul>`;
                        d.warning_signs.forEach(w => { html += `<li>${w}</li>`; });
                        html += '</ul></div>';
                    }
                    if (d.raw) {
                        html += `<div class="analysis-row"><strong>Analysis:</strong><p>${d.raw}</p></div>`;
                    }
                    html += '</div>';
                    analysisContent.innerHTML = html;
                } else {
                    analysisContent.innerHTML = `<p style="color:#dc2626;">${data.error || 'Analysis failed. Please try again.'}</p>`;
                }
                analysisResult.style.display = 'block';
            } catch (err) {
                analysisContent.innerHTML = '<p style="color:#dc2626;">Error communicating with AI.</p>';
                analysisResult.style.display = 'block';
            }

            analyzeBtn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Analyze with AI';
            analyzeBtn.disabled = false;
        });
    }

    // ---- Drag & Drop Upload ----
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    if (uploadArea) {
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });
        uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('drag-over'));
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            const file = e.dataTransfer.files[0];
            if (file) handleFileUpload(file);
        });
    }

    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) handleFileUpload(file);
        });
    }

    function handleFileUpload(file) {
        if (uploadArea) {
            uploadArea.innerHTML = `
                <div class="upload-icon" style="color:#16a34a;"><i class="fa-solid fa-circle-check"></i></div>
                <h4>${file.name}</h4>
                <p>${(file.size / 1024).toFixed(1)} KB uploaded</p>
            `;
        }
    }

    // ---- Chart.js: Recovery Trend ----
    const recCtx = document.getElementById('recoveryChart')?.getContext('2d');
    if (recCtx) {
        const weekData = {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Recovery Score',
                data: [62, 65, 68, 70, 74, 76, 78],
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37,99,235,0.08)',
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#2563eb',
                pointRadius: 5,
            }, {
                label: 'Medication Adherence',
                data: [80, 85, 88, 90, 92, 91, 92],
                borderColor: '#10b981',
                backgroundColor: 'rgba(16,185,129,0.06)',
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#10b981',
                pointRadius: 5,
            }]
        };

        const monthData = {
            labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            datasets: [{
                label: 'Recovery Score',
                data: [55, 64, 72, 78],
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37,99,235,0.08)',
                fill: true, tension: 0.4,
            }, {
                label: 'Medication Adherence',
                data: [78, 84, 90, 92],
                borderColor: '#10b981',
                backgroundColor: 'rgba(16,185,129,0.06)',
                fill: true, tension: 0.4,
            }]
        };

        const recoveryChart = new Chart(recCtx, {
            type: 'line',
            data: weekData,
            options: {
                responsive: true,
                plugins: { legend: { display: true, position: 'top' } },
                scales: {
                    y: { beginAtZero: false, min: 40, max: 100, grid: { color: 'rgba(0,0,0,0.04)' } },
                    x: { grid: { display: false } }
                }
            }
        });

        window.filterChart = (period, btn) => {
            document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            recoveryChart.data = period === 'week' ? weekData : monthData;
            recoveryChart.update();
        };
    }

    // ---- Chart.js: Medication Donut ----
    const medCtx = document.getElementById('medChart')?.getContext('2d');
    if (medCtx) {
        new Chart(medCtx, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [92, 8],
                    backgroundColor: ['#22c55e', '#ef4444'],
                    borderWidth: 0,
                }]
            },
            options: {
                cutout: '75%',
                plugins: { legend: { display: false } },
                responsive: true,
            }
        });
    }

    // ---- Chart.js: Vitals Sparkline ----
    const vitalCtx = document.getElementById('vitalChart')?.getContext('2d');
    if (vitalCtx) {
        new Chart(vitalCtx, {
            type: 'line',
            data: {
                labels: ['Day 1', 'Day 3', 'Day 5', 'Day 7', 'Day 10', 'Today'],
                datasets: [{
                    label: 'BP Systolic',
                    data: [135, 132, 128, 125, 122, 120],
                    borderColor: '#ef4444',
                    tension: 0.4,
                    pointRadius: 3,
                    borderWidth: 2,
                }]
            },
            options: {
                plugins: { legend: { display: false } },
                scales: { x: { display: false }, y: { display: false } }
            }
        });
    }

    // ---- Chart.js: Mood Trend ----
    const moodCtx = document.getElementById('moodChart')?.getContext('2d');
    if (moodCtx) {
        new Chart(moodCtx, {
            type: 'bar',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Mood Score',
                    data: [3, 4, 3, 5, 4, 4, 5],
                    backgroundColor: [
                        'rgba(239,68,68,0.6)',
                        'rgba(245,158,11,0.6)',
                        'rgba(239,68,68,0.6)',
                        'rgba(34,197,94,0.6)',
                        'rgba(34,197,94,0.6)',
                        'rgba(34,197,94,0.6)',
                        'rgba(37,99,235,0.6)',
                    ],
                    borderRadius: 6,
                }]
            },
            options: {
                plugins: { legend: { display: false } },
                scales: {
                    y: { min: 0, max: 5, ticks: { stepSize: 1 }, grid: { color: 'rgba(0,0,0,0.04)' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }
});

// ---- Quick Msg from Suggestion Chips ----
function sendQuickMsg(msg) {
    const input = document.getElementById('quickChatInput');
    if (input) {
        input.value = msg;
        document.getElementById('quickChatSend')?.click();
    }
}

// ---- Close Analysis ----
function closeAnalysis() {
    document.getElementById('analysisResult').style.display = 'none';
}
