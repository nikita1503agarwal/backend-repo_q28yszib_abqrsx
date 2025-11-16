import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import create_document, get_documents
from schemas import Lead

app = FastAPI(title="Yapp360 New Version API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Backend running", "service": "yapp360-new"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

# Lead endpoints
@app.post("/api/leads")
def create_lead(lead: Lead):
    try:
        inserted_id = create_document("lead", lead)
        return {"status": "ok", "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/leads")
def list_leads(limit: int = 20):
    try:
        docs = get_documents("lead", limit=limit)
        # Convert ObjectId and datetime to strings for JSON
        def normalize(doc):
            d = {}
            for k, v in doc.items():
                if k == "_id":
                    d["id"] = str(v)
                else:
                    d[k] = str(v) if hasattr(v, "isoformat") else v
            return d
        return {"items": [normalize(x) for x in docs]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Schema endpoint for tooling
@app.get("/schema")
def get_schema():
    # Expose available schemas for viewer/tools
    return {
        "lead": {
            "fields": list(Lead.model_fields.keys())
        }
    }

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = getattr(db, 'name', "✅ Connected")
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except ImportError:
        response["database"] = "❌ Database module not found"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
