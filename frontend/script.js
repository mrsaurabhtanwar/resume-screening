/**
 * AI Resume Screening & Candidate Ranking Engine
 * Frontend JavaScript Controller
 */

// Application Configuration & State
let API_BASE_URL = 'http://127.0.0.1:8000';

const state = {
  activeTab: 'dashboard',
  candidates: [],
  jobDescriptions: [],
  leaderboard: [],
  selectedCandidate: null,
  selectedPdfFile: null,
  selectedZipFile: null
};

// Default Mock Data for Standalone Preview Mode (Fallback when API DB is empty)
const MOCK_JOB_DESCRIPTIONS = [
  {
    jd_id: "JD_AI_ENGINEER_01",
    role: "Senior AI / ML Engineer",
    seniority: "Senior",
    company_overview: "Leading AI research startup building real-time LLM systems and vector retrieval pipelines.",
    required_skills: ["Python", "PyTorch", "FastAPI", "Vector DB / FAISS", "Docker"],
    preferred_skills: ["LangChain", "Kubernetes", "AWS S3", "CUDA"],
    responsibilities: ["Build high-throughput RAG search infrastructure", "Optimize vector embeddings using SentenceTransformers", "Deploy containerized ML microservices on Kubernetes"],
    minimum_years_experience: 4
  },
  {
    jd_id: "JD_FULLSTACK_DEV_02",
    role: "Full Stack Engineer",
    seniority: "Mid",
    company_overview: "Enterprise SaaS platform scaling developer productivity tools.",
    required_skills: ["TypeScript", "React", "Node.js", "PostgreSQL", "REST APIs"],
    preferred_skills: ["TailwindCSS", "Docker", "GraphQL", "Redis"],
    responsibilities: ["Develop responsive frontend UI components", "Design database schemas and SQL queries", "Implement RESTful backend endpoints"],
    minimum_years_experience: 2
  }
];

const MOCK_CANDIDATES = [
  {
    candidate_id: "CAND_ALEX_RIVER_9F2A",
    name: "Alex River",
    email: "alex.river@example.com",
    phone: "+1 (555) 234-5678",
    location: "San Francisco, CA",
    target_role: "Senior AI / ML Engineer",
    total_experience_years: 5.5,
    skills: ["Python", "PyTorch", "FastAPI", "FAISS", "Docker", "AWS S3", "LangChain", "PostgreSQL"],
    work_experience: [
      { title: "Lead ML Engineer", company: "NeuroTech Systems", duration: "2022 - Present", description: "Architected FAISS vector search engine indexing 500k+ documents." },
      { title: "AI Research Associate", company: "VisionAI Labs", duration: "2019 - 2022", description: "Fine-tuned Transformer models for semantic parsing and text extraction." }
    ],
    education: [
      { degree: "M.S. Computer Science & AI", institution: "Stanford University", year: "2019" }
    ],
    projects: [
      { name: "CV-Ranker Vector Engine", description: "Multi-signal resume match algorithm using BERT embeddings and FAISS index." }
    ],
    s3_url: "https://example-s3-bucket.s3.amazonaws.com/resumes/CAND_ALEX_RIVER_9F2A/Alex_River_Resume.pdf"
  },
  {
    candidate_id: "CAND_SARA_CHEN_8B3C",
    name: "Dr. Sara Chen",
    email: "sara.chen@example.com",
    phone: "+1 (555) 876-5432",
    location: "Seattle, WA",
    target_role: "Principal Data Scientist",
    total_experience_years: 7.0,
    skills: ["Python", "PyTorch", "Scikit-Learn", "FastAPI", "PostgreSQL", "Docker", "Kubernetes", "NLP"],
    work_experience: [
      { title: "Staff Data Scientist", company: "CloudScale AI", duration: "2020 - Present", description: "Managed candidate ranking algorithms and skill graph recommendation engines." }
    ],
    education: [
      { degree: "Ph.D. Computer Vision & NLP", institution: "UW Seattle", year: "2017" }
    ],
    projects: [
      { name: "Automated Resume Parser", description: "Deep learning NER model extracting contact info and skills from unstructured PDFs." }
    ],
    s3_url: "https://example-s3-bucket.s3.amazonaws.com/resumes/CAND_SARA_CHEN_8B3C/Sara_Chen_Resume.pdf"
  },
  {
    candidate_id: "CAND_MARCUS_VANCE_4D1E",
    name: "Marcus Vance",
    email: "marcus.vance@example.com",
    phone: "+1 (555) 345-6789",
    location: "Austin, TX",
    target_role: "Full Stack Engineer",
    total_experience_years: 3.0,
    skills: ["TypeScript", "React", "Node.js", "PostgreSQL", "Docker", "GraphQL"],
    work_experience: [
      { title: "Full Stack Developer", company: "SaaSify Inc", duration: "2021 - Present", description: "Built scalable web dashboards and backend REST API integration." }
    ],
    education: [
      { degree: "B.S. Software Engineering", institution: "UT Austin", year: "2021" }
    ],
    projects: [
      { name: "Recruiter Analytics Dashboard", description: "Real-time candidate tracking web application." }
    ],
    s3_url: "https://example-s3-bucket.s3.amazonaws.com/resumes/CAND_MARCUS_VANCE_4D1E/Marcus_Vance_CV.pdf"
  }
];

