import os
import json
import re
import cv2
import pytesseract
from PIL import Image

# Configure paths
input_dir = r'C:\Users\prath\OneDrive\Desktop\Bajaj\Preprocessed Images'
output_dir = r'C:\Users\prath\OneDrive\Desktop\Bajaj\Extracted JSON'

# Optional: set path to your Tesseract executable
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Regex patterns
value_pattern = r'[-+]?\d*\.\d+|\d+'  # Match floats or integers
range_pattern = r'(\d+(\.\d+)?\s*[-–]\s*\d+(\.\d+)?)'  # Match reference range like 12.0 - 15.0

def extract_tests(text):
    extracted_data = []

    # Normalize text
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line or len(line.split()) < 2:
            continue

        try:
            # Skip metadata and irrelevant lines
            blacklist_keywords = ["PIN", "KANNADA", "PM", "NO", "@", "==="]
            if any(keyword in line.upper() for keyword in blacklist_keywords):
                continue

            # Normalize line for common OCR artifacts
            line = line.replace('—', '-').replace('–', '-').replace('to', '-').replace(':', '-')
            line = re.sub(r'\s{2,}', ' ', line)

            # Match reference range
            ref_match = re.search(r'(\d+\.?\d*)\s*[-–to]+\s*(\d+\.?\d*)', line)
            if ref_match:
                ref_low = float(ref_match.group(1))
                ref_high = float(ref_match.group(2))
                bio_reference_range = f"{ref_low}-{ref_high}"
            else:
                bio_reference_range = None

            # Match numbers in line
            all_numbers = re.findall(r'(?<!\d)(\d+\.?\d*)(?!\d)', line)
            test_value = None
            if bio_reference_range and len(all_numbers) >= 1:
                ref_vals = [str(ref_low), str(ref_high)]
                test_vals = [v for v in all_numbers if v not in ref_vals]
                if test_vals:
                    test_value = test_vals[0]
                else:
                    test_value = all_numbers[0]
            elif len(all_numbers) == 1:
                test_value = all_numbers[0]

            # Clean test name
            name_candidate = re.sub(r'\d+\.?\d*\s*[-–to:]\s*\d+\.?\d*', '', line)
            if test_value:
                name_candidate = name_candidate.replace(test_value, '')
            test_name = name_candidate.strip()

            # Skip if test name is empty or just noise
            if len(test_name) < 2 or not re.search(r'[a-zA-Z]', test_name):
                continue

            # Detect unit if available
            unit_match = re.search(r'(g/dL|mg/dL|mmol/L|μmol/L|%|IU/L|pg/mL|fl)', line)
            unit = unit_match.group(1) if unit_match else ''

            # Determine if test is out of range
            out_of_range = False
            if bio_reference_range and test_value:
                try:
                    test_float = float(test_value)
                    out_of_range = not (ref_low <= test_float <= ref_high)
                except:
                    out_of_range = False

            # Append result only if test_name and test_value are valid
            if test_value and test_name:
                extracted_data.append({
                    "test_name": test_name,
                    "test_value": test_value,
                    "bio_reference_range": bio_reference_range,
                    "test_unit": unit,
                    "lab_test_out_of_range": out_of_range
                })

        except Exception as e:
            print(f"Line failed: {line} — {e}")
            continue

    return extracted_data

def process_images():
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff')):
            filepath = os.path.join(input_dir, filename)
            image = cv2.imread(filepath)
            text = pytesseract.image_to_string(image)

            tests = extract_tests(text)
            result = {
                "is_success": True,
                "data": tests
            }

            # Write JSON to file
            json_filename = os.path.splitext(filename)[0] + '.json'
            output_path = os.path.join(output_dir, json_filename)
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=4)

            print(f"Processed: {filename} -> {json_filename}")

if __name__ == "__main__":
    os.makedirs(output_dir, exist_ok=True)
    process_images()
