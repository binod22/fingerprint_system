import pickle
import numpy as np
import math

class FingerprintMatcher:
    def __init__(self, threshold=5):
        """
        Initializes the FingerprintMatcher.
        """
        self.threshold = threshold
        self.minutiae_distance_tolerance = 10  # Tolerance for distance between minutiae
        self.angle_tolerance = 20

    def _align_fingerprints(self, minutiae1, minutiae2):
        """Aligns two fingerprints based on their reference points."""

        if not minutiae1 or not minutiae2:
          return [], []
        # Use the first minutiae point as the reference point for each fingerprint
        ref_x1, ref_y1, _ = minutiae1[0]
        ref_x2, ref_y2, _ = minutiae2[0]

        # Calculate translation needed to align reference points
        translation_x = ref_x2 - ref_x1
        translation_y = ref_y2 - ref_y1

        # Apply translation to minutiae1
        aligned_minutiae1 = []
        for x, y, type_ in minutiae1:
            aligned_minutiae1.append((x + translation_x, y + translation_y, type_))

        return aligned_minutiae1, minutiae2
    
    def _calculate_angle(self, p1, p2):
        """Calculates the angle between two points."""
        return math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))

    def _rotate_fingerprint(self, minutiae, center, angle):
      """Rotates a fingerprint around a center point by a given angle."""
      rotated_minutiae = []
      for x, y, type_ in minutiae:
        x -= center[0]
        y -= center[1]
        rad_angle = math.radians(angle)
        new_x = x * math.cos(rad_angle) - y * math.sin(rad_angle)
        new_y = x * math.sin(rad_angle) + y * math.cos(rad_angle)
        rotated_minutiae.append((new_x + center[0], new_y + center[1], type_))
      return rotated_minutiae
    
    def _align_and_rotate_fingerprints(self, minutiae1, minutiae2):
      """Aligns and rotates two fingerprints to maximize minutiae overlap."""
      
      if not minutiae1 or not minutiae2:
        return [], []

      # Reference point for rotation (first minutiae)
      ref_x1, ref_y1, _ = minutiae1[0]
      ref_x2, ref_y2, _ = minutiae2[0]

      # Translation
      translation_x = ref_x2 - ref_x1
      translation_y = ref_y2 - ref_y1
      aligned_minutiae1 = [(x + translation_x, y + translation_y, type_) for x, y, type_ in minutiae1]

      # Use the two first point for angle calculation (we can use others method to get more acurate angle)
      if len(minutiae1) > 1 and len(minutiae2) > 1:
        angle1 = self._calculate_angle(minutiae1[0][:2], minutiae1[1][:2])
        angle2 = self._calculate_angle(minutiae2[0][:2], minutiae2[1][:2])

      else:
        return aligned_minutiae1, minutiae2

      # Calculate the required rotation angle
      rotation_angle = angle2 - angle1

      # Rotate minutiae1
      rotated_minutiae1 = self._rotate_fingerprint(aligned_minutiae1, (ref_x2, ref_y2), rotation_angle)

      return rotated_minutiae1, minutiae2


    def match_templates(self, template1, template2):
        """
        Compares two fingerprint templates and determines if they match.

        Args:
            template1 (bytes): The first fingerprint template.
            template2 (bytes): The second fingerprint template.

        Returns:
            bool: True if the templates match, False otherwise.
        """

        # Load the minutiae data from the templates
        minutiae1 = pickle.loads(template1)
        minutiae2 = pickle.loads(template2)

        # Optimization
        if len(minutiae1) > len(minutiae2):
            minutiae1, minutiae2 = minutiae2, minutiae1

        # Align the fingerprints (this is a crucial step for robustness)
        aligned_minutiae1, minutiae2 = self._align_and_rotate_fingerprints(minutiae1, minutiae2)

        matching_points = 0
        # Compare the aligned minutiae
        for x1, y1, type1 in aligned_minutiae1:
            for x2, y2, type2 in minutiae2:
                dist = np.sqrt((x1 - x2)**2 + (y1 - y2)**2)
                if dist < self.minutiae_distance_tolerance and type1 == type2:
                    matching_points += 1
                    
        print(f"number of matching point {matching_points}")
        # Check if the matching points exceed the threshold
        return matching_points >= self.threshold
