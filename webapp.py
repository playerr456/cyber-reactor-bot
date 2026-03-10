from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import WEBAPP_HOST, WEBAPP_PORT
from db import (
    ALLOWED_TOURNAMENTS,
    get_clash_registration,
    get_registration,
    init_db,
    normalize_clash_context,
    upsert_clash_registration,
    upsert_registration,
)


app = FastAPI()
app.mount("/assets", StaticFiles(directory=Path(__file__).parent / "assets"), name="assets")
app.mount("/logos", StaticFiles(directory=Path(__file__).parent / "logos"), name="logos")


TOURNAMENTS = ["clash royale", "dota 2", "cs go"]


DISCIPLINE_PAGES: dict[str, dict[str, str]] = {
    "cs2": {"title": "COUNTER STRIKE 2", "logo": "/logos/cs2%20logo.png"},
    "dota2": {"title": "DOTA 2", "logo": "/logos/dota2%20logo.png"},
    "mlbb": {"title": "MOBILE LEGENDS", "logo": "/logos/mlbb%20logo.png"},
    "wot": {"title": "МИР ТАНКОВ", "logo": "/logos/wot%20logo.png"},
}


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>КиберРеаткор</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=IBM+Plex+Sans:wght@400;500;700&display=swap"
      rel="stylesheet"
    />
    <style>
      :root {
        --bg: #06080c;
        --text: #f5f7fa;
        --panel: #10141d;
        --panel-line: rgba(255, 255, 255, 0.16);
        --muted: #bac6d8;
        --link: #a8ccff;
        --top-button-size: 44px;
        --top-logo-size: 64px;
        --top-control-bg: #0c1a34;
        --top-control-border: rgba(255, 255, 255, 0.24);
        --top-control-icon: #e7edf9;
        --top-logo-bg: #000000;
        --top-logo-border: rgba(255, 255, 255, 0.08);
      }

      body.theme-light {
        --bg: #f3f5f9;
        --text: #0f172a;
        --panel: #ffffff;
        --panel-line: rgba(15, 23, 42, 0.16);
        --muted: #5a6678;
        --link: #2058cc;
        --top-control-bg: #d7d7d7;
        --top-control-border: rgba(15, 23, 42, 0.28);
        --top-control-icon: #2f3642;
        --top-logo-bg: #000000;
        --top-logo-border: rgba(15, 23, 42, 0.35);
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

      .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
      }

      .menu-toggle,
      .settings-toggle {
        position: fixed;
        top: 14px;
        z-index: 40;
        width: var(--top-button-size);
        height: var(--top-button-size);
        display: inline-grid;
        place-items: center;
        border: 1px solid var(--top-control-border);
        background: var(--top-control-bg);
        color: var(--top-control-icon);
        border-radius: 12px;
        cursor: pointer;
      }

      .menu-toggle {
        left: 14px;
        padding: 0;
      }

      .settings-toggle {
        right: 14px;
        padding: 0;
      }

      .settings-icon {
        display: inline-grid;
        place-items: center;
        width: 26px;
        height: 26px;
        font-size: 27px;
        line-height: 1;
        transform: none;
      }

      .menu-icon {
        width: 22px;
        height: 18px;
        display: grid;
        align-content: space-between;
      }

      .menu-icon .bar {
        display: block;
        height: 3px;
        border-radius: 999px;
        background: var(--top-control-icon);
      }

      .top-logo-badge {
        position: fixed;
        top: 4px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 40;
        width: var(--top-logo-size);
        height: var(--top-logo-size);
        border-radius: 50%;
        background: var(--top-logo-bg);
        border: 1px solid var(--top-logo-border);
        display: grid;
        place-items: center;
        pointer-events: none;
      }

      .top-logo-badge img {
        width: calc(var(--top-logo-size) - 2px);
        height: calc(var(--top-logo-size) - 2px);
        border-radius: 50%;
        object-fit: cover;
      }

      .overlay {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.42);
        z-index: 30;
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.2s ease;
      }

      .overlay.visible {
        opacity: 1;
        pointer-events: auto;
      }

      .sidebar,
      .settings-panel {
        position: fixed;
        top: 0;
        bottom: 0;
        width: min(340px, 84vw);
        background: var(--panel);
        z-index: 50;
        padding: 16px 14px;
        transition: transform 0.22s ease;
      }

      .sidebar {
        left: 0;
        border-right: 1px solid var(--panel-line);
        transform: translateX(-100%);
      }

      .settings-panel {
        right: 0;
        border-left: 1px solid var(--panel-line);
        transform: translateX(100%);
      }

      .sidebar.open,
      .settings-panel.open {
        transform: translateX(0);
      }

      .panel-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
      }

      .panel-head h2 {
        margin: 0;
        font-size: 20px;
      }

      .close-btn {
        width: 34px;
        height: 34px;
        border-radius: 8px;
        border: 1px solid var(--panel-line);
        background: transparent;
        color: var(--text);
        font-size: 18px;
        cursor: pointer;
      }

      .nav-list {
        display: grid;
        gap: 6px;
      }

      .nav-link {
        display: flex;
        align-items: center;
        gap: 10px;
        text-decoration: none;
        color: var(--text);
        border: 1px solid transparent;
        border-radius: 10px;
        padding: 10px 12px;
      }

      .nav-icon {
        width: 22px;
        height: 22px;
        border-radius: 6px;
        display: inline-grid;
        place-items: center;
        font-size: 11px;
        font-weight: 700;
        background: rgba(255, 255, 255, 0.15);
        color: var(--text);
        flex-shrink: 0;
      }

      .nav-link:hover,
      .nav-link.active {
        border-color: var(--panel-line);
      }

      .setting-group {
        display: grid;
        gap: 6px;
        margin-bottom: 12px;
      }

      .setting-group label {
        color: var(--muted);
        font-size: 13px;
      }

      .setting-group select {
        border-radius: 10px;
        border: 1px solid var(--panel-line);
        background: transparent;
        color: var(--text);
        padding: 10px;
        font-family: inherit;
      }

      .page {
        width: min(1100px, 100%);
        margin: 0 auto;
        padding: 72px 0 28px;
      }

      .carousel {
        position: relative;
        overflow: hidden;
        width: 100%;
        height: min(54vw, 460px);
        min-height: 260px;
        border-bottom: 1px solid var(--panel-line);
      }

      .slide {
        position: absolute;
        inset: 0;
        opacity: 0;
        transition: opacity 0.65s ease;
      }

      .slide.active {
        opacity: 1;
      }

      .slide img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
      }

      .dots {
        position: absolute;
        left: 50%;
        bottom: 14px;
        transform: translateX(-50%);
        display: flex;
        gap: 8px;
        z-index: 2;
      }

      .dot {
        width: 10px;
        height: 10px;
        border-radius: 999px;
        border: 0;
        cursor: pointer;
        background: rgba(255, 255, 255, 0.45);
      }

      .dot.active {
        background: #ffffff;
      }

      .contacts-inline {
        padding: 18px 16px 8px;
      }

      .contacts-inline h2 {
        margin: 0 0 12px;
        font-size: clamp(30px, 4vw, 46px);
      }

      .contacts-inline p {
        margin: 6px 0;
        font-size: clamp(20px, 2.4vw, 34px);
      }

      .contacts-inline a {
        color: var(--link);
        text-decoration: none;
      }

      @media (max-width: 680px) {
        .carousel {
          min-height: 220px;
        }

        .contacts-inline h2 {
          margin-bottom: 10px;
        }
      }
    </style>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
  </head>
  <body>
    <button id="menu-toggle" class="menu-toggle" type="button" aria-label="Открыть меню">
      <span class="menu-icon" aria-hidden="true">
        <span class="bar"></span>
        <span class="bar"></span>
        <span class="bar"></span>
      </span>
      <span class="sr-only" data-i18n="menuOpen">Открыть меню</span>
    </button>
    <div class="top-logo-badge" aria-hidden="true">
      <img src="/assets/logo.jpg" alt="" />
    </div>
    <button id="settings-toggle" class="settings-toggle" type="button" aria-label="Настройки">
      <span class="settings-icon" aria-hidden="true">&#9881;</span>
      <span class="sr-only" data-i18n="settingsTitle">Настройки</span>
    </button>
    <div id="overlay" class="overlay"></div>

    <aside id="sidebar" class="sidebar" aria-hidden="true">
      <div class="panel-head">
        <h2 data-i18n="sidebarTitle">Навигация</h2>
        <button id="close-menu" class="close-btn" type="button" aria-label="Закрыть">x</button>
      </div>
      <nav class="nav-list">
        <a href="#top-banner" class="nav-link active">
          <span class="nav-icon">HM</span>
          <span data-i18n="navMain">Главная страница</span>
        </a>
        <a href="/games?view=teams" class="nav-link">
          <span class="nav-icon">SB</span>
          <span data-i18n="navHome">Сборные</span>
        </a>
        <a href="/games?view=tournaments" class="nav-link">
          <span class="nav-icon">TR</span>
          <span data-i18n="navClash">Турниры</span>
        </a>
        <a href="/achievements" class="nav-link">
          <span class="nav-icon">DG</span>
          <span data-i18n="navCs2">Достижения</span>
        </a>
      </nav>
    </aside>

    <aside id="settings-panel" class="settings-panel" aria-hidden="true">
      <div class="panel-head">
        <h2 data-i18n="settingsTitle">Настройки</h2>
        <button id="close-settings" class="close-btn" type="button" aria-label="Закрыть">x</button>
      </div>
      <div class="setting-group">
        <label for="language-select" data-i18n="languageLabel">Язык</label>
        <select id="language-select">
          <option value="ru" data-i18n="langRu">Русский</option>
          <option value="en" data-i18n="langEn">English</option>
        </select>
      </div>
      <div class="setting-group">
        <label for="theme-select" data-i18n="themeLabel">Тема</label>
        <select id="theme-select">
          <option value="dark" data-i18n="themeDark">Темная</option>
          <option value="light" data-i18n="themeLight">Светлая</option>
        </select>
      </div>
    </aside>

    <main class="page">
      <section id="top-banner" class="carousel" aria-label="Баннеры">
        <div class="slide active">
          <img src="/assets/banner1.jpg" alt="Баннер 1" />
        </div>
        <div class="slide">
          <img src="/assets/banner2.jpg" alt="Баннер 2" />
        </div>
        <div class="slide">
          <img src="/assets/banner3.jpg" alt="Баннер 3" />
        </div>
        <div class="dots">
          <button class="dot active" type="button" data-index="0" aria-label="Баннер 1"></button>
          <button class="dot" type="button" data-index="1" aria-label="Баннер 2"></button>
          <button class="dot" type="button" data-index="2" aria-label="Баннер 3"></button>
        </div>
      </section>

      <section id="contacts" class="contacts-inline">
        <h2 data-i18n="feedbackTitle">Обратная связь</h2>
        <p><span data-i18n="emailLabel">Почта</span>: <a href="mailto:123@gmail.com">123@gmail.com</a></p>
        <p><span data-i18n="tgLabel">TG</span>: <a href="https://t.me/matve88" target="_blank" rel="noopener">@matve88</a></p>
      </section>
    </main>

    <script>
      function parseUserFromQueryString(raw) {
        if (!raw) {
          return null;
        }
        try {
          const userJson = new URLSearchParams(raw).get("user");
          return userJson ? JSON.parse(userJson) : null;
        } catch {
          return null;
        }
      }

      function parseUserFromLocation() {
        try {
          const hashParams = new URLSearchParams(window.location.hash.replace(/^#/, ""));
          const searchParams = new URLSearchParams(window.location.search);
          const tgWebAppData = hashParams.get("tgWebAppData") || searchParams.get("tgWebAppData");
          if (tgWebAppData) {
            const decoded = decodeURIComponent(tgWebAppData);
            const fromData = parseUserFromQueryString(decoded);
            if (fromData) {
              return fromData;
            }
          }
          const tgWebAppUser = hashParams.get("tgWebAppUser") || searchParams.get("tgWebAppUser");
          if (tgWebAppUser) {
            return JSON.parse(decodeURIComponent(tgWebAppUser));
          }
        } catch {
          return null;
        }
        return null;
      }

      function cacheTelegramIdentity() {
        const tg = window.Telegram?.WebApp;
        if (tg) {
          tg.ready?.();
          tg.expand?.();
        }

        const unsafeUser = tg?.initDataUnsafe?.user || null;
        const parsedUser = !unsafeUser && tg?.initData ? parseUserFromQueryString(tg.initData) : null;
        const urlUser = parseUserFromLocation();
        const user = unsafeUser || parsedUser || urlUser || null;

        const rawId = user?.id ?? null;
        const parsedId = rawId !== null ? Number.parseInt(String(rawId), 10) : NaN;
        if (!Number.isFinite(parsedId) || parsedId <= 0) {
          return;
        }

        try {
          localStorage.setItem(
            "cyber_tg_user_cache",
            JSON.stringify({
              id: parsedId,
              username: user?.username ? String(user.username).toLowerCase() : null,
              ts: Date.now(),
            }),
          );
        } catch {}
      }

      cacheTelegramIdentity();

      const I18N = {
        ru: {
          menuOpen: "Открыть меню",
          sidebarTitle: "Навигация",
          settingsTitle: "Настройки",
          navMain: "Главная страница",
          navHome: "Сборные",
          navClash: "Турниры",
          navCs2: "Достижения",
          navDota: "Достижения",
          languageLabel: "Язык",
          themeLabel: "Тема",
          langRu: "Русский",
          langEn: "English",
          themeDark: "Темная",
          themeLight: "Светлая",
          brandTitle: "КиберРеаткор",
          feedbackTitle: "Обратная связь",
          emailLabel: "Почта",
          tgLabel: "TG",
          close: "Закрыть",
        },
        en: {
          menuOpen: "Open menu",
          sidebarTitle: "Navigation",
          settingsTitle: "Settings",
          navMain: "Home",
          navHome: "National teams",
          navClash: "Tournaments",
          navCs2: "Achievements",
          navDota: "Achievements",
          languageLabel: "Language",
          themeLabel: "Theme",
          langRu: "Russian",
          langEn: "English",
          themeDark: "Dark",
          themeLight: "Light",
          brandTitle: "CyberReactor",
          feedbackTitle: "Feedback",
          emailLabel: "Email",
          tgLabel: "TG",
          close: "Close",
        },
      };

      const slides = Array.from(document.querySelectorAll(".slide"));
      const dots = Array.from(document.querySelectorAll(".dot"));
      const overlay = document.getElementById("overlay");
      const sidebar = document.getElementById("sidebar");
      const settingsPanel = document.getElementById("settings-panel");
      const menuToggle = document.getElementById("menu-toggle");
      const settingsToggle = document.getElementById("settings-toggle");
      const closeMenu = document.getElementById("close-menu");
      const closeSettings = document.getElementById("close-settings");
      const languageSelect = document.getElementById("language-select");
      const themeSelect = document.getElementById("theme-select");
      const navLinks = Array.from(document.querySelectorAll(".nav-link"));

      let current = 0;
      let autoplayId = null;

      function showSlide(index) {
        current = (index + slides.length) % slides.length;
        slides.forEach((slide, i) => slide.classList.toggle("active", i === current));
        dots.forEach((dot, i) => dot.classList.toggle("active", i === current));
      }

      function nextSlide() {
        showSlide(current + 1);
      }

      function startAutoplay() {
        clearInterval(autoplayId);
        autoplayId = setInterval(nextSlide, 3200);
      }

      function closePanels() {
        sidebar.classList.remove("open");
        settingsPanel.classList.remove("open");
        overlay.classList.remove("visible");
        sidebar.setAttribute("aria-hidden", "true");
        settingsPanel.setAttribute("aria-hidden", "true");
      }

      function openSidebar() {
        settingsPanel.classList.remove("open");
        sidebar.classList.add("open");
        overlay.classList.add("visible");
        sidebar.setAttribute("aria-hidden", "false");
        settingsPanel.setAttribute("aria-hidden", "true");
      }

      function openSettings() {
        sidebar.classList.remove("open");
        settingsPanel.classList.add("open");
        overlay.classList.add("visible");
        sidebar.setAttribute("aria-hidden", "true");
        settingsPanel.setAttribute("aria-hidden", "false");
      }

      function applyTheme(theme) {
        const safeTheme = theme === "light" ? "light" : "dark";
        document.body.classList.toggle("theme-light", safeTheme === "light");
        themeSelect.value = safeTheme;
        localStorage.setItem("cyber_theme", safeTheme);
      }

      function translate(lang) {
        const safeLang = I18N[lang] ? lang : "ru";
        localStorage.setItem("cyber_lang", safeLang);
        languageSelect.value = safeLang;
        document.documentElement.lang = safeLang;

        document.querySelectorAll("[data-i18n]").forEach((el) => {
          const key = el.dataset.i18n;
          el.textContent = I18N[safeLang][key] || I18N.ru[key] || key;
        });

        closeMenu.setAttribute("aria-label", I18N[safeLang].close);
        closeSettings.setAttribute("aria-label", I18N[safeLang].close);
        menuToggle.setAttribute("aria-label", I18N[safeLang].menuOpen);
        settingsToggle.setAttribute("aria-label", I18N[safeLang].settingsTitle);
      }

      dots.forEach((dot) => {
        dot.addEventListener("click", () => {
          showSlide(Number(dot.dataset.index || 0));
          startAutoplay();
        });
      });

      menuToggle.addEventListener("click", openSidebar);
      settingsToggle.addEventListener("click", openSettings);
      closeMenu.addEventListener("click", closePanels);
      closeSettings.addEventListener("click", closePanels);
      overlay.addEventListener("click", closePanels);

      navLinks.forEach((link) => {
        link.addEventListener("click", () => {
          navLinks.forEach((l) => l.classList.remove("active"));
          link.classList.add("active");
          closePanels();
        });
      });

      languageSelect.addEventListener("change", (e) => translate(e.target.value));
      themeSelect.addEventListener("change", (e) => applyTheme(e.target.value));

      document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
          closePanels();
        }
      });

      showSlide(0);
      startAutoplay();
      applyTheme(localStorage.getItem("cyber_theme") || "dark");
      translate(localStorage.getItem("cyber_lang") || "ru");
    </script>
  </body>
