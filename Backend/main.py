from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from Backend.rag_pipeline import get_agent_executor, add_to_vectorstore, split_docs
from Backend.data_loader import load_uploaded_file, load_website
from Backend.schemas import ChatQuery, ChatResponse, CrawlRequest
from Backend.config import Config
from Backend.utils import log_query

import os
import shutil
import json

app = FastAPI(title="Appic Softwares AI Advisor API")

# ✅ CORS (frontend connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Session storage (for chat memory)
sessions = {}

def get_session_agent(session_id: str):
    if session_id not in sessions:
        sessions[session_id] = get_agent_executor()
    return sessions[session_id]


# ✅ Health check
@app.get("/")
async def root():
    return {"status": "Appic AI Backend is running 🚀"}


# 🔥 MAIN CHAT API (UPDATED)
@app.post("/chat", response_model=ChatResponse)
async def chat(query: ChatQuery):
    session_id = query.session_id or "default"
    agent_executor = get_session_agent(session_id)

    try:
        # 🔥 invoke agent
        result = agent_executor.invoke({"input": query.question})

        # ✅ new structured response
        message = result.get("message", "")
        options = result.get("options", [])

        # 🧠 logging
        log_query(query.question, message)

        # 🔍 debug (optional)
        print("USER:", query.question)
        print("BOT:", message)
        print("OPTIONS:", options)

        return ChatResponse(
            message=message,
            options=options
        )

    except Exception as e:
        print(f"❌ Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ✅ GET LEADS
@app.get("/leads")
async def get_leads():
    try:
        leads = []
        if os.path.exists(Config.LEADS_FILE):
            with open(Config.LEADS_FILE, "r") as f:
                for line in f:
                    if line.strip():
                        leads.append(json.loads(line))
        return {"leads": leads}
    except Exception as e:
        print(f"❌ Leads Fetch Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch leads: {str(e)}")


# ✅ GET PROJECTS
@app.get("/projects")
async def get_projects():
    try:
        projects = []
        project_file = "data/projects.json"

        if os.path.exists(project_file):
            with open(project_file, "r") as f:
                for line in f:
                    if line.strip():
                        projects.append(json.loads(line))

        return {"projects": projects}

    except Exception as e:
        print(f"❌ Projects Fetch Error: {e}")
        return {"projects": []}


# 🔥 FILE UPLOAD (RAG update)
@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Form("default")
):
    temp_path = f"temp_{file.filename}"

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        docs = load_uploaded_file(temp_path)
        chunks = split_docs(docs)
        add_to_vectorstore(chunks)

        return {
            "message": f"✅ Successfully indexed {file.filename}. Knowledge base updated."
        }

    except Exception as e:
        print(f"❌ Upload Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


# 🔥 WEBSITE CRAWL (RAG update)
@app.post("/crawl")
async def crawl_site(
    url: str = Form(...),
    max_pages: int = Form(20),
    session_id: str = Form("default")
):
    try:
        docs = load_website(url, max_pages=max_pages)
        chunks = split_docs(docs)
        add_to_vectorstore(chunks)

        return {
            "message": f"✅ Crawled & indexed {url} (max {max_pages} pages)"
        }

    except Exception as e:
        print(f"❌ Crawl Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))