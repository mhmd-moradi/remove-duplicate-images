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