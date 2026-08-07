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
      tab_settings: "Notifications",
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
      server_dual_hint: "UDP and TCP share PKI/CCD and the same VPN subnet. Do not connect both profiles at once with one CN. Open the firewall for the secondary port.",
      server_network: "Network & policy",
      server_crypto: "Crypto",
      server_port: "Listen port",
      server_proto: "Protocol",
      server_external_host: "External host / IP (NAT)",
      server_external_port: "External port (NAT)",
      server_external_hint: "Written into client .ovpn remote. Leave empty to use template host and listen port.",
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
      server_restart_after: "Restart after save",
      server_save: "Save",
      server_saved: "Server settings saved",
      server_restart: "Restart",
      server_restart_confirm: "Restart this OpenVPN instance? Active sessions on it will drop briefly.",
      server_restarted: "OpenVPN instance restarted",
      server_enable: "Enable instance",
      server_enable_confirm: "Create conf and enable the {id} OpenVPN instance?",
      server_disable: "Disable",
      server_disable_confirm: "Disable the {id} instance? Conf file is kept.",
      server_enabled: "Instance enabled",
      server_disabled: "Instance disabled",
      server_raw_title: "Raw conf",
      server_raw_save: "Save raw",
      server_raw_confirm: "Overwrite this server conf with raw text?",
      server_raw_saved: "Raw conf saved",
      server_backups_title: "Backups",
      server_restore: "Restore",
      server_restore_confirm: "Restore backup {id}?",
      server_restored: "Backup restored",
      server_unit: "Unit",
      server_state: "State",
      server_primary: "primary",
      server_disabled_label: "disabled",
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
      form_deliver_email: "Email .ovpn after issue (all enabled profiles)",
      form_deliver_telegram: "Telegram .ovpn after issue (all enabled profiles)",
      form_issue: "Issue",
      loading: "Loading…",
      no_clients: "No client certificates in PKI.",
      no_sessions: "No active sessions.",
      no_events: "No events yet.",
      audit_action_issue: "Issue client",
      audit_action_revoke: "Revoke",
      audit_action_client_renew: "Renew certificate",
      audit_action_disconnect: "Disconnect session",
      audit_action_meta_update: "Update client meta",
      audit_action_deliver_email: "Email delivery",
      audit_action_deliver_telegram: "Telegram delivery",
      audit_action_settings_update: "Update notifications",
      audit_action_server_conf_update: "Update server conf",
      audit_action_server_enable: "Enable instance",
      audit_action_server_disable: "Disable instance",
      audit_action_server_restart: "Restart instance",
      audit_action_server_restore: "Restore backup",
      download: "Download",
      download_udp: "UDP",
      download_tcp: "TCP",
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
      tab_settings: "Уведомления",
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
      server_dual_hint: "UDP и TCP делят PKI/CCD и одну VPN-подсеть. Не подключайте оба профиля сразу с одним CN. Откройте firewall на вторичный порт.",
      server_network: "Сеть и политика",
      server_crypto: "Крипто",
      server_port: "Порт прослушивания",
      server_proto: "Протокол",
      server_external_host: "Внешний хост / IP (NAT)",
      server_external_port: "Внешний порт (NAT)",
      server_external_hint: "Пишется в remote клиентского .ovpn. Пусто = хост из шаблона и порт прослушивания.",
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
      server_restart_after: "Перезапустить после сохранения",
      server_save: "Сохранить",
      server_saved: "Настройки сервера сохранены",
      server_restart: "Перезапуск",
      server_restart_confirm: "Перезапустить этот инстанс OpenVPN? Его сессии кратко оборвутся.",
      server_restarted: "Инстанс OpenVPN перезапущен",
      server_enable: "Включить инстанс",
      server_enable_confirm: "Создать conf и включить инстанс {id}?",
      server_disable: "Выключить",
      server_disable_confirm: "Выключить инстанс {id}? Файл conf сохранится.",
      server_enabled: "Инстанс включён",
      server_disabled: "Инстанс выключен",
      server_raw_title: "Сырой conf",
      server_raw_save: "Сохранить conf",
      server_raw_confirm: "Перезаписать conf этим текстом?",
      server_raw_saved: "Сырой conf сохранён",
      server_backups_title: "Бэкапы",
      server_restore: "Восстановить",
      server_restore_confirm: "Восстановить бэкап {id}?",
      server_restored: "Бэкап восстановлен",
      server_unit: "Юнит",
      server_state: "Состояние",
      server_primary: "основной",
      server_disabled_label: "выключен",
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
      form_deliver_email: "Отправить .ovpn по email (все включённые профили)",
      form_deliver_telegram: "Отправить .ovpn в Telegram (все включённые профили)",
      form_issue: "Выпустить",
      loading: "Загрузка…",
      no_clients: "Нет клиентских сертификатов в PKI.",
      no_sessions: "Нет активных сессий.",
      no_events: "Пока нет событий.",
      audit_action_issue: "Выпуск клиента",
      audit_action_revoke: "Отзыв",
      audit_action_client_renew: "Продление сертификата",
      audit_action_disconnect: "Отключение сессии",
      audit_action_meta_update: "Обновление метки/заметок",
      audit_action_deliver_email: "Отправка по email",
      audit_action_deliver_telegram: "Отправка в Telegram",
      audit_action_settings_update: "Настройки уведомлений",
      audit_action_server_conf_update: "Изменение conf сервера",
      audit_action_server_enable: "Включение инстанса",
      audit_action_server_disable: "Выключение инстанса",
      audit_action_server_restart: "Перезапуск инстанса",
      audit_action_server_restore: "Восстановление бэкапа",
      download: "Скачать",
      download_udp: "UDP",
      download_tcp: "TCP",
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
          const profiles = Array.isArray(c.profiles) && c.profiles.length
            ? c.profiles
            : ["udp"];
          for (const proto of profiles) {
            const label = proto === "tcp" ? t("download_tcp") : t("download_udp");
            const dl = button(label, "secondary", async () => {
              const blob = await api(
                `/api/v1/clients/${encodeURIComponent(c.cn)}/ovpn?proto=${encodeURIComponent(proto)}`,
                { expectBlob: true }
              );
              downloadBlob(blob, `${c.cn}-${proto}.ovpn`);
            });
            actions.append(dl);
          }
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
          actions.append(renewBtn, rev);
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

  function auditActionLabel(action) {
    const key = `audit_action_${String(action || "").trim()}`;
    const label = t(key);
    return label === key ? String(action || "") : label;
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
          <td>${escapeHtml(auditActionLabel(e.action))}</td>
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

  function protoOptions(family, selected) {
    const opts = family === "tcp" ? ["tcp", "tcp6"] : ["udp", "udp6"];
    return opts
      .map(
        (p) =>
          `<option value="${p}" ${selected === p ? "selected" : ""}>${p}</option>`
      )
      .join("");
  }

  function renderInstanceCard(iid, inst) {
    const s = inst.settings || {};
    const svc = inst.service_status || {};
    const enabled = Boolean(inst.enabled);
    const card = document.createElement("div");
    card.className = "instance-card";
    card.dataset.instance = iid;
    const badges = [];
    if (inst.primary) badges.push(`<span class="badge online">${escapeHtml(t("server_primary"))}</span>`);
    if (!enabled) badges.push(`<span class="badge offline">${escapeHtml(t("server_disabled_label"))}</span>`);
    badges.push(
      `<span class="badge ${svc.running ? "online" : "offline"}">${escapeHtml(svc.active || "unknown")}</span>`
    );

    if (!enabled) {
      card.innerHTML = `
        <div class="panel-head">
          <h3>${escapeHtml(iid.toUpperCase())}</h3>
          <div class="actions">${badges.join(" ")}</div>
        </div>
        <p class="hint muted">${escapeHtml(inst.conf || "")}</p>
        <div class="actions" data-role="enable-actions"></div>
      `;
      const enableBtn = button(t("server_enable"), "", async () => {
        if (!confirm(t("server_enable_confirm", { id: iid.toUpperCase() }))) return;
        await api(`/api/v1/server/instances/${iid}/enable`, { method: "POST" });
        showStatus(t("server_enabled"), "ok");
        await loadServer();
      });
      card.querySelector("[data-role='enable-actions']").append(enableBtn);
      return card;
    }

    const selectedProto = s.proto || (iid === "tcp" ? "tcp" : "udp");
    card.innerHTML = `
      <div class="panel-head">
        <h3>${escapeHtml(iid.toUpperCase())}</h3>
        <div class="actions">${badges.join(" ")}</div>
      </div>
      <div class="service-meta muted">
        ${escapeHtml(t("server_unit"))}: ${escapeHtml(svc.unit || inst.service || "—")}
        · ${escapeHtml(inst.conf || "")}
      </div>
      <form class="form" data-role="settings">
        <label><span>${escapeHtml(t("server_port"))}</span> <input name="port" type="number" min="1" max="65535" value="${escapeHtml(s.port != null ? s.port : inst.port || "")}" /></label>
        <label><span>${escapeHtml(t("server_proto"))}</span>
          <select name="proto">${protoOptions(iid, selectedProto)}</select>
        </label>
        <label><span>${escapeHtml(t("server_external_host"))}</span> <input name="external_host" type="text" autocomplete="off" placeholder="vpn.example.com" value="${escapeHtml(inst.external_host || "")}" /></label>
        <label><span>${escapeHtml(t("server_external_port"))}</span> <input name="external_port" type="number" min="1" max="65535" placeholder="${escapeHtml(String(s.port != null ? s.port : inst.port || ""))}" value="${escapeHtml(inst.external_port != null ? inst.external_port : "")}" /></label>
        <p class="hint muted">${escapeHtml(t("server_external_hint"))}</p>
        <label class="check"><input name="duplicate_cn" type="checkbox" ${s.duplicate_cn ? "checked" : ""} /> <span>${escapeHtml(t("server_duplicate_cn"))}</span></label>
        <label class="check"><input name="client_to_client" type="checkbox" ${s.client_to_client ? "checked" : ""} /> <span>${escapeHtml(t("server_client_to_client"))}</span></label>
        <label class="check"><input name="redirect_gateway" type="checkbox" ${s.redirect_gateway ? "checked" : ""} /> <span>${escapeHtml(t("server_redirect_gateway"))}</span></label>
        <label><span>${escapeHtml(t("server_dns"))}</span> <textarea name="dns" rows="2">${escapeHtml((s.dns || []).join("\n"))}</textarea></label>
        <label><span>${escapeHtml(t("server_local_networks"))}</span> <textarea name="local_networks" rows="2">${escapeHtml((s.local_networks || []).join("\n"))}</textarea></label>
        <label><span>${escapeHtml(t("server_tls_mode"))}</span> <input name="tls_mode" readonly value="${escapeHtml(s.tls_mode || "none")}" /></label>
        <label><span>${escapeHtml(t("server_cipher"))}</span> <input name="cipher" value="${escapeHtml(s.cipher || "")}" /></label>
        <label><span>${escapeHtml(t("server_data_ciphers"))}</span> <input name="data_ciphers" value="${escapeHtml(s.data_ciphers || "")}" /></label>
        <label><span>${escapeHtml(t("server_auth"))}</span> <input name="auth" value="${escapeHtml(s.auth || "")}" /></label>
        <label><span>${escapeHtml(t("server_tls_min"))}</span> <input name="tls_version_min" value="${escapeHtml(s.tls_version_min || "")}" /></label>
        <label class="check"><input name="restart" type="checkbox" /> <span>${escapeHtml(t("server_restart_after"))}</span></label>
        <div class="actions" data-role="settings-actions"></div>
      </form>
      <form class="form" data-role="raw">
        <label><span>${escapeHtml(t("server_raw_title"))}</span> <textarea name="content" rows="8" spellcheck="false"></textarea></label>
        <label class="check"><input name="restart" type="checkbox" /> <span>${escapeHtml(t("server_restart_after"))}</span></label>
        <div class="actions" data-role="raw-actions"></div>
      </form>
      <div>
        <div class="panel-head subhead"><h3>${escapeHtml(t("server_backups_title"))}</h3></div>
        <div class="table-wrap"><table><tbody data-role="backups"></tbody></table></div>
      </div>
    `;

    const settingsForm = card.querySelector("form[data-role='settings']");
    const saveBtn = button(t("server_save"), "", async () => {
      const fd = new FormData(settingsForm);
      const externalPortRaw = String(fd.get("external_port") || "").trim();
      const body = {
        port: Number(fd.get("port") || 0) || null,
        proto: String(fd.get("proto") || "").trim(),
        external_host: String(fd.get("external_host") || "").trim(),
        external_port: externalPortRaw ? Number(externalPortRaw) : null,
        duplicate_cn: Boolean(fd.get("duplicate_cn")),
        client_to_client: Boolean(fd.get("client_to_client")),
        redirect_gateway: Boolean(fd.get("redirect_gateway")),
        dns: linesToList(fd.get("dns")),
        local_networks: linesToList(fd.get("local_networks")),
        cipher: String(fd.get("cipher") || "").trim(),
        data_ciphers: String(fd.get("data_ciphers") || "").trim(),
        auth: String(fd.get("auth") || "").trim(),
        tls_version_min: String(fd.get("tls_version_min") || "").trim(),
        restart: Boolean(fd.get("restart")),
      };
      await api(`/api/v1/server/instances/${iid}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      showStatus(t("server_saved"), "ok");
      await loadServer();
    });
    const restartBtn = button(t("server_restart"), "danger", async () => {
      if (!confirm(t("server_restart_confirm"))) return;
      await api(`/api/v1/server/instances/${iid}/restart`, { method: "POST" });
      showStatus(t("server_restarted"), "ok");
      await loadServer();
    });
    const settingsActions = card.querySelector("[data-role='settings-actions']");
    settingsActions.append(saveBtn, restartBtn);
    if (!inst.primary) {
      const disableBtn = button(t("server_disable"), "secondary", async () => {
        if (!confirm(t("server_disable_confirm", { id: iid.toUpperCase() }))) return;
        await api(`/api/v1/server/instances/${iid}/disable`, { method: "POST" });
        showStatus(t("server_disabled"), "ok");
        await loadServer();
      });
      settingsActions.append(disableBtn);
    }

    const rawForm = card.querySelector("form[data-role='raw']");
    api(`/api/v1/server/instances/${iid}/conf`)
      .then((raw) => {
        rawForm.content.value = raw.content || "";
      })
      .catch((err) => showStatus(err.message, "error"));
    const rawSave = button(t("server_raw_save"), "danger", async () => {
      if (!confirm(t("server_raw_confirm"))) return;
      await api(`/api/v1/server/instances/${iid}/conf`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: String(rawForm.content.value || ""),
          restart: Boolean(rawForm.restart.checked),
        }),
      });
      showStatus(t("server_raw_saved"), "ok");
      await loadServer();
    });
    card.querySelector("[data-role='raw-actions']").append(rawSave);

    const backupsBody = card.querySelector("[data-role='backups']");
    api(`/api/v1/server/instances/${iid}/backups`)
      .then((rows) => {
        if (!rows.length) {
          backupsBody.innerHTML = `<tr><td>${escapeHtml(t("no_backups"))}</td></tr>`;
          return;
        }
        backupsBody.innerHTML = "";
        for (const b of rows.slice(0, 8)) {
          const tr = document.createElement("tr");
          tr.innerHTML = `<td><code>${escapeHtml(b.id)}</code></td><td class="actions"></td>`;
          const restoreBtn = button(t("server_restore"), "secondary", async () => {
            if (!confirm(t("server_restore_confirm", { id: b.id }))) return;
            const restart = confirm(t("server_restart_confirm"));
            await api(
              `/api/v1/server/instances/${iid}/backups/${encodeURIComponent(b.id)}/restore`,
              {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ restart }),
              }
            );
            showStatus(t("server_restored"), "ok");
            await loadServer();
          });
          tr.querySelector(".actions").append(restoreBtn);
          backupsBody.appendChild(tr);
        }
      })
      .catch((err) => {
        backupsBody.innerHTML = `<tr><td>${escapeHtml(err.message)}</td></tr>`;
      });

    return card;
  }

  async function loadServer() {
    const grid = $("#server-instances");
    const hint = $("#server-hint");
    if (!grid) return;
    grid.innerHTML = `<p>${escapeHtml(t("loading"))}</p>`;
    try {
      const data = await api("/api/v1/server");
      if (hint) hint.textContent = t("server_dual_hint");
      grid.innerHTML = "";
      for (const iid of ["udp", "tcp"]) {
        const inst = (data.instances || {})[iid];
        if (!inst) continue;
        grid.appendChild(renderInstanceCard(iid, inst));
      }
      showStatus("");
    } catch (err) {
      grid.innerHTML = `<p>${escapeHtml(err.message)}</p>`;
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
    else if (tab === "server") loadServer();
    else if (tab === "audit") loadAudit();
    else if (tab === "settings") loadSettings();
  });

  $("#refresh-clients").addEventListener("click", loadClients);
  $("#refresh-sessions").addEventListener("click", loadSessions);
  $("#refresh-server").addEventListener("click", loadServer);
  $("#refresh-audit").addEventListener("click", loadAudit);
  $("#refresh-settings").addEventListener("click", loadSettings);

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
