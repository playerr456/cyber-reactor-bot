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
    <title>Cyber Reactor Tournaments</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@500;700;800&display=swap" rel="stylesheet">
    <style>
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: "Manrope", "Segoe UI", sans-serif;
        background: #f4f5f7;
        color: #121417;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
        padding: 20px;
      }
      .card {
        width: min(460px, 100%);
        padding: 22px 18px;
        border-radius: 16px;
        background: #ffffff;
        box-shadow: 0 8px 30px rgba(18, 20, 23, 0.08);
        border: 1px solid #e8ebef;
      }
      h1 { margin: 0 0 6px; font-size: 24px; font-weight: 800; letter-spacing: -0.02em; }
      p { margin: 0 0 16px; color: #5a6472; font-size: 14px; }
      .meta {
        margin-bottom: 14px;
        font-size: 13px;
        color: #364152;
        padding: 10px 12px;
        background: #f8fafc;
        border: 1px solid #e8ebef;
        border-radius: 10px;
      }
      .grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 8px;
      }
      .tour-btn {
        text-align: left;
        border: 1px solid #d7dce3;
        border-radius: 10px;
        background: #ffffff;
        color: #1f2937;
        padding: 12px;
        font-size: 14px;
        font-weight: 700;
        cursor: pointer;
        transition: 0.15s ease;
      }
      .tour-btn:hover { border-color: #1f2937; }
      .tour-btn.active {
        border-color: #111827;
        background: #f3f4f6;
        box-shadow: none;
      }
      .register-btn {
        width: 100%;
        margin-top: 14px;
        border: 1px solid #111827;
        border-radius: 10px;
        background: #111827;
        color: #ffffff;
        font-size: 14px;
        font-weight: 700;
        padding: 11px 12px;
        cursor: pointer;
      }
      .register-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }
      .status {
        min-height: 20px;
        margin-top: 12px;
        font-size: 12px;
        color: #5a6472;
      }
    </style>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
  </head>
  <body>
    <main class="card">
      <h1>Регистрация на турнир</h1>
      <p>Выбери дисциплину и нажми кнопку регистрации.</p>

      <div class="meta">Пользователь: <span id="username">гость</span></div>

      <div class="grid" id="tournaments"></div>

      <button id="register-btn" class="register-btn" disabled>Зарегистрироваться</button>
      <div class="status" id="status"></div>
    </main>

    <script>
      const tg = window.Telegram?.WebApp;
      if (tg) tg.expand();

      const TOURNAMENTS = ["clash royale", "dota 2", "cs go"];
      const tournamentsEl = document.getElementById("tournaments");
      const registerBtn = document.getElementById("register-btn");
      const statusEl = document.getElementById("status");

      const user = tg?.initDataUnsafe?.user || {};
      const userId = user.id || null;

      document.getElementById("username").textContent =
        user.username ? `@${user.username}` : (user.first_name || "гость");

      let selectedTournament = null;

      function setStatus(text, isError = false) {
        statusEl.textContent = text;
        statusEl.style.color = isError ? "#fca5a5" : "#93c5fd";
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
