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
      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
        background: #06080c;
        color: #f5f7fa;
        min-height: 100vh;
      }

      .page {
        width: min(1100px, 100%);
        margin: 0 auto;
        padding-bottom: 28px;
      }

      .carousel {
        position: relative;
        overflow: hidden;
        width: 100%;
        height: min(54vw, 460px);
        min-height: 260px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.14);
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
        background: linear-gradient(180deg, transparent 0%, rgba(6, 8, 12, 0.42) 70%, #06080c 100%);
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
        border: 1px solid rgba(255, 255, 255, 0.2);
      }

      .contacts {
        margin: 22px auto 0;
        width: min(680px, calc(100% - 24px));
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.16);
        background: rgba(255, 255, 255, 0.03);
        padding: 16px 16px 18px;
      }

      .contacts h2 {
        margin: 0 0 10px;
        font-size: 26px;
        letter-spacing: 0.01em;
      }

      .contacts p {
        margin: 5px 0;
        font-size: 17px;
      }

      .contacts a {
        color: #a8ccff;
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
    <main class="page">
      <section class="carousel" aria-label="Баннеры">
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

      <section class="brand">
        <h1>КиберРеаткор</h1>
        <img class="logo" src="/assets/logo.jpg" alt="Лого КиберРеаткор" />
      </section>

      <section class="contacts">
        <h2>Обратная связь</h2>
        <p>Email: <a href="mailto:123@gmail.com">123@gmail.com</a></p>
        <p>TG: <a href="https://t.me/matve88" target="_blank" rel="noopener">@matve88</a></p>
      </section>
    </main>

    <script>
      const slides = Array.from(document.querySelectorAll(".slide"));
      const dots = Array.from(document.querySelectorAll(".dot"));
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

      dots.forEach((dot) => {
        dot.addEventListener("click", () => {
          const index = Number(dot.dataset.index || 0);
          showSlide(index);
          startAutoplay();
        });
      });

      showSlide(0);
      startAutoplay();
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

