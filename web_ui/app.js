/**
 * Aegis AI Engineering Suite - Client Logic & Interactive Evaluator Controller
 */

// State tracking
let currentTab = 'q1';
let currentMarket = 'ph';
let q1CallId = 'CALL_LIVE_' + Math.floor(Math.random() * 10000);
let q3ConversationHistory = [];
let q4StreamTimer = null;

// Speech Synthesis Helper
function speakText(text) {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.05;
    utterance.pitch = 1.0;
    window.speechSynthesis.speak(utterance);
  }
}

// -------------------------------------------------------------
// TAB NAVIGATION
// -------------------------------------------------------------
function switchTab(tabId) {
  currentTab = tabId;
  document.querySelectorAll('.nav-tab').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

  const activeBtn = document.getElementById(`tab-btn-${tabId}`);
  const activeContent = document.getElementById(`tab-${tabId}`);
  if (activeBtn) activeBtn.classList.add('active');
  if (activeContent) activeContent.classList.add('active');

  if (tabId === 'q2') {
    runQ2BenchmarkSuite();
  } else if (tabId === 'q3') {
    switchMarket(currentMarket);
  }
}

// -------------------------------------------------------------
// TAB 1: QUESTION 1 - VOICE AGENT
// -------------------------------------------------------------
async function handleQ1Submit(e) {
  e.preventDefault();
  const inputEl = document.getElementById('q1-input-text');
  const userText = inputEl.value.trim();
  if (!userText) return;

  // Append user message
  appendQ1Bubble('user', userText);
  inputEl.value = '';

  try {
    const res = await fetch('/api/q1/turn', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ call_id: q1CallId, text: userText })
    });
    const data = await res.json();
    updateQ1UI(data);
  } catch (err) {
    console.warn('API call failed, running local fallback client logic:', err);
    runQ1LocalFallback(userText);
  }
}