</html>
"""


GAMES_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Дисциплины</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;700&display=swap"
      rel="stylesheet"
    />
    <style>
      :root {
        --bg: #06080c;
        --text: #f5f7fa;
        --panel: #10141d;
        --panel-line: rgba(255, 255, 255, 0.16);
        --muted: #bac6d8;
        --link: #a8ccff;
      }

      body.theme-light {
        --bg: #f3f5f9;
        --text: #0f172a;
        --panel: #ffffff;
        --panel-line: rgba(15, 23, 42, 0.16);
        --muted: #5a6678;
        --link: #2058cc;
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        min-height: 100vh;
        font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
        background: var(--bg);
        color: var(--text);
      }

      .page {
        width: min(860px, calc(100% - 20px));
        margin: 0 auto;
        padding: 72px 0 26px;
      }

      .top-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
      }

      .back-link {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        text-decoration: none;
        color: var(--text);
        border: 1px solid var(--panel-line);
        border-radius: 10px;
        padding: 9px 12px;
        background: var(--panel);
        font-weight: 600;
      }

      .top-caption {
        color: var(--muted);
        font-size: 14px;
      }

      h1 {
        margin: 16px 0 12px;
        font-size: clamp(28px, 5vw, 42px);
        line-height: 1;
      }

      .games-list {
        display: grid;
        gap: 10px;
      }

      .game-link {
        display: flex;
        align-items: center;
        gap: 12px;
        border: 1px solid var(--panel-line);
        border-radius: 12px;
        padding: 8px;
        text-decoration: none;
        color: var(--text);
        background: var(--panel);
      }

      .game-thumb {
        width: 90px;
        height: 58px;
        border-radius: 8px;
        object-fit: contain;
        background: #0a0f18;
        padding: 4px;
        flex-shrink: 0;
      }

      .game-thumb.cs2-thumb {
        width: 82px;
        height: 52px;
        padding: 6px;
      }

      body.theme-light .game-thumb {
        background: #edf2fb;
      }

      .game-name {
        font-size: clamp(16px, 3vw, 26px);
        line-height: 1.1;
        font-weight: 700;
      }
    </style>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
  </head>
  <body>
    <main class="page">
      <div class="top-row">
        <a id="games-back-link" class="back-link" href="/">← Главная страница</a>
        <span id="games-mode-caption" class="top-caption">Сборные</span>
      </div>
      <h1 id="games-title">Игровые дисциплины</h1>

      <section class="games-list">
        <a id="cs2-link" class="game-link" href="/discipline/cs2?context=teams">
          <img class="game-thumb cs2-thumb" src="/logos/cs2%20logo.png" alt="Counter Strike 2" />
          <span class="game-name">COUNTER STRIKE 2</span>
        </a>
        <a id="dota2-link" class="game-link" href="/discipline/dota2?context=teams">
          <img class="game-thumb" src="/logos/dota2%20logo.png" alt="Dota 2" />
          <span class="game-name">DOTA 2</span>
        </a>
        <a id="clash-royale-link" class="game-link" href="/clash-royale?context=teams">
          <img class="game-thumb" src="/logos/cr%20logo.png" alt="Clash Royale" />
          <span class="game-name">CLASH ROYALE</span>
        </a>
        <a id="mlbb-link" class="game-link" href="/discipline/mlbb?context=teams">
          <img class="game-thumb" src="/logos/mlbb%20logo.png" alt="Mobile Legends" />
          <span class="game-name">MOBILE LEGENDS</span>
        </a>
        <a id="wot-link" class="game-link" href="/discipline/wot?context=teams">
          <img id="wot-thumb" class="game-thumb" src="/logos/wot%20logo.png" alt="Мир Танков" />
          <span id="wot-label" class="game-name">МИР ТАНКОВ</span>
        </a>
      </section>
    </main>

    <script>
      const tg = window.Telegram?.WebApp;
      if (tg) {
        tg.ready?.();
        tg.expand?.();
      }

      const safeLang = localStorage.getItem("cyber_lang") === "en" ? "en" : "ru";
      const I18N = {
        ru: {
          pageTitle: "Дисциплины",
          backToMain: "← Главная страница",
          modeTeams: "Сборные",
          modeTournaments: "Турниры",
          disciplinesTitle: "Игровые дисциплины",
          wotTitle: "МИР ТАНКОВ",
        },
        en: {
          pageTitle: "Disciplines",
          backToMain: "← Home",
          modeTeams: "National teams",
          modeTournaments: "Tournaments",
          disciplinesTitle: "Game disciplines",
          wotTitle: "WORLD OF TANKS",
        },
      };
      const text = I18N[safeLang];

      document.documentElement.lang = safeLang;
      document.title = text.pageTitle;

      const backLink = document.getElementById("games-back-link");
      const modeCaption = document.getElementById("games-mode-caption");
      const gamesTitle = document.getElementById("games-title");
      const mode = new URLSearchParams(window.location.search).get("view");
      const clashRoyaleLink = document.getElementById("clash-royale-link");
      const cs2Link = document.getElementById("cs2-link");
      const dota2Link = document.getElementById("dota2-link");
      const mlbbLink = document.getElementById("mlbb-link");
      const wotLink = document.getElementById("wot-link");
      const wotThumb = document.getElementById("wot-thumb");
      const wotLabel = document.getElementById("wot-label");
      const safeMode = mode === "tournaments" ? "tournaments" : "teams";
      if (backLink) {
        backLink.textContent = text.backToMain;
      }
      if (gamesTitle) {
        gamesTitle.textContent = text.disciplinesTitle;
      }
      if (wotThumb) {
        wotThumb.alt = text.wotTitle;
      }
      if (wotLabel) {
        wotLabel.textContent = text.wotTitle;
      }
      if (modeCaption) {
        if (safeMode === "tournaments") {
          modeCaption.textContent = text.modeTournaments;
        } else {
          modeCaption.textContent = text.modeTeams;
        }
      }
      if (cs2Link) {
        cs2Link.href = `/discipline/cs2?context=${safeMode}`;
      }
      if (dota2Link) {
        dota2Link.href = `/discipline/dota2?context=${safeMode}`;
      }
      if (clashRoyaleLink) {
        clashRoyaleLink.href = `/clash-royale?context=${safeMode}`;
      }
      if (mlbbLink) {
        mlbbLink.href = `/discipline/mlbb?context=${safeMode}`;
      }
      if (wotLink) {
        wotLink.href = `/discipline/wot?context=${safeMode}`;
      }

      const safeTheme = localStorage.getItem("cyber_theme") || "dark";
      document.body.classList.toggle("theme-light", safeTheme === "light");
    </script>
  </body>
</html>
"""


