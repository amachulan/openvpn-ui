(() => {
  const tokenKey = "vpnctl_api_token";
  const $ = (sel) => document.querySelector(sel);

  const statusEl = $("#status");
  const tokenInput = $("#token");

  function showStatus(message, kind = "") {
    statusEl.hidden = !message;
    statusEl.textContent = message || "";
    statusEl.className = `status ${kind}`.trim();
  }

  function getToken() {
    return localStorage.getItem(tokenKey) || "";
  }

  function setToken(value) {
    localStorage.setItem(tokenKey, value);
  }

  async function api(path, options = {}) {
    const headers = Object.assign({}, options.headers || {});
    const token = getToken();
    if (!token && !path.endsWith("/health")) {
      throw new Error("Paste API token (from /etc/vpnctl/config.yaml) and click Save");
    }
    if (token) headers.Authorization = `Bearer ${token}`;
    let resp;
    try {
      resp = await fetch(path, { ...options, headers });
    } catch (err) {
      throw new Error(
        `Cannot reach API (${err.message}). Check: systemctl status vpnctl; api.host=0.0.0.0; firewall port 8080`
      );
    }
    const contentType = resp.headers.get("content-type") || "";
    let body = null;
    if (contentType.includes("application/json")) {
      body = await resp.json();
    } else if (resp.ok && options.expectBlob) {
      body = await resp.blob();
    } else {
      body = await resp.text();
    }
    if (!resp.ok) {
      const detail =
        body && typeof body === "object" ? body.detail || JSON.stringify(body) : body;
      throw new Error(detail || `HTTP ${resp.status}`);
    }
    return body;
  }

  function fmtBytes(n) {
    const v = Number(n) || 0;
    if (v < 1024) return `${v} B`;
    if (v < 1024 ** 2) return `${(v / 1024).toFixed(1)} KB`;
    if (v < 1024 ** 3) return `${(v / 1024 ** 2).toFixed(1)} MB`;
    return `${(v / 1024 ** 3).toFixed(1)} GB`;
  }

  function switchTab(name) {
    document.querySelectorAll(".tab").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.tab === name);
    });
    document.querySelectorAll(".panel").forEach((panel) => {
      panel.classList.toggle("active", panel.id === `panel-${name}`);
    });
    if (name === "clients") loadClients();
    if (name === "sessions") loadSessions();
    if (name === "audit") loadAudit();
  }

  async function loadClients() {
    const tbody = $("#clients-body");
    tbody.innerHTML = `<tr><td colspan="6">Loading…</td></tr>`;
    try {
      const clients = await api("/api/v1/clients");
      const warnDays = 30;
      const expiry = clients.filter(
        (c) => c.status === "valid" && c.days_remaining != null && c.days_remaining <= warnDays
      );
      const banner = $("#expiry-banner");
      if (expiry.length) {
        banner.hidden = false;
        banner.textContent = `Expiring soon: ${expiry
          .map((c) => `${c.cn} (${c.days_remaining}d)`)
          .join(", ")}`;
      } else {
        banner.hidden = true;
      }
      if (!clients.length) {
        tbody.innerHTML = `<tr><td colspan="6">No client certificates in PKI.</td></tr>`;
        return;
      }
      tbody.innerHTML = "";
      for (const c of clients) {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><strong>${escapeHtml(c.cn)}</strong></td>
          <td><span class="badge ${escapeHtml(c.status)}">${escapeHtml(c.status)}</span></td>
          <td>${escapeHtml(c.expires_at || "—")}${
            c.days_remaining != null ? ` (${c.days_remaining}d)` : ""
          }</td>
          <td>${escapeHtml(c.label || "")}</td>
          <td><span class="badge ${c.online ? "online" : "offline"}">${
            c.online ? "online" : "offline"
          }</span></td>
          <td class="actions"></td>
        `;
        const actions = tr.querySelector(".actions");
        if (c.status === "valid") {
          const dl = button("Download", "secondary", async () => {
            const blob = await api(`/api/v1/clients/${encodeURIComponent(c.cn)}/ovpn`, {
              expectBlob: true,
            });
            downloadBlob(blob, `${c.cn}.ovpn`);
          });
          const rev = button("Revoke", "danger", async () => {
            if (!confirm(`Revoke ${c.cn}?`)) return;
            await api(`/api/v1/clients/${encodeURIComponent(c.cn)}/revoke`, {
              method: "POST",
            });
            showStatus(`Revoked ${c.cn}`, "ok");
            loadClients();
          });
          actions.append(dl, rev);
        }
        tbody.appendChild(tr);
      }
      showStatus("");
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="6">${escapeHtml(err.message)}</td></tr>`;
      showStatus(err.message, "error");
    }
  }

  async function loadSessions() {
    const tbody = $("#sessions-body");
    tbody.innerHTML = `<tr><td colspan="6">Loading…</td></tr>`;
    try {
      const sessions = await api("/api/v1/sessions");
      if (!sessions.length) {
        tbody.innerHTML = `<tr><td colspan="6">No active sessions.</td></tr>`;
        return;
      }
      tbody.innerHTML = "";
      for (const s of sessions) {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><strong>${escapeHtml(s.cn)}</strong></td>
          <td>${escapeHtml(s.real_address || "")}</td>
          <td>${escapeHtml(s.virtual_address || "")}</td>
          <td>${escapeHtml(s.connected_since || "")}</td>
          <td>↓ ${fmtBytes(s.bytes_received)} / ↑ ${fmtBytes(s.bytes_sent)}</td>
          <td class="actions"></td>
        `;
        const kick = button("Disconnect", "danger", async () => {
          await api("/api/v1/sessions/disconnect", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              cn: s.cn,
              client_id: s.client_id || "",
              real_address: s.real_address || "",
            }),
          });
          showStatus(`Disconnected ${s.cn}`, "ok");
          loadSessions();
        });
        tr.querySelector(".actions").append(kick);
        tbody.appendChild(tr);
      }
      showStatus("");
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="6">${escapeHtml(err.message)}</td></tr>`;
      showStatus(err.message, "error");
    }
  }

  async function loadAudit() {
    const tbody = $("#audit-body");
    tbody.innerHTML = `<tr><td colspan="4">Loading…</td></tr>`;
    try {
      const events = await api("/api/v1/audit?limit=100");
      if (!events.length) {
        tbody.innerHTML = `<tr><td colspan="4">No events yet.</td></tr>`;
        return;
      }
      tbody.innerHTML = "";
      for (const e of events) {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td>${escapeHtml(e.ts)}</td>
          <td>${escapeHtml(e.action)}</td>
          <td>${escapeHtml(e.cn || "")}</td>
          <td>${escapeHtml(e.detail || "")}</td>
        `;
        tbody.appendChild(tr);
      }
      showStatus("");
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="4">${escapeHtml(err.message)}</td></tr>`;
      showStatus(err.message, "error");
    }
  }

  function button(label, cls, onClick) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = label;
    if (cls) btn.className = cls;
    btn.addEventListener("click", async () => {
      btn.disabled = true;
      try {
        await onClick();
      } catch (err) {
        showStatus(err.message, "error");
      } finally {
        btn.disabled = false;
      }
    });
    return btn;
  }

  function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  document.querySelectorAll(".tab").forEach((btn) => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
  });

  $("#save-token").addEventListener("click", () => {
    setToken(tokenInput.value.trim());
    showStatus("Token saved in this browser", "ok");
    loadClients();
  });

  $("#refresh-clients").addEventListener("click", loadClients);
  $("#refresh-sessions").addEventListener("click", loadSessions);
  $("#refresh-audit").addEventListener("click", loadAudit);

  $("#issue-form").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const fd = new FormData(ev.target);
    const body = {
      cn: String(fd.get("cn") || "").trim(),
      days: Number(fd.get("days") || 3650),
      label: String(fd.get("label") || ""),
      notes: String(fd.get("notes") || ""),
      email: String(fd.get("email") || ""),
      telegram_chat_id: String(fd.get("telegram_chat_id") || ""),
      deliver_email: Boolean(fd.get("deliver_email")),
      deliver_telegram: Boolean(fd.get("deliver_telegram")),
    };
    try {
      const result = await api("/api/v1/clients", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      showStatus(`Issued ${result.cn}`, "ok");
      ev.target.reset();
      switchTab("clients");
    } catch (err) {
      showStatus(err.message, "error");
    }
  });

  tokenInput.value = getToken();
  loadClients();
})();
