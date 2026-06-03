const API_BASE = window.location.origin;

// Utility Functions
function logPortal(msg, type='info') {
    const logs = document.getElementById('portal-logs');
    const entry = document.createElement('div');
    entry.className = `log-entry ${type === 'success' ? 'log-success' : type === 'error' ? 'log-error' : ''}`;
    entry.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
    logs.prepend(entry);
}

// Fetch endpoints
async function fetchFixture(name) {
    try {
        const res = await fetch(`${API_BASE}/fixtures/${name}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    } catch (e) {
        logPortal(`Error loading fixture ${name}: ${e.message}`, 'error');
        return null;
    }
}

async function runPipeline(candidateType) {
    const cand = await fetchFixture(`candidate_${candidateType}`);
    const role = await fetchFixture("role_backend_senior");
    
    if (!cand || !role) return;

    // Use a random ID so we can submit the same person multiple times to see the queue grow
    const mockId = `cand-${Math.floor(Math.random() * 100000)}`;
    cand.id = mockId;
    // Prefix name to identify them
    cand.name = `${cand.name.split(' ')[0]} #${mockId.split('-')[1]}`;

    logPortal(`Pushing: ${cand.name} (${candidateType})`);
    
    try {
        const res = await fetch(`${API_BASE}/pipeline/run`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                candidates: [cand],
                role: role,
                webhook_url: "https://httpbin.org/post" // Mock target
            })
        });
        const data = await res.json();
        logPortal(`Response: ${data.status}`, 'success');
        refreshQueue();
    } catch (e) {
        logPortal(`Pipeline Error: ${e.message}`, 'error');
    }
}

async function finalizeBattle() {
    const role = await fetchFixture("role_backend_senior");
    if (!role) return;

    logPortal("Triggering Level 2 Battle on approved candidates...");
    try {
        const res = await fetch(`${API_BASE}/pipeline/finalize_battle`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(role)
        });
        
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail.message || err.detail || "Battle Failed");
        }
        
        const data = await res.json();
        logPortal(`Battle Complete. Evaluated ${data.total_evaluated} total candidates.`, 'success');
        renderLeaderboard(data.candidates);
        refreshQueue(); // Clear queue out locally
    } catch (e) {
        logPortal(`Battle Error: ${e.message}`, 'error');
    }
}

async function refreshQueue() {
    try {
        const res = await fetch(`${API_BASE}/supervisor/queue`);
        const queue = await res.json();
        renderQueue(queue);
    } catch (e) {
        console.error("Failed to fetch queue", e);
    }
}

async function makeDecision(candidateId, approved) {
    logPortal(`${approved ? 'Approving' : 'Rejecting'} candidate: ${candidateId}...`);
    try {
        await fetch(`${API_BASE}/supervisor/decision`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ candidate_id: candidateId, approved: approved })
        });
        refreshQueue();
        logPortal(`Decision recorded. Webhook fired.`, 'success');
    } catch (e) {
        console.error("Decision failed", e);
    }
}

async function resetPipeline() {
    try {
        await fetch(`${API_BASE}/pipeline/reset`, { method: "POST" });
        logPortal("Pipeline and Database Reset.", 'success');
        document.getElementById('leaderboard-container').innerHTML = '<div class="empty-state">No results yet</div>';
        refreshQueue();
    } catch (e) {
        logPortal("Reset Failed.", 'error');
    }
}

// Rendering
function renderQueue(queue) {
    const container = document.getElementById('queue-container');
    if (queue.length === 0) {
        container.innerHTML = '<div class="empty-state">Queue is empty</div>';
        return;
    }
    
    container.innerHTML = '';
    queue.forEach(item => {
        const c = item.candidate;
        const div = document.createElement('div');
        div.className = 'queue-item';
        div.innerHTML = `
            <div class="queue-item-header">
                <span class="queue-name">${c.name}</span>
                <span class="queue-role">Stream A</span>
            </div>
            <p style="font-size: 0.8rem; color: var(--text-muted)">
                ${c.github ? c.github.repos.length + " Repos" : "No GitHub"} | 
                CTC: ${c.current_ctc || 'N/A'} LPA
            </p>
            <div class="queue-actions">
                <button class="btn btn-success" onclick="makeDecision('${c.id}', true)">Approve</button>
                <button class="btn btn-danger" onclick="makeDecision('${c.id}', false)">Reject</button>
            </div>
        `;
        container.appendChild(div);
    });
}

function renderLeaderboard(candidates) {
    const container = document.getElementById('leaderboard-container');
    if (candidates.length === 0) {
        container.innerHTML = '<div class="empty-state">No results yet</div>';
        return;
    }
    
    container.innerHTML = '';
    candidates.forEach(c => {
        const div = document.createElement('div');
        div.className = 'ranked-item';
        div.innerHTML = `
            <div class="ranked-header">
                <div class="rank-badge">#${c.rank}</div>
                <div class="queue-name">${c.verdict.candidate_id}</div>
                <div class="ranked-score">${c.verdict.overall.toFixed(1)}</div>
            </div>
            <div style="margin-bottom: 0.5rem">
                <span class="verdict-badge verdict-${c.verdict.verdict}">${c.verdict.verdict.replace('_', ' ')}</span>
            </div>
            <p style="font-size: 0.8rem; color: var(--text-muted)">
                ${c.verdict.human_review_notes || c.verdict.dimensions.job_fit.rationale || 'Failed early in routing stage.'}
            </p>
        `;
        container.appendChild(div);
    });
}

// Event Listeners
document.getElementById('btn-reset').addEventListener('click', resetPipeline);
document.getElementById('btn-send-promising').addEventListener('click', () => runPipeline('promising'));
document.getElementById('btn-send-polished').addEventListener('click', () => runPipeline('polished'));
document.getElementById('btn-finalize').addEventListener('click', finalizeBattle);

// Init
logPortal("UI initialized and ready.", "success");
refreshQueue();
setInterval(refreshQueue, 2000); // Auto-refresh queue for demo effect