ACHIEVEMENTS_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Достижения</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;700&display=swap"
      rel="stylesheet"
    />
    <style>
      :root {
        --bg: #06080c;
        --text: #f5f7fa;
        --panel: #10141d;
        --panel-line: rgba(255, 255, 255, 0.16);
        --muted: #bac6d8;
      }

      body.theme-light {
        --bg: #f3f5f9;
        --text: #0f172a;
        --panel: #ffffff;
        --panel-line: rgba(15, 23, 42, 0.16);
        --muted: #5a6678;
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        min-height: 100vh;
        font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
        background: var(--bg);
        color: var(--text);
      }

      .page {
        width: min(900px, calc(100% - 24px));
        margin: 0 auto;
        padding: 74px 0 28px;
      }

      .back-link {
        display: inline-flex;
        align-items: center;
        text-decoration: none;
        color: var(--text);
        border: 1px solid var(--panel-line);
        border-radius: 10px;
        padding: 9px 12px;
        background: var(--panel);
        margin-bottom: 16px;
      }

      .message {
        font-size: clamp(24px, 5vw, 46px);
        line-height: 1.15;
        font-weight: 700;
      }
    </style>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
  </head>
  <body>
    <main class="page">
      <a id="achievements-back-link" class="back-link" href="/">← Главная страница</a>
      <div id="achievements-message" class="message">Слишком много добились, не поместится на сайте</div>
    </main>

    <script>
      const tg = window.Telegram?.WebApp;
      if (tg) {
        tg.ready?.();
        tg.expand?.();
      }

      const safeLang = localStorage.getItem("cyber_lang") === "en" ? "en" : "ru";
      const I18N = {
        ru: {
          pageTitle: "Достижения",
          backToMain: "← Главная страница",
          message: "Слишком много добились, не поместится на сайте",
        },
        en: {
          pageTitle: "Achievements",
          backToMain: "← Home",
          message: "We've achieved too much, it won't fit on the website.",
        },
      };
      const text = I18N[safeLang];
      document.documentElement.lang = safeLang;
      document.title = text.pageTitle;

      const backLink = document.getElementById("achievements-back-link");
      const message = document.getElementById("achievements-message");
      if (backLink) {
        backLink.textContent = text.backToMain;
      }
      if (message) {
        message.textContent = text.message;
      }

      const safeTheme = localStorage.getItem("cyber_theme") || "dark";
      document.body.classList.toggle("theme-light", safeTheme === "light");
    </script>
  </body>
