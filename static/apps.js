const API = "/api";

const jobsList = document.getElementById("jobsList");
const emptyState = document.getElementById("emptyState");
const year = document.getElementById("year");
year.textContent = new Date().getFullYear();

document.getElementById("searchBtn").addEventListener("click", loadJobs);
document.getElementById("refreshBtn").addEventListener("click", () => {
  document.getElementById("q").value = "";
  document.getElementById("city").value = "";
  loadJobs();
});

document.getElementById("postForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const msg = document.getElementById("postMsg");
  msg.textContent = "Posting...";

  const form = new FormData(e.target);
  const payload = Object.fromEntries(form.entries());

  // fix numeric fields
  payload.pay_amount = Number(payload.pay_amount);
  if (payload.duration_hours) payload.duration_hours = Number(payload.duration_hours);
  else payload.duration_hours = null;

  const res = await fetch(`${API}/jobs`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    msg.textContent = "Error posting job ❌";
    return;
  }

  e.target.reset();
  msg.textContent = "Job posted ✅";
  await loadJobs();
  location.hash = "#jobs";
});

async function loadJobs(){
  const q = document.getElementById("q").value.trim();
  const city = document.getElementById("city").value.trim();

  const url = new URL(`${location.origin}${API}/jobs`);
  if (q) url.searchParams.set("q", q);
  if (city) url.searchParams.set("city", city);

  const res = await fetch(url.toString());
  const jobs = await res.json();

  jobsList.innerHTML = "";
  if (!jobs.length){
    emptyState.style.display = "block";
    return;
  }
  emptyState.style.display = "none";

  for (const j of jobs){
    const div = document.createElement("div");
    div.className = "job";
    div.innerHTML = `
      <h4>${escapeHtml(j.title)}</h4>
      <div class="meta">${escapeHtml(j.city)} • ${escapeHtml(j.category)} • <strong>$${j.pay_amount}</strong> (${escapeHtml(j.pay_type)})</div>
      <div class="small">${j.description ? escapeHtml(j.description) : "No description."}</div>

      <div class="actions" style="margin-top:10px;">
        <button class="btn btn--primary" data-apply="${j.id}">Apply</button>
        <a class="btn btn--ghost" href="#post">Post a job</a>
      </div>

      <div class="apply" style="display:none;margin-top:10px;" id="apply-${j.id}">
        <input placeholder="Your name" id="name-${j.id}" />
        <input placeholder="Phone or email" id="contact-${j.id}" />
        <textarea placeholder="Message (optional)" id="msg-${j.id}"></textarea>
        <button class="btn btn--primary" data-send="${j.id}">Send application</button>
        <div class="small" id="status-${j.id}"></div>
      </div>
    `;
    jobsList.appendChild(div);
  }

  // Apply toggles
  document.querySelectorAll("[data-apply]").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-apply");
      const box = document.getElementById(`apply-${id}`);
      box.style.display = box.style.display === "none" ? "block" : "none";
    });
  });

  // Send application
  document.querySelectorAll("[data-send]").forEach(btn => {
    btn.addEventListener("click", async () => {
      const id = btn.getAttribute("data-send");
      const status = document.getElementById(`status-${id}`);
      status.textContent = "Sending...";

      const payload = {
        name: document.getElementById(`name-${id}`).value.trim(),
        phone_or_email: document.getElementById(`contact-${id}`).value.trim(),
        message: document.getElementById(`msg-${id}`).value.trim()
      };

      const res = await fetch(`${API}/jobs/${id}/apply`, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify(payload)
      });

      if (!res.ok){
        status.textContent = "Error ❌";
        return;
      }
      status.textContent = "Sent ✅";
    });
  });
}

function escapeHtml(s){
  return String(s)
    .replaceAll("&","&amp;")
    .replaceAll("<","&lt;")
    .replaceAll(">","&gt;")
    .replaceAll('"',"&quot;")
    .replaceAll("'","&#039;");
}

loadJobs();