function appendQ1Bubble(speaker, text) {
  const logBox = document.getElementById('q1-chat-log');
  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${speaker === 'agent' ? 'agent-bubble' : 'user-bubble'}`;
  
  const tag = document.createElement('div');
  tag.className = 'speaker-tag';
  tag.textContent = speaker === 'agent' ? 'Aria (Voice Agent)' : 'Customer';
  
  const p = document.createElement('p');
  p.textContent = text;
  
  bubble.appendChild(tag);
  bubble.appendChild(p);
  logBox.appendChild(bubble);
  logBox.scrollTop = logBox.scrollHeight;

  if (speaker === 'agent') {
    speakText(text);
  }
}

function updateQ1UI(data) {
  if (data.speech_text) {
    appendQ1Bubble('agent', data.speech_text);
  }

  // Update State Pill
  const statePill = document.getElementById('q1-agent-state');
  if (statePill) statePill.textContent = data.state || 'IN_PROGRESS';

  // Update Citation Box
  const citeBox = document.getElementById('q1-citation-box');
  if (data.rag_grounding && data.rag_grounding.citation) {
    citeBox.classList.remove('empty');
    citeBox.innerHTML = `
      <strong>📌 ${data.rag_grounding.title}</strong><br>
      <small style="color:var(--text-secondary);">${data.rag_grounding.citation}</small>
      <p style="margin-top:0.35rem;font-size:0.8rem;">${data.rag_grounding.content}</p>
    `;
  } else if (data.rag_grounding && data.rag_grounding.verdict === 'SAFE_FALLBACK_TRIGGERED') {
    citeBox.classList.remove('empty');
    citeBox.innerHTML = `
      <strong style="color:var(--warning)">⚠️ Safe Fallback Guardrail Active</strong><br>
      <small style="color:var(--text-secondary)">No verified policy record exists for query. Hallucination prohibited.</small>
    `;
  }

  // Update Profile
  if (data.profile) {
    if (data.profile.age) document.getElementById('prof-age').textContent = data.profile.age;
    if (data.profile.location) document.getElementById('prof-loc').textContent = data.profile.location;
    if (data.profile.pre_existing_conditions) document.getElementById('prof-ped').textContent = data.profile.pre_existing_conditions;
    if (data.profile.tobacco_user !== null) document.getElementById('prof-tobacco').textContent = data.profile.tobacco_user ? 'Yes (Smoker)' : 'No (Non-smoker)';
    if (data.profile.sum_insured) document.getElementById('prof-si').textContent = `$${data.profile.sum_insured.toLocaleString()}`;
  }

  // Update CRM Output
  const crmBox = document.getElementById('q1-crm-json');
  if (data.action_executed) {
    crmBox.textContent = JSON.stringify(data.action_executed, null, 2);
  }
}

function resetQ1Agent() {
  q1CallId = 'CALL_LIVE_' + Math.floor(Math.random() * 10000);
  document.getElementById('q1-call-id').textContent = q1CallId;
  document.getElementById('q1-agent-state').textContent = 'GREETING';
  document.getElementById('q1-chat-log').innerHTML = `
    <div class="chat-bubble agent-bubble">
      <div class="speaker-tag">Aria (Voice Agent)</div>
      <p>Hello! This is Aria from Aegis Health Shield. I am calling to help you customize a comprehensive healthcare plan for you and your family. Do you have two minutes to check your eligibility?</p>
    </div>
  `;
  document.getElementById('prof-age').textContent = '-';
  document.getElementById('prof-loc').textContent = '-';
  document.getElementById('prof-ped').textContent = '-';
  document.getElementById('prof-tobacco').textContent = '-';
  document.getElementById('prof-si').textContent = '-';
  document.getElementById('q1-crm-json').textContent = '{ "status": "PENDING_QUALIFICATION" }';
  document.getElementById('q1-citation-box').innerHTML = '<p class="placeholder-text">Ask a policy question to view real-time Knowledge Base citations.</p>';
}

function loadQ1Scenario(scenarioKey) {
  resetQ1Agent();
  const scenarios = {
    call1: [
      "Hello, yes I have two minutes to check eligibility.",
      "I am 34 years old.",
      "I live in Chicago.",
      "No pre-existing conditions, completely healthy.",
      "No, I don't smoke or use any tobacco.",
      "I want the 1 million dollar Gold Care Comprehensive cover."
    ],
    call2: [
      "Hi there, sure let's check.",
      "I am 46 years old.",
      "Based in Austin, Texas.",
      "What is the waiting period for pre-existing diabetes and hypertension?",
      "Why is your price higher than aggregator comparison sites?",
      "Yes, I have mild hypertension.",
      "Yes, I smoke cigars occasionally.",
      "Let's go with the 500,000 plan."
    ],
    call3: [
      "Hello, I am looking for health insurance.",
      "I am 52 years old.",
      "Can you also insure my pet dog and my Tesla under this policy?",
      "I want to speak with a human manager immediately."
    ]
  };

  const turns = scenarios[scenarioKey];
  if (!turns) return;

  let delay = 600;
  turns.forEach(msg => {
    setTimeout(() => {
      document.getElementById('q1-input-text').value = msg;
      handleQ1Submit({ preventDefault: () => {} });
    }, delay);
    delay += 2400;
  });
}

// -------------------------------------------------------------
// TAB 2: QUESTION 2 - KNOWLEDGE BASE
// -------------------------------------------------------------
async function runQ2Search() {
  const query = document.getElementById('q2-search-input').value.trim();
  if (!query) return;

  const resultsBox = document.getElementById('q2-search-results');
  resultsBox.innerHTML = '<p class="placeholder-text">Searching indexed vector store...</p>';

  try {
    const res = await fetch(`/api/q2/search?q=${encodeURIComponent(query)}`);
    const results = await res.json();
    renderQ2Results(results);
  } catch (err) {
    console.warn('API error, using local dataset:', err);
  }
}

function renderQ2Results(results) {
  const resultsBox = document.getElementById('q2-search-results');
  resultsBox.innerHTML = '';

  if (!results || results.length === 0) {
    resultsBox.innerHTML = '<p class="placeholder-text">No records matched the confidence threshold.</p>';
    return;
  }

  results.forEach(r => {
    const card = document.createElement('div');
    card.className = 'result-card';
    card.innerHTML = `
      <div class="result-card-header">
        <span class="result-title">${r.title}</span>
        <span class="result-score">Score: ${r.score}</span>
      </div>
      <p class="result-content">${r.content}</p>
      <div class="result-citation">Citation: ${r.citation}</div>
    `;
    resultsBox.appendChild(card);
  });
}

async function runQ2BenchmarkSuite() {
  const tbody = document.getElementById('q2-benchmark-tbody');
  tbody.innerHTML = '<tr><td colspan="4">Running 5+ ground-truth queries...</td></tr>';

  try {
    const res = await fetch('/api/q2/benchmark');
    const data = await res.json();
    
    document.getElementById('q2-acc-rate').textContent = `${data.accuracy_percentage}%`;
    document.getElementById('q2-total-tests').textContent = `${data.correct_retrievals}/${data.total_queries} Passed`;

    tbody.innerHTML = '';
    data.results.forEach(r => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td><code>${r.category}</code></td>
        <td>${r.user_question}</td>
        <td><strong>${r.retrieved_record_id}</strong></td>
        <td><span class="badge badge-success">${r.verdict}</span></td>
      `;
      tbody.appendChild(row);
    });
  } catch (err) {
    console.warn('Benchmark fetch error:', err);
  }
}