</html>
"""


DISCIPLINE_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>__DISCIPLINE_TITLE__</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;700&display=swap"
      rel="stylesheet"
    />
    <style>
      :root {
        --bg: #06080c;
        --text: #f5f7fa;
        --panel: #10141d;
        --panel-line: rgba(255, 255, 255, 0.16);
        --muted: #bac6d8;
        --accent: #4f8cff;
        --ok: #6ee7b7;
      }

      body.theme-light {
        --bg: #f3f5f9;
        --text: #0f172a;
        --panel: #ffffff;
        --panel-line: rgba(15, 23, 42, 0.16);
        --muted: #5a6678;
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        min-height: 100vh;
        font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
        background: var(--bg);
        color: var(--text);
      }

      .page {
        width: min(860px, calc(100% - 24px));
        margin: 0 auto;
        padding: 74px 0 28px;
      }

      .top-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
      }

      .back-link {
        display: inline-flex;
        align-items: center;
        text-decoration: none;
        color: var(--text);
        border: 1px solid var(--panel-line);
        border-radius: 10px;
        padding: 9px 12px;
        background: var(--panel);
      }

      .mode-caption {
        color: var(--muted);
        font-size: 14px;
      }

      .card {
        margin-top: 14px;
        border: 1px solid var(--panel-line);
        border-radius: 14px;
        background: var(--panel);
        padding: 14px;
      }

      .discipline-head {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 14px;
      }

      .discipline-logo {
        width: 96px;
        height: 62px;
        object-fit: contain;
        border-radius: 8px;
        background: #0a0f18;
        padding: 4px;
      }

      body.theme-light .discipline-logo {
        background: #edf2fb;
      }

      .discipline-title {
        margin: 0;
        font-size: clamp(24px, 4vw, 36px);
        line-height: 1.1;
      }

      .entry-stage {
        min-height: 250px;
        display: grid;
        place-items: center;
      }

      .action-btn {
        border-radius: 10px;
        border: 1px solid var(--accent);
        background: var(--accent);
        color: #ffffff;
        font-weight: 700;
        padding: 12px 14px;
        width: min(360px, 100%);
        cursor: pointer;
      }

      .status {
        min-height: 22px;
        margin-top: 12px;
        color: var(--ok);
        font-weight: 500;
      }

      .hidden {
        display: none !important;
      }

      .modal-backdrop {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.46);
        z-index: 50;
        display: grid;
        place-items: center;
        padding: 16px;
      }

      .modal {
        width: min(640px, 100%);
        border-radius: 14px;
        border: 1px solid var(--panel-line);
        background: var(--panel);
        padding: 16px;
      }

      .modal-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 10px;
      }

      .modal-top h2 {
        margin: 0;
        font-size: clamp(20px, 3vw, 28px);
      }

      .close-modal-btn {
        border: 1px solid var(--panel-line);
        background: transparent;
        color: var(--text);
        border-radius: 8px;
        width: 34px;
        height: 34px;
        cursor: pointer;
      }

      .form {
        display: grid;
        gap: 10px;
      }

      label {
        font-size: 13px;
        color: var(--muted);
      }

      input {
        width: 100%;
        border-radius: 10px;
        border: 1px solid var(--panel-line);
        background: transparent;
        color: var(--text);
        padding: 10px 12px;
        font-family: inherit;
      }
    </style>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
  </head>
  <body>
    <main class="page">
      <div class="top-row">
        <a id="back-link" class="back-link" href="/games?view=teams">← Назад к дисциплинам</a>
        <span id="mode-caption" class="mode-caption">Сборные</span>
      </div>

      <section class="card" data-discipline-slug="__DISCIPLINE_SLUG__">
        <div class="discipline-head">
          <img id="discipline-logo" class="discipline-logo" src="__DISCIPLINE_LOGO__" alt="__DISCIPLINE_TITLE__" />
          <h1 id="discipline-title" class="discipline-title">__DISCIPLINE_TITLE__</h1>
        </div>

        <section id="entry-stage" class="entry-stage">
          <button id="primary-btn" class="action-btn" type="button">Подать заявку в сборную</button>
        </section>

        <div id="status" class="status"></div>
      </section>
    </main>

    <div id="team-modal-backdrop" class="modal-backdrop hidden" role="dialog" aria-modal="true" aria-labelledby="team-form-title">
      <section class="modal">
        <div class="modal-top">
          <h2 id="team-form-title">Подача заявления в сборную</h2>
          <button id="close-modal-btn" class="close-modal-btn" type="button" aria-label="Закрыть">x</button>
        </div>

        <form id="team-form" class="form">
          <div>
            <label id="team-full-name-label" for="team-full-name">ФИО</label>
            <input id="team-full-name" type="text" maxlength="140" placeholder="Иванов Иван Иванович" required />
          </div>
          <div>
            <label id="team-group-number-label" for="team-group-number">Номер группы</label>
            <input id="team-group-number" type="text" maxlength="60" placeholder="БИ-22-1" required />
          </div>
          <div>
            <label id="team-game-id-label" for="team-game-id">Игровой ID / Никнейм</label>
            <input id="team-game-id" type="text" maxlength="80" placeholder="Ник или ID в игре" required />
          </div>
          <button id="team-submit-btn" class="action-btn" type="submit">Отправить заявление</button>
        </form>
      </section>
    </div>

    <script>
      const tg = window.Telegram?.WebApp;
      if (tg) {
        tg.ready?.();
        tg.expand?.();
      }

      const safeLang = localStorage.getItem("cyber_lang") === "en" ? "en" : "ru";
      const I18N = {
        ru: {
          backToDisciplines: "← Назад к дисциплинам",
          modeTeams: "Сборные",
          modeTournaments: "Турниры",
          actionTeams: "Подать заявку в сборную",
          actionTournaments: "Зарегистрироваться на турнир",
          teamFormTitle: "Подача заявления в сборную",
          close: "Закрыть",
          fullName: "ФИО",
          fullNamePlaceholder: "Иванов Иван Иванович",
          groupNumber: "Номер группы",
          groupNumberPlaceholder: "БИ-22-1",
          gameId: "Игровой ID / Никнейм",
          gameIdPlaceholder: "Ник или ID в игре",
          submitTeam: "Отправить заявление",
          registrationClosed: "Пока регистрация не открыта",
          teamApplicationSent: "Заявление в сборную отправлено",
        },
        en: {
          backToDisciplines: "← Back to disciplines",
          modeTeams: "National teams",
          modeTournaments: "Tournaments",
          actionTeams: "Apply to national team",
          actionTournaments: "Register for tournament",
          teamFormTitle: "National team application",
          close: "Close",
          fullName: "Full name",
          fullNamePlaceholder: "John Doe",
          groupNumber: "Group number",
          groupNumberPlaceholder: "BI-22-1",
          gameId: "Game ID / Nickname",
          gameIdPlaceholder: "Nickname or in-game ID",
          submitTeam: "Submit application",
          registrationClosed: "Registration is not open yet",
          teamApplicationSent: "Team application sent",
        },
      };
      const text = I18N[safeLang];
      document.documentElement.lang = safeLang;

      const safeTheme = localStorage.getItem("cyber_theme") || "dark";
      document.body.classList.toggle("theme-light", safeTheme === "light");

      const params = new URLSearchParams(window.location.search);
      const context = params.get("context") === "tournaments" ? "tournaments" : "teams";
      const modeCaption = document.getElementById("mode-caption");
      const backLink = document.getElementById("back-link");
      const primaryBtn = document.getElementById("primary-btn");
      const status = document.getElementById("status");
      const modalBackdrop = document.getElementById("team-modal-backdrop");
      const closeModalBtn = document.getElementById("close-modal-btn");
      const teamFormTitle = document.getElementById("team-form-title");
      const teamFullNameLabel = document.getElementById("team-full-name-label");
      const teamFullNameInput = document.getElementById("team-full-name");
      const teamGroupNumberLabel = document.getElementById("team-group-number-label");
      const teamGroupNumberInput = document.getElementById("team-group-number");
      const teamGameIdLabel = document.getElementById("team-game-id-label");
      const teamGameIdInput = document.getElementById("team-game-id");
      const teamSubmitBtn = document.getElementById("team-submit-btn");
      const teamForm = document.getElementById("team-form");
      const disciplineTitle = document.getElementById("discipline-title");
      const disciplineLogo = document.getElementById("discipline-logo");
      const disciplineCard = document.querySelector(".card[data-discipline-slug]");
      const disciplineSlug = disciplineCard ? disciplineCard.dataset.disciplineSlug : "";
      const DISCIPLINE_TITLES = {
        cs2: { ru: "COUNTER STRIKE 2", en: "COUNTER STRIKE 2" },
        dota2: { ru: "DOTA 2", en: "DOTA 2" },
        mlbb: { ru: "MOBILE LEGENDS", en: "MOBILE LEGENDS" },
        wot: { ru: "МИР ТАНКОВ", en: "WORLD OF TANKS" },
      };
      const localizedDisciplineTitle = DISCIPLINE_TITLES[disciplineSlug]?.[safeLang];
      if (localizedDisciplineTitle) {
        if (disciplineTitle) {
          disciplineTitle.textContent = localizedDisciplineTitle;
        }
        if (disciplineLogo) {
          disciplineLogo.alt = localizedDisciplineTitle;
        }
        document.title = localizedDisciplineTitle;
      }

      if (backLink) {
        backLink.textContent = text.backToDisciplines;
      }
      if (teamFormTitle) {
        teamFormTitle.textContent = text.teamFormTitle;
      }
      if (closeModalBtn) {
        closeModalBtn.setAttribute("aria-label", text.close);
      }
      if (teamFullNameLabel) {
        teamFullNameLabel.textContent = text.fullName;
      }
      if (teamFullNameInput) {
        teamFullNameInput.placeholder = text.fullNamePlaceholder;
      }
      if (teamGroupNumberLabel) {
        teamGroupNumberLabel.textContent = text.groupNumber;
      }
      if (teamGroupNumberInput) {
        teamGroupNumberInput.placeholder = text.groupNumberPlaceholder;
      }
      if (teamGameIdLabel) {
        teamGameIdLabel.textContent = text.gameId;
      }
      if (teamGameIdInput) {
        teamGameIdInput.placeholder = text.gameIdPlaceholder;
      }
      if (teamSubmitBtn) {
        teamSubmitBtn.textContent = text.submitTeam;
      }

      if (context === "tournaments") {
        modeCaption.textContent = text.modeTournaments;
        primaryBtn.textContent = text.actionTournaments;
        backLink.href = "/games?view=tournaments";
      } else {
        modeCaption.textContent = text.modeTeams;
        primaryBtn.textContent = text.actionTeams;
        backLink.href = "/games?view=teams";
      }

      function setStatus(text) {
        status.textContent = text;
      }

      function openTeamModal() {
        modalBackdrop.classList.remove("hidden");
      }

      function closeTeamModal() {
        modalBackdrop.classList.add("hidden");
      }

      primaryBtn.addEventListener("click", () => {
        if (context === "tournaments") {
          setStatus(text.registrationClosed);
          return;
        }
        openTeamModal();
      });

      closeModalBtn.addEventListener("click", closeTeamModal);
      modalBackdrop.addEventListener("click", (event) => {
        if (event.target === modalBackdrop) {
          closeTeamModal();
        }
      });

      teamForm.addEventListener("submit", (event) => {
        event.preventDefault();
        closeTeamModal();
        teamForm.reset();
        setStatus(text.teamApplicationSent);
      });
    </script>
  </body>
</html>
"""


