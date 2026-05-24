document.addEventListener('DOMContentLoaded', () => {
    // === STATE ===
    let sessionId = localStorage.getItem('cs_session_id');
    if (!sessionId) {
        sessionId = crypto.randomUUID();
        localStorage.setItem('cs_session_id', sessionId);
    }

    // Check for magic link token in URL
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    if (token) verifyMagicLink(token);

    // === DOM ELEMENTS ===
    const notesInput        = document.getElementById('notes');
    const generateBtn       = document.getElementById('generateBtn');
    const loadingState      = document.getElementById('loadingState');
    const resultsSection    = document.getElementById('resultsSection');
    const cardsContainer    = document.getElementById('cardsContainer');
    const generationsText   = document.getElementById('generationsRemainingText');
    const progressBarFill   = document.getElementById('progressBarFill');
    const loaderError       = document.getElementById('loaderError');
    const loaderErrorMsg    = document.getElementById('loaderErrorMsg');
    const loaderRetryBtn    = document.getElementById('loaderRetryBtn');

    // Modals
    const paywallModal      = document.getElementById('paywallModal');
    const closePaywallBtn   = document.getElementById('closePaywallBtn');
    const checkoutBtn       = document.getElementById('checkoutBtn');
    const loginBtn          = document.getElementById('loginBtn');
    const restoreBtn        = document.getElementById('restoreBtn');
    const magicLinkModal    = document.getElementById('magicLinkModal');
    const closeMagicLinkBtn = document.getElementById('closeMagicLinkBtn');
    const sendMagicLinkBtn  = document.getElementById('sendMagicLinkBtn');
    const loginEmail        = document.getElementById('loginEmail');
    const magicLinkMessage  = document.getElementById('magicLinkMessage');

    // === INIT ===
    updateGenerationsText(3);

    // === LOADING SEQUENCE ===
    const STAGES = [
        { id: 1, progress: 12,  delay: 0    },
        { id: 2, progress: 48,  delay: 8000 },
        { id: 3, progress: 82,  delay: 18000 },
    ];
    let stageTimers = [];

    function activateStage(stageNum) {
        for (let i = 1; i <= 3; i++) {
            const el      = document.getElementById(`stage-${i}`);
            const spinner = document.getElementById(`stage-${i}-spinner`);
            const check   = document.getElementById(`stage-${i}-check`);

            el.classList.remove('active', 'done');
            spinner.classList.add('hidden');
            check.classList.add('hidden');

            if (i < stageNum) {
                el.classList.add('done');
                check.classList.remove('hidden');
            } else if (i === stageNum) {
                el.classList.add('active');
                spinner.classList.remove('hidden');
            }
        }
    }

    function runLoadingSequence() {
        // Reset error state
        loaderError.classList.add('hidden');
        progressBarFill.style.width = '0%';

        STAGES.forEach(({ id, progress, delay }) => {
            const t = setTimeout(() => {
                activateStage(id);
                progressBarFill.style.width = `${progress}%`;
            }, delay);
            stageTimers.push(t);
        });
    }

    function stopLoadingSequence() {
        stageTimers.forEach(clearTimeout);
        stageTimers = [];
    }

    function showLoadingError(message) {
        stopLoadingSequence();
        loaderErrorMsg.textContent = message || 'Something went wrong. Please try again.';
        loaderError.classList.remove('hidden');
        document.getElementById('skeletonCards').classList.add('hidden');
    }

    // === GENERATE ===
    async function doGenerate() {
        const notes = notesInput.value.trim();
        if (notes.length < 10) {
            alert('Please provide more detailed notes (at least 10 characters).');
            return;
        }

        // UI — show loader, hide results
        generateBtn.disabled = true;
        resultsSection.classList.add('hidden');
        document.getElementById('skeletonCards').classList.remove('hidden');
        loaderError.classList.add('hidden');
        loadingState.classList.remove('hidden');

        // Scroll so the progress bar is immediately in view
        setTimeout(() => {
            loadingState.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 50);

        runLoadingSequence();

        try {
            const response = await fetch('/api/v1/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ notes, session_id: sessionId })
            });

            if (response.status === 403) {
                loadingState.classList.add('hidden');
                stopLoadingSequence();
                paywallModal.classList.remove('hidden');
                paywallModal.classList.add('flex');
                return;
            }

            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                showLoadingError(err.detail || 'Generation failed. Please try again.');
                return;
            }

            const data = await response.json();
            stopLoadingSequence();

            // Snap progress to 100% then reveal
            progressBarFill.style.width = '100%';
            activateStage(3);
            // Mark stage 3 done
            setTimeout(() => {
                document.getElementById('stage-3').classList.remove('active');
                document.getElementById('stage-3').classList.add('done');
                document.getElementById('stage-3-spinner').classList.add('hidden');
                document.getElementById('stage-3-check').classList.remove('hidden');
            }, 400);

            setTimeout(() => {
                loadingState.classList.add('hidden');
                updateGenerationsText(data.generations_remaining);
                renderCards(data.angles);
                // Give the DOM a tick to paint the cards, then scroll into view
                requestAnimationFrame(() => {
                    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                });
            }, 800);

        } catch (err) {
            console.error(err);
            showLoadingError('Network error. Check your connection and try again.');
        } finally {
            generateBtn.disabled = false;
        }
    }

    generateBtn.addEventListener('click', doGenerate);

    loaderRetryBtn.addEventListener('click', () => {
        loaderError.classList.add('hidden');
        document.getElementById('skeletonCards').classList.remove('hidden');
        doGenerate();
    });

    // === REFINE (event delegation) ===
    cardsContainer.addEventListener('click', async (e) => {
        const btn = e.target.closest('button');
        if (!btn) return;
        const action = btn.dataset.action;
        if (!action) return;

        const card        = btn.closest('.card-container');
        const textElement = card.querySelector('.angle-content');
        const originalText = textElement.textContent.trim().replace(/^"|"$/g, '');

        if (action === 'copy') {
            navigator.clipboard.writeText(originalText);
            const orig = btn.innerHTML;
            btn.innerHTML = '✓ Copied!';
            setTimeout(() => btn.innerHTML = orig, 2000);
            return;
        }

        btn.disabled = true;
        const origHtml = btn.innerHTML;
        btn.innerHTML = 'Refining...';
        textElement.classList.add('animate-pulse', 'text-gray-400');

        try {
            const response = await fetch('/api/v1/refine', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    original_text: originalText,
                    refinement_type: action,
                    session_id: sessionId
                })
            });

            if (!response.ok) throw new Error('Refine failed');
            const data = await response.json();
            textElement.textContent = `"${data.refined_text}"`;
        } catch (err) {
            console.error(err);
        } finally {
            btn.disabled = false;
            btn.innerHTML = origHtml;
            textElement.classList.remove('animate-pulse', 'text-gray-400');
        }
    });

    // === MODALS ===
    closePaywallBtn.addEventListener('click', () => {
        paywallModal.classList.add('hidden');
        paywallModal.classList.remove('flex');
    });

    const openLoginModal = () => {
        paywallModal.classList.add('hidden');
        paywallModal.classList.remove('flex');
        magicLinkModal.classList.remove('hidden');
        magicLinkModal.classList.add('flex');
    };

    loginBtn.addEventListener('click', openLoginModal);
    restoreBtn.addEventListener('click', openLoginModal);

    closeMagicLinkBtn.addEventListener('click', () => {
        magicLinkModal.classList.add('hidden');
        magicLinkModal.classList.remove('flex');
        magicLinkMessage.classList.add('hidden');
        loginEmail.value = '';
    });

    checkoutBtn.addEventListener('click', () => {
        window.location.href = 'https://your-store.lemonsqueezy.com/checkout/buy/variant-id';
    });

    sendMagicLinkBtn.addEventListener('click', async () => {
        const email = loginEmail.value.trim();
        if (!email) return;
        sendMagicLinkBtn.disabled = true;
        sendMagicLinkBtn.textContent = 'Sending...';

        try {
            const response = await fetch('/api/v1/auth/request-magic-link', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });
            magicLinkMessage.classList.remove('hidden');
            if (response.ok) {
                magicLinkMessage.textContent = 'If an account exists, a magic link has been sent!';
                magicLinkMessage.className = 'text-sm font-medium text-green-600 mt-2';
            } else {
                const err = await response.json();
                magicLinkMessage.textContent = err.detail || 'Failed to send link.';
                magicLinkMessage.className = 'text-sm font-medium text-red-600 mt-2';
            }
        } catch {
            magicLinkMessage.classList.remove('hidden');
            magicLinkMessage.textContent = 'Network error.';
            magicLinkMessage.className = 'text-sm font-medium text-red-600 mt-2';
        } finally {
            sendMagicLinkBtn.disabled = false;
            sendMagicLinkBtn.textContent = 'Send Magic Link';
        }
    });

    // === HELPERS ===
    function updateGenerationsText(remaining) {
        const dotColor  = remaining > 0 ? 'text-green-600' : 'text-red-500';
        const bgColor   = remaining > 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-700';
        generationsText.className = `inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${bgColor}`;
        generationsText.innerHTML = `
            <svg class="-ml-1 mr-1.5 h-2 w-2 ${dotColor}" fill="currentColor" viewBox="0 0 8 8"><circle cx="4" cy="4" r="3"/></svg>
            Free Plan: ${remaining}/3 Remaining
        `;
    }

    async function verifyMagicLink(token) {
        try {
            const res = await fetch(`/api/v1/auth/verify?token=${token}`);
            if (res.ok) {
                window.history.replaceState({}, document.title, window.location.pathname);
                generationsText.className = 'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-indigo-100 text-indigo-800';
                generationsText.innerHTML = `
                    <svg class="-ml-1 mr-1.5 h-2 w-2 text-indigo-600" fill="currentColor" viewBox="0 0 8 8"><circle cx="4" cy="4" r="3"/></svg>
                    Premium Access ✨
                `;
            } else {
                alert('Magic link invalid or expired.');
            }
        } catch (e) {
            console.error('Token verify failed', e);
        }
    }

    function renderCards(angles) {
        cardsContainer.innerHTML = '';
        const colors = {
            'Benefit-Driven':   'indigo',
            'Problem/Solution': 'blue',
            'FOMO/Urgency':     'orange'
        };

        angles.forEach((angle, i) => {
            const color = colors[angle.angle_type] || 'gray';
            const delay = i * 120;

            const wrapper = document.createElement('div');
            wrapper.className = 'card-reveal';
            wrapper.style.animationDelay = `${delay}ms`;

            wrapper.innerHTML = `
            <div class="card-container bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:border-${color}-300 transition-colors">
                <div class="bg-${color}-50 px-6 py-3 border-b border-${color}-100 flex justify-between items-center">
                    <span class="text-sm font-semibold text-${color}-800 uppercase tracking-wider">${angle.angle_type}</span>
                </div>
                <div class="p-6">
                    <p class="angle-content text-lg text-gray-800 leading-relaxed font-medium transition-all duration-300">
                        "${angle.content}"
                    </p>
                </div>
                <div class="px-6 py-3 bg-gray-50 border-t border-gray-100 flex items-center justify-end space-x-3">
                    <button data-action="shorter" class="text-sm font-medium text-gray-600 hover:text-${color}-600 transition-colors inline-flex items-center gap-1 disabled:opacity-50">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                        Make Shorter
                    </button>
                    <button data-action="casual" class="text-sm font-medium text-gray-600 hover:text-${color}-600 transition-colors inline-flex items-center gap-1 disabled:opacity-50">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                        More Casual
                    </button>
                    <div class="h-4 w-px bg-gray-300"></div>
                    <button data-action="copy" class="text-sm font-semibold text-${color}-600 hover:text-${color}-800 transition-colors inline-flex items-center gap-1">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
                        Copy
                    </button>
                </div>
            </div>`;

            cardsContainer.appendChild(wrapper);
        });

        resultsSection.classList.remove('hidden');
    }
});
