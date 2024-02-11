import uuid
from comic_generator import ComicGenerator

class JobManager:
    def __init__(self):
        self.jobs = {}
    
    def new_job(self, prompt):
        job_id = self.generate_job_id()
        
        comic_generator = ComicGenerator(prompt, job_id)
        self.add_job(job_id, comic_generator)
    
    def generate_job_id(self):
        return str(uuid.uuid4())
    
    def add_job(self, job_id, job):
        self.jobs[job_id] = job
    
    def get_job_status(self, job_id):
        return self[job_id].progress
    
    def __getitem__(self, job_id):
        return self.jobs[job_id]