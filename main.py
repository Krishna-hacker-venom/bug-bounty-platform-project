from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional
import uvicorn
import datetime
from bson import ObjectId

app = FastAPI()

# Templates
templates = Jinja2Templates(directory="templates")

# --- MONGODB CONNECTION ---
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.bug_bounty_project 
reports_collection = db.reports 
users_collection = db.users      
targets_collection = db.targets  # Fixed typo: targerts -> targets

# ---------- PAGE ROUTES (GET) ----------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/start_hunting", response_class=HTMLResponse)
async def start_hunting(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def hacker_dashboard(request: Request):
    cursor = reports_collection.find().sort("created_at", -1)
    reports_list = await cursor.to_list(length=100)
    return templates.TemplateResponse("hacker_dashboard.html", {"request": request, "reports": reports_list})

@app.get("/submit-report", response_class=HTMLResponse)
async def report_page(request: Request):
    return templates.TemplateResponse("submit_report.html", {"request": request})

@app.get("/learn", response_class=HTMLResponse)
async def learn_page(request: Request):
    return templates.TemplateResponse("learn.html", {"request": request})

@app.get("/target", response_class=HTMLResponse)
async def target_page(request: Request):
    return templates.TemplateResponse("target.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

@app.get("/company_dashboard", response_class=HTMLResponse)
async def company_dashboard(request: Request):
    # Fetch reports for the company table
    cursor = reports_collection.find().sort("created_at", -1)
    reports_list = await cursor.to_list(length=100)
    return templates.TemplateResponse("company_dashboard.html", {"request": request, "reports": reports_list})
# FIX: This handles the old "/company" URL so you don't get a 404 error
@app.get("/company", response_class=RedirectResponse)
async def redirect_old_company_url(request: Request):
    return RedirectResponse(url="/company_dashboard", status_code=303)

# --- HACKER VIEW ---
@app.get("/new_target", response_class=HTMLResponse)
async def new_target(request: Request):
    user_type = request.cookies.get("user_role") 
    # Fetch only active targets from MongoDB
    cursor = targets_collection.find({"status": "Active"}).sort("created_at", -1)
    live_targets = await cursor.to_list(length=100)
    
    return templates.TemplateResponse("new_target.html", {
        "request": request, 
        "targets": live_targets,
        "user_role": user_type 
    })

# @app.get("/admin", response_class=HTMLResponse)
# async def admin_dashboard(request: Request):
#     # Fetch real data for the tables
#     users_list = await users_collection.find().to_list(length=100)
#     targets_list = await targets_collection.find().to_list(length=100)
    
#     # Calculate live stats
#     stats = {
#         "reports_count": await reports_collection.count_documents({}),
#         "users_count": await users_collection.count_documents({}),
#         "targets_count": await targets_collection.count_documents({"status": "Active"})
#     }
    
#     return templates.TemplateResponse("admin_dashboard.html", {
#         "request": request,
#         "users": users_list,
#         "targets": targets_list,
#         "stats": stats
#     })
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    # Fetch real data from your MongoDB collections
    users_list = await users_collection.find().to_list(length=100)
    targets_list = await targets_collection.find().to_list(length=100)
    
    # Calculate counts for the top stats cards
    total_reports = await reports_collection.count_documents({})
    active_progs = await targets_collection.count_documents({"status": "Active"})
    total_users = await users_collection.count_documents({})

    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "users": users_list,
        "targets": targets_list,
        "stats": {
            "reports": total_reports,
            "progs": active_progs,
            "users": total_users
        }
    })
# for view all user
@app.get("/admin/users", response_class=HTMLResponse)
async def view_all_users(request: Request):
    # Fetch all users from your MongoDB
    users_list = await users_collection.find().to_list(length=1000)
    return templates.TemplateResponse("all_users.html", {
        "request": request, 
        "users": users_list
    })

# --- COMPANY VIEW ---
@app.get("/company_dashboard", response_class=HTMLResponse)
async def company_dashboard(request: Request):
    # Fetch reports for the submissions table
    report_cursor = reports_collection.find().sort("created_at", -1)
    reports_list = await report_cursor.to_list(length=100)
    
    # Fetch targets created by companies to display on their dashboard
    target_cursor = targets_collection.find().sort("created_at", -1)
    all_targets = await target_cursor.to_list(length=100)
    
    return templates.TemplateResponse("company_dashboard.html", {
        "request": request, 
        "reports": reports_list,
        "targets": all_targets # Now the company can see their published list
    })