// Initialize Application on DOM Ready
document.addEventListener('DOMContentLoaded', async () => {
  initNavigation();
  initDragAndDrop();
  initFormListeners();
  await checkApiHealth();
  loadInitialData();
});

/* ==========================================================================
   NAVIGATION & TAB SYSTEM
   ========================================================================== */
function initNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const tabName = item.getAttribute('data-tab');
      switchTab(tabName);
    });
  });
}

function switchTab(tabName) {
  state.activeTab = tabName;

  // Update Sidebar Active Class
  document.querySelectorAll('.nav-item').forEach(btn => {
    if (btn.getAttribute('data-tab') === tabName) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // Switch Tab View Section
  document.querySelectorAll('.tab-view').forEach(view => {
    if (view.id === tabName) {
      view.classList.add('active');
    } else {
      view.classList.remove('active');
    }
  });

  // Refresh tab specific content if needed
  if (tabName === 'dashboard') {
    renderDashboard();
  } else if (tabName === 'jobd') {
    renderJobDescriptions();
  } else if (tabName === 'candidates') {
    fetchCandidates();
  } else if (tabName === 'ranking') {
    populateJdDropdown('rankingJdSelect');
  }
}

/* ==========================================================================
   API CONNECTION & INITIAL DATA LOADING
   ========================================================================== */
async function checkApiHealth() {
  const statusText = document.getElementById('apiConnectionText');
  const statusDot = document.querySelector('.status-dot');

  // Candidate backend URLs to probe automatically
  const possibleUrls = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'http://127.0.0.1:8080',
    'http://localhost:8080',
    window.location.origin
  ];

  for (const url of possibleUrls) {
    if (!url || url.startsWith('file:')) continue;
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 6000);

      const res = await fetch(`${url}/api/jobd/job-descriptions`, {
        method: 'GET',
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (res.ok) {
        API_BASE_URL = url;
        const port = new URL(url).port || '80';
        if (statusText) statusText.innerText = `Connected (Port ${port})`;
        if (statusDot) statusDot.className = 'status-dot online';
        console.log(`[API Health] Successfully connected to FastAPI backend at ${url}`);
        return true;
      }
    } catch (err) {
      console.warn(`[API Health] Could not reach ${url}:`, err.message);
    }
  }

  if (statusText) statusText.innerText = 'Backend Offline (Mock Data)';
  if (statusDot) statusDot.className = 'status-dot offline';
  return false;
}

async function loadInitialData() {
  await fetchJobDescriptions();
  await fetchCandidates();
  renderDashboard();
}

/* ==========================================================================
   JOB DESCRIPTIONS MANAGEMENT
   ========================================================================== */
async function fetchJobDescriptions() {
  try {
    console.log(`[Fetch JD] Fetching from ${API_BASE_URL}/api/jobd/job-descriptions...`);
    const res = await fetch(`${API_BASE_URL}/api/jobd/job-descriptions`);
    if (res.ok) {
      const data = await res.json();
      state.jobDescriptions = Array.isArray(data) ? data : [];
      console.log(`[Fetch JD] Loaded ${state.jobDescriptions.length} job descriptions from API.`);
    } else {
      console.warn(`[Fetch JD] Non-200 status: ${res.status}`);
      state.jobDescriptions = [];
    }
  } catch (e) {
    console.error(`[Fetch JD] Error fetching job descriptions:`, e);
    state.jobDescriptions = [];
  }
  
  renderJobDescriptions();
  populateJdDropdown('dashJdSelect');
  populateJdDropdown('rankingJdSelect');
  updateStatsCounters();
}

function renderJobDescriptions() {
  const container = document.getElementById('jdGridContainer');
  if (!container) return;

  if (state.jobDescriptions.length === 0) {
    container.innerHTML = `
      <div class="col-span-full glass-card text-center py-5">
        <i class="fa-solid fa-briefcase icon-header text-muted"></i>
        <h3>No Job Descriptions Created Yet</h3>
        <p class="text-muted">Click "Create Job Description" to post a new target opening.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = state.jobDescriptions.map(jd => {
    const reqSkills = Array.isArray(jd.required_skills) ? jd.required_skills : [];
    const prefSkills = Array.isArray(jd.preferred_skills) ? jd.preferred_skills : [];

    return `
      <div class="glass-card jd-card">
        <div>
          <div class="jd-title-row">
            <div>
              <h3>${escapeHtml(jd.role)}</h3>
              <span class="badge">${escapeHtml(jd.seniority)} Level</span>
            </div>
            <button class="btn-remove" onclick="deleteJobDescription('${escapeHtml(jd.jd_id)}')" title="Delete Job">
              <i class="fa-solid fa-trash-can"></i>
            </button>
          </div>
          <div class="jd-meta">
            <span><i class="fa-solid fa-hashtag"></i> ID: ${escapeHtml(jd.jd_id)}</span>
            <span><i class="fa-solid fa-clock"></i> ${jd.minimum_years_experience}+ Yrs Exp</span>
          </div>
          <p class="text-muted text-sm mb-3">${escapeHtml(jd.company_overview || '')}</p>

          <div class="mb-3">
            <span class="jd-section-label">Required Skills</span>
            <div class="skills-flex-wrap">
              ${reqSkills.map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join('')}
            </div>
          </div>

          ${prefSkills.length > 0 ? `
            <div class="mb-3">
              <span class="jd-section-label">Preferred Skills</span>
              <div class="skills-flex-wrap">
                ${prefSkills.map(s => `<span class="skill-tag" style="opacity:0.8;">${escapeHtml(s)}</span>`).join('')}
              </div>
            </div>
          ` : ''}
        </div>

        <button class="btn btn-secondary btn-full mt-3" onclick="quickMatchJob('${escapeHtml(jd.jd_id)}')">
          <i class="fa-solid fa-ranking-star color-blue"></i> Rank Candidates
        </button>
      </div>
    `;
  }).join('');
}

function populateJdDropdown(selectId) {
  const select = document.getElementById(selectId);
  if (!select) return;

  if (state.jobDescriptions.length === 0) {
    select.innerHTML = `<option value="">No job descriptions available</option>`;
    return;
  }

  select.innerHTML = `
    <option value="">-- Select Job Role --</option>
    ${state.jobDescriptions.map(jd => `
      <option value="${escapeHtml(jd.jd_id)}">${escapeHtml(jd.seniority)} ${escapeHtml(jd.role)} (${escapeHtml(jd.jd_id)})</option>
    `).join('')}
  `;
}

async function deleteJobDescription(jdId) {
  if (!confirm(`Are you sure you want to delete Job Description '${jdId}'?`)) return;

  try {
    const res = await fetch(`${API_BASE_URL}/api/jobd/job-descriptions/${jdId}`, { method: 'DELETE' });
    if (!res.ok) {
      throw new Error('Delete failed');
    }
    showToast('Job Description deleted successfully!', 'success');
  } catch (e) {
    showToast('Unable to delete the job description.', 'error');
    return;
  }

  await fetchJobDescriptions();
}

/* ==========================================================================
   CANDIDATE DATABASE & FILTERING
   ========================================================================== */
async function fetchCandidates(filters = {}) {
  const queryParams = new URLSearchParams();
  if (filters.search) queryParams.append('search', filters.search);
  if (filters.skill) queryParams.append('skill', filters.skill);
  if (filters.role) queryParams.append('role', filters.role);
  if (filters.minExp) queryParams.append('min_exp', filters.minExp);
  if (filters.maxExp) queryParams.append('max_exp', filters.maxExp);

  try {
    console.log(`[Fetch Candidates] Querying ${API_BASE_URL}/api/candidate/candidates...`);
    const res = await fetch(`${API_BASE_URL}/api/candidate/candidates?${queryParams.toString()}`);
    if (res.ok) {
      const data = await res.json();
      state.candidates = Array.isArray(data.candidates) ? data.candidates : [];
      console.log(`[Fetch Candidates] Loaded ${state.candidates.length} candidate records from backend database.`);
    } else {
      console.warn(`[Fetch Candidates] Non-200 response: ${res.status}`);
      state.candidates = [];
    }
  } catch (e) {
    console.error(`[Fetch Candidates] Error fetching candidates:`, e);
    state.candidates = [];
  }

  renderCandidatesGrid();
  updateStatsCounters();
}

function renderCandidatesGrid() {
  const container = document.getElementById('candidatesGridContainer');
  if (!container) return;

  if (state.candidates.length === 0) {
    container.innerHTML = `
      <div class="col-span-full glass-card text-center py-5">
        <i class="fa-solid fa-user-slash icon-header text-muted"></i>
        <h3>No Candidates Found</h3>
        <p class="text-muted">Try adjusting search filters or upload candidate resumes.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = state.candidates.map(c => {
    const skills = Array.isArray(c.skills) ? c.skills : [];
    const initials = c.name ? c.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() : 'CV';

    return `
      <div class="glass-card candidate-card">
        <div>
          <div class="cand-card-header">
            <div class="avatar-md">${initials}</div>
            <div>
              <h3 style="font-size: 1.05rem; font-weight:700;">${escapeHtml(c.name || 'Unknown')}</h3>
              <p class="text-primary" style="font-size: 0.8rem; font-weight:600;">${escapeHtml(c.target_role || 'Candidate')}</p>
            </div>
          </div>

          <div class="jd-meta">
            <span><i class="fa-solid fa-briefcase"></i> ${c.total_experience_years || 0} Yrs Exp</span>
            <span><i class="fa-solid fa-location-dot"></i> ${escapeHtml(c.location || 'Remote')}</span>
          </div>

          <div class="mb-3">
            <span class="jd-section-label">Extracted Skills</span>
            <div class="skills-flex-wrap">
              ${skills.slice(0, 5).map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join('')}
              ${skills.length > 5 ? `<span class="skill-tag">+${skills.length - 5} more</span>` : ''}
            </div>
          </div>
        </div>

        <div class="flex-row gap-2 mt-3">
          <button class="btn btn-secondary flex-1 btn-sm" onclick="openCandidateModal('${escapeHtml(c.candidate_id)}')">
            <i class="fa-solid fa-eye"></i> View Profile
          </button>
          <button class="btn btn-danger btn-sm" onclick="deleteCandidate('${escapeHtml(c.candidate_id)}')" title="Delete">
            <i class="fa-solid fa-trash-can"></i>
          </button>
        </div>
      </div>
    `;
  }).join('');
}

function openCandidateModal(candidateId) {
  const candidate = state.candidates.find(c => c.candidate_id === candidateId);
  
  if (!candidate) return;
  state.selectedCandidate = candidate;

  const initials = candidate.name ? candidate.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() : 'CV';
  document.getElementById('modalCandidateAvatar').innerText = initials;
  document.getElementById('modalCandidateName').innerText = candidate.name || 'Unknown';
  document.getElementById('modalCandidateRole').innerText = candidate.target_role || 'Candidate';
  document.getElementById('modalCandidateExp').innerHTML = `<i class="fa-solid fa-briefcase"></i> ${candidate.total_experience_years || 0} Years Exp`;
  document.getElementById('modalCandidateLocation').innerHTML = `<i class="fa-solid fa-location-dot"></i> ${escapeHtml(candidate.location || 'Remote')}`;
  document.getElementById('modalCandidateEmail').innerHTML = `<i class="fa-solid fa-envelope"></i> ${escapeHtml(candidate.email || 'N/A')}`;
  document.getElementById('modalCandidatePhone').innerHTML = `<i class="fa-solid fa-phone"></i> ${escapeHtml(candidate.phone || 'N/A')}`;

  // Skills
  const skills = Array.isArray(candidate.skills) ? candidate.skills : [];
  document.getElementById('modalCandidateSkills').innerHTML = skills.map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join('');

  // Work Experience
  const work = Array.isArray(candidate.work_experience) ? candidate.work_experience : [];
  document.getElementById('modalCandidateWork').innerHTML = work.length > 0 ? work.map(w => `
    <div class="timeline-item">
      <div class="timeline-title">${escapeHtml(w.title || 'Role')} - <span class="text-primary">${escapeHtml(w.company || '')}</span></div>
      <div class="timeline-sub">${escapeHtml(w.duration || '')}</div>
      <p class="text-sm text-muted mt-1">${escapeHtml(Array.isArray(w.bullet_points) ? w.bullet_points.join(' ') : w.description || '')}</p>
    </div>
  `).join('') : '<p class="text-muted">No explicit work experience timeline logged.</p>';

  // Education
  const edu = Array.isArray(candidate.education) ? candidate.education : [];
  document.getElementById('modalCandidateEdu').innerHTML = edu.length > 0 ? edu.map(e => `
      <div class="timeline-item" style="border-left-color: var(--accent-green);">
        <div class="timeline-title">${escapeHtml(e.degree || 'Degree')}</div>
      <div class="timeline-sub">${escapeHtml(e.university || e.institution || '')} (${escapeHtml(e.year || '')})</div>
    </div>
  `).join('') : '<p class="text-muted">No education details recorded.</p>';

  // Projects
  const proj = Array.isArray(candidate.projects) ? candidate.projects : [];
  document.getElementById('modalCandidateProjects').innerHTML = proj.length > 0 ? proj.map(p => `
    <div class="timeline-item" style="border-left-color: var(--accent-orange);">
      <div class="timeline-title">${escapeHtml(p.name || 'Project')}</div>
      <p class="text-sm text-muted mt-1">${escapeHtml(Array.isArray(p.bullet_points) ? p.bullet_points.join(' ') : p.description || '')}</p>
    </div>
  `).join('') : '<p class="text-muted">No projects specified.</p>';

  // S3 URL
  const s3Btn = document.getElementById('modalS3LinkBtn');
  if (candidate.s3_url) {
    s3Btn.href = candidate.s3_url;
    s3Btn.classList.remove('hidden');
  } else {
    s3Btn.classList.add('hidden');
  }

  // Show Modal
  document.getElementById('candidateModal').classList.remove('hidden');
}

async function deleteCandidate(candidateId) {
  if (!confirm(`Delete candidate '${candidateId}' from PostgreSQL, S3, and FAISS index?`)) return;

  try {
    const res = await fetch(`${API_BASE_URL}/api/candidate/candidates/${candidateId}`, { method: 'DELETE' });
    if (!res.ok) {
      throw new Error('Delete failed');
    }
    showToast('Candidate successfully deleted from database & FAISS vector store!', 'success');
  } catch (e) {
    showToast('Unable to delete the candidate.', 'error');
    return;
  }

  await fetchCandidates();
  renderDashboard();
  closeCandidateModal();
}

function closeCandidateModal() {
  document.getElementById('candidateModal').classList.add('hidden');
}

/* ==========================================================================
   AI CANDIDATE RANKING LEADERBOARD
   ========================================================================== */
async function executeRanking() {
  const jdId = document.getElementById('rankingJdSelect').value;
  const topK = document.getElementById('topKSelect').value;

  if (!jdId) {
    showToast('Please select a Job Description to run AI ranking.', 'error');
    return;
  }

  const resultsContainer = document.getElementById('rankingResultsContainer');
  resultsContainer.innerHTML = `
    <div class="glass-card text-center py-5">
      <div class="spinner"></div>
      <h3 class="mt-3">Computing Multi-Signal FAISS Embeddings...</h3>
      <p class="text-muted">Calculating cosine similarity, skill gap overlap, experience alignment, and composite scores.</p>
    </div>
  `;

  try {
    const res = await fetch(`${API_BASE_URL}/api/ranking/rank?jd_id=${jdId}&top_k=${topK}`, { method: 'POST' });
    if (!res.ok) {
      const error = await res.json().catch(() => ({}));
      throw new Error(error.detail || 'Ranking request failed');
    }
    const data = await res.json();
    renderLeaderboardResults(data);
  } catch (e) {
    resultsContainer.innerHTML = `
      <div class="glass-card text-center py-5">
        <i class="fa-solid fa-triangle-exclamation icon-header text-muted"></i>
        <h3>Ranking Unavailable</h3>
        <p class="text-muted">${escapeHtml(e.message)}</p>
      </div>
    `;
    showToast('Unable to run candidate ranking.', 'error');
  }
}

function renderLeaderboardResults(data) {
  const container = document.getElementById('rankingResultsContainer');
  const leaderboard = data.leaderboard || [];

  if (leaderboard.length === 0) {
    container.innerHTML = `
      <div class="glass-card text-center py-5">
        <i class="fa-solid fa-triangle-exclamation icon-header text-muted"></i>
        <h3>No Candidates Ranked</h3>
        <p class="text-muted">Ensure candidates are uploaded and parsed in FAISS vector store.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="card-header mb-4">
      <div>
        <h3><i class="fa-solid fa-trophy color-orange"></i> Leaderboard for: ${escapeHtml(data.job_title || data.jd_id)}</h3>
        <p class="text-muted text-sm">${data.total_candidates_ranked} candidates evaluated via multi-signal vector scoring</p>
      </div>
      <span class="badge positive"><i class="fa-solid fa-check"></i> FAISS Vector Match</span>
    </div>

    <div class="leaderboard-list">
      ${leaderboard.map(item => {
        const scores = item.section_scores || {};
        const missing = item.missing_required_skills || [];
        const rankClass = item.rank <= 3 ? `rank-${item.rank}` : '';
        const medal = item.rank === 1 ? '🥇' : item.rank === 2 ? '🥈' : item.rank === 3 ? '🥉' : `#${item.rank}`;
        const vectorScore = normalizeScore(scores.vector_similarity);
        const skillsScore = normalizeScore(scores.combined_skills);
        const experienceScore = normalizeScore(scores.elastic_experience);
        const educationScore = normalizeScore(scores.education_pedigree);

        return `
          <div class="glass-card candidate-rank-card ${rankClass}">
            <div class="rank-badge-box">
              <span style="font-size: 1.1rem;">${medal}</span>
            </div>

            <div class="candidate-main-info">
              <div class="candidate-name-row">
                <h3>${escapeHtml(item.name || 'Candidate')}</h3>
                <span class="badge">${item.total_experience_years || 0} Yrs Exp</span>
              </div>
              <p class="text-muted text-sm mt-1">${escapeHtml(item.target_role || '')} • ${escapeHtml(item.email || '')}</p>
              
              ${missing.length > 0 ? `
                <div class="mt-2">
                  <span class="jd-section-label" style="color:#f87171;">Missing Required Skills:</span>
                  <div class="skills-flex-wrap">
                    ${missing.map(m => `<span class="skill-tag missing"><i class="fa-solid fa-xmark"></i> ${escapeHtml(m)}</span>`).join('')}
                  </div>
                </div>
              ` : `
                <div class="mt-2">
                  <span class="badge positive"><i class="fa-solid fa-circle-check"></i> 100% Required Skills Covered</span>
                </div>
              `}
            </div>

            <div class="score-breakdown-box">
              <div class="score-item">
                <div class="score-item-label">
                  <span>Semantic Vector Match</span>
                  <span>${vectorScore}%</span>
                </div>
                <div class="progress-bar-bg">
                  <div class="progress-bar-fill" style="width: ${vectorScore}%;"></div>
                </div>
              </div>

              <div class="score-item">
                <div class="score-item-label">
                  <span>Skill Alignment</span>
                  <span>${skillsScore}%</span>
                </div>
                <div class="progress-bar-bg">
                  <div class="progress-bar-fill" style="width: ${skillsScore}%; background: linear-gradient(90deg, #10b981, #059669);"></div>
                </div>
              </div>

              <div class="score-item">
                <div class="score-item-label">
                  <span>Experience Score</span>
                  <span>${experienceScore}%</span>
                </div>
                <div class="progress-bar-bg">
                  <div class="progress-bar-fill" style="width: ${experienceScore}%; background: linear-gradient(90deg, #f59e0b, #d97706);"></div>
                </div>
              </div>

              <div class="score-item">
                <div class="score-item-label">
                  <span>Education Score</span>
                  <span>${educationScore}%</span>
                </div>
                <div class="progress-bar-bg">
                  <div class="progress-bar-fill" style="width: ${educationScore}%; background: linear-gradient(90deg, #8b5cf6, #7c3aed);"></div>
                </div>
              </div>
            </div>

            <div class="score-composite-ring">
              <span class="ring-score-val">${Math.round(item.composite_score || 85)}%</span>
              <span class="stat-label">Composite</span>
              <button class="btn btn-secondary btn-sm mt-2" onclick="openCandidateModal('${escapeHtml(item.candidate_id)}')">
                Details
              </button>
            </div>
          </div>
        `;
      }).join('')}
    </div>
  `;
}

function quickMatchJob(jdId) {
  switchTab('ranking');
  const select = document.getElementById('rankingJdSelect');
  if (select) select.value = jdId;
  executeRanking();
}

/* ==========================================================================
   RESUME FILE UPLOAD PORTAL
   ========================================================================== */
function initDragAndDrop() {
  // PDF Dropzone
  const pdfDropZone = document.getElementById('pdfDropZone');
  const pdfInput = document.getElementById('pdfFileInput');
  
  pdfDropZone.addEventListener('click', () => pdfInput.click());
  pdfDropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    pdfDropZone.classList.add('dragover');
  });
  pdfDropZone.addEventListener('dragleave', () => pdfDropZone.classList.remove('dragover'));
  pdfDropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    pdfDropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
      handlePdfFileSelection(e.dataTransfer.files[0]);
    }
  });
  pdfInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handlePdfFileSelection(e.target.files[0]);
    }
  });

  // ZIP Dropzone
  const zipDropZone = document.getElementById('zipDropZone');
  const zipInput = document.getElementById('zipFileInput');

  zipDropZone.addEventListener('click', () => zipInput.click());
  zipDropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    zipDropZone.classList.add('dragover');
  });
  zipDropZone.addEventListener('dragleave', () => zipDropZone.classList.remove('dragover'));
  zipDropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    zipDropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
      handleZipFileSelection(e.dataTransfer.files[0]);
    }
  });
  zipInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleZipFileSelection(e.target.files[0]);
    }
  });

  // Remove File Buttons
  document.getElementById('removePdfBtn').addEventListener('click', () => {
    state.selectedPdfFile = null;
    document.getElementById('pdfFilePreview').classList.add('hidden');
    document.getElementById('pdfDropZone').classList.remove('hidden');
    pdfInput.value = '';
  });

  document.getElementById('removeZipBtn').addEventListener('click', () => {
    state.selectedZipFile = null;
    document.getElementById('zipFilePreview').classList.add('hidden');
    document.getElementById('zipDropZone').classList.remove('hidden');
    zipInput.value = '';
  });
}

function handlePdfFileSelection(file) {
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    showToast('Please select a valid .PDF resume file.', 'error');
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    showToast('PDF files must be 10 MiB or smaller.', 'error');
    return;
  }
  state.selectedPdfFile = file;
  document.getElementById('pdfFileName').innerText = file.name;
  document.getElementById('pdfFileSize').innerText = (file.size / (1024 * 1024)).toFixed(2) + ' MB';
  document.getElementById('pdfDropZone').classList.add('hidden');
  document.getElementById('pdfFilePreview').classList.remove('hidden');
}

function handleZipFileSelection(file) {
  if (!file.name.toLowerCase().endsWith('.zip')) {
    showToast('Please select a valid .ZIP file archive.', 'error');
    return;
  }
  if (file.size > 50 * 1024 * 1024) {
    showToast('ZIP archives must be 50 MiB or smaller.', 'error');
    return;
  }
  state.selectedZipFile = file;
  document.getElementById('zipFileName').innerText = file.name;
  document.getElementById('zipFileSize').innerText = (file.size / (1024 * 1024)).toFixed(2) + ' MB';
  document.getElementById('zipDropZone').classList.add('hidden');
  document.getElementById('zipFilePreview').classList.remove('hidden');
}

async function uploadPdfFile() {
  if (!state.selectedPdfFile) return;

  const file = state.selectedPdfFile;
  const formData = new FormData();
  formData.append('file', file);

  logConsole(`Uploading ${file.name} to FastAPI upload endpoint...`);
  document.getElementById('uploadStatusBadge').innerText = 'Uploading...';
  document.getElementById('uploadStatusBadge').className = 'badge warning';

  try {
    const res = await fetch(`${API_BASE_URL}/api/upload/upload-file/`, {
      method: 'POST',
      body: formData
    });

    if (res.ok) {
      const data = await res.json();
      logConsole(`SUCCESS: ${data.msg}`);
      logConsole(`Generated Candidate ID: ${data.candidate_id}`);
      logConsole(`S3 Storage URL: ${data.url}`);
      showToast('Resume uploaded! Background parsing & FAISS indexing started.', 'success');
    } else {
      const errData = await res.json();
      throw new Error(errData.detail || 'Upload failed');
    }
  } catch (err) {
    logConsole(`ERROR: ${err.message}`);
    showToast(`Resume upload failed: ${err.message}`, 'error');
    document.getElementById('uploadStatusBadge').innerText = 'Failed';
    document.getElementById('uploadStatusBadge').className = 'badge';
    return;
  }

  document.getElementById('uploadStatusBadge').innerText = 'Completed';
  document.getElementById('uploadStatusBadge').className = 'badge positive';
  document.getElementById('removePdfBtn').click();
}

async function uploadZipFile() {
  if (!state.selectedZipFile) return;

  const file = state.selectedZipFile;
  const formData = new FormData();
  formData.append('file', file);

  logConsole(`Uploading Zip archive ${file.name}...`);
  document.getElementById('uploadStatusBadge').innerText = 'Processing ZIP...';

  try {
    const res = await fetch(`${API_BASE_URL}/api/upload/upload-zip-file/`, {
      method: 'POST',
      body: formData
    });

    if (res.ok) {
      const data = await res.json();
      logConsole(`SUCCESS: ${data.msg}`);
      logConsole(`S3 Zip URL: ${data.url}`);
      showToast('ZIP archive uploaded to S3. It is not parsed automatically.', 'info');
    } else {
      const errData = await res.json();
      throw new Error(errData.detail || 'ZIP upload failed');
    }
  } catch (err) {
    logConsole(`ERROR: ${err.message}`);
    showToast(`ZIP upload failed: ${err.message}`, 'error');
    document.getElementById('uploadStatusBadge').innerText = 'Failed';
    document.getElementById('uploadStatusBadge').className = 'badge';
    return;
  }

  document.getElementById('uploadStatusBadge').innerText = 'Completed';
  document.getElementById('removeZipBtn').click();
}

function logConsole(msg) {
  const consoleBox = document.getElementById('uploadConsoleLog');
  if (!consoleBox) return;

  const timestamp = new Date().toLocaleTimeString();
  const line = document.createElement('div');
  line.className = 'console-line';
  line.innerHTML = `<span class="timestamp">[${timestamp}]</span> ${escapeHtml(msg)}`;
  consoleBox.appendChild(line);
  consoleBox.scrollTop = consoleBox.scrollHeight;
}

/* ==========================================================================
   FORM LISTENERS & MODAL CONTROLS
   ========================================================================== */
function initFormListeners() {
  // Upload Buttons
  document.getElementById('uploadPdfSubmitBtn').addEventListener('click', uploadPdfFile);
  document.getElementById('uploadZipSubmitBtn').addEventListener('click', uploadZipFile);

  // Add Job Description Modal
  const openJdBtn = document.getElementById('openAddJdModalBtn');
  const openJdBtn2 = document.getElementById('openJdModalBtn2');
  const closeJdBtn = document.getElementById('closeAddJdModalBtn');
  const cancelJdBtn = document.getElementById('cancelAddJdBtn');
  const addJdModal = document.getElementById('addJdModal');

  const openJdModal = () => addJdModal.classList.remove('hidden');
  const closeJdModal = () => addJdModal.classList.add('hidden');

  if (openJdBtn) openJdBtn.addEventListener('click', openJdModal);
  if (openJdBtn2) openJdBtn2.addEventListener('click', openJdModal);
  if (closeJdBtn) closeJdBtn.addEventListener('click', closeJdModal);
  if (cancelJdBtn) cancelJdBtn.addEventListener('click', closeJdModal);

  // Submit New Job Description Form
  document.getElementById('addJdForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const reqSkills = document.getElementById('jdReqSkillsInput').value.split(',').map(s => s.trim()).filter(Boolean);
    const prefSkills = document.getElementById('jdPrefSkillsInput').value.split(',').map(s => s.trim()).filter(Boolean);
    const resp = document.getElementById('jdRespInput').value.split(/[\n,]/).map(s => s.trim()).filter(Boolean);

    const newJd = {
      jd_id: document.getElementById('jdIdInput').value.trim(),
      role: document.getElementById('jdRoleInput').value.trim(),
      seniority: document.getElementById('jdSeniorityInput').value,
      company_overview: document.getElementById('jdOverviewInput').value.trim(),
      required_skills: reqSkills,
      preferred_skills: prefSkills,
      responsibilities: resp,
      minimum_years_experience: parseFloat(document.getElementById('jdExpInput').value) || 0
    };

    try {
      const res = await fetch(`${API_BASE_URL}/api/jobd/job-descriptions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newJd)
      });

      if (res.ok) {
        showToast('Job Description created successfully!', 'success');
      } else {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to save job description');
      }
    } catch (err) {
      showToast(`Unable to create the job description: ${err.message}`, 'error');
      return;
    }

    await fetchJobDescriptions();
    closeJdModal();
    document.getElementById('addJdForm').reset();
  });

  // Candidate Detail Modal Close
  document.getElementById('closeCandidateModalBtn').addEventListener('click', closeCandidateModal);
  document.getElementById('modalDeleteCandBtn').addEventListener('click', () => {
    if (state.selectedCandidate) {
      deleteCandidate(state.selectedCandidate.candidate_id);
    }
  });

  // Ranking Execution Button
  document.getElementById('executeRankingBtn').addEventListener('click', executeRanking);

  // Dashboard Instant Match Button
  document.getElementById('dashRunMatchBtn').addEventListener('click', () => {
    const jdId = document.getElementById('dashJdSelect').value;
    if (jdId) quickMatchJob(jdId);
    else showToast('Please select a Job Role to match', 'error');
  });

  // Database Filter Buttons
  document.getElementById('applyFiltersBtn').addEventListener('click', () => {
    const filters = {
      search: document.getElementById('filterSearchInput').value.trim(),
      skill: document.getElementById('filterSkillInput').value.trim(),
      role: document.getElementById('filterRoleInput').value.trim(),
      minExp: document.getElementById('filterMinExpInput').value.trim()
    };
    fetchCandidates(filters);
  });

  document.getElementById('resetFiltersBtn').addEventListener('click', () => {
    document.getElementById('filterSearchInput').value = '';
    document.getElementById('filterSkillInput').value = '';
    document.getElementById('filterRoleInput').value = '';
    document.getElementById('filterMinExpInput').value = '';
    fetchCandidates();
  });

  // Global Header Search Bar
  document.getElementById('globalSearchInput').addEventListener('keyup', (e) => {
    if (e.key === 'Enter') {
      const query = e.target.value.trim();
      switchTab('candidates');
      document.getElementById('filterSearchInput').value = query;
      fetchCandidates({ search: query });
    }
  });

  // Refresh Button
  document.getElementById('refreshDataBtn').addEventListener('click', () => {
    showToast('Refreshing system database...', 'info');
    loadInitialData();
  });
}

