# backend/services/iris_code_generator.py

"""
Generate a binary iris code from a normalised iris strip using 2-D Gabor
filters (Daugman-style encoding).

Tuned for noisy mobile camera images:
  - Larger kernel (21×21) smooths out sensor noise
  - 8 orientations for richer angular encoding
  - 4 wavelengths capturing coarse-to-fine texture
  - Both real and imaginary Gabor responses (2 bits per filter)
    for doubled discriminative power
"""

import cv2
import numpy as np
from config import Config


class IrisCodeGenerator:
    """Generate a binary iris code from a normalised iris image
    using 2-D Gabor filters (Daugman-style encoding)."""

    def __init__(self):
        self.code_height, self.code_width = Config.IRIS_CODE_SIZE
        # Gabor filter parameters — tuned for mobile noise resilience
        self.num_orientations = 8
        self.wavelengths = [4, 6, 8, 10]
        self.ksize = (21, 21)
        self.sigma = 5.0

    def generate(self, normalised_iris, noise_mask=None):
        """
        Apply Gabor filters at multiple orientations and wavelengths.
        Quantise the real AND imaginary filter responses into a binary code.

        Parameters
        ----------
        normalised_iris : np.ndarray
            A grayscale, enhanced iris strip (e.g. 64 × 512).
        noise_mask : np.ndarray or None
            Binary mask (1=valid, 0=occluded) of same spatial size.

        Returns
        -------
        tuple (iris_code, expanded_mask)
            iris_code : list[int] — binary code as a flat list of 0s and 1s
            expanded_mask : list[int] — mask tiled to match iris_code length
        """
        if normalised_iris is None or normalised_iris.size == 0:
            return None, None

        # Resize to a consistent encoding size
        resized = cv2.resize(
            normalised_iris, (self.code_width, self.code_height)
        ).astype(np.float64)

        # Normalise pixel range to [0, 1]
        if resized.max() > 0:
            resized = resized / 255.0

        # Prepare base mask (same spatial dims as resized)
        if noise_mask is not None:
            base_mask = cv2.resize(
                noise_mask.astype(np.uint8), (self.code_width, self.code_height),
                interpolation=cv2.INTER_NEAREST
            ).flatten()
        else:
            base_mask = np.ones(self.code_height * self.code_width, dtype=np.uint8)

        iris_code_bits = []
        mask_bits = []

        for wavelength in self.wavelengths:
            for orientation_idx in range(self.num_orientations):
                theta = orientation_idx * np.pi / self.num_orientations

                # Create Gabor kernel (real part, psi=0)
                kernel_real = cv2.getGaborKernel(
                    ksize=self.ksize,
                    sigma=self.sigma,
                    theta=theta,
                    lambd=wavelength,
                    gamma=0.5,
                    psi=0,
                    ktype=cv2.CV_64F,
                )

                # Create Gabor kernel (imaginary part, psi=π/2)
                kernel_imag = cv2.getGaborKernel(
                    ksize=self.ksize,
                    sigma=self.sigma,
                    theta=theta,
                    lambd=wavelength,
                    gamma=0.5,
                    psi=np.pi / 2,
                    ktype=cv2.CV_64F,
                )

                # Filter the iris image
                response_real = cv2.filter2D(resized, cv2.CV_64F, kernel_real)
                response_imag = cv2.filter2D(resized, cv2.CV_64F, kernel_imag)

                # Quantise: response > 0 → 1, else → 0
                bits_real = (response_real > 0).astype(int).flatten()
                bits_imag = (response_imag > 0).astype(int).flatten()

                iris_code_bits.append(bits_real)
                iris_code_bits.append(bits_imag)

                # Tile the base mask for each bit plane
                mask_bits.append(base_mask.copy())
                mask_bits.append(base_mask.copy())

        # Concatenate all bit vectors
        full_code = np.concatenate(iris_code_bits)
        full_mask = np.concatenate(mask_bits)

        return full_code.tolist(), full_mask.tolist()

    def code_length(self):
        """Return the expected length of a generated iris code."""
        return (
            self.code_height
            * self.code_width
            * self.num_orientations
            * len(self.wavelengths)
            * 2  # real + imaginary
        )
