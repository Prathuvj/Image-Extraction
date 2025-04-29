import os
import cv2
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

# Preprocessing Functions
def deskew(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    coords = np.column_stack(np.where(gray > 0))
    
    if coords.shape[0] == 0:
        return image
    
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

def preprocess_image(image_path, output_path):
    img = cv2.imread(image_path)
    
    if img is None:
        print(f"Error reading image: {image_path}")
        return False
    
    # Step 1: Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Step 2: Denoise
    denoised = cv2.fastNlMeansDenoising(gray, None, 30, 7, 21)
    
    # Step 3: Thresholding
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Step 4: Deskew
    deskewed = deskew(cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR))
    
    # Save preprocessed image
    cv2.imwrite(output_path, deskewed)
    
    return True

def process_images_multithreaded(input_folder, output_folder, max_workers=8):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    image_files = [f for f in os.listdir(input_folder) if f.lower().endswith(('png', 'jpg', 'jpeg', 'bmp', 'tiff'))]
    
    print(f"Found {len(image_files)} images. Starting multithreaded preprocessing...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        
        for image_file in image_files:
            input_path = os.path.join(input_folder, image_file)
            output_path = os.path.join(output_folder, image_file)
            futures.append(executor.submit(preprocess_image, input_path, output_path))
        
        for idx, future in enumerate(as_completed(futures), start=1):
            try:
                success = future.result()
                if success:
                    print(f"[{idx}/{len(image_files)}] Successfully processed.")
                else:
                    print(f"[{idx}/{len(image_files)}] Failed to process.")
            except Exception as e:
                print(f"[{idx}/{len(image_files)}] Exception: {e}")

# --- Your Actual Paths ---
input_directory = r'C:\Users\prath\Downloads\Dataset\lbmaske'
output_directory = r'C:\Users\prath\OneDrive\Desktop\Bajaj\Preprocessed Images'

# Process Images
process_images_multithreaded(input_directory, output_directory, max_workers=8)
