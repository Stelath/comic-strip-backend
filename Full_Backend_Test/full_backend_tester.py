from story_generator.story_prompter import ComicBookPrompter
from fine_tuned_diffusion.diffusion import get_image

import os
import time
from multiprocessing import Pool


def process_prompt(data):
    i, prompt = data
    print(f"Gathering image for frame {i}")
    image = get_image(prompt)
    print(f"Image for frame {i} gathered")
    return image


if __name__ == "__main__":
    start_time = time.time()

    """Testing"""
    user_prompt = "Young man meets a girl and learns the power of artillery"
    story = ComicBookPrompter(user_prompt)
    print("Story built")

    # Write story to file
    with open("Full_Backend_Test/story_output.txt", "w") as file:
        file.write(story.__str__())

    # Get images for each frame using multiprocessing
    with Pool() as p:
        # Process the prompts and store them in frame_images using multiprocessing
        # The order of the frames is important, so we use enumerate to keep track of the index
        frame_images = p.map(process_prompt, enumerate(story.frame_diffusion_prompts))

    from text_bubble_adder.text_bubble import add_text_bubbles
    # Add text bubbles to each frame

    for i, image in enumerate(frame_images):
        image = add_text_bubbles(image, story.frames[i])
        image.save(f"Full_Backend_Test/frame_{i}.png")
        print(f"Frame {i} saved")

    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")
