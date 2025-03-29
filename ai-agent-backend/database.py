from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URI = "mongodb+srv://ravi:ravi@cluster0.bdi0mhr.mongodb.net/app_db?retryWrites=true&w=majority"

client = AsyncIOMotorClient(MONGO_URI)
database = client.app_db  # This ensures we are using the 'app_db' database
applications_collection = database.applications  # This is our collection
