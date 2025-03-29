from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import motor.motor_asyncio
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timedelta
from typing import Optional
import os

app = FastAPI()

# ✅ CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to your frontend domain for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ MongoDB Connection
MONGO_URI = "mongodb+srv://ravi:ravi@cluster0.bdi0mhr.mongodb.net/?retryWrites=true&w=majority"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client["app_db"]
applications_collection = db["applications"]

@app.get("/")
def home():
    return {"message": "FastAPI + MongoDB Atlas is running!"}

# ✅ Mount static files (for favicon)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ✅ Serve the favicon
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    favicon_path = os.path.join("static", "favicon.ico")
    return FileResponse(favicon_path)

# ✅ Application Data Model
class ApplicationInput(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str  
    ssn_last4: str  
    address: str

class Application(ApplicationInput):
    submission_date: str  
    status: str
    approval_eta: Optional[int]  
    approval_estimated_date: Optional[str]  
    approval_date: Optional[str]  

# ✅ Function to Calculate ETA & Estimated Approval Date
def calculate_eta(submission_date: str, status: str):
    try:
        submission_datetime = datetime.strptime(submission_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date format: {submission_date}. Expected format: YYYY-MM-DD.")
    
    if status in ["Approved", "Rejected"]:
        return 0, None  
    
    today = datetime.utcnow()
    days_since_submission = (today - submission_datetime).days
    approval_eta = 5 if days_since_submission <= 3 else 3
    approval_estimated_date = submission_datetime + timedelta(days=approval_eta)
    
    return approval_eta, approval_estimated_date.strftime("%Y-%m-%d")

# ✅ Create Application (POST)
from fastapi.encoders import jsonable_encoder

@app.post("/applications/")
async def create_application(app: ApplicationInput):
    try:
        submission_date = datetime.utcnow().strftime("%Y-%m-%d")
        status = "Pending"
        approval_eta, approval_estimated_date = calculate_eta(submission_date, status)

        app_dict = app.dict()
        app_dict.update({
            "submission_date": submission_date,
            "status": status,
            "approval_eta": approval_eta,
            "approval_estimated_date": approval_estimated_date,
            "approval_date": None
        })

        result = await applications_collection.insert_one(app_dict)

        # Convert ObjectId to string before returning
        app_dict["_id"] = str(result.inserted_id)

        return jsonable_encoder(app_dict)  # ✅ Ensure JSON serialization
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ✅ Get All Applications (GET)
@app.get("/applications/")
async def get_applications():
    applications = await applications_collection.find().to_list(length=100)
    for app in applications:
        app["_id"] = str(app["_id"])  # ✅ Convert ObjectId to string
    return jsonable_encoder(applications)

# ✅ Get Single Application by ID (GET)
@app.get("/applications/{app_id}")
async def get_application(app_id: str):
    try:
        obj_id = ObjectId(app_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid application ID")

    app = await applications_collection.find_one({"_id": obj_id})
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    app["_id"] = str(app["_id"])
    return app

# ✅ Update Application (PUT)
@app.put("/applications/{app_id}")
async def update_application(app_id: str, status: str):
    try:
        obj_id = ObjectId(app_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid application ID")

    application = await applications_collection.find_one({"_id": obj_id})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    submission_date = application.get("submission_date", datetime.utcnow().strftime("%Y-%m-%d"))
    approval_eta, approval_estimated_date = calculate_eta(submission_date, status)

    approval_date = datetime.utcnow().strftime("%Y-%m-%d") if status == "Approved" else None

    update_data = {
        "status": status,
        "approval_eta": approval_eta,
        "approval_estimated_date": approval_estimated_date,
        "approval_date": approval_date
    }

    await applications_collection.update_one({"_id": obj_id}, {"$set": update_data})

    updated_application = await applications_collection.find_one({"_id": obj_id})
    updated_application["_id"] = str(updated_application["_id"])  # Convert ObjectId to string
    
    return jsonable_encoder({
        "message": "Application status updated successfully",
        "updated_application": updated_application
    })

# ✅ Delete Application (DELETE)
@app.delete("/applications/{app_id}")
async def delete_application(app_id: str):
    try:
        obj_id = ObjectId(app_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid application ID")

    result = await applications_collection.delete_one({"_id": obj_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Application not found")

    return {"message": "Application deleted successfully"} 
