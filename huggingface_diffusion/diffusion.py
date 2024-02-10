import requests
import io
from PIL import Image

API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": "Bearer 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"}


def get_image(prompt):
    """
    Given a prompt, get an image from the model
    :param prompt: A string
    :return: A PIL Image
    """
    payload = {
        "inputs": prompt,
    }
    good = False
    while not good:
        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()  # What does this line do?  -> This line raises an HTTPError if the HTTP request returned an unsuccessful status code.
            good = True
        except requests.exceptions.HTTPError as err:
            print("Error: " + str(err))

    image_bytes = response.content
    image = Image.open(io.BytesIO(image_bytes))
    return image


if __name__ == "__main__":
    prompt = "A super hero and their sidekick fight each other"
    image = get_image(prompt)
    # Save the image
    image.save("output.png")