# Load model directly
from transformers import AutoProcessor, CLIPSegForImageSegmentation
import torch.nn.functional as F
from PIL import Image
import matplotlib.pyplot as plt
import os

# processor = AutoProcessor.from_pretrained("CIDAS/clipseg-rd64-refined")
# model = CLIPSegForImageSegmentation.from_pretrained("CIDAS/clipseg-rd64-refined")


def get_location(image, texts):
    """
    Given an image and a list of texts, find the location of the text in the image
    :param image: A PIL image
    :param texts: A list of strings
    :return: A tuple of (x, y) coordinates
    """
    texts.append("Human Head")
    # Preprocess image
    inputs = processor(text=texts,
                       images=[image] * len(texts), return_tensors="pt", padding=True)
    outputs = model(**inputs)

    # Normalize the second dimension of the logits so it's between 0 and 1 for if there is a head there or not
    min_val = outputs.logits[1].min()
    max_val = outputs.logits[1].max()
    outputs.logits = (outputs.logits - min_val) / (max_val - min_val)

    # Multiplying the layers together as a AND essentially
    combined_logits = outputs.logits[0] * outputs.logits[1]

    # Flatten the tensor and find the index of the maximum value
    max_index = combined_logits.view(-1).argmax()

    # Convert the index back to 2D coordinates
    y, x = divmod(max_index.item(), combined_logits.shape[1])

    # Calculate the scaling factor
    scale_x = image.width / combined_logits.shape[1]
    scale_y = image.height / combined_logits.shape[0]

    # Scale the coordinates
    x = x * scale_x
    y = y * scale_y

    # Scale the logits so they can be used for edge detection
    # Scale the logits so they can be used for edge detection
    logits = combined_logits.unsqueeze(0).unsqueeze(0)  # Add batch size and channel dimensions
    scaled_logits = F.interpolate(logits, size=(image.height, image.width), mode='bilinear', align_corners=False)
    # Render the logits
    plt.imshow(scaled_logits.squeeze(0).squeeze(0).detach().numpy())
    # plt.show()

    scaled_logits = scaled_logits.squeeze(0).squeeze(0)
    return x, y, scaled_logits
