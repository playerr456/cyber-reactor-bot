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
    <link
      href="https://fonts.googleapis.com/css2?family=Exo+2:wght@500;700;800&family=IBM+Plex+Sans:wght@400;500;700&display=swap"
      rel="stylesheet"
    />
    <style>
      :root {
        --bg: #08111f;
        --bg-soft: #102139;
        --text: #eff6ff;
        --text-muted: #98a8c7;
        --line: #243751;
        --card: #0e1b2f;
        --accent: #36d1b1;
        --accent-2: #ff9657;
        --ok: #7df5d8;
        --error: #ff9f9f;
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
        background:
          radial-gradient(1200px 600px at 65% -12%, #174778 0%, transparent 65%),
          linear-gradient(180deg, #060c16 0%, #0b172a 48%, #08111f 100%);
        color: var(--text);
        min-height: 100vh;
      }

      .menu-toggle {
        position: fixed;
        left: 16px;
        top: 16px;
        z-index: 40;
        border: 1px solid rgba(255, 255, 255, 0.16);
        background: rgba(10, 24, 43, 0.92);
        color: var(--text);
        border-radius: 11px;
        padding: 9px 12px;
        font-weight: 700;
        cursor: pointer;
        backdrop-filter: blur(4px);
      }

      .overlay {
        position: fixed;
        inset: 0;
        background: rgba(1, 6, 14, 0.68);
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
        background: linear-gradient(180deg, #0d1b2e 0%, #111f34 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
        transform: translateX(-100%);
        transition: transform 0.25s ease;
        padding: 18px 12px 18px 16px;
        overflow-y: auto;
      }

      .sidebar.open {
        transform: translateX(0);
      }

      .sidebar-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
      }

      .sidebar-head h2 {
        margin: 0;
        font-family: "Exo 2", "Segoe UI", sans-serif;
        font-size: 20px;
      }

      .close-menu {
        border: 0;
        background: transparent;
        color: #d4e5ff;
        cursor: pointer;
        font-size: 24px;
      }

      .channel-list {
        display: flex;
        flex-direction: column;
        gap: 2px;
      }

      .channel-link {
        display: flex;
        align-items: center;
        gap: 10px;
        text-decoration: none;
        color: #d6e7ff;
        padding: 8px 8px;
        border-radius: 10px;
        transition: background 0.15s ease, transform 0.15s ease;
      }

      .channel-link:hover,
      .channel-link.active {
        background: rgba(94, 156, 227, 0.14);
        transform: translateX(2px);
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
        color: #07111e;
      }

      .channel-meta {
        min-width: 0;
      }

      .channel-title {
        margin: 0;
        font-size: 16px;
        font-weight: 700;
      }

      .channel-preview {
        margin: 2px 0 0;
        color: #85b4eb;
        font-size: 13px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .page {
        width: min(1024px, 100%);
        margin: 0 auto;
        padding: 78px 16px 22px;
      }

      .hero {
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 22px;
        padding: 28px 22px;
        background: linear-gradient(120deg, #12345a 0%, #184472 48%, #255f72 100%);
      }

      .hero::after {
        content: "";
        position: absolute;
        right: -80px;
        top: -80px;
        width: 220px;
        height: 220px;
        border-radius: 999px;
        background: radial-gradient(circle, rgba(255, 150, 87, 0.4) 0%, transparent 70%);
      }

      .hero-tag {
        display: inline-block;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #ffe5d4;
        background: rgba(8, 17, 31, 0.35);
        border: 1px solid rgba(255, 255, 255, 0.16);
        border-radius: 999px;
        padding: 5px 10px;
      }

      .hero h1 {
        margin: 12px 0 8px;
        font-family: "Exo 2", "Segoe UI", sans-serif;
        font-size: clamp(29px, 7vw, 44px);
        line-height: 1.03;
        letter-spacing: 0.01em;
        max-width: 16ch;
      }

      .hero p {
        margin: 0;
        color: #d7e7ff;
        max-width: 56ch;
      }

      .hero-cta {
        margin-top: 16px;
        display: inline-block;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.28);
        background: rgba(8, 17, 31, 0.34);
        color: #ffffff;
        padding: 10px 14px;
        text-decoration: none;
        font-weight: 700;
      }

      .stack {
        margin-top: 14px;
        display: grid;
        gap: 14px;
      }

      .panel {
        border-radius: 16px;
        border: 1px solid var(--line);
        background: var(--card);
        padding: 18px 16px;
      }

      .panel h2 {
        margin: 0;
        font-family: "Exo 2", "Segoe UI", sans-serif;
        font-size: 25px;
      }

      .panel p {
        margin: 7px 0 14px;
        color: var(--text-muted);
      }

      .meta {
        margin-bottom: 13px;
        font-size: 14px;
        color: #d9ecff;
        padding: 10px 12px;
        background: #0a1525;
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
        border: 1px solid #3b516f;
        border-radius: 11px;
        background: #13253e;
        color: #e8f3ff;
        padding: 12px;
        font-size: 14px;
        font-weight: 700;
        cursor: pointer;
      }

      .tour-btn:hover {
        border-color: #79c8e5;
      }

      .tour-btn.active {
        border-color: var(--accent);
        background: #173348;
      }

      .register-btn,
      .feedback-btn {
        width: 100%;
        margin-top: 12px;
        border: 1px solid transparent;
        border-radius: 11px;
        background: linear-gradient(120deg, var(--accent) 0%, #57b7ff 100%);
        color: #051426;
        font-size: 14px;
        font-weight: 800;
        padding: 11px 12px;
        cursor: pointer;
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
        color: #c6dbf9;
      }

      .feedback-form input,
      .feedback-form textarea {
        width: 100%;
        border-radius: 10px;
        border: 1px solid #324764;
        background: #0a1525;
        color: #eff6ff;
        padding: 10px 12px;
        font-family: inherit;
        font-size: 14px;
      }

      .feedback-form textarea {
        min-height: 120px;
        resize: vertical;
      }

      .feedback-btn {
        background: linear-gradient(120deg, var(--accent-2) 0%, #ffd062 100%);
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
    <button id="menu-toggle" class="menu-toggle" type="button">Каналы</button>
    <div id="menu-overlay" class="overlay"></div>

    <aside id="sidebar" class="sidebar" aria-hidden="true">
      <div class="sidebar-head">
        <h2>Каналы</h2>
        <button id="close-menu" class="close-menu" type="button" aria-label="Закрыть">x</button>
      </div>

      <nav class="channel-list">
        <a href="#banner" class="channel-link active">
          <span class="channel-icon" style="background:#ffb637">CS</span>
          <div class="channel-meta">
            <p class="channel-title">CS2</p>
            <p class="channel-preview">Andrey: Сбор в 20:00</p>
          </div>
        </a>
        <a href="#registration" class="channel-link">
          <span class="channel-icon" style="background:#adb9c8">#</span>
          <div class="channel-meta">
            <p class="channel-title">General</p>
            <p class="channel-preview">Даня: /join турнир</p>
          </div>
        </a>
        <a href="#registration" class="channel-link">
          <span class="channel-icon" style="background:#68ff9b">F</span>
          <div class="channel-meta">
            <p class="channel-title">FIFA</p>
            <p class="channel-preview">Денис: кто сегодня в сетке?</p>
          </div>
        </a>
        <a href="#registration" class="channel-link">
          <span class="channel-icon" style="background:#e7cc97">M</span>
          <div class="channel-meta">
            <p class="channel-title">MLBB</p>
            <p class="channel-preview">Данила: окей, играем</p>
          </div>
        </a>
        <a href="#registration" class="channel-link">
          <span class="channel-icon" style="background:#8cb7ff">H</span>
          <div class="channel-meta">
            <p class="channel-title">Hearthstone</p>
            <p class="channel-preview">Andrey: свисс на 4 раунда</p>
          </div>
        </a>
        <a href="#registration" class="channel-link">
          <span class="channel-icon" style="background:#ff6568">D2</span>
          <div class="channel-meta">
            <p class="channel-title">Dota 2</p>
            <p class="channel-preview">Камиль: 3 место гарант</p>
          </div>
        </a>
        <a href="#feedback" class="channel-link">
          <span class="channel-icon" style="background:#ff964d">MT</span>
          <div class="channel-meta">
            <p class="channel-title">Мир Танков</p>
            <p class="channel-preview">Данила: собираю стак</p>
          </div>
        </a>
        <a href="#feedback" class="channel-link">
          <span class="channel-icon" style="background:#8ab4d8">CH</span>
          <div class="channel-meta">
            <p class="channel-title">Общий чат</p>
            <p class="channel-preview">Евгений: по 5м без афк</p>
          </div>
        </a>
        <a href="#feedback" class="channel-link">
          <span class="channel-icon" style="background:#ffd367">T</span>
          <div class="channel-meta">
            <p class="channel-title">Tekken</p>
            <p class="channel-preview">Andrey: УДАР!</p>
          </div>
        </a>
      </nav>
    </aside>

    <main class="page">
      <header class="hero" id="banner">
        <span class="hero-tag">Cyber Reactor</span>
        <h1>Титульная страница турниров</h1>
        <p>Следи за лобби, выбирай дисциплину и регистрируйся на ближайшие матчи прямо из мини-приложения.</p>
        <a href="#registration" class="hero-cta">К регистрации</a>
      </header>

      <div class="stack">
        <section class="panel" id="registration">
          <h2>Регистрация на турнир</h2>
          <p>Выбери дисциплину и нажми кнопку регистрации.</p>

          <div class="meta">Пользователь: <span id="username">гость</span></div>

          <div class="grid" id="tournaments"></div>

          <button id="register-btn" class="register-btn" disabled>Зарегистрироваться</button>
          <div class="status" id="status"></div>
        </section>

        <section class="panel" id="feedback">
          <h2>Обратная связь</h2>
          <p>Напиши, что улучшить в расписании, комнатах или интерфейсе.</p>

          <form id="feedback-form" class="feedback-form">
            <div>
              <label for="feedback-name">Имя</label>
              <input id="feedback-name" name="name" type="text" maxlength="70" placeholder="Как к тебе обращаться" />
            </div>
            <div>
              <label for="feedback-message">Сообщение</label>
              <textarea id="feedback-message" name="message" maxlength="1000" placeholder="Твой отзыв"></textarea>
            </div>
            <button class="feedback-btn" type="submit">Отправить отзыв</button>
            <div class="feedback-status" id="feedback-status"></div>
          </form>
        </section>
      </div>
    </main>

    <script>
      const tg = window.Telegram?.WebApp;
      if (tg) tg.expand();

      const TOURNAMENTS = ["clash royale", "dota 2", "cs go"];
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
      const channelLinks = document.querySelectorAll(".channel-link");

      const user = tg?.initDataUnsafe?.user || {};
      const userId = user.id || null;

      document.getElementById("username").textContent =
        user.username ? `@${user.username}` : (user.first_name || "гость");
      feedbackNameEl.value = user.first_name || user.username || "";

      let selectedTournament = null;

      function setStatus(text, isError = false) {
        statusEl.textContent = text;
        statusEl.style.color = isError ? "var(--error)" : "var(--ok)";
      }

      function setFeedbackStatus(text, isError = false) {
        feedbackStatusEl.textContent = text;
        feedbackStatusEl.style.color = isError ? "var(--error)" : "var(--ok)";
      }

      function openMenu() {
        sidebar.classList.add("open");
        menuOverlay.classList.add("visible");
        sidebar.setAttribute("aria-hidden", "false");
      }

      function closeSidebar() {
        sidebar.classList.remove("open");
        menuOverlay.classList.remove("visible");
        sidebar.setAttribute("aria-hidden", "true");
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
            setStatus(`Выбрано: ${name}`);
          });
          tournamentsEl.appendChild(btn);
        });
      }

      async function loadExistingRegistration() {
        if (!userId) {
          setStatus("Открой мини-приложение из Telegram, чтобы зарегистрироваться.", true);
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
          setStatus(`Ты уже зарегистрирован на: ${selectedTournament}`);
        } catch {
          setStatus("Не удалось загрузить текущую регистрацию.", true);
        }
      }

      registerBtn.addEventListener("click", async () => {
        if (!userId || !selectedTournament) {
          setStatus("Сначала выбери турнир.", true);
          return;
        }

        registerBtn.disabled = true;
        setStatus("Сохраняю в базу...");

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

          setStatus(data.message || "Регистрация сохранена.");
          if (tg) {
            tg.sendData(JSON.stringify({ type: "registration", tournament: selectedTournament }));
          }
        } catch (err) {
          setStatus(err.message || "Ошибка регистрации.", true);
        } finally {
          registerBtn.disabled = false;
        }
      });

      feedbackForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const message = feedbackMessageEl.value.trim();
        if (message.length < 3) {
          setFeedbackStatus("Напиши хотя бы 3 символа.", true);
          return;
        }

        setFeedbackStatus("Отправляю...");
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
          setFeedbackStatus(data.message || "Спасибо за отзыв!");
          feedbackMessageEl.value = "";
        } catch (err) {
          setFeedbackStatus(err.message || "Не удалось отправить отзыв.", true);
        }
      });

      menuToggle.addEventListener("click", openMenu);
      closeMenu.addEventListener("click", closeSidebar);
      menuOverlay.addEventListener("click", closeSidebar);
      channelLinks.forEach((link) => {
        link.addEventListener("click", () => {
          channelLinks.forEach((item) => item.classList.remove("active"));
          link.classList.add("active");
          closeSidebar();
        });
      });

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
