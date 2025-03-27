from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import motor.motor_asyncio
from bson import ObjectId
from datetime import datetime, timedelta

app = FastAPI()

# ✅ MongoDB Connection
MONGO_URI = "mongodb://localhost:27017"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client["app_db"]
applications_collection = db["applications"]

# ✅ Home Route
@app.get("/")
def home():
    return {"message": "FastAPI is running!"}

# ✅ Application Data Model
class Application(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str  # Format: YYYY-MM-DD
    ssn_last4: str  # Last 4 digits only
    address: str
    submission_date: str  # Format: YYYY-MM-DD
    status: str = "Pending"  # Default status
    approval_eta: int = 0  # Days until approval
    approval_date: str = ""

# ✅ Function to Calculate ETA
def calculate_eta(submission_date: str, status: str) -> int:
    if status in ["Approved", "Rejected"]:
        return 0  # No ETA needed
    submission_datetime = datetime.strptime(submission_date, "%Y-%m-%d")
    today = datetime.today()

    # Basic Rule: Processing takes between 3 to 7 days
    base_eta = 5

    # Priority Cases: If submission is over 3 days old, expedite
    days_since_submission = (today - submission_datetime).days
    if days_since_submission > 3:
        base_eta = 3

    return base_eta

# ✅ Create Application (POST)
@app.post("/applications/")
async def create_application(app: Application):
    app_dict = app.dict()
    
    # Calculate ETA based on submission date
    app_dict["approval_eta"] = calculate_eta(app.submission_date, app.status)
    
    result = await applications_collection.insert_one(app_dict)
    return {"id": str(result.inserted_id), "message": "Application submitted successfully"}

# ✅ Get All Applications (GET)
@app.get("/applications/")
async def get_applications():
    applications = await applications_collection.find().to_list(length=100)
    for app in applications:
        app["_id"] = str(app["_id"])  # Convert ObjectId to string
    return applications

# ✅ Get Single Application by ID (GET)
@app.get("/applications/{app_id}")
async def get_application(app_id: str):
    app = await applications_collection.find_one({"_id": ObjectId(app_id)})
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    app["_id"] = str(app["_id"])
    return app

# ✅ Update Application Status & ETA (PUT)
@app.put("/applications/{app_id}")
async def update_application(app_id: str, status: str):
    application = await applications_collection.find_one({"_id": ObjectId(app_id)})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Update approval date if approved
    approval_date = datetime.today().strftime("%Y-%m-%d") if status == "Approved" else ""
    
    # Recalculate ETA
    approval_eta = calculate_eta(application["submission_date"], status)
    
    result = await applications_collection.update_one(
        {"_id": ObjectId(app_id)},
        {"$set": {"status": status, "approval_eta": approval_eta, "approval_date": approval_date}}
    )
    
    return {"message": "Application status updated successfully"}

# ✅ Delete Application (DELETE)
@app.delete("/applications/{app_id}")
async def delete_application(app_id: str):
    result = await applications_collection.delete_one({"_id": ObjectId(app_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"message": "Application deleted successfully"}
