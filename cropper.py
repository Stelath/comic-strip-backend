import os
import cv2
import numpy as np
from PIL import Image
from tqdm import tqdm
from multiprocessing import Pool

from skimage.color import rgb2gray, label2rgb
from skimage.feature import canny
from skimage.morphology import dilation
from skimage.measure import label
from skimage.measure import regionprops

from scipy import ndimage as ndi

import argparse

def smart_crop(img_path, output_dir, image_num):
    im = np.array(Image.open(img_path))

    grayscale = rgb2gray(im)
    Image.fromarray((grayscale * 255).astype('uint8'), 'L')

    edges = canny(grayscale)
    Image.fromarray(edges)

    thick_edges = dilation(dilation(edges))
    Image.fromarray(thick_edges)

    segmentation = ndi.binary_fill_holes(thick_edges)
    Image.fromarray(segmentation)

    labels = label(segmentation)

    segmented_img = Image.fromarray(np.uint8(label2rgb(labels, bg_label=0) * 255))


    def do_bboxes_overlap(a, b):
        return (
            a[0] < b[2] and
            a[2] > b[0] and
            a[1] < b[3] and
            a[3] > b[1]
        )

    def merge_bboxes(a, b):
        return (
            min(a[0], b[0]),
            min(a[1], b[1]),
            max(a[2], b[2]),
            max(a[3], b[3])
        )

    regions = regionprops(labels)
    panels = []

    for region in regions:

        for i, panel in enumerate(panels):
            if do_bboxes_overlap(region.bbox, panel):
                panels[i] = merge_bboxes(panel, region.bbox)
                break
        else:
            panels.append(region.bbox)

    saved_count = 0
    for panel in panels:
        minr, minc, maxr, maxc = panel
        if maxr - minr > 256 and maxc - minc > 256:
            cropped = im[minr:maxr, minc:maxc]
            cropped_img = Image.fromarray(cropped)
            cropped_img.save(f"{output_dir}/image_{image_num:04}_{saved_count:02}.png")
            saved_count += 1

def main(folder_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    image_files = [(os.path.join(folder_path, filename), output_dir, i) 
                   for i, filename in enumerate(os.listdir(folder_path)) 
                   if filename.endswith(('.jpg', '.png', '.jpeg'))]

    with Pool(os.cpu_count()) as p:
        p.starmap(smart_crop, image_files)

def dataset_crop(folder_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    frame_size = 768
    
    image_files = [os.path.join(folder_path, filename) for filename in os.listdir(folder_path)]
    
    saved_images = 0
    for image_file in tqdm(image_files):
        img = Image.open(image_file)
        width, height = img.size

        if width > 1768 or height > 2564:
            continue

        if width < frame_size + (15 * 2) or height < frame_size + (15 * 2):
            continue
        
        left = np.random.randint(15, width - (frame_size + 15))
        upper = np.random.randint(15, height - (frame_size + 15))
        right = left + frame_size
        lower = upper + frame_size

        cropped_img = img.crop((left, upper, right, lower))
        cropped_img.save(os.path.join(output_dir, f'image_{saved_images:05}.png'))
        saved_images += 1
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Smart crop images in a folder.')
    parser.add_argument('-f', '--folder-path', type=str, help='Path to the folder containing images')
    parser.add_argument('-o', '--output-dir', type=str, default='smart_crop_frames', help='Path to the folder to save the cropped images')
    parser.add_argument('--dataset-crop', action='store_true', help='Use this flag to crop images for the dataset')
    args = parser.parse_args()
    
    if args.dataset_crop:
        dataset_crop(args.folder_path, args.output_dir)
    else:
        main(args.folder_path, args.output_dir)