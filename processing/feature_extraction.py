import cv2
import numpy as np

def extract_minutiae(image):
    """Extracts minutiae points (ridge endings, bifurcations) from the image."""
    height, width = image.shape
    minutiae = []

    for y in range(1, height - 1):
        for x in range(1, width - 1):
            if image[y, x] == 255:  # Assuming white is the ridge
                neighborhood = image[y-1:y+2, x-1:x+2]
                neighbors_count = np.sum(neighborhood == 255) - 1

                if neighbors_count == 1:  # Ridge ending
                    minutiae.append((x, y, "ending"))
                elif neighbors_count == 3:  # Bifurcation
                    minutiae.append((x, y, "bifurcation"))

    return minutiae
