from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from config import WEBAPP_HOST, WEBAPP_PORT


app = FastAPI()


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Telegram Mini App</title>
    <style>
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: #050816;
        color: #f9fafb;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
      }
      .card {
        width: min(420px, 100%);
        padding: 24px 20px;
        border-radius: 18px;
        background: radial-gradient(circle at top, #22c1c3 0, #050816 55%);
        box-shadow: 0 24px 60px rgba(15, 23, 42, 0.9);
      }
      h1 {
        margin: 0 0 8px;
        font-size: 24px;
      }
      p {
        margin: 0 0 16px;
        color: #e5e7eb;
        font-size: 14px;
      }
      .pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(15, 23, 42, 0.7);
        color: #bfdbfe;
        font-size: 11px;
        margin-bottom: 16px;
      }
      .pill-dot {
        width: 7px;
        height: 7px;
        border-radius: 999px;
        background: #22c55e;
      }
      .field {
        margin-bottom: 12px;
        font-size: 13px;
      }
      .field-label {
        opacity: 0.7;
        margin-bottom: 4px;
      }
      .field-value {
        font-weight: 600;
      }
      button {
        width: 100%;
        margin-top: 18px;
        padding: 10px 14px;
        border-radius: 999px;
        border: none;
        cursor: pointer;
        font-size: 14px;
        font-weight: 600;
        color: #0b1120;
        background: linear-gradient(135deg, #22c1c3, #6366f1);
        box-shadow: 0 12px 30px rgba(59, 130, 246, 0.6);
      }
      button:active {
        transform: translateY(1px);
        box-shadow: 0 6px 16px rgba(59, 130, 246, 0.8);
      }
      small {
        display: block;
        margin-top: 10px;
        font-size: 11px;
        opacity: 0.6;
      }
    </style>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
  </head>
  <body>
    <main class="card">
      <div class="pill">
        <span class="pill-dot"></span>
        <span>Cyber Reactor Mini App</span>
      </div>
      <h1>Привет, <span id="username">гость</span> 👋</h1>
      <p>Это шаблон мини‑приложения. Ты можешь менять логику и интерфейс как тебе нужно.</p>

      <div class="field">
        <div class="field-label">ID пользователя</div>
        <div class="field-value" id="user-id">—</div>
      </div>
      <div class="field">
        <div class="field-label">Юзернейм</div>
        <div class="field-value" id="user-username">—</div>
      </div>

      <button id="send-data-btn">Отправить данные боту</button>
      <small>Данные отправятся обратно в чат через WebAppData.</small>
    </main>

    <script>
      const tg = window.Telegram?.WebApp;

      if (tg) {
        tg.expand();

        const initDataUnsafe = tg.initDataUnsafe || {};
        const user = initDataUnsafe.user || {};

        document.getElementById("username").textContent = user.first_name || "гость";
        document.getElementById("user-id").textContent = user.id || "—";
        document.getElementById("user-username").textContent = user.username
          ? "@" + user.username
          : "—";

        document.getElementById("send-data-btn").addEventListener("click", () => {
          const payload = {
            id: user.id,
            username: user.username,
            ts: Date.now(),
          };

          tg.sendData(JSON.stringify(payload));
          tg.close();
        });
      }
    </script>
  </body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return HTMLResponse(content=HTML_TEMPLATE)


def run() -> None:
    import uvicorn

    uvicorn.run("webapp:app", host=WEBAPP_HOST, port=WEBAPP_PORT, reload=True)


if __name__ == "__main__":
    run()