@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse("contact_us.html", {"request": request})

@app.get("/back_hacker_dashboard", response_class=HTMLResponse)
async def back_hacker_dashboard(request: Request):
    return RedirectResponse("/dashboard", status_code=303)

@app.get("/new_target", response_class=HTMLResponse)
async def new_target(request: Request):
    # Logic to determine user type from cookie
    user_type = request.cookies.get("user_role") 
    cursor = targets_collection.find({"status": "Active"})
    live_targets = await cursor.to_list(length=100)
    
    return templates.TemplateResponse("new_target.html", {
        "request": request, 
        "targets": live_targets,
        "user_role": user_type 
    })

# ---------- ACTION ROUTES (POST) ----------
@app.post("/admin/delete-target/{target_id}")
async def admin_delete_target(target_id: str):
    # Deletes the target from MongoDB
    await targets_collection.delete_one({"_id": ObjectId(target_id)})
    return RedirectResponse("/admin", status_code=303)

# --- ACTION: ADD TARGET ---
@app.post("/add-target")
async def add_target(
    company_name: str = Form(...),
    scope: str = Form(...),
    max_bounty: int = Form(...),
    description: str = Form(...)
):
    # Store in MongoDB
    new_target_doc = {
        "company_name": company_name,
        "scope": scope,
        "max_bounty": max_bounty,
        "description": description,
        "status": "Active",
        "created_at": datetime.datetime.utcnow()
    }
    await targets_collection.insert_one(new_target_doc)
    # Redirect to see the updated list
    return RedirectResponse("/company_dashboard", status_code=303)

@app.post("/add-target")
async def add_target(
    company_name: str = Form(...),
    scope: str = Form(...),
    max_bounty: int = Form(...),
    description: str = Form(...)
):
    new_target_doc = {
        "company_name": company_name,
        "scope": scope,
        "max_bounty": max_bounty,
        "description": description,
        "status": "Active",
        "created_at": datetime.datetime.utcnow()
    }
    await targets_collection.insert_one(new_target_doc)
    return RedirectResponse("/new_target", status_code=303)

@app.post("/login")
async def do_login(username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "admin123":
        response = RedirectResponse("/admin", status_code=303)
        response.set_cookie(key="user_role", value="admin")
    elif username == "company":
        response = RedirectResponse("/company_dashboard", status_code=303)
        response.set_cookie(key="user_role", value="company")
    else:
        response = RedirectResponse("/dashboard", status_code=303)
        response.set_cookie(key="user_role", value="hacker")
    return response
    
@app.post("/register")
async def do_register(
    role: str = Form(...),
    firstName: str = Form(...),
    lastName: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    user_doc = {
        "role": role,
        "name": f"{firstName} {lastName}",
        "username": username,
        "email": email,
        "password": password
    }
    await users_collection.insert_one(user_doc)

    if role == "researcher":
        response = RedirectResponse("/dashboard", status_code=303)
        response.set_cookie(key="user_role", value="hacker")
    elif role == "company":
        response = RedirectResponse("/company_dashboard", status_code=303)
        response.set_cookie(key="user_role", value="company")
    else:
        response = RedirectResponse("/", status_code=303)
    return response

@app.post("/submit-bug")
async def handle_report(
    email: str = Form(...),
    title: str = Form(...),
    steps: str = Form(...),
    attachments: Optional[List[UploadFile]] = File(None)
):
    new_report = {
        "email": email,
        "title": title,
        "steps": steps,
        "status": "Pending",
        "created_at": datetime.datetime.utcnow()
    }
    await reports_collection.insert_one(new_report)
    return RedirectResponse(url="/dashboard", status_code=303)

@app.post("/admin/suspend/{user_id}")
async def suspend_user(user_id: str):
    return {"status": "success", "user": user_id}

@app.post("/company/pay/{report_id}")
async def pay_bounty(report_id: str):
    return {"status": "paid", "report": report_id}

# ---------- SERVER ----------

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)