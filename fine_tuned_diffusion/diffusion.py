import requests
import io
import time
from PIL import Image
import base64

# API_URL = "https://api-inference.huggingface.co/models/Stelath/textual_inversion_comic_strip_test"
# key = open("huggingface_diffusion/hf_key", "r").read()
# headers = {"Authorization": f"Bearer {key}"}


API_URL = "https://stsunag27z4o1dpn.us-east-1.aws.endpoints.huggingface.cloud/"
headers = {
    "Accept": "application/json",
    "Authorization": "Bearer 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",
    "Content-Type": "application/json"
}


def get_images(prompts):
    """
    Given a prompt, get an image from the model
    :param prompt: A string
    :return: A PIL Image
    """

    prompts = ["An illustration in <comic-strip> style of " + prompt for prompt in prompts]

    payload = {
        "inputs": prompts,
        "negative_prompt": "text bubble, black and white, low saturation, blurry, low res, photorealistic, low contrast"
    }
    good = False
    while not good:
        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()  # What does this line do?  -> This line raises an HTTPError if the HTTP request returned an unsuccessful status code.
            good = True
        except requests.exceptions.HTTPError as err:
            print("Error: " + str(err) + " Prompts: " + str(prompts))
            time.sleep(5)

    response = response.json()
    # print("response: ", response.keys())
    image_prompt_pairs = []
    from_server_image_prompt_pairs = response["outputs"]
    for data in from_server_image_prompt_pairs:
        image_string = data["image"]  # This is a jpeg image encoded to string utf-8 from base 64
        image_bytes = base64.b64decode(image_string)
        image = Image.open(io.BytesIO(image_bytes))

        prompt = data["prompt"]
        image_prompt_pairs.append((image, prompt))

    images = []

    # Fill the images list with the images from the image_prompt_pairs
    # such that the order of the images matches the order of the prompts originally passed in

    for prompt in prompts:
        for image, image_prompt in image_prompt_pairs:
            if prompt == image_prompt:
                images.append(image)
                break
    return images


if __name__ == "__main__":
    prompts = ["strawberry on a beach", "lettuce on an iceberg", "carrot in a garden"]
    images = get_images(prompts)
    for image in images:
        image.show()
