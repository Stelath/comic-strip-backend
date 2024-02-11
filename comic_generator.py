from story_generator.story_prompter import ComicBookPrompter
from fine_tuned_diffusion.diffusion import get_image

import os
import time
from multiprocessing import Pool

def process_prompt(data):
    i, prompt = data
    print(f"Gathering image for frame {i}")
    image = get_image(prompt)
    print(f"Got image: {i}")
    
    return image

class ComicGenerator():
    def __init__(self, prompt, job_id) -> None:
        self.start_time = time.time()
        self.end_time = None
        self.time_taken = None
        self.user_prompt = prompt
        self.job_id = job_id
        
        self.progress = 0
        self.current_state = "Building Story"
        
        self.frames = []
    
    def generate(self):
        output_dir = os.path.join('generated_comics', self.job_id)
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, 'frames'), exist_ok=True)
        
        story = ComicBookPrompter(self.user_prompt, num_frames=8)
        self.current_state = "Story built"
        self.progress = 0.2
        
        # Write story to file
        with open(os.path.join(output_dir, 'story_output.txt'), "w") as file:
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
            
            frame_name = f"frame_{i:03}.png"
            # print(f"Saving frame {i} to {os.path.join(output_dir, 'frames', frame_name)}")
            image.save(os.path.join(output_dir, 'frames', frame_name))
            self.frames.append(os.path.join('/api', 'images', self.job_id, frame_name))
        
        self.current_state = "Text Bubbles Added"
        self.progress = 1.0
        
        self.end_time = time.time()
        self.time_taken = self.end_time - self.start_time
        self.current_state = "Completed"
