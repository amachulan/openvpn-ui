(() => {
  const tokenKey = "openvpn_ui_api_token";
  const themeKey = "openvpn_ui_theme";
  const langKey = "openvpn_ui_lang";
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
      tab_server: "Server",
      tab_audit: "Audit",
      tab_settings: "Notification settings",
      clients_title: "Clients",
      sessions_title: "Sessions",
      server_title: "OpenVPN server",
      audit_title: "Audit",
      settings_title: "Notification settings",
      settings_hint: "Saved to /etc/openvpn-ui/config.yaml. Leave password/token blank to keep the current value.",
      settings_mail: "Email (SMTP)",
      settings_telegram: "Telegram",
      settings_enabled: "Enabled",
      settings_smtp_host: "SMTP host",
      settings_smtp_port: "SMTP port",
      settings_smtp_user: "SMTP user",
      settings_smtp_password: "SMTP password",
      settings_use_tls: "STARTTLS",
      settings_from_addr: "From address",
      settings_subject: "Subject",
      settings_bot_token: "Bot token",
      settings_chat_id: "Default chat id",
      settings_secret_keep: "Leave blank to keep",
      settings_secret_set: "saved — leave blank to keep",
      settings_save: "Save notifications",
      settings_saved: "Notification settings saved",
      server_hint: "Edits write server.conf (with backup). OpenVPN must be restarted to apply most changes.",
      server_network: "Network & policy",
      server_crypto: "Crypto",
      server_port: "Port",
      server_proto: "Protocol",
      server_duplicate_cn: "Allow same cert on multiple devices",
      server_client_to_client: "Client-to-client",
      server_redirect_gateway: "Route internet through VPN",
      server_dns: "DNS (one per line)",
      server_local_networks: "Local networks CIDR (one per line)",
      server_tls_mode: "TLS mode (read-only)",
      server_cipher: "Cipher",
      server_data_ciphers: "data-ciphers",
      server_auth: "auth",
      server_tls_min: "tls-version-min",
      server_restart_after: "Restart OpenVPN after save",
      server_save: "Save server settings",
      server_saved: "Server settings saved",
      server_restart: "Restart OpenVPN",
      server_restart_confirm: "Restart OpenVPN now? Active sessions will drop briefly.",
      server_restarted: "OpenVPN restarted",
      server_raw_title: "Advanced: raw server.conf",
      server_raw_label: "server.conf",
      server_raw_save: "Save raw conf",
      server_raw_confirm: "Overwrite server.conf with this raw text?",
      server_raw_saved: "Raw server.conf saved",
      server_backups_title: "Backups",
      server_restore: "Restore",
      server_restore_confirm: "Restore backup {id}? Current conf will be backed up first.",
      server_restored: "Backup restored",
      server_unit: "Unit",
      server_state: "State",
      server_pid: "PID",
      col_backup: "Backup",
      col_size: "Size",
      no_backups: "No backups yet.",
      renew: "Renew",
      renew_confirm: "Renew certificate for {cn}?",
      renewed: "Renewed {cn}",
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
      token_missing: "Paste API token (from /etc/openvpn-ui/config.yaml) and click Save",
      api_unreachable: "Cannot reach API ({msg}). Check: systemctl status openvpn-ui; api.host=0.0.0.0; firewall port 8080",
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
      tab_server: "Сервер",
      tab_audit: "Аудит",
      tab_settings: "Настройки уведомлений",
      clients_title: "Клиенты",
      sessions_title: "Сессии",
      server_title: "Сервер OpenVPN",
      audit_title: "Аудит",
      settings_title: "Настройки уведомлений",
      settings_hint: "Сохраняется в /etc/openvpn-ui/config.yaml. Пустой пароль/токен — оставить текущее значение.",
      settings_mail: "Почта (SMTP)",
      settings_telegram: "Telegram",
      settings_enabled: "Включено",
      settings_smtp_host: "SMTP-хост",
      settings_smtp_port: "SMTP-порт",
      settings_smtp_user: "SMTP-пользователь",
      settings_smtp_password: "SMTP-пароль",
      settings_use_tls: "STARTTLS",
      settings_from_addr: "Адрес отправителя",
      settings_subject: "Тема письма",
      settings_bot_token: "Токен бота",
      settings_chat_id: "Chat id по умолчанию",
      settings_secret_keep: "Оставьте пустым, чтобы не менять",
      settings_secret_set: "сохранён — оставьте пустым, чтобы не менять",
      settings_save: "Сохранить уведомления",
      settings_saved: "Настройки уведомлений сохранены",
      server_hint: "Изменения пишутся в server.conf (с бэкапом). Для применения обычно нужен restart OpenVPN.",
      server_network: "Сеть и политика",
      server_crypto: "Крипто",
      server_port: "Порт",
      server_proto: "Протокол",
      server_duplicate_cn: "Один сертификат на нескольких устройствах",
      server_client_to_client: "Клиент-клиент",
      server_redirect_gateway: "Интернет через VPN",
      server_dns: "DNS (по одному в строке)",
      server_local_networks: "Локальные сети CIDR (по одному в строке)",
      server_tls_mode: "TLS-режим (только чтение)",
      server_cipher: "Cipher",
      server_data_ciphers: "data-ciphers",
      server_auth: "auth",
      server_tls_min: "tls-version-min",
      server_restart_after: "Перезапустить OpenVPN после сохранения",
      server_save: "Сохранить настройки сервера",
      server_saved: "Настройки сервера сохранены",
      server_restart: "Перезапустить OpenVPN",
      server_restart_confirm: "Перезапустить OpenVPN сейчас? Активные сессии кратко оборвутся.",
      server_restarted: "OpenVPN перезапущен",
      server_raw_title: "Дополнительно: сырой server.conf",
      server_raw_label: "server.conf",
      server_raw_save: "Сохранить сырой conf",
      server_raw_confirm: "Перезаписать server.conf этим текстом?",
      server_raw_saved: "Сырой server.conf сохранён",
      server_backups_title: "Резервные копии",
      server_restore: "Восстановить",
      server_restore_confirm: "Восстановить бэкап {id}? Текущий conf сначала сохранится.",
      server_restored: "Бэкап восстановлен",
      server_unit: "Юнит",
      server_state: "Состояние",
      server_pid: "PID",
      col_backup: "Бэкап",
      col_size: "Размер",
      no_backups: "Пока нет бэкапов.",
      renew: "Продлить",
      renew_confirm: "Продлить сертификат {cn}?",
      renewed: "Продлён {cn}",
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
      token_missing: "Вставьте API-токен из /etc/openvpn-ui/config.yaml и нажмите «Сохранить»",
      api_unreachable: "Нет доступа к API ({msg}). Проверьте: systemctl status openvpn-ui; api.host=0.0.0.0; firewall :8080",
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
    if (name === "server") loadServer();
    if (name === "audit") loadAudit();
    if (name === "settings") loadSettings();
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
          const renewBtn = button(t("renew"), "secondary", async () => {
            if (!confirm(t("renew_confirm", { cn: c.cn }))) return;
            await api(`/api/v1/clients/${encodeURIComponent(c.cn)}/renew`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ days: 3650 }),
            });
            showStatus(t("renewed", { cn: c.cn }), "ok");
            loadClients();
          });
          const rev = button(t("revoke"), "danger", async () => {
            if (!confirm(t("revoke_confirm", { cn: c.cn }))) return;
            await api(`/api/v1/clients/${encodeURIComponent(c.cn)}/revoke`, {
              method: "POST",
            });
            showStatus(t("revoked", { cn: c.cn }), "ok");
            loadClients();
          });
          actions.append(dl, renewBtn, rev);
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

  function secretPlaceholder(isSet) {
    return isSet ? t("settings_secret_set") : t("settings_secret_keep");
  }

  async function loadSettings() {
    const form = $("#settings-form");
    if (!form) return;
    try {
      const data = await api("/api/v1/settings/notify");
      const mail = data.mail || {};
      const tg = data.telegram || {};
      form.mail_enabled.checked = Boolean(mail.enabled);
      form.smtp_host.value = mail.smtp_host || "";
      form.smtp_port.value = mail.smtp_port != null ? mail.smtp_port : 25;
      form.smtp_user.value = mail.smtp_user || "";
      form.smtp_password.value = "";
      form.smtp_password.placeholder = secretPlaceholder(mail.smtp_password_set);
      form.use_tls.checked = Boolean(mail.use_tls);
      form.from_addr.value = mail.from_addr || "";
      form.subject.value = mail.subject || "";
      form.tg_enabled.checked = Boolean(tg.enabled);
      form.bot_token.value = "";
      form.bot_token.placeholder = secretPlaceholder(tg.bot_token_set);
      form.chat_id.value = tg.chat_id || "";
      showStatus("");
    } catch (err) {
      showStatus(err.message, "error");
    }
  }

  function linesToList(text) {
    return String(text || "")
      .split(/\r?\n/)
      .map((s) => s.trim())
      .filter(Boolean);
  }

  async function loadServer() {
    const form = $("#server-form");
    const rawForm = $("#server-raw-form");
    const card = $("#server-service");
    try {
      const data = await api("/api/v1/server");
      const s = data.settings || {};
      const svc = data.service || {};
      if (card) {
        card.innerHTML = `
          <span><span class="muted">${escapeHtml(t("server_unit"))}:</span> ${escapeHtml(svc.unit || "—")}</span>
          <span><span class="muted">${escapeHtml(t("server_state"))}:</span>
            <span class="badge ${svc.running ? "online" : "offline"}">${escapeHtml(svc.active || "unknown")}</span>
          </span>
          <span><span class="muted">${escapeHtml(t("server_pid"))}:</span> ${escapeHtml(svc.main_pid || "—")}</span>
        `;
      }
      if (form) {
        form.port.value = s.port != null ? s.port : "";
        form.proto.value = s.proto || "udp";
        form.duplicate_cn.checked = Boolean(s.duplicate_cn);
        form.client_to_client.checked = Boolean(s.client_to_client);
        form.redirect_gateway.checked = Boolean(s.redirect_gateway);
        form.dns.value = (s.dns || []).join("\n");
        form.local_networks.value = (s.local_networks || []).join("\n");
        form.tls_mode.value = s.tls_mode || "none";
        form.cipher.value = s.cipher || "";
        form.data_ciphers.value = s.data_ciphers || "";
        form.auth.value = s.auth || "";
        form.tls_version_min.value = s.tls_version_min || "";
        form.restart.checked = false;
      }
      const raw = await api("/api/v1/server/conf");
      if (rawForm) {
        rawForm.content.value = raw.content || "";
        rawForm.restart.checked = false;
      }
      await loadBackups();
      showStatus("");
    } catch (err) {
      if (card) card.textContent = err.message;
      showStatus(err.message, "error");
    }
  }

  async function loadBackups() {
    const tbody = $("#backups-body");
    if (!tbody) return;
    tbody.innerHTML = `<tr><td colspan="4">${escapeHtml(t("loading"))}</td></tr>`;
    try {
      const rows = await api("/api/v1/server/backups");
      if (!rows.length) {
        tbody.innerHTML = `<tr><td colspan="4">${escapeHtml(t("no_backups"))}</td></tr>`;
        return;
      }
      tbody.innerHTML = "";
      for (const b of rows) {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><code>${escapeHtml(b.id)}</code></td>
          <td>${escapeHtml(b.mtime || "")}</td>
          <td>${escapeHtml(fmtBytes(b.size || 0))}</td>
          <td class="actions"></td>
        `;
        const restoreBtn = button(t("server_restore"), "secondary", async () => {
          if (!confirm(t("server_restore_confirm", { id: b.id }))) return;
          const restart = confirm(t("server_restart_confirm"));
          await api(`/api/v1/server/backups/${encodeURIComponent(b.id)}/restore`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ restart }),
          });
          showStatus(t("server_restored"), "ok");
          await loadServer();
        });
        tr.querySelector(".actions").append(restoreBtn);
        tbody.appendChild(tr);
      }
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="4">${escapeHtml(err.message)}</td></tr>`;
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
    else if (tab === "server") loadServer();
    else if (tab === "audit") loadAudit();
    else if (tab === "settings") loadSettings();
  });

  $("#refresh-clients").addEventListener("click", loadClients);
  $("#refresh-sessions").addEventListener("click", loadSessions);
  $("#refresh-server").addEventListener("click", loadServer);
  $("#refresh-backups").addEventListener("click", loadBackups);
  $("#refresh-audit").addEventListener("click", loadAudit);
  $("#refresh-settings").addEventListener("click", loadSettings);

  $("#restart-server").addEventListener("click", async () => {
    if (!confirm(t("server_restart_confirm"))) return;
    try {
      await api("/api/v1/server/restart", { method: "POST" });
      showStatus(t("server_restarted"), "ok");
      await loadServer();
    } catch (err) {
      showStatus(err.message, "error");
    }
  });

  $("#server-form").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const form = ev.target;
    const body = {
      port: Number(form.port.value || 0) || null,
      proto: String(form.proto.value || "").trim(),
      duplicate_cn: Boolean(form.duplicate_cn.checked),
      client_to_client: Boolean(form.client_to_client.checked),
      redirect_gateway: Boolean(form.redirect_gateway.checked),
      dns: linesToList(form.dns.value),
      local_networks: linesToList(form.local_networks.value),
      cipher: String(form.cipher.value || "").trim(),
      data_ciphers: String(form.data_ciphers.value || "").trim(),
      auth: String(form.auth.value || "").trim(),
      tls_version_min: String(form.tls_version_min.value || "").trim(),
      restart: Boolean(form.restart.checked),
    };
    try {
      await api("/api/v1/server", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      showStatus(t("server_saved"), "ok");
      await loadServer();
    } catch (err) {
      showStatus(err.message, "error");
    }
  });

  $("#server-raw-form").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    if (!confirm(t("server_raw_confirm"))) return;
    const form = ev.target;
    try {
      await api("/api/v1/server/conf", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: String(form.content.value || ""),
          restart: Boolean(form.restart.checked),
        }),
      });
      showStatus(t("server_raw_saved"), "ok");
      await loadServer();
    } catch (err) {
      showStatus(err.message, "error");
    }
  });

  $("#settings-form").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const form = ev.target;
    const body = {
      mail: {
        enabled: Boolean(form.mail_enabled.checked),
        smtp_host: String(form.smtp_host.value || "").trim(),
        smtp_port: Number(form.smtp_port.value || 25),
        smtp_user: String(form.smtp_user.value || "").trim(),
        smtp_password: String(form.smtp_password.value || ""),
        use_tls: Boolean(form.use_tls.checked),
        from_addr: String(form.from_addr.value || "").trim(),
        subject: String(form.subject.value || "").trim(),
      },
      telegram: {
        enabled: Boolean(form.tg_enabled.checked),
        bot_token: String(form.bot_token.value || ""),
        chat_id: String(form.chat_id.value || "").trim(),
      },
    };
    try {
      await api("/api/v1/settings/notify", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      showStatus(t("settings_saved"), "ok");
      await loadSettings();
    } catch (err) {
      showStatus(err.message, "error");
    }
  });

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
