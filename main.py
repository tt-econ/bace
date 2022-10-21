# Package Imports
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import time

# Custom Imports
from BACE import router_standard
from BACE.user import router_qualtrics_custom
from BACE.user.configuration import author_name

# Initialize Fast API app
app=FastAPI()
app.include_router(router_qualtrics_custom.router)
app.include_router(router_standard.router)

# Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# General functions to run on startup and shutdown of dynos.
@app.on_event("startup")
def on_startup():
    print('Print starting up.')
    # subprocess.run("bash buildpack-run.sh", shell=True)

@app.on_event("shutdown")
async def on_shutdown():
    print('Shutting down session')


# Router home page.
@app.get('/', response_class=HTMLResponse)
def index():

    homepage = f"""
    <html>
        <head>
            <title>BACE Homepage</title>
        </head>
        <p><b>Bayesian Adaptive Choice Experiment (BACE)</b></p>
        <p>Author: {author_name}</p>
        <p>Your application is up and running.</p>
    </html>
    """

    return HTMLResponse(content=homepage, status_code=200)
