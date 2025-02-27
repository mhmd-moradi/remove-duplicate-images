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