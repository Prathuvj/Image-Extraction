from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import shutil
import os
import uuid
import cv2
import pytesseract
from extraction import extract_tests

app = FastAPI()

# Enable CORS for local development and browser support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with specific origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folder for frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

# -----------------------------------------------
# Route: Serve Frontend
# -----------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# -----------------------------------------------
# Response Models
# -----------------------------------------------
class LabTest(BaseModel):
    test_name: str
    test_value: str
    test_unit: str
    bio_reference_range: Optional[str]  # Allow None for missing ranges
    lab_test_out_of_range: bool

class LabTestResponse(BaseModel):
    is_success: bool
    message: str
    data: List[LabTest]


# -----------------------------------------------
# Route: Upload and Extract Lab Tests
# -----------------------------------------------
@app.post("/get-lab-tests", response_model=LabTestResponse)
async def get_lab_tests(file: UploadFile = File(...)):
    temp_filename = f"temp_{uuid.uuid4()}.jpg"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Perform OCR
        image = cv2.imread(temp_filename)
        text = pytesseract.image_to_string(image)

        # Extract lab test data
        extracted_data = extract_tests(text)

        return {
            "is_success": True,
            "message": "Lab tests extracted successfully.",
            "data": extracted_data
        }

    except Exception as e:
        return {
            "is_success": False,
            "message": f"Failed to process image: {str(e)}",
            "data": []
        }

    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
