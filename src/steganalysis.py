"""
Advanced Steganalysis Detection Module
Detects presence of hidden data using multi-feature statistical ensemble.
Uses classical steganalysis + advanced texture/noise/edge analysis.
"""

import numpy as np
from PIL import Image
import io
import logging
import math
from typing import Tuple, Dict, List

# Optional cv2 — graceful fallback if missing
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

logger = logging.getLogger(__name__)


class SteganalysisDetector:
    """Detects steganographic content in images using multiple methods."""
    
    def __init__(self):
        """Initialize the detector."""
        pass
    
    def analyze(self, image_file) -> Dict:
        """
        Comprehensive steganalysis on image.
        
        Returns dict with:
        - stego_probability: 0.0-1.0 (likelihood of hidden content)
        - confidence: confidence in prediction
        - analysis_type: which method was used
        - features: dict of individual feature scores
        - recommendation: Safe/Suspicious/High Risk
        """
        try:
            # Load image
            img = Image.open(image_file).convert('RGB')
            img_array = np.array(img)
            
            # Run all analysis methods
            features = {
                'lsb_anomaly': self._lsb_anomaly_score(img_array),
                'pixel_pairs': self._pixel_pairs_score(img_array),
                'chi_squared': self._chi_squared_test(img_array),
                'histogram_anomaly': self._histogram_anomaly(img_array),
                'spatial_correlation': self._spatial_correlation(img_array),
                'texture_complexity': self._texture_complexity(img_array),
                'noise_floor': self._noise_floor_analysis(img_array),
            }
            
            # Weighted ensemble — weights tuned for LSB steganography detection
            weights = {
                'lsb_anomaly': 0.25,
                'chi_squared': 0.20,
                'spatial_correlation': 0.15,
                'pixel_pairs': 0.15,
                'noise_floor': 0.10,
                'texture_complexity': 0.10,
                'histogram_anomaly': 0.05,
            }
            
            stego_prob = sum(features[k] * weights[k] for k in weights)
            stego_prob = float(np.clip(stego_prob, 0.0, 1.0))
            
            # Determine recommendation
            if stego_prob < 0.3:
                recommendation = "Safe"
            elif stego_prob < 0.6:
                recommendation = "Suspicious"
            else:
                recommendation = "High Risk"
            
            analysis_type = "Multi-Feature Ensemble (7 detectors)"
            
            return {
                'stego_probability': stego_prob,
                'confidence': self._calculate_confidence(stego_prob, features),
                'analysis_type': analysis_type,
                'recommendation': recommendation,
                'features': {k: round(v, 4) for k, v in features.items()},
                'image_info': {
                    'width': img_array.shape[1],
                    'height': img_array.shape[0],
                    'pixels': img_array.shape[0] * img_array.shape[1],
                }
            }
        
        except Exception as e:
            logger.error(f'Steganalysis error: {e}')
            raise ValueError(f'Analysis failed: {str(e)}')
    
    def _lsb_anomaly_score(self, img_array: np.ndarray) -> float:
        """
        Detect LSB plane anomalies.
        Pure noise / perfect 50-50 in LSB → likely steganography.
        Natural images have a slight bias away from 50/50.
        """
        lsb_plane = img_array & 1
        flat = lsb_plane.flatten()
        
        count_1 = np.sum(flat)
        total = len(flat)
        count_0 = total - count_1
        
        if total == 0:
            return 0.0
        
        ratio = abs(count_0 - count_1) / total
        
        # Natural images: ratio is typically 0.01-0.05
        # Stego images: ratio approaches 0 (perfect 50/50)
        # Score higher if ratio is very close to 0
        anomaly_score = 1.0 - min(ratio * 20.0, 1.0)
        return float(np.clip(anomaly_score, 0, 1))
    
    def _pixel_pairs_score(self, img_array: np.ndarray) -> float:
        """
        RS (Regular-Singular) steganalysis detector.
        Measures how LSB flipping affects smoothness groups.
        """
        scores = []
        
        for channel in range(3):
            channel_data = img_array[:, :, channel].astype(np.int16)
            
            # Sample rows for efficiency on large images
            rows = channel_data.shape[0]
            step = max(1, rows // 100)
            sampled = channel_data[::step, :]
            
            if sampled.shape[1] < 4:
                continue
            
            # Calculate smoothness: sum of absolute differences between adjacent pixels
            def smoothness(arr):
                return np.sum(np.abs(np.diff(arr, axis=1)))
            
            original_smooth = smoothness(sampled)
            
            # Flip LSB (Regular group)
            flipped = sampled.copy()
            flipped[:, ::2] = flipped[:, ::2] ^ 1
            regular_smooth = smoothness(flipped)
            
            # Negative flip (Singular group)
            neg_flipped = sampled.copy()
            neg_flipped[:, 1::2] = neg_flipped[:, 1::2] ^ 1
            singular_smooth = smoothness(neg_flipped)
            
            if original_smooth == 0:
                continue
            
            # RS ratio: if R ≈ S, image is likely clean
            # If R > S significantly, steganography likely
            r_ratio = regular_smooth / (original_smooth + 1e-6)
            s_ratio = singular_smooth / (original_smooth + 1e-6)
            
            diff = abs(r_ratio - s_ratio)
            score = np.clip(diff * 2.0, 0, 1)
            scores.append(score)
        
        return float(np.mean(scores)) if scores else 0.0
    
    def _chi_squared_test(self, img_array: np.ndarray) -> float:
        """
        Chi-squared test on Pairs of Values (PoVs).
        Steganography makes adjacent histogram bins more similar.
        """
        scores = []
        
        for channel in range(3):
            channel_data = img_array[:, :, channel].flatten()
            hist, _ = np.histogram(channel_data, bins=256, range=(0, 256))
            
            # Chi-squared on pairs of values (2i, 2i+1)
            chi_sq = 0.0
            n_pairs = 0
            
            for i in range(0, 256, 2):
                h0 = hist[i]
                h1 = hist[i + 1] if i + 1 < 256 else 0
                expected = (h0 + h1) / 2.0
                
                if expected > 5:  # Standard chi-sq threshold
                    chi_sq += ((h0 - expected) ** 2 + (h1 - expected) ** 2) / expected
                    n_pairs += 1
            
            if n_pairs == 0:
                continue
            
            # Normalize: low chi-sq → pairs are similar → stego
            # High chi-sq → pairs differ → natural
            normalized = chi_sq / (n_pairs + 1e-6)
            
            # In clean images, chi-sq/pair is typically > 2
            # In stego images, chi-sq/pair approaches 0
            score = 1.0 - min(normalized / 4.0, 1.0)
            scores.append(float(np.clip(score, 0, 1)))
        
        return float(np.mean(scores)) if scores else 0.0
    
    def _histogram_anomaly(self, img_array: np.ndarray) -> float:
        """
        Detect histogram anomalies. Steganography can create
        unnatural smoothing in the histogram of pixel values.
        """
        scores = []
        
        for channel in range(3):
            channel_data = img_array[:, :, channel].flatten()
            hist, _ = np.histogram(channel_data, bins=256, range=(0, 256))
            
            hist_float = hist.astype(float)
            
            # Measure roughness: sum of second derivatives
            if len(hist_float) < 3:
                continue
            
            second_deriv = np.diff(hist_float, n=2)
            roughness = np.sum(np.abs(second_deriv))
            
            total_pixels = len(channel_data)
            if total_pixels == 0:
                continue
            
            # Normalize roughness by total pixels
            normalized_roughness = roughness / total_pixels
            
            # Stego tends to smooth the histogram → lower roughness
            # Natural images have higher roughness
            # Typical clean: 0.5-2.0, stego: 0.1-0.4
            score = 1.0 - min(normalized_roughness / 1.0, 1.0)
            scores.append(float(np.clip(score, 0, 1)))
        
        return float(np.mean(scores)) if scores else 0.0
    
    def _spatial_correlation(self, img_array: np.ndarray) -> float:
        """
        Analyze spatial correlation of LSB plane.
        Natural LSBs have spatial structure; stego LSBs are random.
        """
        scores = []
        
        for channel in range(3):
            lsb = (img_array[:, :, channel] & 1).astype(float)
            
            # Subsample for performance on large images
            step = max(1, min(lsb.shape[0], lsb.shape[1]) // 200)
            lsb_sub = lsb[::step, ::step]
            
            if lsb_sub.shape[0] < 3 or lsb_sub.shape[1] < 3:
                continue
            
            try:
                # Horizontal autocorrelation of LSB plane
                h1 = lsb_sub[:, :-1].flatten()
                h2 = lsb_sub[:, 1:].flatten()
                
                if len(h1) < 10:
                    continue
                
                # Calculate correlation
                corr_matrix = np.corrcoef(h1, h2)
                h_corr = corr_matrix[0, 1] if not np.isnan(corr_matrix[0, 1]) else 0.0
                
                # Natural LSB: slight positive correlation (~0.01-0.1)
                # Stego LSB: near-zero correlation
                # Score: low correlation → high score (stego likely)
                score = 1.0 - abs(h_corr) * 10.0
                scores.append(float(np.clip(score, 0, 1)))
            except Exception:
                scores.append(0.5)
        
        return float(np.mean(scores)) if scores else 0.0
    
    def _texture_complexity(self, img_array: np.ndarray) -> float:
        """
        Analyze texture complexity using local variance.
        Steganography increases noise in smooth regions.
        """
        gray = np.mean(img_array, axis=2)
        
        # Subsample for performance
        step = max(1, min(gray.shape[0], gray.shape[1]) // 300)
        gray_sub = gray[::step, ::step]
        
        h, w = gray_sub.shape
        if h < 8 or w < 8:
            return 0.5
        
        # Calculate local variance in 4x4 blocks
        block_size = 4
        variances = []
        
        for y in range(0, h - block_size, block_size):
            for x in range(0, w - block_size, block_size):
                block = gray_sub[y:y+block_size, x:x+block_size]
                variances.append(np.var(block))
        
        if not variances:
            return 0.5
        
        variances = np.array(variances)
        
        # Identify "smooth" blocks (low variance)
        smooth_threshold = np.percentile(variances, 25)
        smooth_blocks = variances[variances <= smooth_threshold]
        
        if len(smooth_blocks) == 0:
            return 0.5
        
        # In smooth regions, LSB stego increases variance slightly
        # Measure the minimum variance in "smooth" blocks
        min_smooth_var = np.mean(smooth_blocks)
        
        # Clean smooth regions: variance ~0-2
        # Stego smooth regions: variance ~1-5 (noise added)
        score = min(min_smooth_var / 3.0, 1.0)
        return float(np.clip(score, 0, 1))
    
    def _noise_floor_analysis(self, img_array: np.ndarray) -> float:
        """
        Analyze noise floor using high-pass filtering.
        Steganography raises the noise floor uniformly.
        """
        if HAS_CV2:
            return self._noise_floor_cv2(img_array)
        else:
            return self._noise_floor_numpy(img_array)
    
    def _noise_floor_cv2(self, img_array: np.ndarray) -> float:
        """Noise floor analysis using OpenCV."""
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # High-pass filter: Laplacian
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        noise_energy = np.var(laplacian)
        
        # Also check LSB plane noise
        lsb = gray & 1
        lsb_laplacian = cv2.Laplacian(lsb.astype(np.float64), cv2.CV_64F)
        lsb_noise = np.var(lsb_laplacian)
        
        # High LSB Laplacian variance → random LSBs → stego
        # Natural LSBs have lower Laplacian variance (spatial structure)
        score = min(lsb_noise / 0.5, 1.0)
        return float(np.clip(score, 0, 1))
    
    def _noise_floor_numpy(self, img_array: np.ndarray) -> float:
        """Noise floor analysis using pure NumPy (fallback)."""
        gray = np.mean(img_array, axis=2)
        
        # Simple high-pass: difference from neighbors
        if gray.shape[0] < 3 or gray.shape[1] < 3:
            return 0.5
        
        # Compute horizontal and vertical gradients
        dx = np.diff(gray, axis=1)
        dy = np.diff(gray, axis=0)
        
        noise_energy = np.var(dx) + np.var(dy)
        
        # LSB plane analysis
        lsb = (img_array[:, :, 0] & 1).astype(float)
        lsb_dx = np.diff(lsb, axis=1)
        lsb_dy = np.diff(lsb, axis=0)
        lsb_noise = np.var(lsb_dx) + np.var(lsb_dy)
        
        # Random LSBs → high gradient variance → stego
        score = min(lsb_noise / 0.5, 1.0)
        return float(np.clip(score, 0, 1))
    
    def _calculate_confidence(self, stego_prob: float, features: Dict) -> float:
        """
        Calculate confidence based on agreement between detectors.
        High confidence when all detectors agree.
        """
        values = list(features.values())
        
        # Standard deviation of feature scores — low std = high agreement
        std = np.std(values)
        
        # Also factor in distance from 0.5 (uncertain zone)
        distance_from_middle = abs(stego_prob - 0.5)
        
        # Combine: high agreement + far from 0.5 = high confidence
        agreement_factor = 1.0 - min(std * 2.0, 1.0)
        certainty_factor = distance_from_middle * 2.0
        
        confidence = (agreement_factor * 0.6 + certainty_factor * 0.4)
        return float(np.clip(confidence, 0, 1))


# Convenience function
def detect_steganography(image_file) -> Dict:
    """Detect if image contains steganography."""
    detector = SteganalysisDetector()
    return detector.analyze(image_file)