/* ==========================================================================
   DASHBOARD RENDER & UTILITIES
   ========================================================================== */
function renderDashboard() {
  updateStatsCounters();

  const tableBody = document.getElementById('recentCandidatesTableBody');
  if (!tableBody) return;

  const recent = state.candidates.slice(0, 5);

  if (recent.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="5" class="text-center py-4 text-muted">
          No candidates stored in database yet.
        </td>
      </tr>
    `;
    return;
  }

  tableBody.innerHTML = recent.map(c => {
    const skills = Array.isArray(c.skills) ? c.skills : [];
    return `
      <tr>
        <td>
          <div style="font-weight:600;">${escapeHtml(c.name || 'Candidate')}</div>
          <div class="text-muted" style="font-size:0.75rem;">${escapeHtml(c.email || '')}</div>
        </td>
        <td><span class="badge">${escapeHtml(c.target_role || 'Developer')}</span></td>
        <td>${c.total_experience_years || 0} Yrs</td>
        <td>
          <div class="skills-flex-wrap">
            ${skills.slice(0, 3).map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join('')}
          </div>
        </td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="openCandidateModal('${escapeHtml(c.candidate_id)}')">
            <i class="fa-solid fa-eye"></i>
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

function updateStatsCounters() {
  document.getElementById('statTotalCandidates').innerText = state.candidates.length;
  document.getElementById('statTotalJds').innerText = state.jobDescriptions.length;
  document.getElementById('statIndexedResumes').innerText = state.candidates.length;
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  const icon = type === 'success' ? 'fa-circle-check' : type === 'error' ? 'fa-triangle-exclamation' : 'fa-circle-info';
  toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${escapeHtml(message)}</span>`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function normalizeScore(value) {
  const numericValue = Number(value);
  if (!Number.isFinite(numericValue)) return 0;
  return Math.round(Math.min(100, Math.max(0, numericValue)));
}
