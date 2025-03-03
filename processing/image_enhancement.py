import cv2
import numpy as np
from skimage.filters import frangi

def enhance_fingerprint(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Could not load image at {image_path}")   
    # 1. Normalization
    normalized_image = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)
    # 2. Orientation Field Estimation
    sobelx = cv2.Sobel(normalized_image, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(normalized_image, cv2.CV_64F, 0, 1, ksize=3)
    orientation_field = cv2.phase(sobelx, sobely)
    # 3. Frequency Estimation
    frequency_data = np.abs(np.fft.fft2(normalized_image))
    # 4. Gabor Filtering 
    gabor_kernel = cv2.getGaborKernel((21, 21), 8.0, np.pi / 2, 10.0, 0.5, 0, ktype=cv2.CV_32F)
    filtered_image = cv2.filter2D(normalized_image, cv2.CV_8UC3, gabor_kernel)
    # 5. Binarization
    ret, binary_image = cv2.threshold(filtered_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # 6. Thinning
    thinned_image = cv2.ximgproc.thinning(binary_image)

    return thinned_image