CLASH_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Регистрация Clash Royale</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=IBM+Plex+Sans:wght@400;500;700&display=swap"
      rel="stylesheet"
    />
    <style>
      :root {
        --bg: #06080c;
        --text: #f5f7fa;
        --panel: #10141d;
        --panel-line: rgba(255, 255, 255, 0.16);
        --muted: #bac6d8;
        --link: #a8ccff;
        --accent: #4f8cff;
        --ok: #6ee7b7;
        --error: #fda4af;
      }

      body.theme-light {
        --bg: #f3f5f9;
        --text: #0f172a;
        --panel: #ffffff;
        --panel-line: rgba(15, 23, 42, 0.16);
        --muted: #5a6678;
        --link: #2058cc;
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        min-height: 100vh;
        font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
        background: var(--bg);
        color: var(--text);
      }

      .page {
        width: min(1100px, 100%);
        margin: 0 auto;
        padding: 74px 12px 28px;
      }

      .card {
        width: min(760px, 100%);
        margin: 0 auto;
        border: 1px solid var(--panel-line);
        background: var(--panel);
        border-radius: 14px;
        padding: 18px;
      }

      .top-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
      }

      .back-btn {
        display: inline-flex;
        align-items: center;
        border: 1px solid var(--panel-line);
        border-radius: 10px;
        padding: 8px 10px;
        color: var(--text);
        text-decoration: none;
        font-size: 14px;
        font-weight: 700;
      }

      .game-tag {
        border: 1px solid var(--panel-line);
        border-radius: 999px;
        padding: 6px 10px;
        font-size: 12px;
        color: var(--muted);
        letter-spacing: 0.04em;
      }

      h1 {
        margin: 14px 0 6px;
        font-family: "Bebas Neue", "Arial Narrow", sans-serif;
        font-size: clamp(38px, 8vw, 58px);
        letter-spacing: 0.04em;
        line-height: 0.95;
      }

      .subtitle {
        margin: 0 0 14px;
        color: var(--muted);
      }

      .form {
        display: grid;
        gap: 12px;
      }

      label {
        font-size: 13px;
        color: var(--muted);
        display: inline-block;
        margin-bottom: 6px;
      }

      input {
        width: 100%;
        border-radius: 10px;
        border: 1px solid var(--panel-line);
        background: transparent;
        color: var(--text);
        padding: 10px 12px;
        font-family: inherit;
        font-size: 14px;
      }

      .submit-btn {
        margin-top: 4px;
        border-radius: 10px;
        border: 1px solid var(--accent);
        background: var(--accent);
        color: #ffffff;
        font-weight: 700;
        padding: 11px 12px;
        cursor: pointer;
      }

      .submit-btn:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }

      .status {
        min-height: 20px;
        margin-top: 8px;
        font-size: 13px;
        color: var(--muted);
      }

      .existing-action {
        margin-bottom: 12px;
      }

      .entry-stage {
        min-height: 250px;
        display: grid;
        place-items: center;
        padding: 16px 0;
      }

      .entry-btn {
        width: min(340px, 100%);
        padding: 13px 14px;
        font-size: 16px;
      }

      .hidden {
        display: none !important;
      }

      .modal-backdrop {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.46);
        z-index: 50;
        display: grid;
        place-items: center;
        padding: 16px;
      }

      .modal {
        width: min(640px, 100%);
        border-radius: 14px;
        border: 1px solid var(--panel-line);
        background: var(--panel);
        padding: 16px;
      }

      .modal-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 10px;
      }

      .modal-top h2 {
        margin: 0;
        font-size: clamp(20px, 3vw, 28px);
      }

      .close-modal-btn {
        border: 1px solid var(--panel-line);
        background: transparent;
        color: var(--text);
        border-radius: 8px;
        width: 34px;
        height: 34px;
        cursor: pointer;
      }
    </style>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
  </head>
  <body>
    <main class="page">
      <section class="card">
        <div class="top-row">
          <a id="back-btn" class="back-btn" href="/">← На главную</a>
          <span class="game-tag">CLASH ROYALE</span>
        </div>

        <section id="entry-stage" class="entry-stage">
          <button id="open-form-btn" class="submit-btn entry-btn" type="button">Зарегистрироваться на турнир</button>
        </section>
      </section>
    </main>

    <div id="clash-modal-backdrop" class="modal-backdrop hidden" role="dialog" aria-modal="true" aria-labelledby="form-title">
      <section class="modal">
        <div class="modal-top">
          <h2 id="form-title">Регистрация</h2>
          <button id="close-modal-btn" class="close-modal-btn" type="button" aria-label="Закрыть">x</button>
        </div>
        <p id="form-subtitle" class="subtitle">Заполни данные для регистрации на дисциплину.</p>

        <div id="existing-action" class="existing-action hidden">
          <button id="edit-existing-btn" class="submit-btn" type="button">Изменить данные в регистрации</button>
        </div>

        <form id="clash-form" class="form">
          <div>
            <label id="full-name-label" for="full-name">ФИО</label>
            <input id="full-name" name="full_name" type="text" maxlength="140" placeholder="Иванов Иван Иванович" required />
          </div>
          <div>
            <label id="group-number-label" for="group-number">Номер группы</label>
            <input id="group-number" name="group_number" type="text" maxlength="60" placeholder="БИ-22-1" required />
          </div>
          <div>
            <label id="supercell-id-label" for="supercell-id">SUPERCELL ID</label>
            <input id="supercell-id" name="supercell_id" type="text" maxlength="40" placeholder="#2ABCDEF9" required />
          </div>
          <button id="submit-btn" class="submit-btn" type="submit">Зарегистрироваться</button>
        </form>

        <div id="status" class="status"></div>
      </section>
    </div>

    <script>
      const tg = window.Telegram?.WebApp;
      if (tg) {
        tg.ready?.();
        tg.expand?.();
      }

      const safeLang = localStorage.getItem("cyber_lang") === "en" ? "en" : "ru";
      const I18N = {
        ru: {
          pageTitle: "Регистрация Clash Royale",
          backToMain: "← На главную",
          entryTournament: "Зарегистрироваться на турнир",
          entryTeams: "Подать заявку в сборную",
          close: "Закрыть",
          titleTournament: "Регистрация на турнир",
          titleTeams: "Подача заявления в сборную",
          subtitleTournament: "Заполни данные для регистрации на турнир.",
          subtitleTeams: "Заполни данные для подачи заявления в сборную.",
          editRegistration: "Изменить данные в регистрации",
          fullName: "ФИО",
          groupNumber: "Номер группы",
          supercellId: "SUPERCELL ID",
          fullNamePlaceholder: "Иванов Иван Иванович",
          groupNumberPlaceholder: "БИ-22-1",
          supercellIdPlaceholder: "#2ABCDEF9",
          saveChanges: "Сохранить изменения",
          telegramRequired: "Открой мини-приложение из Telegram, чтобы зарегистрироваться.",
          fillAllFields: "Заполни все поля.",
          saving: "Сохраняю...",
          registrationError: "Ошибка регистрации",
          registrationSaved: "Регистрация сохранена.",
          registrationErrorGeneric: "Ошибка регистрации.",
          editHint: "Измени данные и нажми «Сохранить изменения».",
        },
        en: {
          pageTitle: "Clash Royale Registration",
          backToMain: "← Home",
          entryTournament: "Register for tournament",
          entryTeams: "Apply to national team",
          close: "Close",
          titleTournament: "Tournament registration",
          titleTeams: "National team application",
          subtitleTournament: "Fill in the details for tournament registration.",
          subtitleTeams: "Fill in the details for the national team application.",
          editRegistration: "Edit registration details",
          fullName: "Full name",
          groupNumber: "Group number",
          supercellId: "SUPERCELL ID",
          fullNamePlaceholder: "John Doe",
          groupNumberPlaceholder: "BI-22-1",
          supercellIdPlaceholder: "#2ABCDEF9",
          saveChanges: "Save changes",
          telegramRequired: "Open the mini app from Telegram to register.",
          fillAllFields: "Fill in all fields.",
          saving: "Saving...",
          registrationError: "Registration error",
          registrationSaved: "Registration saved.",
          registrationErrorGeneric: "Registration error.",
          editHint: "Update your data and click \"Save changes\".",
        },
      };
      const text = I18N[safeLang];
      document.documentElement.lang = safeLang;
      document.title = text.pageTitle;

      const form = document.getElementById("clash-form");
      const submitBtn = document.getElementById("submit-btn");
      const statusEl = document.getElementById("status");
      const existingActionEl = document.getElementById("existing-action");
      const editExistingBtn = document.getElementById("edit-existing-btn");
      const entryStage = document.getElementById("entry-stage");
      const openFormBtn = document.getElementById("open-form-btn");
      const modalBackdrop = document.getElementById("clash-modal-backdrop");
      const closeModalBtn = document.getElementById("close-modal-btn");
      const formTitle = document.getElementById("form-title");
      const formSubtitle = document.getElementById("form-subtitle");
      const backBtn = document.getElementById("back-btn");
      const fullNameLabel = document.getElementById("full-name-label");
      const groupNumberLabel = document.getElementById("group-number-label");
      const supercellIdLabel = document.getElementById("supercell-id-label");
      const fullNameInput = document.getElementById("full-name");
      const groupNumberInput = document.getElementById("group-number");
      const supercellIdInput = document.getElementById("supercell-id");
      let telegramUserId = null;
      let telegramUsername = null;

      let hasExistingRegistration = false;
      let updateMode = false;
      let registrationBootstrapped = false;
      const contextParam = new URLSearchParams(window.location.search).get("context");
      const isTournamentFlow = contextParam === "tournaments";
      const contextKey = isTournamentFlow ? "tournaments" : "national_teams";
      const primaryActionLabel = isTournamentFlow
        ? text.entryTournament
        : text.entryTeams;
      const formTitleLabel = isTournamentFlow ? text.titleTournament : text.titleTeams;
      const formSubtitleLabel = isTournamentFlow
        ? text.subtitleTournament
        : text.subtitleTeams;
      const defaultSubmitLabel = primaryActionLabel;
      if (backBtn) {
        backBtn.textContent = text.backToMain;
        backBtn.href = isTournamentFlow ? "/games?view=tournaments" : "/games?view=teams";
      }
      if (openFormBtn) {
        openFormBtn.textContent = primaryActionLabel;
      }
      if (formTitle) {
        formTitle.textContent = formTitleLabel;
      }
      if (formSubtitle) {
        formSubtitle.textContent = formSubtitleLabel;
      }
      if (editExistingBtn) {
        editExistingBtn.textContent = text.editRegistration;
      }
      if (fullNameLabel) {
        fullNameLabel.textContent = text.fullName;
      }
      if (groupNumberLabel) {
        groupNumberLabel.textContent = text.groupNumber;
      }
      if (supercellIdLabel) {
        supercellIdLabel.textContent = text.supercellId;
      }
      if (fullNameInput) {
        fullNameInput.placeholder = text.fullNamePlaceholder;
      }
      if (groupNumberInput) {
        groupNumberInput.placeholder = text.groupNumberPlaceholder;
      }
      if (supercellIdInput) {
        supercellIdInput.placeholder = text.supercellIdPlaceholder;
      }
      if (closeModalBtn) {
        closeModalBtn.setAttribute("aria-label", text.close);
      }

      const safeTheme = localStorage.getItem("cyber_theme") || "dark";
      document.body.classList.toggle("theme-light", safeTheme === "light");

      function setStatus(text, isError = false) {
        statusEl.textContent = text;
        statusEl.style.color = isError ? "var(--error)" : "var(--ok)";
      }

      function parseUserFromQueryString(raw) {
        if (!raw) {
          return null;
        }
        try {
          const userJson = new URLSearchParams(raw).get("user");
          return userJson ? JSON.parse(userJson) : null;
        } catch {
          return null;
        }
      }

      function parseUserFromUrl() {
        try {
          const hashParams = new URLSearchParams(window.location.hash.replace(/^#/, ""));
          const searchParams = new URLSearchParams(window.location.search);
          const tgWebAppData = hashParams.get("tgWebAppData") || searchParams.get("tgWebAppData");
          if (tgWebAppData) {
            const decoded = decodeURIComponent(tgWebAppData);
            const userFromData = parseUserFromQueryString(decoded);
            if (userFromData) {
              return userFromData;
            }
          }
          const tgWebAppUser = hashParams.get("tgWebAppUser") || searchParams.get("tgWebAppUser");
          if (tgWebAppUser) {
            return JSON.parse(decodeURIComponent(tgWebAppUser));
          }
        } catch {
          return null;
        }
        return null;
      }

      function parseUserFromCache() {
        try {
          const raw = localStorage.getItem("cyber_tg_user_cache");
          if (!raw) {
            return null;
          }
          const cached = JSON.parse(raw);
          if (!cached || !cached.id) {
            return null;
          }
          if (cached.ts && Date.now() - Number(cached.ts) > 30 * 24 * 60 * 60 * 1000) {
            return null;
          }
          return cached;
        } catch {
          return null;
        }
      }

      function refreshTelegramIdentity() {
        const unsafeUser = tg?.initDataUnsafe?.user || null;
        let parsedUser = null;
        if (!unsafeUser && tg?.initData) {
          parsedUser = parseUserFromQueryString(tg.initData);
        }
        const urlUser = parseUserFromUrl();
        const cachedUser = parseUserFromCache();
        const telegramUser = unsafeUser || parsedUser || urlUser || cachedUser || {};
        const rawUserId = telegramUser.id ?? null;
        const parsedUserId = rawUserId !== null ? Number.parseInt(String(rawUserId), 10) : NaN;
        telegramUserId = Number.isFinite(parsedUserId) && parsedUserId > 0 ? parsedUserId : null;
        telegramUsername = telegramUser.username ? String(telegramUser.username).toLowerCase() : null;

        if (telegramUserId !== null) {
          try {
            localStorage.setItem(
              "cyber_tg_user_cache",
              JSON.stringify({
                id: telegramUserId,
                username: telegramUsername,
                ts: Date.now(),
              }),
            );
          } catch {}
        }
      }

      function ensureTelegramId() {
        if (telegramUserId === null) {
          setStatus(text.telegramRequired, true);
          submitBtn.disabled = true;
          editExistingBtn.disabled = true;
          return false;
        }
        submitBtn.disabled = false;
        editExistingBtn.disabled = false;
        return true;
      }

      function syncButtonText() {
        submitBtn.textContent = updateMode ? text.saveChanges : defaultSubmitLabel;
      }

      function setExistingView(active) {
        if (active) {
          form.classList.add("hidden");
          existingActionEl.classList.remove("hidden");
        } else {
          form.classList.remove("hidden");
          existingActionEl.classList.add("hidden");
        }
      }

      function openModal() {
        modalBackdrop.classList.remove("hidden");
      }

      function closeModal() {
        modalBackdrop.classList.add("hidden");
      }

      async function loadExistingRegistration() {
        refreshTelegramIdentity();
        if (!ensureTelegramId()) {
          setExistingView(false);
          syncButtonText();
          return;
        }

        const query = new URLSearchParams();
        query.set("telegram_user_id", String(telegramUserId));
        query.set("context", contextKey);
        if (telegramUsername) {
          query.set("telegram_username", telegramUsername);
        }

        try {
          const response = await fetch(`/api/clash-royale/registration?${query.toString()}`);
          if (!response.ok) {
            setExistingView(false);
            syncButtonText();
            return;
          }

          const data = await response.json();
          if (!data.registration) {
            setExistingView(false);
            syncButtonText();
            return;
          }

          document.getElementById("full-name").value = data.registration.full_name || "";
          document.getElementById("group-number").value = data.registration.group_number || "";
          document.getElementById("supercell-id").value = data.registration.supercell_id || "";
          hasExistingRegistration = true;
          updateMode = false;
          setExistingView(true);
          syncButtonText();
          setStatus("");
        } catch {
          setExistingView(false);
          syncButtonText();
        }
      }

      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!ensureTelegramId()) {
          return;
        }

        const payload = {
          full_name: document.getElementById("full-name").value.trim(),
          group_number: document.getElementById("group-number").value.trim(),
          supercell_id: document.getElementById("supercell-id").value.trim(),
          telegram_user_id: telegramUserId,
          telegram_username: telegramUsername,
          context: contextKey,
          allow_update: updateMode,
        };

        if (!payload.full_name || !payload.group_number || !payload.supercell_id) {
          setStatus(text.fillAllFields, true);
          return;
        }

        submitBtn.disabled = true;
        setStatus(text.saving);

        try {
          const response = await fetch("/api/clash-royale/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });

          const data = await response.json();
          if (!response.ok) {
            throw new Error(data.detail || text.registrationError);
          }

          setStatus(data.message || text.registrationSaved);
          hasExistingRegistration = true;
          updateMode = false;
          setExistingView(true);
          syncButtonText();
        } catch (error) {
          setStatus(error.message || text.registrationErrorGeneric, true);
        } finally {
          submitBtn.disabled = false;
        }
      });

      editExistingBtn.addEventListener("click", () => {
        updateMode = true;
        setExistingView(false);
        syncButtonText();
        setStatus(text.editHint);
      });

      async function initRegistrationPage() {
        if (registrationBootstrapped) {
          return;
        }
        registrationBootstrapped = true;
        refreshTelegramIdentity();
        syncButtonText();
        setExistingView(false);
        await loadExistingRegistration();
        if (telegramUserId === null) {
          setTimeout(async () => {
            refreshTelegramIdentity();
            if (telegramUserId !== null) {
              await loadExistingRegistration();
            } else {
              ensureTelegramId();
            }
          }, 900);
        }
      }

      openFormBtn.addEventListener("click", async () => {
        openModal();
        setStatus("");
        syncButtonText();
        setExistingView(false);
        await initRegistrationPage();
      });

      closeModalBtn.addEventListener("click", closeModal);
      modalBackdrop.addEventListener("click", (event) => {
        if (event.target === modalBackdrop) {
          closeModal();
        }
      });

      syncButtonText();
      setExistingView(false);
      entryStage.classList.remove("hidden");
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


