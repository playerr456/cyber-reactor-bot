from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from config import WEBAPP_HOST, WEBAPP_PORT
from db import ALLOWED_TOURNAMENTS, get_registration, init_db, upsert_registration


app = FastAPI()


TOURNAMENTS = ["clash royale", "dota 2", "cs go"]


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Cyber Reactor Arena</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;700&display=swap" rel="stylesheet" />
    <style>
      :root {
        --bg: #f6f8fb;
        --surface: #ffffff;
        --surface-soft: #f1f4f8;
        --text: #0f172a;
        --text-muted: #5f6b7a;
        --line: #d7deea;
        --accent: #1f6feb;
        --accent-soft: #e9f1ff;
        --ok: #0f766e;
        --error: #b91c1c;
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
        background: var(--bg);
        color: var(--text);
        min-height: 100vh;
      }

      body.theme-dark {
        --bg: #0f172a;
        --surface: #111827;
        --surface-soft: #1f2937;
        --text: #e5e7eb;
        --text-muted: #9ca3af;
        --line: #334155;
        --accent: #60a5fa;
        --accent-soft: #1e3a5f;
        --ok: #34d399;
        --error: #f87171;
      }

      .menu-toggle {
        position: fixed;
        left: 16px;
        top: 16px;
        z-index: 40;
        border: 1px solid var(--line);
        background: var(--surface);
        color: var(--text);
        border-radius: 10px;
        padding: 10px 12px;
        font-size: 13px;
        font-weight: 600;
        line-height: 1.2;
        cursor: pointer;
      }

      .settings-toggle {
        position: fixed;
        right: 16px;
        top: 16px;
        z-index: 40;
        border: 1px solid var(--line);
        background: var(--surface);
        color: var(--text);
        border-radius: 10px;
        width: 42px;
        height: 42px;
        font-size: 20px;
        line-height: 1;
        cursor: pointer;
      }

      .overlay {
        position: fixed;
        inset: 0;
        background: rgba(15, 23, 42, 0.34);
        z-index: 30;
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.2s ease;
      }

      .overlay.visible {
        opacity: 1;
        pointer-events: auto;
      }

      .sidebar {
        position: fixed;
        left: 0;
        top: 0;
        bottom: 0;
        width: min(320px, 84vw);
        z-index: 50;
        background: var(--surface);
        border-right: 1px solid var(--line);
        transform: translateX(-100%);
        transition: transform 0.22s ease;
        padding: 18px 12px 18px 16px;
        overflow-y: auto;
      }

      .sidebar.open {
        transform: translateX(0);
      }

      .settings-panel {
        position: fixed;
        right: 0;
        top: 0;
        bottom: 0;
        width: min(320px, 84vw);
        z-index: 50;
        background: var(--surface);
        border-left: 1px solid var(--line);
        transform: translateX(100%);
        transition: transform 0.22s ease;
        padding: 18px 12px 18px 16px;
      }

      .settings-panel.open {
        transform: translateX(0);
      }

      .settings-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 14px;
      }

      .settings-head h2 {
        margin: 0;
        font-size: 20px;
        font-weight: 700;
      }

      .settings-group {
        display: grid;
        gap: 6px;
        margin-bottom: 12px;
      }

      .settings-group label {
        font-size: 13px;
        color: var(--text-muted);
      }

      .settings-group select {
        width: 100%;
        border-radius: 10px;
        border: 1px solid var(--line);
        background: var(--surface-soft);
        color: var(--text);
        padding: 10px 12px;
        font-family: inherit;
        font-size: 14px;
      }

      .sidebar-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
      }

      .sidebar-head h2 {
        margin: 0;
        font-size: 20px;
        font-weight: 700;
      }

      .close-menu {
        border: 1px solid var(--line);
        background: var(--surface);
        color: var(--text);
        cursor: pointer;
        font-size: 18px;
        font-weight: 700;
        width: 32px;
        height: 32px;
        border-radius: 8px;
      }

      .channel-list {
        display: flex;
        flex-direction: column;
        gap: 4px;
      }

      .channel-link {
        display: flex;
        align-items: center;
        gap: 10px;
        text-decoration: none;
        color: var(--text);
        padding: 9px 8px;
        border-radius: 10px;
        border: 1px solid transparent;
        transition: background 0.15s ease, border-color 0.15s ease;
      }

      .channel-link:hover,
      .channel-link.active {
        background: var(--surface-soft);
        border-color: var(--line);
      }

      .channel-icon {
        flex-shrink: 0;
        width: 26px;
        height: 26px;
        border-radius: 7px;
        display: grid;
        place-items: center;
        font-size: 12px;
        font-weight: 800;
        color: #1e293b;
      }

      .channel-meta {
        min-width: 0;
      }

      .channel-title {
        margin: 0;
        font-size: 16px;
        font-weight: 700;
      }

      .page {
        width: min(980px, 100%);
        margin: 0 auto;
        padding: 78px 16px 24px;
      }

      .hero {
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 24px 20px;
        background: var(--surface);
      }

      .hero-tag {
        display: inline-block;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: #3b82f6;
        background: var(--accent-soft);
        border: 1px solid #c8dbff;
        border-radius: 999px;
        padding: 4px 10px;
      }

      .hero h1 {
        margin: 12px 0 8px;
        font-size: clamp(28px, 6vw, 40px);
        line-height: 1.08;
        letter-spacing: 0;
        max-width: 16ch;
      }

      .hero p {
        margin: 0;
        color: var(--text-muted);
        max-width: 56ch;
      }

      .hero-cta {
        margin-top: 16px;
        display: inline-block;
        border-radius: 10px;
        border: 1px solid var(--accent);
        background: var(--accent);
        color: #ffffff;
        padding: 10px 14px;
        text-decoration: none;
        font-weight: 600;
      }

      .stack {
        margin-top: 12px;
        display: grid;
        gap: 12px;
      }

      .panel {
        border-radius: 14px;
        border: 1px solid var(--line);
        background: var(--surface);
        padding: 18px 16px;
      }

      .panel h2 {
        margin: 0;
        font-size: 24px;
      }

      .panel p {
        margin: 7px 0 14px;
        color: var(--text-muted);
      }

      .meta {
        margin-bottom: 13px;
        font-size: 14px;
        color: var(--text);
        padding: 10px 12px;
        background: var(--surface-soft);
        border: 1px solid var(--line);
        border-radius: 10px;
      }

      .grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 8px;
      }

      .tour-btn {
        text-align: left;
        border: 1px solid var(--line);
        border-radius: 10px;
        background: #ffffff;
        color: var(--text);
        padding: 12px;
        font-size: 14px;
        font-weight: 700;
        cursor: pointer;
      }

      .tour-btn:hover {
        border-color: #9fb6de;
      }

      .tour-btn.active {
        border-color: var(--accent);
        background: var(--accent-soft);
      }

      .register-btn,
      .feedback-btn {
        width: 100%;
        margin-top: 12px;
        border-radius: 10px;
        font-size: 14px;
        font-weight: 700;
        padding: 11px 12px;
        cursor: pointer;
      }

      .register-btn {
        border: 1px solid var(--accent);
        background: var(--accent);
        color: #ffffff;
      }

      .feedback-btn {
        border: 1px solid var(--line);
        background: var(--surface-soft);
        color: var(--text);
      }

      .register-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      .status,
      .feedback-status {
        min-height: 20px;
        margin-top: 10px;
        font-size: 13px;
        color: var(--text-muted);
      }

      .feedback-form {
        display: grid;
        gap: 10px;
      }

      .feedback-form label {
        font-size: 13px;
        color: var(--text-muted);
      }

      .feedback-form input,
      .feedback-form textarea {
        width: 100%;
        border-radius: 10px;
        border: 1px solid var(--line);
        background: #ffffff;
        color: var(--text);
        padding: 10px 12px;
        font-family: inherit;
        font-size: 14px;
      }

      .feedback-form textarea {
        min-height: 120px;
        resize: vertical;
      }

      @media (min-width: 880px) {
        .page {
          padding-left: 30px;
          padding-right: 30px;
        }
      }
    </style>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
  </head>
  <body>
    <button id="menu-toggle" class="menu-toggle" type="button" data-i18n="menuButton">Киберспортивные дисциплины</button>
    <button id="settings-toggle" class="settings-toggle" type="button" aria-label="Настройки">&#9881;</button>
    <div id="menu-overlay" class="overlay"></div>
    <div id="settings-overlay" class="overlay"></div>

    <aside id="sidebar" class="sidebar" aria-hidden="true">
      <div class="sidebar-head">
        <h2 data-i18n="sidebarTitle">Киберспортивные дисциплины</h2>
        <button id="close-menu" class="close-menu" type="button" aria-label="Закрыть">x</button>
      </div>

      <nav class="channel-list">
        <a href="#banner" class="channel-link active">
          <span class="channel-icon" style="background:#b9ccff">GP</span>
          <div class="channel-meta">
            <p class="channel-title">Главная страница</p>
          </div>
        </a>
        <a href="#banner" class="channel-link">
          <span class="channel-icon" style="background:#ffb637">CS</span>
          <div class="channel-meta">
            <p class="channel-title">CS2</p>
          </div>
        </a>
        <a href="#registration" class="channel-link">
          <span class="channel-icon" style="background:#adb9c8">CR</span>
          <div class="channel-meta">
            <p class="channel-title">CLASH ROYALE</p>
          </div>
        </a>
        <a href="#registration" class="channel-link">
          <span class="channel-icon" style="background:#68ff9b">F</span>
          <div class="channel-meta">
            <p class="channel-title">FIFA</p>
          </div>
        </a>
        <a href="#registration" class="channel-link">
          <span class="channel-icon" style="background:#e7cc97">M</span>
          <div class="channel-meta">
            <p class="channel-title">MLBB</p>
          </div>
        </a>
        <a href="#registration" class="channel-link">
          <span class="channel-icon" style="background:#8cb7ff">H</span>
          <div class="channel-meta">
            <p class="channel-title">Hearthstone</p>
          </div>
        </a>
        <a href="#registration" class="channel-link">
          <span class="channel-icon" style="background:#ff6568">D2</span>
          <div class="channel-meta">
            <p class="channel-title">Dota 2</p>
          </div>
        </a>
      </nav>
    </aside>

    <aside id="settings-panel" class="settings-panel" aria-hidden="true">
      <div class="settings-head">
        <h2 data-i18n="settingsTitle">Настройки</h2>
        <button id="close-settings" class="close-menu" type="button" aria-label="Закрыть">x</button>
      </div>

      <div class="settings-group">
        <label for="language-select" data-i18n="languageLabel">Язык</label>
        <select id="language-select">
          <option value="ru" data-i18n="langRu">Русский</option>
          <option value="en" data-i18n="langEn">English</option>
        </select>
      </div>

      <div class="settings-group">
        <label for="theme-select" data-i18n="themeLabel">Тема</label>
        <select id="theme-select">
          <option value="light" data-i18n="themeLight">Светлая</option>
          <option value="dark" data-i18n="themeDark">Темная</option>
        </select>
      </div>
    </aside>

    <main class="page">
      <header class="hero" id="banner">
        <span class="hero-tag">Cyber Reactor</span>
        <h1 data-i18n="heroTitle">Титульная страница турниров</h1>
        <p data-i18n="heroText">Следи за лобби, выбирай дисциплину и регистрируйся на ближайшие матчи прямо из мини-приложения.</p>
        <a href="#registration" class="hero-cta" data-i18n="heroCta">К регистрации</a>
      </header>

      <div class="stack">
        <section class="panel" id="registration">
          <h2 data-i18n="registrationTitle">Регистрация на турнир</h2>
          <p data-i18n="registrationText">Выбери дисциплину и нажми кнопку регистрации.</p>

          <div class="meta"><span id="user-label" data-i18n="userLabel">Пользователь</span>: <span id="username">гость</span></div>

          <div class="grid" id="tournaments"></div>

          <button id="register-btn" class="register-btn" disabled data-i18n="registerButton">Зарегистрироваться</button>
          <div class="status" id="status"></div>
        </section>

        <section class="panel" id="feedback">
          <h2 data-i18n="feedbackTitle">Обратная связь</h2>
          <p data-i18n="feedbackText">Напиши, что улучшить в расписании, комнатах или интерфейсе.</p>

          <form id="feedback-form" class="feedback-form">
            <div>
              <label for="feedback-name" data-i18n="feedbackNameLabel">Имя</label>
              <input
                id="feedback-name"
                name="name"
                type="text"
                maxlength="70"
                placeholder="Как к тебе обращаться"
                data-i18n-placeholder="feedbackNamePlaceholder"
              />
            </div>
            <div>
              <label for="feedback-message" data-i18n="feedbackMessageLabel">Сообщение</label>
              <textarea
                id="feedback-message"
                name="message"
                maxlength="1000"
                placeholder="Твой отзыв"
                data-i18n-placeholder="feedbackMessagePlaceholder"
              ></textarea>
            </div>
            <button class="feedback-btn" type="submit" data-i18n="feedbackSubmit">Отправить отзыв</button>
            <div class="feedback-status" id="feedback-status"></div>
          </form>
        </section>
      </div>
    </main>

    <script>
      const tg = window.Telegram?.WebApp;
      if (tg) tg.expand();

      const TOURNAMENTS = ["clash royale", "dota 2", "cs go"];
      const I18N = {
        ru: {
          menuButton: "Киберспортивные дисциплины",
          sidebarTitle: "Киберспортивные дисциплины",
          settingsTitle: "Настройки",
          languageLabel: "Язык",
          themeLabel: "Тема",
          langRu: "Русский",
          langEn: "English",
          themeLight: "Светлая",
          themeDark: "Темная",
          heroTitle: "Титульная страница турниров",
          heroText: "Следи за лобби, выбирай дисциплину и регистрируйся на ближайшие матчи прямо из мини-приложения.",
          heroCta: "К регистрации",
          registrationTitle: "Регистрация на турнир",
          registrationText: "Выбери дисциплину и нажми кнопку регистрации.",
          userLabel: "Пользователь",
          guest: "гость",
          registerButton: "Зарегистрироваться",
          feedbackTitle: "Обратная связь",
          feedbackText: "Напиши, что улучшить в расписании, комнатах или интерфейсе.",
          feedbackNameLabel: "Имя",
          feedbackNamePlaceholder: "Как к тебе обращаться",
          feedbackMessageLabel: "Сообщение",
          feedbackMessagePlaceholder: "Твой отзыв",
          feedbackSubmit: "Отправить отзыв",
          close: "Закрыть",
          statusSelected: "Выбрано: {name}",
          statusOpenTelegram: "Открой мини-приложение из Telegram, чтобы зарегистрироваться.",
          statusLoadRegistrationError: "Не удалось загрузить текущую регистрацию.",
          statusAlreadyRegistered: "Ты уже зарегистрирован на: {name}",
          statusChooseFirst: "Сначала выбери турнир.",
          statusSaving: "Сохраняю в базу...",
          statusSaved: "Регистрация сохранена: {name}",
          statusRegistrationError: "Ошибка регистрации.",
          feedbackTooShort: "Напиши хотя бы 3 символа.",
          feedbackSending: "Отправляю...",
          feedbackSent: "Спасибо за отзыв!",
          feedbackError: "Не удалось отправить отзыв.",
        },
        en: {
          menuButton: "Esports Disciplines",
          sidebarTitle: "Esports Disciplines",
          settingsTitle: "Settings",
          languageLabel: "Language",
          themeLabel: "Theme",
          langRu: "Russian",
          langEn: "English",
          themeLight: "Light",
          themeDark: "Dark",
          heroTitle: "Tournament Landing Page",
          heroText: "Follow lobbies, choose a discipline, and register for upcoming matches right from the mini app.",
          heroCta: "Go to registration",
          registrationTitle: "Tournament Registration",
          registrationText: "Choose a discipline and click the registration button.",
          userLabel: "User",
          guest: "guest",
          registerButton: "Register",
          feedbackTitle: "Feedback",
          feedbackText: "Tell us what to improve in schedule, rooms, or interface.",
          feedbackNameLabel: "Name",
          feedbackNamePlaceholder: "How should we address you",
          feedbackMessageLabel: "Message",
          feedbackMessagePlaceholder: "Your feedback",
          feedbackSubmit: "Send feedback",
          close: "Close",
          statusSelected: "Selected: {name}",
          statusOpenTelegram: "Open this mini app from Telegram to register.",
          statusLoadRegistrationError: "Failed to load current registration.",
          statusAlreadyRegistered: "You are already registered for: {name}",
          statusChooseFirst: "Choose a tournament first.",
          statusSaving: "Saving to database...",
          statusSaved: "Registration saved: {name}",
          statusRegistrationError: "Registration error.",
          feedbackTooShort: "Please enter at least 3 characters.",
          feedbackSending: "Sending...",
          feedbackSent: "Thanks for your feedback!",
          feedbackError: "Failed to send feedback.",
        },
      };

      const tournamentsEl = document.getElementById("tournaments");
      const registerBtn = document.getElementById("register-btn");
      const statusEl = document.getElementById("status");
      const feedbackForm = document.getElementById("feedback-form");
      const feedbackNameEl = document.getElementById("feedback-name");
      const feedbackMessageEl = document.getElementById("feedback-message");
      const feedbackStatusEl = document.getElementById("feedback-status");
      const sidebar = document.getElementById("sidebar");
      const menuToggle = document.getElementById("menu-toggle");
      const closeMenu = document.getElementById("close-menu");
      const menuOverlay = document.getElementById("menu-overlay");
      const settingsPanel = document.getElementById("settings-panel");
      const settingsToggle = document.getElementById("settings-toggle");
      const closeSettings = document.getElementById("close-settings");
      const settingsOverlay = document.getElementById("settings-overlay");
      const languageSelect = document.getElementById("language-select");
      const themeSelect = document.getElementById("theme-select");
      const channelLinks = document.querySelectorAll(".channel-link");

      const user = tg?.initDataUnsafe?.user || {};
      const userId = user.id || null;
      let currentLanguage = localStorage.getItem("cyber_lang") || "ru";

      feedbackNameEl.value = user.first_name || user.username || "";
      let selectedTournament = null;

      function t(key, params = {}) {
        const dict = I18N[currentLanguage] || I18N.ru;
        const text = dict[key] || I18N.ru[key] || key;
        return text.replace(/\{(\w+)\}/g, (_, token) => String(params[token] ?? `{${token}}`));
      }

      function renderUserName() {
        const usernameEl = document.getElementById("username");
        usernameEl.textContent = user.username ? `@${user.username}` : (user.first_name || t("guest"));
      }

      function applyLanguage(lang) {
        currentLanguage = I18N[lang] ? lang : "ru";
        document.documentElement.lang = currentLanguage;
        languageSelect.value = currentLanguage;
        localStorage.setItem("cyber_lang", currentLanguage);

        document.querySelectorAll("[data-i18n]").forEach((el) => {
          const key = el.dataset.i18n;
          el.textContent = t(key);
        });

        document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
          const key = el.dataset.i18nPlaceholder;
          el.placeholder = t(key);
        });

        closeMenu.setAttribute("aria-label", t("close"));
        closeSettings.setAttribute("aria-label", t("close"));
        settingsToggle.setAttribute("aria-label", t("settingsTitle"));
        renderUserName();
      }

      function applyTheme(theme) {
        const safeTheme = theme === "dark" ? "dark" : "light";
        document.body.classList.toggle("theme-dark", safeTheme === "dark");
        themeSelect.value = safeTheme;
        localStorage.setItem("cyber_theme", safeTheme);
      }

      function setStatus(text, isError = false) {
        statusEl.textContent = text;
        statusEl.style.color = isError ? "var(--error)" : "var(--ok)";
      }

      function setFeedbackStatus(text, isError = false) {
        feedbackStatusEl.textContent = text;
        feedbackStatusEl.style.color = isError ? "var(--error)" : "var(--ok)";
      }

      function openMenu() {
        closeSettingsPanel();
        sidebar.classList.add("open");
        menuOverlay.classList.add("visible");
        sidebar.setAttribute("aria-hidden", "false");
      }

      function closeSidebar() {
        sidebar.classList.remove("open");
        menuOverlay.classList.remove("visible");
        sidebar.setAttribute("aria-hidden", "true");
      }

      function openSettings() {
        closeSidebar();
        settingsPanel.classList.add("open");
        settingsOverlay.classList.add("visible");
        settingsPanel.setAttribute("aria-hidden", "false");
      }

      function closeSettingsPanel() {
        settingsPanel.classList.remove("open");
        settingsOverlay.classList.remove("visible");
        settingsPanel.setAttribute("aria-hidden", "true");
      }

      function renderTournamentButtons() {
        tournamentsEl.innerHTML = "";
        TOURNAMENTS.forEach((name) => {
          const btn = document.createElement("button");
          btn.className = "tour-btn";
          btn.textContent = name.toUpperCase();
          btn.addEventListener("click", () => {
            selectedTournament = name;
            document.querySelectorAll(".tour-btn").forEach((x) => x.classList.remove("active"));
            btn.classList.add("active");
            registerBtn.disabled = !userId;
            setStatus(t("statusSelected", { name }));
          });
          tournamentsEl.appendChild(btn);
        });
      }

      async function loadExistingRegistration() {
        if (!userId) {
          setStatus(t("statusOpenTelegram"), true);
          return;
        }

        try {
          const res = await fetch(`/api/registration/${userId}`);
          if (!res.ok) return;
          const data = await res.json();
          if (!data.registration) return;

          selectedTournament = data.registration.tournament;
          document.querySelectorAll(".tour-btn").forEach((btn) => {
            if (btn.textContent.toLowerCase() === selectedTournament) {
              btn.classList.add("active");
            }
          });
          registerBtn.disabled = false;
          setStatus(t("statusAlreadyRegistered", { name: selectedTournament }));
        } catch {
          setStatus(t("statusLoadRegistrationError"), true);
        }
      }

      registerBtn.addEventListener("click", async () => {
        if (!userId || !selectedTournament) {
          setStatus(t("statusChooseFirst"), true);
          return;
        }

        registerBtn.disabled = true;
        setStatus(t("statusSaving"));

        try {
          const payload = {
            user_id: userId,
            username: user.username || null,
            first_name: user.first_name || null,
            tournament: selectedTournament,
          };

          const res = await fetch("/api/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });

          const data = await res.json();
          if (!res.ok) {
            throw new Error(data.detail || "Ошибка регистрации");
          }

          setStatus(t("statusSaved", { name: selectedTournament }));
          if (tg) {
            tg.sendData(JSON.stringify({ type: "registration", tournament: selectedTournament }));
          }
        } catch (err) {
          setStatus(err.message || t("statusRegistrationError"), true);
        } finally {
          registerBtn.disabled = false;
        }
      });

      feedbackForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const message = feedbackMessageEl.value.trim();
        if (message.length < 3) {
          setFeedbackStatus(t("feedbackTooShort"), true);
          return;
        }

        setFeedbackStatus(t("feedbackSending"));
        const payload = {
          name: feedbackNameEl.value.trim() || null,
          message,
          user_id: userId,
          username: user.username || null,
        };

        try {
          const res = await fetch("/api/feedback", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });
          const data = await res.json();
          if (!res.ok) {
            throw new Error(data.detail || "Ошибка отправки");
          }
          setFeedbackStatus(t("feedbackSent"));
          feedbackMessageEl.value = "";
        } catch (err) {
          setFeedbackStatus(err.message || t("feedbackError"), true);
        }
      });

      menuToggle.addEventListener("click", openMenu);
      closeMenu.addEventListener("click", closeSidebar);
      menuOverlay.addEventListener("click", closeSidebar);
      settingsToggle.addEventListener("click", openSettings);
      closeSettings.addEventListener("click", closeSettingsPanel);
      settingsOverlay.addEventListener("click", closeSettingsPanel);
      languageSelect.addEventListener("change", (event) => applyLanguage(event.target.value));
      themeSelect.addEventListener("change", (event) => applyTheme(event.target.value));
      channelLinks.forEach((link) => {
        link.addEventListener("click", () => {
          channelLinks.forEach((item) => item.classList.remove("active"));
          link.classList.add("active");
          closeSidebar();
        });
      });

      applyTheme(localStorage.getItem("cyber_theme") || "light");
      applyLanguage(currentLanguage);
      renderTournamentButtons();
      loadExistingRegistration();
    </script>
  </body>
