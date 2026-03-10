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
    upsert_clash_registration,
    upsert_registration,
)


app = FastAPI()
app.mount("/assets", StaticFiles(directory=Path(__file__).parent / "assets"), name="assets")


TOURNAMENTS = ["clash royale", "dota 2", "cs go"]


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>КиберРеактор</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;700;800&display=swap"
      rel="stylesheet"
    />
    <style>
      :root {
        --bg: #1f2024;
        --phone: #efefef;
        --panel: #3f4045;
        --card: #d8d8d8;
        --text: #101010;
        --muted: #595959;
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

      .app-shell {
        width: 100%;
        min-height: 100vh;
        display: grid;
        place-items: center;
        padding: 16px;
      }

      .frame {
        width: min(390px, calc(100vw - 20px));
      }

      .frame-title {
        margin: 0 0 8px;
        color: #86888d;
        font-size: 33px;
        line-height: 1;
        font-weight: 500;
      }

      .phone {
        position: relative;
        width: 100%;
        min-height: 640px;
        background: var(--phone);
        overflow: hidden;
      }

      .menu-backdrop {
        position: absolute;
        inset: 0;
        background: rgba(0, 0, 0, 0.24);
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.2s ease;
        z-index: 25;
      }

      .menu-backdrop.open {
        opacity: 1;
        pointer-events: auto;
      }

      .menu-panel {
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: min(250px, 72vw);
        background: var(--panel);
        padding: 18px 14px;
        transform: translateX(-100%);
        transition: transform 0.2s ease;
        z-index: 30;
      }

      .menu-panel.open {
        transform: translateX(0);
      }

      .menu-head {
        display: flex;
        justify-content: flex-start;
      }

      .menu-btn,
      .menu-btn-fake {
        width: 42px;
        height: 42px;
        border-radius: 11px;
        border: 0;
        background: #dcdcdc;
        display: inline-grid;
        place-items: center;
        cursor: pointer;
        flex-shrink: 0;
      }

      .menu-btn-fake {
        cursor: default;
      }

      .menu-lines,
      .menu-lines::before,
      .menu-lines::after {
        display: block;
        width: 17px;
        height: 2px;
        background: #787878;
        border-radius: 999px;
        content: "";
      }

      .menu-lines {
        position: relative;
      }

      .menu-lines::before {
        position: absolute;
        top: -5px;
      }

      .menu-lines::after {
        position: absolute;
        top: 5px;
      }

      .menu-nav {
        margin-top: 18px;
        display: grid;
        gap: 10px;
      }

      .menu-link {
        border: 0;
        border-radius: 10px;
        background: #e2e2e2;
        color: #1e1e1e;
        font-family: inherit;
        font-size: 30px;
        font-weight: 500;
        line-height: 1;
        padding: 11px 12px;
        cursor: pointer;
      }

      .topbar {
        height: 74px;
        background: #f7f7f7;
        display: flex;
        align-items: center;
        padding: 0 12px;
      }

      .topbar .menu-btn {
        z-index: 10;
      }

      .brand-logo {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        object-fit: cover;
        margin: 0 auto;
        border: 2px solid #0d0d0d;
      }

      .topbar-spacer {
        width: 42px;
        flex-shrink: 0;
      }

      .screen-wrap {
        padding: 14px 10px 16px;
      }

      .screen {
        display: none;
      }

      .screen.active {
        display: block;
      }

      .banner-placeholder {
        height: 220px;
        width: 100%;
        background: #cdcdcd;
        display: grid;
        place-items: center;
        font-size: 35px;
        letter-spacing: 0.03em;
        color: #252525;
        margin-bottom: 14px;
      }

      .game-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px;
      }

      .game-card {
        border-radius: 8px;
        border: 0;
        background: var(--card);
        min-height: 74px;
        padding: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
      }

      .game-card.actionable {
        cursor: pointer;
      }

      .game-card.empty {
        min-height: 62px;
      }

      .game-logo {
        width: 40px;
        height: 40px;
        border-radius: 9px;
        border: 2px solid #111;
        display: grid;
        place-items: center;
        background: #fafafa;
        font-size: 13px;
        font-weight: 800;
        flex-shrink: 0;
      }

      .game-logo.gold {
        background: #d9cc9f;
        border-color: #bba96e;
      }

      .game-name {
        font-size: 37px;
        line-height: 0.92;
        font-weight: 800;
        text-align: left;
      }

      .game-name.small {
        font-size: 30px;
      }

      .center-pill {
        margin: 108px auto 0;
        width: min(180px, 70%);
        background: var(--card);
        border-radius: 10px;
        padding: 14px 10px;
        font-size: 37px;
        line-height: 1;
        text-align: center;
        font-weight: 800;
      }

      .team-title {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        margin-bottom: 14px;
      }

      .team-title h2 {
        margin: 0;
        font-size: 40px;
        line-height: 1;
      }

      .player-list {
        display: grid;
        gap: 8px;
      }

      .player-card {
        position: relative;
        border-radius: 16px;
        border: 0;
        background: var(--card);
        min-height: 118px;
        padding: 12px 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        cursor: pointer;
      }

      .player-card.static {
        cursor: default;
      }

      .player-names {
        display: grid;
        gap: 2px;
      }

      .player-first {
        margin: 0;
        font-size: 30px;
        line-height: 1;
        font-weight: 700;
      }

      .player-nick {
        margin: 0;
        font-size: 47px;
        line-height: 0.94;
        font-weight: 800;
      }

      .player-last {
        margin: 0;
        font-size: 30px;
        line-height: 1;
        font-weight: 700;
      }

      .photo-placeholder {
        width: 116px;
        height: 96px;
        border-radius: 14px;
        background: linear-gradient(145deg, #c2c2c2, #e9e9e9);
        color: #676767;
        font-size: 18px;
        display: grid;
        place-items: center;
        text-align: center;
        flex-shrink: 0;
      }

      .captain {
        position: absolute;
        right: 9px;
        top: 9px;
        width: 23px;
        height: 23px;
        border-radius: 50%;
        background: #f1c400;
        color: #121212;
        font-size: 16px;
        font-weight: 800;
        display: grid;
        place-items: center;
      }

      .player-info {
        margin-top: 14px;
      }

      .player-info p {
        margin: 0 0 8px;
        font-size: 26px;
        line-height: 1.2;
        font-weight: 600;
      }

      .achievements-card {
        margin-top: 70px;
        border-radius: 12px;
        background: var(--card);
        padding: 22px 14px;
        text-align: center;
        font-size: 33px;
        line-height: 1;
        font-weight: 700;
      }

      @media (max-width: 420px) {
        .frame-title {
          font-size: 22px;
        }

        .menu-link {
          font-size: 24px;
        }

        .game-name {
          font-size: 30px;
        }

        .game-name.small {
          font-size: 24px;
        }

        .center-pill {
          font-size: 31px;
        }

        .team-title h2 {
          font-size: 34px;
        }

        .player-first,
        .player-last,
        .player-info p {
          font-size: 22px;
        }

        .player-nick {
          font-size: 35px;
        }

        .photo-placeholder {
          width: 92px;
          height: 78px;
          font-size: 14px;
        }
      }
    </style>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
  </head>
  <body>
    <div class="app-shell">
      <div class="frame">
        <p id="frame-title" class="frame-title">ДомСтр М</p>
        <section class="phone">
          <div id="menu-backdrop" class="menu-backdrop"></div>
          <aside id="menu-panel" class="menu-panel" aria-hidden="true">
            <div class="menu-head">
              <div class="menu-btn-fake"><span class="menu-lines"></span></div>
            </div>
            <nav class="menu-nav">
              <button type="button" class="menu-link" data-screen-target="teams">Сборные</button>
              <button type="button" class="menu-link" data-screen-target="tournaments">Турниры</button>
              <button type="button" class="menu-link" data-screen-target="achievements">Достижения</button>
            </nav>
          </aside>

          <header class="topbar">
            <button id="menu-btn" class="menu-btn" type="button" aria-label="Открыть меню">
              <span class="menu-lines"></span>
            </button>
            <img class="brand-logo" src="/assets/reactor-logo.jpg" alt="Логотип" />
            <div class="topbar-spacer"></div>
          </header>

          <main class="screen-wrap">
            <section class="screen active" data-screen="home">
              <div class="banner-placeholder">БАННЕРЫ</div>
            </section>

            <section class="screen" data-screen="teams">
              <div class="game-grid">
                <div class="game-card actionable" data-go-screen="team-mt">
                  <div class="game-logo">MT</div>
                  <div class="game-name">МИР ТАНКОВ</div>
                </div>
                <div class="game-card">
                  <div class="game-logo gold">ML</div>
                  <div class="game-name small">MOBILE LEGENDS</div>
                </div>
                <div class="game-card">
                  <div class="game-name small">COUNTER STRIKE 2</div>
                </div>
                <div class="game-card">
                  <div class="game-name small">DOTA 2</div>
                </div>
                <div class="game-card empty"></div>
                <div class="game-card empty"></div>
              </div>
            </section>

            <section class="screen" data-screen="tournaments">
              <div class="center-pill">ПОБЕДА</div>
            </section>

            <section class="screen" data-screen="achievements">
              <div class="achievements-card">Блок достижений</div>
            </section>

            <section class="screen" data-screen="team-mt">
              <div class="team-title">
                <div class="game-logo">MT</div>
                <h2>МИР ТАНКОВ</h2>
              </div>
              <div class="player-list">
                <div class="player-card" data-go-screen="player-1">
                  <div class="player-names">
                    <p class="player-first">Сергей</p>
                    <p class="player-nick">SAM_05_2</p>
                    <p class="player-last">Грачев</p>
                  </div>
                  <div class="photo-placeholder">Фото игрока позже</div>
                  <span class="captain">К</span>
                </div>
                <div class="player-card static">
                  <div class="player-names">
                    <p class="player-first">Денис</p>
                    <p class="player-nick">EgorTitov9</p>
                    <p class="player-last">Машуков</p>
                  </div>
                  <div class="photo-placeholder">Фото игрока позже</div>
                </div>
              </div>
            </section>

            <section class="screen" data-screen="player-1">
              <div class="team-title">
                <div class="game-logo">MT</div>
                <h2>МИР ТАНКОВ</h2>
              </div>
              <div class="player-card static">
                <div class="player-names">
                  <p class="player-first">Сергей</p>
                  <p class="player-nick">SAM_05_2</p>
                  <p class="player-last">Грачев</p>
                </div>
                <div class="photo-placeholder">Фото игрока позже</div>
                <span class="captain">К</span>
              </div>
              <div class="player-info">
                <p>Группа: C24-722</p>
                <p>Играет в Мир Танков с 2015 года...</p>
              </div>
            </section>
          </main>
        </section>
      </div>
    </div>

    <script>
      const tg = window.Telegram?.WebApp;
      if (tg) {
        tg.ready?.();
        tg.expand?.();
      }

      const frameTitle = document.getElementById("frame-title");
      const menuBtn = document.getElementById("menu-btn");
      const menuPanel = document.getElementById("menu-panel");
      const menuBackdrop = document.getElementById("menu-backdrop");
      const screens = Array.from(document.querySelectorAll(".screen"));
      const menuLinks = Array.from(document.querySelectorAll("[data-screen-target]"));
      const screenJumpers = Array.from(document.querySelectorAll("[data-go-screen]"));

      const titles = {
        home: "ДомСтр М",
        teams: "Сборные М",
        tournaments: "Турниры М",
        achievements: "Достижения М",
        "team-mt": "Сборная MT М",
        "player-1": "Игрок 1 MT М",
      };

      function setMenuOpen(open) {
        menuPanel.classList.toggle("open", open);
        menuBackdrop.classList.toggle("open", open);
        menuPanel.setAttribute("aria-hidden", String(!open));
      }

      function showScreen(screenName) {
        const target = screens.find((screen) => screen.dataset.screen === screenName) ? screenName : "home";
        screens.forEach((screen) => {
          const isActive = screen.dataset.screen === target;
          screen.classList.toggle("active", isActive);
        });

        menuLinks.forEach((link) => {
          const isCurrent = link.dataset.screenTarget === target;
          link.style.opacity = isCurrent ? "1" : "0.85";
        });

        frameTitle.textContent = titles[target] || titles.home;
        window.location.hash = target;
        setMenuOpen(false);
      }

      menuBtn.addEventListener("click", () => {
        const open = !menuPanel.classList.contains("open");
        setMenuOpen(open);
      });

      menuBackdrop.addEventListener("click", () => setMenuOpen(false));

      menuLinks.forEach((link) => {
        link.addEventListener("click", () => {
          showScreen(link.dataset.screenTarget || "home");
        });
      });

      screenJumpers.forEach((item) => {
        item.addEventListener("click", () => {
          showScreen(item.dataset.goScreen || "home");
        });
      });

      document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
          setMenuOpen(false);
        }
      });

      const initialScreen = window.location.hash.replace("#", "");
      showScreen(initialScreen || "home");
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

      .hidden {
        display: none !important;
      }
    </style>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
  </head>
  <body>
    <main class="page">
      <section class="card">
        <div class="top-row">
          <a class="back-btn" href="/">← На главную</a>
          <span class="game-tag">CLASH ROYALE</span>
        </div>

        <h1>Регистрация</h1>
        <p class="subtitle">Заполни данные для регистрации на дисциплину.</p>

        <div id="existing-action" class="existing-action hidden">
          <button id="edit-existing-btn" class="submit-btn" type="button">Изменить данные в регистрации</button>
        </div>

        <form id="clash-form" class="form">
          <div>
            <label for="full-name">ФИО</label>
            <input id="full-name" name="full_name" type="text" maxlength="140" placeholder="Иванов Иван Иванович" required />
          </div>
          <div>
            <label for="group-number">Номер группы</label>
            <input id="group-number" name="group_number" type="text" maxlength="60" placeholder="БИ-22-1" required />
          </div>
          <div>
            <label for="supercell-id">SUPERCELL ID</label>
            <input id="supercell-id" name="supercell_id" type="text" maxlength="40" placeholder="#2ABCDEF9" required />
          </div>
          <button id="submit-btn" class="submit-btn" type="submit">Зарегистрироваться</button>
        </form>

        <div id="status" class="status"></div>
      </section>
    </main>

    <script>
      const tg = window.Telegram?.WebApp;
      if (tg) {
        tg.ready?.();
        tg.expand?.();
      }

      const form = document.getElementById("clash-form");
      const submitBtn = document.getElementById("submit-btn");
      const statusEl = document.getElementById("status");
      const existingActionEl = document.getElementById("existing-action");
      const editExistingBtn = document.getElementById("edit-existing-btn");
      let telegramUserId = null;
      let telegramUsername = null;

      let hasExistingRegistration = false;
      let updateMode = false;

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
          setStatus("Открой мини-приложение из Telegram, чтобы зарегистрироваться.", true);
          submitBtn.disabled = true;
          editExistingBtn.disabled = true;
          return false;
        }
        submitBtn.disabled = false;
        editExistingBtn.disabled = false;
        return true;
      }

      function syncButtonText() {
        submitBtn.textContent = updateMode ? "Сохранить изменения" : "Зарегистрироваться";
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

      async function loadExistingRegistration() {
        refreshTelegramIdentity();
        if (!ensureTelegramId()) {
          setExistingView(false);
          syncButtonText();
          return;
        }

        const query = new URLSearchParams();
        query.set("telegram_user_id", String(telegramUserId));
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
          allow_update: updateMode,
        };

        if (!payload.full_name || !payload.group_number || !payload.supercell_id) {
          setStatus("Заполни все поля.", true);
          return;
        }

        submitBtn.disabled = true;
        setStatus("Сохраняю...");

        try {
          const response = await fetch("/api/clash-royale/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });

          const data = await response.json();
          if (!response.ok) {
            throw new Error(data.detail || "Ошибка регистрации");
          }

          setStatus(data.message || "Регистрация сохранена.");
          hasExistingRegistration = true;
          updateMode = false;
          setExistingView(true);
          syncButtonText();
        } catch (error) {
          setStatus(error.message || "Ошибка регистрации.", true);
        } finally {
          submitBtn.disabled = false;
        }
      });

      editExistingBtn.addEventListener("click", () => {
        updateMode = true;
        setExistingView(false);
        syncButtonText();
        setStatus("Измени данные и нажми «Сохранить изменения».");
      });

      async function initRegistrationPage() {
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

      syncButtonText();
      setExistingView(false);
      initRegistrationPage();
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


@app.get("/clash-royale", response_class=HTMLResponse)
async def clash_royale_page(request: Request) -> HTMLResponse:
    return HTMLResponse(content=CLASH_TEMPLATE)


@app.get("/api/clash-royale/registration")
async def clash_royale_registration(
    telegram_user_id: int | None = None,
    telegram_username: str | None = None,
) -> dict[str, object]:
    if getattr(app.state, "db_error", None):
        raise HTTPException(status_code=503, detail=f"DB is unavailable: {app.state.db_error}")

    data = get_clash_registration(telegram_user_id=telegram_user_id, telegram_username=telegram_username)
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
            allow_update=payload.allow_update,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
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



