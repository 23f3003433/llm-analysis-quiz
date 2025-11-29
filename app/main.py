from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import json

from .config import STUDENT_EMAIL, STUDENT_SECRET
from .solver.chain import solve_quiz_chain
from .solver.models import QuizRequest
from dotenv import load_dotenv
load_dotenv()


app = FastAPI()


class QuizRequest(BaseModel):
    email: str
    secret: str
    url: str


@app.post("/")
async def handle_quiz(request: Request):
    # Parse JSON
    try:
        raw = await request.body()
        data = json.loads(raw.decode("utf-8"))
        quiz_req = QuizRequest(**data)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Validate secret & email
    if quiz_req.secret != STUDENT_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")

    if quiz_req.email != STUDENT_EMAIL:
        raise HTTPException(status_code=403, detail="Invalid email")

    # Build chain request
    chain_req = QuizRequest(
        email=quiz_req.email,
        secret=quiz_req.secret,
        url=quiz_req.url,
    )

    # ✅ Run ASYNC solver
    result = await solve_quiz_chain(chain_req, quiz_req.url)

    return {
        "status": "completed",
        "result": result,
    }
