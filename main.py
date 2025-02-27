import cv2
from tqdm import tqdm
import os
import cv2
import re
import datetime
from imaging_interview import preprocess_image_change_detection, compare_frames_change_detection

invalid_images = []
image_folder = os.path.expanduser("~/Downloads/dataset-candidates-ml/dataset") # dataset folder example path
min_contour_area = 200 # Minimum contour area to detect as a change
change_threshold = 800 # Change score threshold to trigger difference detection

def convert_to_yyyymmddhhmmss(timestamp_ms):
    """Convert Unix timestamp in milliseconds to YYYYMMDDHHMMSS format."""
    dt = datetime.datetime.fromtimestamp(int(timestamp_ms) / 1000)
    return dt.strftime("%Y%m%d%H%M%S")

def load_image(image_folder, filename):
    """Load an image from the given folder and filename."""
    return cv2.imread(os.path.join(image_folder, filename))

def images_resolutions(images_by_camera_id):
    """Get the resolutions of the images for each camera ID."""
    for camera_id in images_by_camera_id:
        print(f"Image Resolutions by Camera ID: {camera_id}")
        resolutions = {}
        for img in tqdm(images_by_camera_id[camera_id]):
            image = load_image(image_folder, images_by_camera_id[camera_id][img])
            if (image.shape[1], image.shape[0]) not in resolutions:
                resolutions[(image.shape[1], image.shape[0])] = 0
            resolutions[(image.shape[1], image.shape[0])] += 1
        print(f"Camera ID: {camera_id} - Image Resolutions: {resolutions} \n")

def preprocess_dataset(image_folder):
    """
    Preprocess the images in the given folder and return a dictionary of images by camera ID.
    """
    print(f"Preprocessing images in {image_folder}...\n")
    images_by_camera_id = {}
    # Get list of files in the folder
    filenames = os.listdir(image_folder)

    for filename in tqdm(filenames, desc="Processing images", unit="file"):
        if not filename.endswith(".png"):  # Skip non-image files
            continue

        # Match different filename formats
        match_millis = re.match(r"c(\d+)-(\d{13})\.png", filename)  # c{camera_id}-{timestamp_ms}.png
        match_underscore = re.match(r"c(\d+)_(\d{4})_(\d{2})_(\d{2})__(\d{2})_(\d{2})_(\d{2})\.png", filename)  # c{camera_id}_YYYY-MM-DD__HH-MM-SS.png
        if match_millis:  # Convert ms timestamp to YYYYMMDDHHMMSS
            camera_id, timestamp_ms = match_millis.groups()
            timestamp = convert_to_yyyymmddhhmmss(timestamp_ms)
        elif match_underscore:  # Convert YYYY-MM-DD__HH-MM-SS to YYYYMMDDHHMMSS
            camera_id = match_underscore.group(1)
            timestamp = f"{match_underscore.group(2)}{match_underscore.group(3)}{match_underscore.group(4)}" \
                        f"{match_underscore.group(5)}{match_underscore.group(6)}{match_underscore.group(7)}"
        else:
            print(f"Skipping unrecognized file: {filename}")
            continue
        # Create the new filename in YYYYMMDDHHMMSS format
        if camera_id == "20" and match_underscore:
            new_filename = f"c{camera_id}_{timestamp}.png"
        else:
            new_filename = f"c{camera_id}-{timestamp}.png"

        if camera_id not in images_by_camera_id:
            images_by_camera_id[camera_id] = {}

        # check if image is valid
        if cv2.imread(os.path.join(image_folder, filename)) is None:
            print(f"Invalid image: {filename}")
            invalid_images.append(filename)
            continue
        
        # Add image to dictionary
        images_by_camera_id[camera_id][new_filename] = filename

    # Sort the images within each camera_id dictionary based on the timestamp in new filenames
    for camera_id in images_by_camera_id:
        if camera_id == "20":
            # Separate filenames into two lists
            dash_images = {k: v for k, v in images_by_camera_id[camera_id].items() if k.startswith(f"c{camera_id}-")}
            underscore_images = {k: v for k, v in images_by_camera_id[camera_id].items() if k.startswith(f"c{camera_id}_")}
            # Sort each group based on the timestamp
            sorted_dash_images = dict(sorted(dash_images.items(), key=lambda item: item[0].split('-')[1]))
            sorted_underscore_images = dict(sorted(underscore_images.items(), key=lambda item: item[0].split('_')[1]))
            # Merge the sorted dictionaries
            sorted_images = {**sorted_dash_images, **sorted_underscore_images}
        else:
            # Sort the dictionary by the new filenames (timestamps)
            sorted_images = dict(sorted(images_by_camera_id[camera_id].items(), key=lambda item: item[0].split('-')[1]))
        # Update the images_by_camera_id dictionary with the sorted dictionary
        images_by_camera_id[camera_id] = sorted_images

    return images_by_camera_id

def compare_images(image_folder, camera_id, images_by_camera_id, image_1, image_2, min_contour_area):
    """
    Compare two images from the same camera ID and return the change score and contours.
    """
    # Get the filenames of the images
    first_image_path = images_by_camera_id[camera_id][image_1]
    second_image_path = images_by_camera_id[camera_id][image_2]

    # Load the images
    first_image = load_image(image_folder, first_image_path)
    second_image = load_image(image_folder, second_image_path)

    if first_image is None or second_image is None:
        print("Error loading images.")
        return -1, [], None

    # Determine which image is larger and resize it to match the smaller one
    if first_image.shape != second_image.shape:
        # Get the target dimensions (smaller image)
        target_height = min(first_image.shape[0], second_image.shape[0])
        target_width = min(first_image.shape[1], second_image.shape[1])

        # Resize the larger image
        if first_image.shape[0] > second_image.shape[0] or first_image.shape[1] > second_image.shape[1]:
            first_image = cv2.resize(first_image, (target_width, target_height), interpolation=cv2.INTER_NEAREST)
        else:
            second_image = cv2.resize(second_image, (target_width, target_height), interpolation=cv2.INTER_NEAREST)

    # Preprocess the images
    first_image_processed = preprocess_image_change_detection(first_image)
    second_image_processed = preprocess_image_change_detection(second_image)

    # Compare the processed images
    score, contours, thresh = compare_frames_change_detection(
        first_image_processed, second_image_processed, min_contour_area)

    return score, contours, thresh