import requests

API_URL = "https://api-inference.huggingface.co/models/Stelath/textual_inversion_comic_strip_test"
headers = {"Authorization": "Bearer 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"}

def query(payload):
	response = requests.post(API_URL, headers=headers, json=payload)
	return response.content
image_bytes = query({
	"inputs": "Astronaut riding a horse",
})
# You can access the image with PIL.Image for example
import io
from PIL import Image
image = Image.open(io.BytesIO(image_bytes))
image.save("output.png")