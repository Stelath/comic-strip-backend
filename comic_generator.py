from story_generator.story_prompter import ComicBookPrompter
from fine_tuned_diffusion.diffusion import get_image

import os
import time
from multiprocessing import Pool


def process_prompt(data):
    i, prompt = data
    print(f"Gathering image for frame {i}")
    return get_image(prompt)

class ComicGenerator():
    def __init__(self, prompt, job_id) -> None:
        self.start_time = time.time()
        self.end_time = None
        self.time_taken = None
        self.user_prompt = prompt
        self.job_id = job_id
        
        self.progress = 0
        self.current_state = "Building Story"
    
    def generate(self):
        story = ComicBookPrompter(self.user_prompt)
        self.current_state = "Story built"
        self.progress = 0.2

        # Write story to file
        with open("Full_Backend_Test/story_output.txt", "w") as file:
            file.write(story.__str__())

        # Get images for each frame using multiprocessing
        with Pool() as p:
            # Process the prompts and store them in frame_images using multiprocessing
            # The order of the frames is important, so we use enumerate to keep track of the index
            frame_images = p.map(process_prompt, enumerate(story.frame_diffusion_prompts))
        
        self.current_state = "Generated Images"
        self.progress = 0.8
        
        # Wait to import so multiprocessing doesn't by default
        from text_bubble_adder.text_bubble import add_text_bubbles
        
        for i, image in enumerate(frame_images):
            image = add_text_bubbles(image, story.frames[i])
            image.save(f"generated_comics/{self.job_id}/frame_{i}.png")
            print(f"Frame {i} saved")
        
        self.current_state = "Text Bubbles Added"
        self.progress = 1.0

        self.end_time = time.time()
        self.time_taken = self.end_time - self.start_time
