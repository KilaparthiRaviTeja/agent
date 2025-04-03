from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import motor.motor_asyncio
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timedelta
from typing import Optional
import joblib
import pandas as pd

app = FastAPI()

# ✅ Secure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ MongoDB Connection
MONGO_URI = "mongodb+srv://ravi:bunny@cluster0.m6iwsdt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client["app_db"]
applications_collection = db["applications"]

# ✅ Load Models
eligibility_model = joblib.load("approval_model.pkl")  
rf_model = joblib.load("random_forest_model.pkl")  
scaler = joblib.load("scaler.pkl")  

# ✅ Approved Government Assistance Programs
APPROVED_PROGRAMS = {
    "SNAP", "SSI", "Medicaid", "Federal Public Housing Assistance",
    "Bureau of Indian Affairs General Assistance", "TTANF",
    "FDPIR", "Head Start"
}

@app.get("/")
def home():
    return {"message": "FastAPI with AI Model and MongoDB is running!"}

# ✅ Data Models
class ApplicationInput(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str
    ssn_last4: str
    income: float
    address: str
    is_enrolled_in_program: bool = False
    program_name: Optional[str] = None
    household_size: int

class ApplicationRequest(BaseModel):
    date_of_birth: str  
    income: float
    household_size: int
    is_enrolled_in_program: bool
    program_name: Optional[str] = None 

class Application(ApplicationInput):
    submission_date: str
    status: str
    approval_eta: Optional[int]
    approval_estimated_date: Optional[str]
    approval_date: Optional[str]

# ✅ Function to Calculate ETA
def calculate_eta(submission_date: str, status: str):
    if status in ["Approved", "Rejected"]:
        return 0, None
    
    try:
        submission_datetime = datetime.strptime(submission_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date format: {submission_date}. Expected format: YYYY-MM-DD.")
    
    days_since_submission = (datetime.utcnow() - submission_datetime).days
    approval_eta = 5 if days_since_submission <= 3 else 3
    approval_estimated_date = submission_datetime + timedelta(days=approval_eta)

    return approval_eta, approval_estimated_date.strftime("%Y-%m-%d")

# ✅ AI Eligibility Prediction
@app.post("/predict-eligibility/")
def predict_eligibility(app: ApplicationRequest):
    try:
        # ✅ Calculate Age
        birth_date = datetime.strptime(app.date_of_birth, "%Y-%m-%d")
        today = datetime.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

        if age < 18:
            return {"approved": False, "reason": "Applicant must be at least 18 years old."}

        # ✅ Income Eligibility
        income_limit = 1.35 * (15060 + (app.household_size - 1) * 5400)
        income_eligible = 1 if app.income <= income_limit else 0

        # ✅ Government Assistance Check
        gov_program = 1 if app.program_name in APPROVED_PROGRAMS else 0

        # ✅ Prepare Input for Model
        input_data = pd.DataFrame([[age, income_eligible, gov_program]], 
                                  columns=["age", "income_eligible", "gov_program"])

        # ✅ Scale Age
        input_data["age"] = scaler.transform(input_data[["age"]])

        # ✅ Predict Approval
        prediction = eligibility_model.predict(input_data)[0]

        return {"approved": bool(prediction)}

    except Exception as e:
        return {"error": str(e)}

# ✅ AI Final Approval Prediction
@app.post("/predict/")
async def predict_approval(app: ApplicationRequest):
    try:
        # ✅ Calculate Age
        birth_date = datetime.strptime(app.date_of_birth, "%Y-%m-%d")
        today = datetime.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

        # ✅ Determine Income Eligibility
        income_limit = 1.35 * (15060 + (app.household_size - 1) * 5400)
        income_eligible = int(app.income <= income_limit)

        # ✅ Determine Government Program Eligibility
        gov_program = int(app.is_enrolled_in_program)

        # ✅ Prepare Data for Model
# ✅ Corrected Order
        input_data = pd.DataFrame([[age, income_eligible, gov_program]], 
        columns=["age", "income_eligible", "gov_program"])


        # ✅ Predict Final Approval
        prediction = rf_model.predict(input_data)[0]
        if prediction == 1:
            return {"status": "Approved"}
        else:
             
             reasons = []
             if income_eligible == 0:
                  reasons.append("Income exceeds eligibility limit.")
             if gov_program == 0 and app.is_enrolled_in_program:
                 reasons.append("Program is not an approved government assistance program.")
             if age < 18:
                 reasons.append("Applicant must be at least 18 years old.")

             return {
               "status": "Denied",
               "reason": reasons if reasons else ["Not eligible based on approval criteria."]
            }
        
        

    except Exception as e:
        return {"error": str(e)}

# ✅ Application Endpoints
@app.get("/applications/")
async def get_applications():
    applications = await applications_collection.find().to_list(length=100)
    for app in applications:
        app["_id"] = str(app["_id"])
    return applications

@app.post("/applications/", response_model=Application)
async def create_application(app: ApplicationInput):
    try:
        submission_date = datetime.utcnow().strftime("%Y-%m-%d")
        status = "Pending"
        approval_eta, approval_estimated_date = calculate_eta(submission_date, status)

        if app.is_enrolled_in_program and not app.program_name:
            raise HTTPException(status_code=400, detail="Program name is required if enrolled.")

        app_dict = app.dict()
        app_dict.update({
            "submission_date": submission_date,
            "status": status,
            "approval_eta": approval_eta,
            "approval_estimated_date": approval_estimated_date,
            "approval_date": None
        })

        result = await applications_collection.insert_one(app_dict)
        app_dict["_id"] = str(result.inserted_id)

        return app_dict
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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

@app.put("/applications/{app_id}")
async def update_application(app_id: str, status: str):
    obj_id = ObjectId(app_id)
    await applications_collection.update_one({"_id": obj_id}, {"$set": {"status": status}})
    return {"message": "Application status updated"}

@app.delete("/applications/{app_id}")
async def delete_application(app_id: str):
    result = await applications_collection.delete_one({"_id": ObjectId(app_id)})
    return {"message": "Application deleted successfully"} if result.deleted_count else HTTPException(status_code=404, detail="Application not found")
