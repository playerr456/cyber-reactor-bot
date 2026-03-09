from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import WEBAPP_HOST, WEBAPP_PORT
from db import ALLOWED_TOURNAMENTS, get_registration, init_db, upsert_registration


app = FastAPI()
app.mount("/assets", StaticFiles(directory=Path(__file__).parent / "assets"), name="assets")


TOURNAMENTS = ["clash royale", "dota 2", "cs go"]


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
        font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
        background: var(--bg);
        color: var(--text);
        min-height: 100vh;
      }

      .menu-toggle,
      .settings-toggle {
        position: fixed;
        top: 14px;
        z-index: 40;
        border: 1px solid var(--panel-line);
        background: var(--panel);
        color: var(--text);
        border-radius: 10px;
        cursor: pointer;
      }

      .menu-toggle {
        left: 14px;
        padding: 10px 12px;
        font-size: 14px;
        font-weight: 700;
      }

      .settings-toggle {
        right: 14px;
        width: 42px;
        height: 42px;
        font-size: 20px;
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
        display: block;
        text-decoration: none;
        color: var(--text);
        border: 1px solid transparent;
        border-radius: 10px;
        padding: 10px 12px;
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

      .carousel::after {
        content: "";
        position: absolute;
        inset: 0;
        pointer-events: none;
        background: linear-gradient(180deg, transparent 0%, rgba(6, 8, 12, 0.35) 70%, var(--bg) 100%);
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

      .brand {
        display: grid;
        justify-items: center;
        gap: 12px;
        padding: 22px 16px 4px;
      }

      .brand h1 {
        margin: 0;
        font-family: "Bebas Neue", "Arial Narrow", sans-serif;
        font-size: clamp(52px, 12vw, 96px);
        letter-spacing: 0.04em;
        line-height: 0.95;
      }

      .logo {
        width: min(240px, 58vw);
        aspect-ratio: 1 / 1;
        object-fit: cover;
        border-radius: 14px;
        border: 1px solid var(--panel-line);
      }

      .contacts {
        margin: 22px auto 0;
        width: min(680px, calc(100% - 24px));
        border-radius: 14px;
        border: 1px solid var(--panel-line);
        background: var(--panel);
        padding: 16px 16px 18px;
      }

      .contacts h2 {
        margin: 0 0 10px;
        font-size: 26px;
      }

      .contacts p {
        margin: 5px 0;
        font-size: 17px;
      }

      .contacts a {
        color: var(--link);
        text-decoration: none;
      }

      @media (max-width: 680px) {
        .carousel {
          min-height: 220px;
        }

        .contacts h2 {
          font-size: 22px;
        }

        .contacts p {
          font-size: 16px;
        }
      }
    </style>
  </head>
  <body>
    <button id="menu-toggle" class="menu-toggle" type="button" data-i18n="menuOpen">Меню</button>
    <button id="settings-toggle" class="settings-toggle" type="button" aria-label="Настройки">&#9881;</button>
    <div id="overlay" class="overlay"></div>

    <aside id="sidebar" class="sidebar" aria-hidden="true">
      <div class="panel-head">
        <h2 data-i18n="sidebarTitle">Навигация</h2>
        <button id="close-menu" class="close-btn" type="button" aria-label="Закрыть">x</button>
      </div>
      <nav class="nav-list">
        <a href="#top-banner" class="nav-link active" data-i18n="navHome">Главная страница</a>
        <a href="#top-banner" class="nav-link" data-i18n="navBanner">Баннеры</a>
        <a href="#brand" class="nav-link" data-i18n="navLogo">Лого</a>
        <a href="#contacts" class="nav-link" data-i18n="navFeedback">Обратная связь</a>
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

      <section id="brand" class="brand">
        <h1 data-i18n="brandTitle">КиберРеаткор</h1>
        <img class="logo" src="/assets/logo.jpg" alt="Лого КиберРеаткор" />
      </section>

      <section id="contacts" class="contacts">
        <h2 data-i18n="feedbackTitle">Обратная связь</h2>
        <p><span data-i18n="emailLabel">Почта</span>: <a href="mailto:123@gmail.com">123@gmail.com</a></p>
        <p><span data-i18n="tgLabel">TG</span>: <a href="https://t.me/matve88" target="_blank" rel="noopener">@matve88</a></p>
      </section>
    </main>

    <script>
      const I18N = {
        ru: {
          menuOpen: "Меню",
          sidebarTitle: "Навигация",
          settingsTitle: "Настройки",
          navHome: "Главная страница",
          navBanner: "Баннеры",
          navLogo: "Лого",
          navFeedback: "Обратная связь",
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
          menuOpen: "Menu",
          sidebarTitle: "Navigation",
          settingsTitle: "Settings",
          navHome: "Home",
          navBanner: "Banners",
          navLogo: "Logo",
          navFeedback: "Feedback",
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