class ClashRoyaleRegistrationRequest(BaseModel):
    full_name: str
    group_number: str
    supercell_id: str
    telegram_user_id: int | None = None
    telegram_username: str | None = None
    context: str = "tournaments"
    allow_update: bool = False


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


@app.get("/games", response_class=HTMLResponse)
async def games_page(request: Request) -> HTMLResponse:
    return HTMLResponse(content=GAMES_TEMPLATE)


@app.get("/discipline/{slug}", response_class=HTMLResponse)
async def discipline_page(slug: str, request: Request) -> HTMLResponse:
    info = DISCIPLINE_PAGES.get(slug)
    if not info:
        raise HTTPException(status_code=404, detail="Discipline not found")

    html = (
        DISCIPLINE_TEMPLATE.replace("__DISCIPLINE_TITLE__", info["title"])
        .replace("__DISCIPLINE_LOGO__", info["logo"])
        .replace("__DISCIPLINE_SLUG__", slug)
    )
    return HTMLResponse(content=html)


@app.get("/achievements", response_class=HTMLResponse)
async def achievements_page(request: Request) -> HTMLResponse:
    return HTMLResponse(content=ACHIEVEMENTS_TEMPLATE)


@app.get("/clash-royale", response_class=HTMLResponse)
async def clash_royale_page(request: Request) -> HTMLResponse:
    return HTMLResponse(content=CLASH_TEMPLATE)


