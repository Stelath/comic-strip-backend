import os
import argparse
from PIL import Image
from tqdm import tqdm

def resize_and_crop(img_path, size):
    img = Image.open(img_path)
    width, height = img.size

    if width > height:
        left = (width - height)/2
        top = 0
        right = (width + height)/2
        bottom = height
    else:
        top = (height - width)/2
        left = 0
        bottom = (height + width)/2
        right = width

    img = img.crop((left, top, right, bottom))
    img = img.resize(size, Image.Resampling.LANCZOS)
    img.save(img_path)

def main(folder_path):
    for filename in tqdm(os.listdir(folder_path)):
        if filename.endswith(('.jpg', '.png', '.jpeg')):
            img_path = os.path.join(folder_path, filename)
            resize_and_crop(img_path, (512, 512))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Resize and crop images in a folder to 512x512.')
    parser.add_argument('-f', '--folder-path', type=str, help='Path to the folder containing images')
    args = parser.parse_args()
    main(args.folder_path)