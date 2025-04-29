import os
import cv2
import numpy as np
from PIL import Image
import math

# Preprocessing Functions
def deskew(image):
    # Detect skew angle using moments and deskew image
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    coords = np.column_stack(np.where(gray > 0))
    angle = cv2.minAreaRect(coords)[-1]
    
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, rotation_matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    
    return rotated

def preprocess_image(image_path):
    img = cv2.imread(image_path)
    
    # Step 1: Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Step 2: Denoise image using Non-Local Means Denoising
    denoised = cv2.fastNlMeansDenoising(gray, None, 30, 7, 21)
    
    # Step 3: Binarize image using Otsu's thresholding
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Step 4: Deskew the image if needed
    deskewed = deskew(thresh)
    
    return deskewed

def process_images(input_folder, output_folder):
    # Create output folder if not exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Get all image files from the input folder
    image_files = [f for f in os.listdir(input_folder) if f.lower().endswith(('png', 'jpg', 'jpeg', 'bmp', 'tiff'))]
    
    for image_file in image_files:
        image_path = os.path.join(input_folder, image_file)
        
        # Preprocess image
        preprocessed_img = preprocess_image(image_path)
        
        # Save the processed image
        output_image_path = os.path.join(output_folder, image_file)
        cv2.imwrite(output_image_path, preprocessed_img)
        print(f"Processed and saved: {image_file}")

# Define input and output directories
input_directory = 'path/to/your/images'  # Replace with your folder of lab report images
output_directory = 'path/to/save/processed_images'  # Replace with the folder to save processed images

# Process all images
process_images(input_directory, output_directory)
