// Initialize Webhook Configuration from localStorage
const defaultUrl = `${window.location.origin}/webhook/ats`;
const defaultSecret = localStorage.getItem('meritengine_webhook_secret') || "sk_merit_9f82d7a6b5c4e3";

const urlInput = document.getElementById('webhook-target-url');
const secretInput = document.getElementById('webhook-target-secret');

urlInput.value = localStorage.getItem('meritengine_webhook_url') || defaultUrl;
secretInput.value = localStorage.getItem('meritengine_webhook_secret') || defaultSecret;

// Save inputs on change
urlInput.addEventListener('input', () => {
    localStorage.setItem('meritengine_webhook_url', urlInput.value.trim());
});
secretInput.addEventListener('input', () => {
    localStorage.setItem('meritengine_webhook_secret', secretInput.value.trim());
});

document.getElementById('btn-save').addEventListener('click', async () => {
    // Gather form data
    const name = document.getElementById('cand-name').value.trim();
    const email = document.getElementById('cand-email').value.trim();
    const skills = document.getElementById('cand-skills').value.trim();
    const github = document.getElementById('cand-github').value.trim();
    const notice = document.getElementById('cand-notice').value.trim();
    const ctc = document.getElementById('cand-ctc').value.trim();
    const score = document.getElementById('cand-score').value.trim();

    if (!name || !email || !skills || !notice || !ctc) {
        alert("Please fill all required fields.");
        return;
    }

    // Parse comma separated values
    const skillsList = skills.split(',').map(s => s.trim()).filter(s => s);
    const githubUrls = github.split(',').map(s => s.trim()).filter(s => s);
    
    // Parse GitHub URLs into the expected repo structure
    const githubRepos = githubUrls.map(url => {
        const parts = url.split('/');
        const repoName = parts[parts.length - 1] || "unknown-repo";
        return { name: repoName };
    });

    // Create a realistic ATS payload (like a Greenhouse or Lever webhook)
    const payload = {
        application_id: `ATS-${Math.floor(Math.random() * 1000000)}`,
        name: name,
        email_addresses: [{ value: email }],
        skills_claimed: skillsList,
        notice_period_days: parseInt(notice),
        current_ctc: parseFloat(ctc),
        expected_ctc: parseFloat(ctc),
        github: {
            username: email.split('@')[0], // mock username
            repos: githubRepos
        }
    };

    if (score) {
        payload.assessment = { score: parseFloat(score) };
    }

    const btn = document.getElementById('btn-save');
    btn.textContent = "Transmitting to MeritEngine...";
    btn.disabled = true;

    const targetUrl = urlInput.value.trim() || defaultUrl;
    const secretToken = secretInput.value.trim();

    try {
        const res = await fetch(targetUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-API-Key": secretToken
            },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            alert("Success! Candidate securely transmitted via Webhook.");
            document.getElementById('candidateForm').reset();
        } else {
            const err = await res.json();
            alert(`Transmission Error: ${err.detail || JSON.stringify(err)}`);
        }
    } catch (e) {
        alert(`Network Error: ${e.message}`);
    } finally {
        btn.textContent = "Save Candidate & Trigger Webhook";
        btn.disabled = false;
    }
});