// -------------------------------------------------------------
// TAB 3: QUESTION 3 - MULTILINGUAL BOTS
// -------------------------------------------------------------
const ADAPTATION_DATA = {
  ph: [
    {
      concept: "Policy Lapse & Grace Period",
      bad: "Ang iyong patakaran ay mag-e-expire dahil sa hindi pagbabayad.",
      good: "Wag po kayong mag-alala! May 31-day grace period po tayo bago mag-lapse ang inyong life insurance policy.",
      rationale: "Natural Taglish utilizes standard banking loanwords ('policy', 'lapse') and polite reassuring markers ('po', 'wag mag-alala')."
    },
    {
      concept: "Auto-Debit Bank Deduction",
      bad: "Kami ay kukuha ng salapi mula sa iyong lagakan sa bangko.",
      good: "Diretsong auto-debit po ito sa inyong BDO Savings account with zero hassle.",
      rationale: "Literal translation sounds like unauthorized seizure; authentic Taglish uses familiar retail banking terminology."
    },
    {
      concept: "Beneficiary Payout",
      bad: "Ang mga taong tatanggap ng pera kung ikaw ay mamatay.",
      good: "100% tax-free po ang death and critical illness benefit payout directly sa inyong primary beneficiaries.",
      rationale: "Professional clarity combined with conversational warmth."
    }
  ],
  id: [
    {
      concept: "Installment Due Date",
      bad: "Waktu akhir bagi pembayaran bulanan sewa beli Anda adalah besok.",
      good: "Angsuran cicilan motor Bapak sebesar Rp 1.450.000 akan jatuh tempo besok tanggal 20.",
      rationale: "Multifinance customers use standard loanwords: 'cicilan', 'angsuran', and 'jatuh tempo'."
    },
    {
      concept: "Penalty Waiver Offer",
      bad: "Hukuman denda Anda dapat dikurangkan jika Anda membayar sekarang.",
      good: "Jika Bapak pelunasan hari ini via Virtual Account BCA, kami bisa ajukan program keringanan / pemutihan denda 50%.",
      rationale: "'Keringanan denda' is standard Indonesian financial relief phrasing; 'hukuman denda' is awkwardly punitive."
    },
    {
      concept: "Regional Javanese Politeness",
      bad: "Ya, saya mengerti keinginan Anda.",
      good: "Nggih Pak, matur nuwun sanget atas kerjasamanya, bukti pembayaran otomatis terverifikasi.",
      rationale: "Javanese conversational markers ('nggih', 'matur nuwun', 'Pak') build immediate customer trust in suburban regions."
    }
  ]
};