@app.get("/api/clash-royale/registration")
async def clash_royale_registration(
    telegram_user_id: int | None = None,
    telegram_username: str | None = None,
    context: str = "tournaments",
) -> dict[str, object]:
    if getattr(app.state, "db_error", None):
        raise HTTPException(status_code=503, detail=f"DB is unavailable: {app.state.db_error}")

    data = get_clash_registration(
        telegram_user_id=telegram_user_id,
        telegram_username=telegram_username,
        context=normalize_clash_context(context),
    )
    return {"registration": data}


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


@app.post("/api/clash-royale/register")
async def clash_royale_register(payload: ClashRoyaleRegistrationRequest) -> dict[str, str]:
    if getattr(app.state, "db_error", None):
        raise HTTPException(status_code=503, detail=f"DB is unavailable: {app.state.db_error}")

    full_name = payload.full_name.strip()
    group_number = payload.group_number.strip()
    supercell_id = payload.supercell_id.strip().upper()
    telegram_user_id = payload.telegram_user_id
    telegram_username = payload.telegram_username.strip() if payload.telegram_username else None
    context = normalize_clash_context(payload.context)

    if len(full_name) < 5:
        raise HTTPException(status_code=400, detail="Укажи корректное ФИО.")
    if len(group_number) < 2:
        raise HTTPException(status_code=400, detail="Укажи корректный номер группы.")
    if len(supercell_id) < 3:
        raise HTTPException(status_code=400, detail="Укажи корректный SUPERCELL ID.")

    try:
        action = upsert_clash_registration(
            full_name=full_name,
            group_number=group_number,
            supercell_id=supercell_id,
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_username,
            context=context,
            allow_update=payload.allow_update,
        )
    except ValueError as exc:
        code = str(exc)
        if code == "SUPERCELL_ID_ALREADY_USED":
            raise HTTPException(status_code=409, detail="Этот SUPERCELL ID уже занят другим игроком.") from exc
        if code == "USER_ALREADY_REGISTERED":
            raise HTTPException(
                status_code=409,
                detail="Ты уже зарегистрирован. Нажми кнопку «Изменить данные в регистрации».",
            ) from exc
        if code == "REGISTRATION_NOT_FOUND":
            raise HTTPException(status_code=404, detail="Регистрация пользователя не найдена.") from exc
        if code == "IDENTITY_REQUIRED":
            raise HTTPException(status_code=400, detail="Не удалось определить Telegram ID пользователя.") from exc
        raise HTTPException(status_code=400, detail=code) from exc

    message = "Данные регистрации обновлены." if action == "updated" else "Регистрация на Clash Royale сохранена."
    return {"message": message}


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


