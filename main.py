from fastapi import FastAPI
import os
from dotenv import load_dotenv

# routers
from routers.line_router import router as line_router, line_bot_api
from routers.api_router  import api as api_router

# scheduler
from services.scheduler_service import start_scheduler

load_dotenv()

app = FastAPI()
app.include_router(line_router)
app.include_router(api_router)

# 啟動排程（把 line_bot_api 傳進 scheduler）
start_scheduler(line_bot_api)