</html>
"""


class RegisterRequest(BaseModel):
    user_id: int
    username: str | None = None
    first_name: str | None = None
    tournament: str


class FeedbackRequest(BaseModel):
    message: str
    name: str | None = None
    user_id: int | None = None
    username: str | None = None


@app.on_event("startup")
def startup() -> None:
    try:
        init_db()
        app.state.db_error = None
    except Exception as exc:
        # Do not crash the whole app on serverless startup.
        app.state.db_error = str(exc)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return HTMLResponse(content=HTML_TEMPLATE)


@app.post("/api/register")
async def register(payload: RegisterRequest) -> dict[str, str]:
    if getattr(app.state, "db_error", None):
        raise HTTPException(status_code=503, detail=f"DB is unavailable: {app.state.db_error}")

    tournament = payload.tournament.strip().lower()
    if tournament not in ALLOWED_TOURNAMENTS:
        raise HTTPException(status_code=400, detail="Unsupported tournament")

    upsert_registration(
        user_id=payload.user_id,
        username=payload.username,
        first_name=payload.first_name,
        tournament=tournament,
    )
    return {"message": f"Регистрация сохранена: {tournament}"}


@app.post("/api/feedback")
async def feedback(payload: FeedbackRequest) -> dict[str, str]:
    message = payload.message.strip()
    if len(message) < 3:
        raise HTTPException(status_code=400, detail="Feedback message is too short")
    if len(message) > 1000:
        raise HTTPException(status_code=400, detail="Feedback message is too long")

    sender = payload.name or payload.username or "anonymous"
    print(f"[feedback] from={sender} user_id={payload.user_id} message={message}")
    return {"message": "Спасибо! Отзыв принят."}


@app.get("/api/registration/{user_id}")
async def registration(user_id: int) -> dict[str, object]:
    if getattr(app.state, "db_error", None):
        raise HTTPException(status_code=503, detail=f"DB is unavailable: {app.state.db_error}")

    data = get_registration(user_id)
    return {"registration": data}


@app.get("/api/tournaments")
async def tournaments() -> dict[str, list[str]]:
    return {"items": TOURNAMENTS}


def run() -> None:
    import uvicorn

    uvicorn.run("webapp:app", host=WEBAPP_HOST, port=WEBAPP_PORT, reload=True)


if __name__ == "__main__":
    run()
