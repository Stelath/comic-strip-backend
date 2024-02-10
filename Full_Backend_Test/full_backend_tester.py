from story_generator.story_prompter import ComicBookPrompter
from huggingface_diffusion.diffusion import get_image
from text_bubble_adder.text_bubble import add_text_bubbles

import os
import time
from multiprocessing import Pool

def process_prompt(data):
    i, prompt = data
    print(f"Gathering image for frame {i}")
    image = get_image(prompt)
    # image = add_text_bubbles(image, story.frames[i])
    image.save(f"Full_Backend_Test/frame_{i}.png")
    print(f"Frame {i} saved")


if __name__ == "__main__":
    start_time = time.time()


    """Testing"""
    user_prompt = "A super hero and their sidekick fight each other"
    print("Building story...")
    story = ComicBookPrompter(user_prompt)
    print("Story built")

    # Write story to file
    with open("Full_Backend_Test/story_output.txt", "w") as file:
        file.write(story.__str__())

    # Get images for each frame using multiprocessing
    with Pool() as p:
        p.map(process_prompt, [(i, prompt) for i, prompt in enumerate(story.frame_diffusion_prompts)])
    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")
