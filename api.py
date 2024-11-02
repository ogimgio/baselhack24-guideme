from fastapi import FastAPI, File, UploadFile, HTTPException, Response
from typing import List

import requests
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI, UploadFile, Form
from pydantic import BaseModel
from typing import List, Optional
import json
from fastapi import FastAPI, UploadFile, Form
from pydantic import BaseModel
from typing import List
import json
from fastapi import FastAPI, UploadFile, File
from typing import List
import uvicorn
from helpers import process_files_with_descriptions, encode_image_resized
import base64
from dotenv import load_dotenv

import os
# imports
from openai import OpenAI
import os
from PIL import Image
import base64
from pydantic import BaseModel
from PIL import Image
import io
import json


# FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Page(BaseModel):
    id: int
    content: str

class Instructions(BaseModel):
    pages_instructions: list[str]

load_dotenv()


@app.get("/")
async def read_root():
    return {"message": "Welcome to the API"}

@app.post("/api/generate")
async def generate_pages(
    file: UploadFile = File(...),  # Changed to File(...)
    description: Optional[str] = Form(None)  # Made description optional
):
    try:
        # Log received data for debugging
        print(f"Received file: {file.filename}")
        print(f"Description: {description}")

        # Mock pages data
        pages = [
            {
                "id": 1,
                 "content": f"""# Introduction
This is an automatically generated document based on your input: {description}

## Overview
Here's what we found in your file: {file.filename}

- Point 1: Key findings
- Point 2: Important metrics
- Point 3: Recommendations"""
            },
            {
                "id": 2,
                "content": """# Detailed Analysis

## Key Metrics
- Metric 1: Value
- Metric 2: Value
- Metric 3: Value

## Insights
Here are some interesting patterns we found..."""
            },
        ]
        
        return {
            "status": "success",
            "pages": pages
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@app.post("/uploadfiles/")
async def uploadfiles(files: List[UploadFile] = File(...)):
    """
    Upload multiple files and return their filenames and descriptions.

    Args:
        files (List[UploadFile]): List of files to be uploaded.

    Returns:
        dict: A dictionary containing the filenames of the uploaded files and descriptions.
    """
    filenames = [file.filename for file in files]
    
    # Process uploaded files and convert them to base64
    images_b64 = []
    for file in files:
        content = await file.read()
        images_b64.append(base64.b64encode(content).decode("utf-8"))
    
    example = [
    "# Section 1 \
    # How to Build a Paper Airplane \
    Follow these easy steps to make a classic paper airplane! \
    ## Materials Needed  \
    - 1 sheet of letter-sized paper (8.5\" x 11\") \
    1. **Prepare the Paper**  \
       - Place the paper on a flat surface in a **vertical orientation** (portrait style) so the long sides are on the left and right. \
       - Fold the paper in half vertically to create a **crease down the center**. This line will guide the following folds. \
       - Unfold to return the paper to its original flat state.",
    
    " # Section 2 \
    2. **Fold the Top Corners to the Center** \
       - Take the top-left corner of the paper and fold it down toward the center crease, aligning the edge with the crease to form a triangle. \
       - Repeat on the top-right corner, bringing it to meet the center crease and creating a **pointed top**.", 
    
    " # Section 3 \
    3. **Fold the Sides Toward the Center** \
        - Fold each side of the paper again toward the center crease, starting from the outer edges. \
        - This will create a longer, **sharper triangle** shape, with a pointed tip at the top.",
    
    " # Section 4 \
    4. **Create the Wings** \
       - Flip the airplane over so the triangle is facing down. \
       - Fold each side downward to form the wings, aligning the edges of the paper with the bottom of the airplane’s body. \
       - Make sure both wings are even so your airplane flies straight. \
    ## Ready for Takeoff! \
    Now your paper airplane is ready to fly! Hold it gently near the bottom and launch it forward for the best flight."
]
    
    # Create a prompt for OpenAI using the filenames
    prompt =f"""I uploaded {len(filenames)} images. These images provide visual instructions for assembling an object. Please analyze each image carefully and generate a clear, concise set of assembly instructions. \
    For each image, provide the following description: Create a detailed instruction in Markdown format that describes what the user should do based on the visual information presented in the corresponding image. \
    Output Format: The response should be structured as a list, where each element is a string that contains the Markdown-formatted instruction for that particular image. Max 1 description per image. So the list should be {len(filenames)} Descriptions (1 description per image)
    
    An example is provided below
    
    Input: 3 images of a paper airplane construction.
    Output: list of lenght = 3 containing the description of each step. eg: {example}
    """

    
    client = OpenAI(
    )
    # Make a call to OpenAI's API to get a description
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png; base64,{images_b64}" },
                    },
                ],
            }
        
        ],
        response_format=Instructions,
    )
    print(response)
    # Extract the generated description from OpenAI's response
    #description = response.choices[0].message['content']
    #descriptions = response.choices[0].message.parsed.json()['pages_instructions']
    #imgsWithDescr = process_files_with_descriptions(images_b64,descriptions)
    # Return filenames and the generated description
    
    # Your JSON string
    json_str = response.choices[0].message.parsed
    print(json_str)
    # Access the list of instructions
    if json_str is None:
        raise HTTPException(status_code=400, detail="Failed to parse instructions from the response.")
    instructions = json_str.pages_instructions
    print(instructions)
    imgsWithDescr = process_files_with_descriptions(images_b64,instructions)
    return  imgsWithDescr
    #try: print("HI)
    #    return {"error": str(e)}
    #except Exception as e:

# Run the FastAPI server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)