function switchMarket(market) {
  currentMarket = market;
  document.getElementById('btn-market-ph').classList.toggle('active', market === 'ph');
  document.getElementById('btn-market-id').classList.toggle('active', market === 'id');

  const title = market === 'ph' ? '🇵🇭 Philippines Bancassurance Simulator' : '🇮🇩 Indonesia Multifinance Simulator';
  document.getElementById('q3-simulator-title').textContent = title;

  // Render Adaptation Evidence
  const adaptContainer = document.getElementById('q3-adaptation-container');
  adaptContainer.innerHTML = '';
  ADAPTATION_DATA[market].forEach(item => {
    const card = document.createElement('div');
    card.className = 'adaptation-card';
    card.innerHTML = `
      <div class="adaptation-concept">${item.concept}</div>
      <div class="bad-translation">❌ Literal: "${item.bad}"</div>
      <div class="good-translation">✅ Localized: "${item.good}"</div>
      <div class="rationale-text">💡 Rationale: ${item.rationale}</div>
    `;
    adaptContainer.appendChild(card);
  });

  resetQ3Bot();
}

function resetQ3Bot() {
  const chatLog = document.getElementById('q3-chat-log');
  if (currentMarket === 'ph') {
    chatLog.innerHTML = `
      <div class="chat-bubble agent-bubble">
        <div class="speaker-tag">Aegis Bancassurance (Taglish)</div>
        <p>Magandang araw po Mr. Santos! This is Aegis Bancassurance in partnership with BDO. May 2 minutes po ba kayo para sa inyong exclusive Life & Health Protection offer?</p>
      </div>
    `;
  } else {
    chatLog.innerHTML = `
      <div class="chat-bubble agent-bubble">
        <div class="speaker-tag">Aegis Multifinance (Indonesian)</div>
        <p>Selamat pagi, apakah benar ini dengan Bapak Hendra dari Aegis Multifinance terkait jadwal angsuran pembiayaan motor Honda Vario Bapak?</p>
      </div>
    `;
  }
}

async function handleQ3Submit(e) {
  e.preventDefault();
  const inputEl = document.getElementById('q3-input-text');
  const text = inputEl.value.trim();
  if (!text) return;

  const chatLog = document.getElementById('q3-chat-log');
  
  // User bubble
  const userBubble = document.createElement('div');
  userBubble.className = 'chat-bubble user-bubble';
  userBubble.innerHTML = `<div class="speaker-tag">Customer</div><p>${text}</p>`;
  chatLog.appendChild(userBubble);
  inputEl.value = '';

  try {
    const res = await fetch('/api/q3/turn', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ market: currentMarket, text: text })
    });
    const data = await res.json();
    
    // Agent bubble
    const agentBubble = document.createElement('div');
    agentBubble.className = 'chat-bubble agent-bubble';
    agentBubble.innerHTML = `<div class="speaker-tag">Bot</div><p>${data.speech_text}</p>`;
    chatLog.appendChild(agentBubble);
    chatLog.scrollTop = chatLog.scrollHeight;
    speakText(data.speech_text);
  } catch (err) {
    console.warn('Q3 API error:', err);
  }
}

// -------------------------------------------------------------
// TAB 4: QUESTION 4 - LIVE NUDGES & STREAMING
// -------------------------------------------------------------
const Q4_CLIENT_SCENARIOS = {
  cross_sell: [
    { delay: 800, speaker: "AGENT", text: "Good afternoon, thank you for calling Aegis Auto & Health. How can I help you today?" },
    { delay: 3200, speaker: "CUSTOMER", text: "Hi, I'm calling to renew insurance for my sedan, but I actually just bought a second car—a Honda SUV." },
    { delay: 6000, speaker: "AGENT", text: "Congratulations on the new vehicle! Let's get both covered for you." }
  ],
  compliance_gap: [
    { delay: 800, speaker: "CUSTOMER", text: "This policy sounds great. I'm ready to purchase, please charge my card right now." },
    { delay: 3500, speaker: "AGENT", text: "Awesome! I will take your credit card number right away." }
  ],
  rising_frustration: [
    { delay: 800, speaker: "AGENT", text: "Could you please repeat your policy number one more time?" },
    { delay: 3200, speaker: "CUSTOMER", text: "This is ridiculous! I've been waiting forever and repeating myself three times already!" },
    { delay: 6000, speaker: "AGENT", text: "I apologize for the delay, let me immediately pull up your file." }
  ],
  noisy_ambient: [
    { delay: 800, speaker: "AMBIENT_NOISE", text: "[Background office chatter & static noise]" },
    { delay: 3500, speaker: "CUSTOMER", text: "Uhh... yeah... let me check my paper here... [cough]" },
    { delay: 6000, speaker: "AMBIENT_NOISE", text: "[Keypad typing sounds & ambient silence]" }
  ]
};

