import pickle
import numpy as np
from scipy.spatial import KDTree
from joblib import Parallel, delayed

class FingerprintMatcher:
    def __init__(self, threshold=5, n_jobs=-5):
        self.threshold = threshold
        self.minutiae_distance_tolerance = 10
        self.angle_tolerance = 20
        self.n_jobs = n_jobs 

    def _calculate_angle(self, p1, p2):
        """Calculates the angle between two points."""
        return np.degrees(np.arctan2(p2[1] - p1[1], p2[0] - p1[0]))

    def _rotate_fingerprint(self, minutiae, center, angle):
        """Rotates a fingerprint around a center point by a given angle."""
        rad_angle = np.radians(angle)
        cos_angle, sin_angle = np.cos(rad_angle), np.sin(rad_angle)
        minutiae = np.array(minutiae, dtype=object)
        x, y = minutiae[:, 0].astype(float) - center[0], minutiae[:, 1].astype(float) - center[1]
        new_x = x * cos_angle - y * sin_angle + center[0]
        new_y = x * sin_angle + y * cos_angle + center[1]

        return np.column_stack((new_x, new_y, minutiae[:, 2]))

    def _align_and_rotate_fingerprints(self, minutiae1, minutiae2):
        """Aligns and rotates fingerprints to maximize minutiae overlap."""
        if len(minutiae1) == 0 or len(minutiae2) == 0:
            return np.empty((0, 3)), np.empty((0, 3))  

        minutiae1, minutiae2 = np.array(minutiae1, dtype=object), np.array(minutiae2, dtype=object)
        translation = minutiae2[0][:2].astype(float) - minutiae1[0][:2].astype(float)
        minutiae1[:, :2] = minutiae1[:, :2].astype(float) + translation
        if len(minutiae1) > 1 and len(minutiae2) > 1:
            angle1 = self._calculate_angle(minutiae1[0][:2], minutiae1[1][:2])
            angle2 = self._calculate_angle(minutiae2[0][:2], minutiae2[1][:2])
            rotation_angle = angle2 - angle1
            minutiae1 = self._rotate_fingerprint(minutiae1, minutiae2[0][:2], rotation_angle)

        return minutiae1, minutiae2

    def _match_points(self, aligned_coords1, coords2, types1, types2, tree):
        """Match points using KDTree and return the count of matching points."""
        def _query_point(point, type_):
            dist, index = tree.query(point, distance_upper_bound=self.minutiae_distance_tolerance)
            if dist != np.inf and type_ == types2[index]:
                return 1
            return 0
        matching_points = Parallel(n_jobs=self.n_jobs)(
            delayed(_query_point)(point, type_)
            for point, type_ in zip(aligned_coords1, types1)
        )
        return sum(matching_points)

    def match_templates(self, template1, template2):
        """Compares two fingerprint templates and determines if they match."""
        minutiae1, minutiae2 = pickle.loads(template1), pickle.loads(template2)
        if len(minutiae1) > len(minutiae2):
            minutiae1, minutiae2 = minutiae2, minutiae1
        aligned_minutiae1, minutiae2 = self._align_and_rotate_fingerprints(minutiae1, minutiae2)
        coords1 = np.array([(x, y) for x, y, _ in aligned_minutiae1], dtype=np.float32)
        types1 = np.array([t for _, _, t in aligned_minutiae1], dtype=object)

        coords2 = np.array([(x, y) for x, y, _ in minutiae2], dtype=np.float32)
        types2 = np.array([t for _, _, t in minutiae2], dtype=object)
        tree = KDTree(coords2)
        matching_points = self._match_points(coords1, coords2, types1, types2, tree)
        print(f"Matching Points: {matching_points}")
        return matching_points >= self.threshold