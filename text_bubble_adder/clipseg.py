# Load model directly
from transformers import AutoProcessor, CLIPSegForImageSegmentation
import torch.nn.functional as F
from PIL import Image
import matplotlib.pyplot as plt

processor = AutoProcessor.from_pretrained("CIDAS/clipseg-rd64-refined")
model = CLIPSegForImageSegmentation.from_pretrained("CIDAS/clipseg-rd64-refined")


def get_location(image, texts):
    """
    Given an image and a list of texts, find the location of the text in the image
    :param image: A PIL image
    :param texts: A list of strings
    :return: A tuple of (x, y) coordinates
    """
    # Preprocess image
    inputs = processor(text=texts, images=[image] * len(texts), return_tensors="pt", padding=True)
    outputs = model(**inputs)

    # Flatten the tensor and find the index of the maximum value
    max_index = outputs.logits.view(-1).argmax()

    # Convert the index back to 2D coordinates
    y, x = divmod(max_index.item(), outputs.logits.shape[1])

    # Calculate the scaling factor
    scale_x = image.width / outputs.logits.shape[1]
    scale_y = image.height / outputs.logits.shape[0]

    # Scale the coordinates
    x = x * scale_x
    y = y * scale_y

    # Scale the logits so they can be used for edge detection
    print("outputs.logits shape:", outputs.logits.shape)
    # Scale the logits so they can be used for edge detection
    logits = outputs.logits.unsqueeze(0).unsqueeze(0)  # Add batch size and channel dimensions
    scaled_logits = F.interpolate(logits, size=(image.height, image.width), mode='bilinear', align_corners=False)

    # Convert to shape of [1024, 1024]
    scaled_logits = scaled_logits.squeeze(0).squeeze(0)
    return x, y, scaled_logits