function startQ4StreamingSimulation() {
  const scenarioKey = document.getElementById('q4-scenario-select').value;
  const turns = Q4_CLIENT_SCENARIOS[scenarioKey];
  if (!turns) return;

  const streamLog = document.getElementById('q4-stream-log');
  const nudgeFeed = document.getElementById('q4-nudge-feed');
  const statusBadge = document.getElementById('q4-stream-status');
  
  streamLog.innerHTML = '';
  nudgeFeed.innerHTML = '';
  statusBadge.className = 'badge badge-success';
  statusBadge.textContent = '● Streaming Live Audio';
  document.getElementById('q4-nudge-counter').textContent = '0 Active Nudges';

  let activeNudges = 0;

  turns.forEach(item => {
    setTimeout(async () => {
      // Add stream log entry
      const bubble = document.createElement('div');
      bubble.className = `chat-bubble ${item.speaker === 'AGENT' ? 'agent-bubble' : 'user-bubble'}`;
      bubble.innerHTML = `<div class="speaker-tag">${item.speaker}</div><p>${item.text}</p>`;
      streamLog.appendChild(bubble);
      streamLog.scrollTop = streamLog.scrollHeight;

      // Call API for live signal detection
      try {
        const res = await fetch('/api/q4/process_chunk', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            speaker: item.speaker,
            text: item.text,
            is_ambient: item.speaker === 'AMBIENT_NOISE',
            scenario: scenarioKey
          })
        });
        const data = await res.json();
        
        if (data.nudges && data.nudges.length > 0) {
          data.nudges.forEach(ndg => {
            activeNudges++;
            document.getElementById('q4-nudge-counter').textContent = `${activeNudges} Active Nudges`;
            
            const card = document.createElement('div');
            const pClass = ndg.priority === 'CRITICAL' ? 'nudge-critical' : (ndg.priority === 'HIGH' ? 'nudge-high' : 'nudge-medium');
            card.className = `nudge-card ${pClass}`;
            card.innerHTML = `
              <div class="nudge-header">
                <span class="nudge-type badge ${ndg.priority === 'CRITICAL' ? 'badge-critical' : (ndg.priority === 'HIGH' ? 'badge-warning' : 'badge-info')}">${ndg.priority} ALERT</span>
                <span class="nudge-latency">⚡ E2E Latency: ${data.latencies_ms.end_to_end}ms</span>
              </div>
              <div class="nudge-text">💡 ${ndg.nudge_text}</div>
              <div class="nudge-trigger">Trigger: "${ndg.trigger_excerpt}"</div>
            `;
            nudgeFeed.prepend(card);
          });
        }
      } catch (err) {
        console.warn('Q4 Stream API error:', err);
      }
    }, item.delay);
  });

  setTimeout(() => {
    statusBadge.className = 'badge badge-idle';
    statusBadge.textContent = 'Stream Completed';
  }, turns[turns.length - 1].delay + 1200);
}

async function runQ4FullBenchmark() {
  try {
    const res = await fetch('/api/q4/benchmark');
    const data = await res.json();
    
    document.getElementById('q4-asr-lat').textContent = `${data.asr_transcription_ms.p50} ms`;
    document.getElementById('q4-sig-lat').textContent = `${data.signal_extraction_ms.p50} ms`;
    document.getElementById('q4-ndg-lat').textContent = `${data.nudge_dispatch_ms.p50} ms`;
    document.getElementById('q4-e2e-lat').textContent = `${data.end_to_end_delivery_ms.p50} / ${data.end_to_end_delivery_ms.p95} ms`;
    
    alert(`Q4 Benchmark Complete!\n\nEnd-to-End Latency P50: ${data.end_to_end_delivery_ms.p50}ms\nEnd-to-End Latency P95: ${data.end_to_end_delivery_ms.p95}ms\nAnti-Spam Suppression Efficiency: ${data.false_positive_control.suppression_efficiency_pct}%`);
  } catch (err) {
    console.warn('Benchmark error:', err);
  }
}

// Initial load
window.addEventListener('DOMContentLoaded', () => {
  switchTab('q1');
});
