(() => {
  const tokenKey = "vpnctl_api_token";
  const themeKey = "vpnctl_theme";
  const langKey = "vpnctl_lang";
  const $ = (sel) => document.querySelector(sel);

  const I18N = {
    en: {
      tag: "OpenVPN Community management",
      token_label: "API token",
      token_placeholder: "Bearer token",
      save: "Save",
      tab_clients: "Clients",
      tab_issue: "Issue",
      tab_sessions: "Sessions",
      tab_audit: "Audit",
      clients_title: "Clients",
      sessions_title: "Sessions",
      audit_title: "Audit",
      issue_title: "Issue client",
      refresh: "Refresh",
      col_cn: "CN",
      col_status: "Status",
      col_expires: "Expires",
      col_label: "Label",
      col_online: "Online",
      col_real: "Real address",
      col_virtual: "Virtual IP",
      col_since: "Since",
      col_traffic: "Traffic",
      col_time: "Time",
      col_action: "Action",
      col_detail: "Detail",
      form_cn: "Client name",
      form_days: "Validity (days)",
      form_label: "Label",
      form_notes: "Notes",
      form_email: "Email",
      form_telegram: "Telegram chat id",
      form_deliver_email: "Email .ovpn after issue",
      form_deliver_telegram: "Telegram .ovpn after issue",
      form_issue: "Issue",
      loading: "Loading…",
      no_clients: "No client certificates in PKI.",
      no_sessions: "No active sessions.",
      no_events: "No events yet.",
      download: "Download",
      revoke: "Revoke",
      disconnect: "Disconnect",
      online: "online",
      offline: "offline",
      status_valid: "valid",
      status_revoked: "revoked",
      status_expired: "expired",
      expiry_soon: "Expiring soon",
      days_short: "d",
      token_saved: "Token saved in this browser",
      token_missing: "Paste API token (from /etc/vpnctl/config.yaml) and click Save",
      api_unreachable: "Cannot reach API ({msg}). Check: systemctl status vpnctl; api.host=0.0.0.0; firewall port 8080",
      revoke_confirm: "Revoke {cn}?",
      revoked: "Revoked {cn}",
      issued: "Issued {cn}",
      disconnected: "Disconnected {cn}",
      theme_to_light: "Light theme",
      theme_to_dark: "Dark theme",
      lang_title: "Switch to Russian",
    },
    ru: {
      tag: "Управление OpenVPN Community",
      token_label: "API-токен",
      token_placeholder: "Bearer-токен",
      save: "Сохранить",
      tab_clients: "Клиенты",
      tab_issue: "Выпуск",
      tab_sessions: "Сессии",
      tab_audit: "Аудит",
      clients_title: "Клиенты",
      sessions_title: "Сессии",
      audit_title: "Аудит",
      issue_title: "Выпуск клиента",
      refresh: "Обновить",
      col_cn: "CN",
      col_status: "Статус",
      col_expires: "Истекает",
      col_label: "Метка",
      col_online: "Онлайн",
      col_real: "Внешний адрес",
      col_virtual: "VPN IP",
      col_since: "С",
      col_traffic: "Трафик",
      col_time: "Время",
      col_action: "Действие",
      col_detail: "Детали",
      form_cn: "Имя клиента",
      form_days: "Срок (дней)",
      form_label: "Метка",
      form_notes: "Заметки",
      form_email: "Email",
      form_telegram: "Telegram chat id",
      form_deliver_email: "Отправить .ovpn по email",
      form_deliver_telegram: "Отправить .ovpn в Telegram",
      form_issue: "Выпустить",
      loading: "Загрузка…",
      no_clients: "Нет клиентских сертификатов в PKI.",
      no_sessions: "Нет активных сессий.",
      no_events: "Пока нет событий.",
      download: "Скачать",
      revoke: "Отозвать",
      disconnect: "Отключить",
      online: "онлайн",
      offline: "офлайн",
      status_valid: "действ.",
      status_revoked: "отозван",
      status_expired: "истёк",
      expiry_soon: "Скоро истекают",
      days_short: "д",
      token_saved: "Токен сохранён в этом браузере",
      token_missing: "Вставьте API-токен из /etc/vpnctl/config.yaml и нажмите «Сохранить»",
      api_unreachable: "Нет доступа к API ({msg}). Проверьте: systemctl status vpnctl; api.host=0.0.0.0; firewall :8080",
      revoke_confirm: "Отозвать {cn}?",
      revoked: "Отозван {cn}",
      issued: "Выпущен {cn}",
      disconnected: "Отключён {cn}",
      theme_to_light: "Светлая тема",
      theme_to_dark: "Тёмная тема",
      lang_title: "Switch to English",
    },
  };

  const statusEl = $("#status");
  const tokenInput = $("#token");
  const themeToggle = $("#theme-toggle");
  const langToggle = $("#lang-toggle");

  function t(key, vars = {}) {
    const lang = currentLang();
    let text = (I18N[lang] && I18N[lang][key]) || I18N.en[key] || key;
    Object.entries(vars).forEach(([k, v]) => {
      text = text.replaceAll(`{${k}}`, String(v));
    });
    return text;
  }

  function currentLang() {
    return document.documentElement.getAttribute("data-lang") === "ru" ? "ru" : "en";
  }

  function currentTheme() {
    return document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark";
  }

  function applyI18n() {
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (key) el.textContent = t(key);
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      const key = el.getAttribute("data-i18n-placeholder");
      if (key) el.setAttribute("placeholder", t(key));
    });
    if (langToggle) {
      langToggle.textContent = currentLang() === "ru" ? "EN" : "RU";
      langToggle.title = t("lang_title");
      langToggle.setAttribute("aria-label", t("lang_title"));
    }
    applyTheme(currentTheme());
  }

  function applyLang(lang) {
    const next = lang === "ru" ? "ru" : "en";
    document.documentElement.setAttribute("data-lang", next);
    document.documentElement.lang = next;
    localStorage.setItem(langKey, next);
    applyI18n();
  }

  function initLang() {
    const saved = localStorage.getItem(langKey);
    if (saved === "ru" || saved === "en") {
      applyLang(saved);
      return;
    }
    applyLang((navigator.language || "").toLowerCase().startsWith("ru") ? "ru" : "en");
  }

  function applyTheme(theme) {
    const next = theme === "light" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem(themeKey, next);
    if (themeToggle) {
      themeToggle.textContent = next === "dark" ? "☀" : "☾";
      themeToggle.title = next === "dark" ? t("theme_to_light") : t("theme_to_dark");
      themeToggle.setAttribute("aria-label", themeToggle.title);
    }
  }

  function initTheme() {
    const saved = localStorage.getItem(themeKey);
    if (saved === "light" || saved === "dark") {
      applyTheme(saved);
      return;
    }
    applyTheme(
      window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark"
    );
  }

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

  function statusLabel(status) {
    if (status === "valid") return t("status_valid");
    if (status === "revoked") return t("status_revoked");
    if (status === "expired") return t("status_expired");
    return status;
  }

  async function api(path, options = {}) {
    const headers = Object.assign({}, options.headers || {});
    const token = getToken();
    if (!token && !path.endsWith("/health")) {
      throw new Error(t("token_missing"));
    }
    if (token) headers.Authorization = `Bearer ${token}`;
    let resp;
    try {
      resp = await fetch(path, { ...options, headers });
    } catch (err) {
      throw new Error(t("api_unreachable", { msg: err.message }));
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

  function activeTab() {
    const active = document.querySelector(".tab.active");
    return active ? active.dataset.tab : "clients";
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
    tbody.innerHTML = `<tr><td colspan="6">${escapeHtml(t("loading"))}</td></tr>`;
    try {
      const clients = await api("/api/v1/clients");
      const warnDays = 30;
      const expiry = clients.filter(
        (c) => c.status === "valid" && c.days_remaining != null && c.days_remaining <= warnDays
      );
      const banner = $("#expiry-banner");
      if (expiry.length) {
        banner.hidden = false;
        banner.textContent = `${t("expiry_soon")}: ${expiry
          .map((c) => `${c.cn} (${c.days_remaining}${t("days_short")})`)
          .join(", ")}`;
      } else {
        banner.hidden = true;
      }
      if (!clients.length) {
        tbody.innerHTML = `<tr><td colspan="6">${escapeHtml(t("no_clients"))}</td></tr>`;
        return;
      }
      tbody.innerHTML = "";
      for (const c of clients) {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><strong>${escapeHtml(c.cn)}</strong></td>
          <td><span class="badge ${escapeHtml(c.status)}">${escapeHtml(statusLabel(c.status))}</span></td>
          <td>${escapeHtml(c.expires_at || "—")}${
            c.days_remaining != null ? ` (${c.days_remaining}${t("days_short")})` : ""
          }</td>
          <td>${escapeHtml(c.label || "")}</td>
          <td><span class="badge ${c.online ? "online" : "offline"}">${
            c.online ? t("online") : t("offline")
          }</span></td>
          <td class="actions"></td>
        `;
        const actions = tr.querySelector(".actions");
        if (c.status === "valid") {
          const dl = button(t("download"), "secondary", async () => {
            const blob = await api(`/api/v1/clients/${encodeURIComponent(c.cn)}/ovpn`, {
              expectBlob: true,
            });
            downloadBlob(blob, `${c.cn}.ovpn`);
          });
          const rev = button(t("revoke"), "danger", async () => {
            if (!confirm(t("revoke_confirm", { cn: c.cn }))) return;
            await api(`/api/v1/clients/${encodeURIComponent(c.cn)}/revoke`, {
              method: "POST",
            });
            showStatus(t("revoked", { cn: c.cn }), "ok");
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
    tbody.innerHTML = `<tr><td colspan="6">${escapeHtml(t("loading"))}</td></tr>`;
    try {
      const sessions = await api("/api/v1/sessions");
      if (!sessions.length) {
        tbody.innerHTML = `<tr><td colspan="6">${escapeHtml(t("no_sessions"))}</td></tr>`;
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
        const kick = button(t("disconnect"), "danger", async () => {
          await api("/api/v1/sessions/disconnect", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              cn: s.cn,
              client_id: s.client_id || "",
              real_address: s.real_address || "",
            }),
          });
          showStatus(t("disconnected", { cn: s.cn }), "ok");
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
    tbody.innerHTML = `<tr><td colspan="4">${escapeHtml(t("loading"))}</td></tr>`;
    try {
      const events = await api("/api/v1/audit?limit=100");
      if (!events.length) {
        tbody.innerHTML = `<tr><td colspan="4">${escapeHtml(t("no_events"))}</td></tr>`;
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
    showStatus(t("token_saved"), "ok");
    loadClients();
  });

  themeToggle.addEventListener("click", () => {
    applyTheme(currentTheme() === "light" ? "dark" : "light");
  });

  langToggle.addEventListener("click", () => {
    applyLang(currentLang() === "ru" ? "en" : "ru");
    const tab = activeTab();
    if (tab === "clients") loadClients();
    else if (tab === "sessions") loadSessions();
    else if (tab === "audit") loadAudit();
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
      showStatus(t("issued", { cn: result.cn }), "ok");
      ev.target.reset();
      switchTab("clients");
    } catch (err) {
      showStatus(err.message, "error");
    }
  });

  tokenInput.value = getToken();
  initTheme();
  initLang();
  loadClients();
})();
