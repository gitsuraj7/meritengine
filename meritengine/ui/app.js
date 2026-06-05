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

    logPortal("Initiating multi-agent consensus alignment evaluation...");
    try {
        const res = await fetch(`${API_BASE}/pipeline/finalize_battle`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(role)
        });
        
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail.message || err.detail || "Evaluation Failed");
        }
        
        const data = await res.json();
        logPortal(`Evaluation Complete. Processed ${data.total_evaluated} candidate files.`, 'success');
        renderLeaderboard(data.candidates);
        refreshQueue(); // Clear queue out locally
    } catch (e) {
        logPortal(`Evaluation Error: ${e.message}`, 'error');
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
window.toggleDetails = function(el) {
    const details = el.querySelector('.details-section');
    if (details) {
        details.classList.toggle('hidden');
    }
}

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
        div.onclick = (e) => {
            if (e.target.closest('.queue-actions')) return;
            window.toggleDetails(div);
        };
        div.innerHTML = `
            <div class="queue-item-header">
                <span class="queue-name">${c.name}</span>
                <span class="queue-role">Stream A</span>
            </div>
            <p style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 0.25rem;">
                ${c.github ? c.github.repos.length + " Repos" : "No GitHub"} | 
                CTC: ${c.current_ctc || 'N/A'} LPA | Location: ${c.location || 'N/A'}
            </p>
            
            <div class="details-section hidden" style="font-size: 0.8rem; margin-top: 0.75rem; border-top: 1px dashed rgba(255,255,255,0.1); padding-top: 0.75rem;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 0.5rem;">
                    <div><strong>Email:</strong> ${c.email || 'N/A'}</div>
                    <div><strong>Notice Period:</strong> ${c.notice_period_days !== undefined ? c.notice_period_days + ' Days' : 'N/A'}</div>
                </div>
                <div style="margin-bottom: 0.5rem;"><strong>Skills Claimed:</strong> ${c.skills_claimed ? c.skills_claimed.join(', ') : 'None'}</div>
                ${c.github ? `
                    <div style="margin-top: 0.5rem; background: rgba(0,0,0,0.25); padding: 0.5rem; border-radius: 6px; display: flex; justify-content: space-between;">
                        <span><strong>Commits (Last Year):</strong> ${c.github.total_commits_last_year || 0}</span>
                        <span><strong>Streak:</strong> ${c.github.contribution_streak_days || 0} days</span>
                    </div>
                ` : ''}
                ${c.side_projects && c.side_projects.length > 0 ? `
                    <div style="margin-top: 0.5rem;">
                        <strong>Side Projects:</strong> 
                        ${c.side_projects.map(p => `<span class="badge" style="background: rgba(255,255,255,0.1); padding: 0.1rem 0.4rem; border-radius: 4px; font-size: 0.75rem; margin-right: 0.25rem;">${p.name} (${p.status})</span>`).join('')}
                    </div>
                ` : ''}
            </div>

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
        div.onclick = () => window.toggleDetails(div);
        
        const hasVerdict = c.verdict && c.verdict.dimensions;
        
        div.innerHTML = `
            <div class="ranked-header">
                <div class="rank-badge">#${c.rank}</div>
                <div class="candidate-meta">
                    <span class="queue-name">${c.verdict.candidate_id}</span>
                    <span class="verdict-badge verdict-${c.verdict.verdict}">${c.verdict.verdict.replace('_', ' ')}</span>
                </div>
                <div class="ranked-score">${c.verdict.overall.toFixed(1)}</div>
            </div>
            
            <p class="preview-notes" style="font-size: 0.8rem; color: var(--text-muted);">
                ${hasVerdict ? c.verdict.dimensions.job_fit.rationale : 'Failed early in routing stage.'}
            </p>
            
            ${hasVerdict ? `
                <div class="details-section hidden" style="margin-top: 0.75rem; border-top: 1px dashed rgba(255,255,255,0.1); padding-top: 0.75rem;">
                    <div class="dimensions-grid" style="display: flex; flex-direction: column; gap: 0.4rem; margin-bottom: 0.75rem;">
                        ${['skill', 'hunger', 'creativity', 'job_fit', 'reliability'].map(dim => {
                            const scoreObj = c.verdict.dimensions[dim];
                            if (!scoreObj) return '';
                            const score = scoreObj.score;
                            const title = dim.replace('_', ' ').toUpperCase();
                            const color = score >= 75 ? 'var(--success)' : score >= 40 ? '#fbbf24' : 'var(--danger)';
                            return `
                                <div class="dim-row" style="display: flex; align-items: center; justify-content: space-between; font-size: 0.75rem;">
                                    <span class="dim-label" style="width: 80px; font-weight: 600;">${title}</span>
                                    <div class="progress-bar-container" style="flex-grow: 1; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; margin: 0 0.5rem; overflow: hidden;">
                                        <div class="progress-bar-fill" style="width: ${score}%; height: 100%; background: ${color}; border-radius: 3px;"></div>
                                    </div>
                                    <span class="dim-score-val" style="width: 25px; text-align: right; font-weight: 700; color: ${color}">${score}</span>
                                </div>
                            `;
                        }).join('')}
                    </div>
                    
                    <!-- Adjustments and Signal Badges -->
                    <div class="adjustments-panel" style="display: flex; flex-direction: column; gap: 0.4rem; font-size: 0.75rem;">
                        ${c.verdict.pedigree_adjustment && c.verdict.pedigree_adjustment.applied ? `
                            <div class="adj-badge discount" style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); padding: 0.4rem; border-radius: 6px;">
                                <strong>⚖️ Pedigree Discount:</strong> -${c.verdict.pedigree_adjustment.net_score_change} pts
                                <p style="margin: 0.2rem 0 0 0; color: var(--text-muted); font-size: 0.7rem;">${c.verdict.pedigree_adjustment.reason}</p>
                            </div>
                        ` : ''}
                        ${c.verdict.growth_signal && c.verdict.growth_signal.detected ? `
                            <div class="adj-badge boost" style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); padding: 0.4rem; border-radius: 6px;">
                                <strong>🚀 Growth Boost:</strong> ${c.verdict.growth_signal.multiplier_applied}x Multiplier
                                <p style="margin: 0.2rem 0 0 0; color: var(--text-muted); font-size: 0.7rem;">${c.verdict.growth_signal.description}</p>
                            </div>
                        ` : ''}
                    </div>

                    <!-- Empathetic Committee Advocacy Notes -->
                    ${c.verdict.human_review_notes ? `
                        <div class="human-advocacy-panel" style="margin-top: 0.5rem; background: rgba(139, 92, 246, 0.08); border: 1px solid rgba(139, 92, 246, 0.25); padding: 0.6rem; border-radius: 8px; font-size: 0.75rem; white-space: pre-line;">
                            <strong style="color: #a78bfa; display: block; margin-bottom: 0.25rem;">🤝 Empathy Committee Advocacy:</strong>
                            ${c.verdict.human_review_notes.replace('=== EMPATHETIC COMMITTEE ADVOCACY NARRATIVE ===\n', '')}
                        </div>
                    ` : ''}
                    
                    <!-- Red Flags -->
                    ${c.verdict.red_flags && c.verdict.red_flags.length > 0 ? `
                        <div class="red-flags-panel" style="margin-top: 0.5rem; background: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.15); padding: 0.4rem; border-radius: 6px; font-size: 0.75rem;">
                            <strong style="color: var(--danger);">⚠️ Risk Factors / Warnings:</strong>
                            <ul style="margin: 0.2rem 0 0 0; padding-left: 1.25rem; color: #f87171;">
                                ${c.verdict.red_flags.map(f => `<li>${f}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            ` : ''}
        `;
        container.appendChild(div);
    });
}

// Event Listeners
document.getElementById('btn-reset').addEventListener('click', resetPipeline);
document.getElementById('btn-send-promising').addEventListener('click', () => runPipeline('promising'));
document.getElementById('btn-send-polished').addEventListener('click', () => runPipeline('polished'));
document.getElementById('btn-finalize').addEventListener('click', finalizeBattle);

// Modal Logic
const modal = document.getElementById('modal-integrations');
document.getElementById('btn-integrations').addEventListener('click', () => {
    modal.classList.remove('hidden');
});
document.getElementById('btn-close-modal').addEventListener('click', () => {
    modal.classList.add('hidden');
});
document.getElementById('btn-done-modal').addEventListener('click', () => {
    modal.classList.add('hidden');
});

// Copy logic
window.copyToClipboard = function(elementId) {
    const el = document.getElementById(elementId);
    el.select();
    document.execCommand('copy');
    logPortal(`Copied ${elementId} to clipboard`, 'success');
}

window.toggleSecret = function() {
    const el = document.getElementById('webhook-secret');
    if (el.type === 'password') {
        el.type = 'text';
    } else {
        el.type = 'password';
    }
}

// Init
document.getElementById('webhook-url').value = `${window.location.origin}/webhook/ats`;
const storedSecret = localStorage.getItem('meritengine_webhook_secret') || "sk_merit_9f82d7a6b5c4e3";
document.getElementById('webhook-secret').value = storedSecret;
localStorage.setItem('meritengine_webhook_secret', storedSecret); // ensure it is stored

document.getElementById('webhook-secret').addEventListener('input', (e) => {
    localStorage.setItem('meritengine_webhook_secret', e.target.value.trim());
});

logPortal("UI initialized and ready.", "success");
refreshQueue();
setInterval(refreshQueue, 2000); // Auto-refresh queue for demo effect

// Modern Startup Splash Screen Animation Timeline
document.addEventListener("DOMContentLoaded", () => {
    const splash = document.getElementById("splash-screen");
    const status = document.getElementById("splash-status");
    const stage = document.getElementById("matching-stage");

    if (splash) {
        const timelines = [
            { time: 400, statusText: "mapping resume vector space...", stageText: "initializing embeddings" },
            { time: 900, statusText: "calculating semantic distance...", stageText: "evaluating skills match" },
            { time: 1400, statusText: "calibrating experience trajectory...", stageText: "analyzing hunger metrics" },
            { time: 1900, statusText: "synergy scoring completed...", stageText: "advocacy consensus" },
            { time: 2300, statusText: "perfect candidate alignment achieved.", stageText: "alignment locked" }
        ];

        timelines.forEach(item => {
            setTimeout(() => {
                if (status) status.textContent = item.statusText;
                if (stage) stage.textContent = item.stageText;
            }, item.time);
        });

        setTimeout(() => {
            splash.classList.add("fade-out");
        }, 2800);
    }
});


