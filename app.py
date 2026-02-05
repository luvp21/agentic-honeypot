"""
Hugging Face Spaces Entrypoint
This file is required for Hugging Face Spaces deployment.
It imports the FastAPI app from main.py and exposes it.
"""

from main import app

# Hugging Face Spaces will look for the 'app' variable
# The app is already configured in main.py with all endpoints and middleware

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
