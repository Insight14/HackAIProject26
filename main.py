from fastapi import FastAPI
from disaster_events import get_active_disaster_events
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/events")
def read_events():
    """API endpoint to get all active disaster events."""
    events = get_active_disaster_events()
    return JSONResponse(content=events)

@app.get("/")
def root():
    return {"message": "Disaster Events API. Use /events to get current events."}
