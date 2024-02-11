import uuid
import time

from comic_generator import ComicGenerator

class JobManager:
    def __init__(self):
        self.jobs = {}
    
    def new_job(self, prompt):
        job_id = self.generate_job_id()
        
        comic_generator = ComicGenerator(prompt, job_id)
        self.add_job(job_id, comic_generator)
        
        comic_generator.generate()
        
        return job_id
    
    def generate_job_id(self):
        return str(uuid.uuid4())
    
    def add_job(self, job_id, job):
        self.jobs[job_id] = job
    
    def get_job_info(self, job_id):
        job = self[job_id]
        
        status = {
            "startTime": job.start_time,
            "elapsedTime": job.time_taken if job.time_taken != None else time.time() - job.start_time,
            "endTime": job.end_time,
            "currentState": job.current_state,
            "progress": job.progress,
            "prompt": job.user_prompt,
            "frames": job.frames,
        }
        
        return status
    
    def __getitem__(self, job_id):
        return self.jobs[job_id]