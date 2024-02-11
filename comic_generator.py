from story_generator.story_prompter import ComicBookPrompter
from fine_tuned_diffusion.diffusion import get_images

import os
import time



class ComicGenerator():
    def __init__(self, prompt, job_id, num_images) -> None:
        self.num_images = num_images
        self.start_time = time.time()
        self.end_time = None
        self.time_taken = None
        self.user_prompt = prompt
        self.job_id = job_id

        self.progress = 0
        self.current_state = "Building Story"

        self.story_title = ""
        self.frames = []

    def generate(self):
        output_dir = os.path.join('generated_comics', self.job_id)
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, 'frames'), exist_ok=True)
        
        story = ComicBookPrompter(self.user_prompt, num_frames=self.num_images)
        self.story_title = story.title
        self.current_state = "Story built"
        self.progress = 0.2

        # Write story to file
        with open(os.path.join(output_dir, 'story_output.txt'), "w") as file:
            file.write(story.__str__())

        batch_size = 3

        # Break the diffusion prompts into batches of at most batch_size prompts
        batches = [story.frame_diffusion_prompts[i:i + batch_size] for i in range(0, len(story.frame_diffusion_prompts), batch_size)]
        frame_images = []
        for batch in batches:
            print("Getting images for batch", batch)
            print("number of prompts in batch", len(batch))
            frame_images.extend(get_images(batch))
            self.progress += 0.6 / len(batches)



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


if __name__ == "__main__":
    # Test the comic generator
    comic = ComicGenerator("Astronaut riding a horse", "test_job")
    comic.generate()
    print(comic.story_title)
    print(comic.frames)
    print(comic.time_taken)
    print(comic.current_state)
    print(comic.progress)
    print(comic.user_prompt)
    print(comic.job_id)