from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI="mongodb+srv://ravi:bunny@cluster0.m6iwsdt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = AsyncIOMotorClient(MONGO_URI)
database = client.app_db  # This ensures we are using the 'app_db' database
applications_collection = database.applications  # This is our collection
