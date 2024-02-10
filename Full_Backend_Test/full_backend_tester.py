from story_generator.story_prompter import ComicBookPrompter
from huggingface_diffusion.diffusion import get_image
from text_bubble_adder.text_bubble import add_text_bubbles

import os
import time

start_time = time.time()


"""Testing"""
user_prompt = "A super hero and their sidekick fight each other"
print("Building story...")
story = ComicBookPrompter(user_prompt)
print("Story built")

# Write story to file
with open("../story_output.txt", "w") as file:
    file.write(story.__str__())

for i, prompt in enumerate(story.frame_diffusion_prompts):
    print(f"Gathering image for frame {i}")
    image = get_image(prompt)
    image = add_text_bubbles(image, story.frames[i].characters)
    image.save(f"frame_{i}.png")
    print(f"Frame {i} saved")
