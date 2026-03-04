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
    <style>
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: "Segoe UI", Tahoma, sans-serif;
        background: radial-gradient(circle at top right, #1d4ed8 0%, #050816 60%);
        color: #f9fafb;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
        padding: 16px;
      }
      .card {
        width: min(460px, 100%);
        padding: 24px 20px;
        border-radius: 18px;
        background: rgba(11, 17, 32, 0.92);
        box-shadow: 0 24px 60px rgba(0, 0, 0, 0.45);
        border: 1px solid rgba(148, 163, 184, 0.24);
      }
      h1 { margin: 0 0 8px; font-size: 24px; }
      p { margin: 0 0 18px; color: #cbd5e1; }
      .meta { margin-bottom: 14px; font-size: 14px; color: #93c5fd; }
      .grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 10px;
      }
      .tour-btn {
        text-align: left;
        border: 1px solid #334155;
        border-radius: 12px;
        background: #0f172a;
        color: #e2e8f0;
        padding: 12px 14px;
        font-size: 15px;
        cursor: pointer;
        transition: 0.15s ease;
      }
      .tour-btn:hover { border-color: #60a5fa; }
      .tour-btn.active {
        border-color: #22d3ee;
        background: linear-gradient(135deg, #0f172a, #1e293b);
        box-shadow: 0 0 0 1px rgba(34, 211, 238, 0.5) inset;
      }
      .register-btn {
        width: 100%;
        margin-top: 16px;
        border: none;
        border-radius: 999px;
        background: linear-gradient(135deg, #22c1c3, #3b82f6);
        color: #0b1120;
        font-size: 15px;
        font-weight: 700;
        padding: 11px 14px;
        cursor: pointer;
      }
      .register-btn:disabled {
        opacity: 0.45;
        cursor: not-allowed;
      }
      .status {
        min-height: 20px;
        margin-top: 12px;
        font-size: 13px;
        color: #93c5fd;
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
