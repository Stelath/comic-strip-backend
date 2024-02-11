import requests
import io
import time
from PIL import Image

# API_URL = "https://api-inference.huggingface.co/models/Stelath/textual_inversion_comic_strip_test"
# key = open("huggingface_diffusion/hf_key", "r").read()
# headers = {"Authorization": f"Bearer {key}"}


API_URL = "https://zlie2z38iazjx0cm.us-east-1.aws.endpoints.huggingface.cloud/"
headers = {
    "Accept" : "image/png",
    "Authorization": "Bearer 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",
    "Content-Type": "application/json"
}



def get_image(prompt):
    """
    Given a prompt, get an image from the model
    :param prompt: A string
    :return: A PIL Image
    """
    print("Using Alex's Diffusion model")
    payload = {
        "inputs": prompt + ", in the style of <comic-strip>",
        "negative_prompt": "text bubble, black and white, low saturation, blurry, low res, photorealistic, low contrast"
    }
    good = False
    while not good:
        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()  # What does this line do?  -> This line raises an HTTPError if the HTTP request returned an unsuccessful status code.
            good = True
        except requests.exceptions.HTTPError as err:
            print("Error: " + str(err) + " Prompt: " + prompt)
            time.sleep(3)

    image_bytes = response.content
    image = Image.open(io.BytesIO(image_bytes))
    return image

if __name__ == "__main__":
    prompt = "strawberry on a beach"
    image = get_image(prompt)
    # Save the image
    image.save("output.png")
    image.show()