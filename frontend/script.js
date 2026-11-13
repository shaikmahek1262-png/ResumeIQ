

const isLocal = ["localhost", "127.0.0.1", ""].includes(location.hostname);
const API_BASE = window.RESUMEIQ_API_BASE || (isLocal
    ? "http://127.0.0.1:5000"
    : "https://resumeiq-1-zmmx.onrender.com");
const STATIC_URL = "data/dashboard.json";

async function fetchDashboard() {
    if (API_BASE) {
        try {
            const res = await fetch(API_BASE + "/api/dashboard");
            if (res.ok) return { data: await res.json(), source: "Live database" };
        } catch (e) {
            console.warn("Backend unreachable, using bundled data.", e);
        }
    }
    const res = await fetch(STATIC_URL);
    if (!res.ok) throw new Error("Could not load dashboard data.");
    const data = await res.json();
    return { data, source: "Sample data" + (data.generated_at ? " (" + data.generated_at + ")" : "") };
}

let candidates = [];
let jobs = [];

async function loadDashboard() {
    const emptyMessage = document.getElementById("emptyMessage");
    emptyMessage.textContent = "Loading candidate results...";
    emptyMessage.style.display = "block";

    try {
        const { data, source } = await fetchDashboard();
        document.getElementById("dataSource").textContent = source;

        candidates = data.results || [];
        jobs = data.jobs || [];

        document.getElementById("totalCandidates").textContent =
            data.total_candidates;

        document.getElementById("totalJobs").textContent =
            data.total_jobs;

        document.getElementById("averageMatch").textContent =
            data.average_match + "%";

        displayCandidates(candidates);
        displayJobs();

    } catch (error) {
        emptyMessage.textContent =
            "Unable to load dashboard data.";
        emptyMessage.style.display = "block";

        console.error("Dashboard error:", error);
    }
}

function displayCandidates(data) {
    const table = document.getElementById("candidateTable");
    const emptyMessage = document.getElementById("emptyMessage");

    table.innerHTML = "";

    if (data.length === 0) {
        emptyMessage.textContent = "No matching candidates found.";
        emptyMessage.style.display = "block";
        return;
    }

    emptyMessage.style.display = "none";

    for (const candidate of data) {
        const row = document.createElement("tr");

        const nameCell = document.createElement("td");
        nameCell.textContent = candidate.name || "Unknown";

        const jobCell = document.createElement("td");
        jobCell.textContent = candidate.job || "Not assigned";

        const matchedCell = document.createElement("td");
        matchedCell.appendChild(
            createSkillElements(candidate.matched || [], false)
        );

        const missingCell = document.createElement("td");
        missingCell.appendChild(
            createSkillElements(candidate.missing || [], true)
        );

        const scoreCell = document.createElement("td");
        const score = Number(candidate.score) || 0;

        const scoreText = document.createElement("span");
        scoreText.className = "score";
        scoreText.textContent = score + "%";

        const bar = document.createElement("div");
        bar.className = "score-bar";

        const fill = document.createElement("div");
        fill.className = "score-fill";
        fill.style.width = Math.max(0, Math.min(100, score)) + "%";

        bar.appendChild(fill);
        scoreCell.append(scoreText, bar);

        row.append(
            nameCell,
            jobCell,
            matchedCell,
            missingCell,
            scoreCell
        );

        table.appendChild(row);
    }
}

function createSkillElements(skills, isMissing) {
    const container = document.createElement("div");

    if (skills.length === 0) {
        container.textContent = "None";
        return container;
    }

    for (const skill of skills) {
        const tag = document.createElement("span");
        tag.className = isMissing ? "skill missing" : "skill";
        tag.textContent = skill;
        container.appendChild(tag);
    }

    return container;
}

function displayJobs() {
    const jobList = document.getElementById("jobList");
    jobList.innerHTML = "";

    for (const job of jobs) {
        const card = document.createElement("div");
        card.className = "job-card";

        const title = document.createElement("h3");
        title.textContent = job.job_title;

        const description = document.createElement("p");
        description.textContent = job.job_description || "";

        const required = document.createElement("p");
        required.className = "required";

        const label = document.createElement("strong");
        label.textContent = "Required Skills: ";

        const skills = document.createElement("span");
        skills.textContent = job.required_skills || "Not specified";

        required.append(label, skills);
        card.append(title, description, required);
        jobList.appendChild(card);
    }
}

document.getElementById("searchInput").addEventListener(
    "input",
    function () {
        const searchText = this.value.toLowerCase();

        const filtered = candidates.filter(candidate =>
            (candidate.name || "").toLowerCase().includes(searchText) ||
            (candidate.job || "").toLowerCase().includes(searchText)
        );

        displayCandidates(filtered);
    }
);

loadDashboard();
