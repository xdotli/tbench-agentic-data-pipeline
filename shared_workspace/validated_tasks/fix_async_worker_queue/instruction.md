Fix the broken asynchronous worker queue system.
The application has a worker queue that processes jobs asynchronously. Currently it has multiple bugs preventing it from working correctly.
The system should:

Accept job submissions via /submit endpoint
Process jobs in the background using async workers
Return job status via /status/{job_id} endpoint
Mark jobs as completed when done
Handle concurrent job processing

Current bugs:

Jobs are not being processed
Job status is not updating correctly
Workers are not running properly
Race condition in job state management

Fix all issues in /app/worker_queue.py to make the system work correctly.
Test the system by running the application and submitting jobs.