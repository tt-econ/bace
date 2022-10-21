// Single worker per dyno
web: gunicorn -w 2 -k uvicorn.workers.UvicornWorker main:app

// Example with 4 workers
//web: gunicorn -w 3 -k uvicorn.workers.UvicornWorker main:app
