'''
Interactive Fresnel Reconstruction of Holograms using Matplotlib
To install required libraries:
pip install numpy matplotlib Pillow scipy
This script allows you to load a hologram image, perform Fresnel reconstruction, and interactively adjust the reconstruction distance using a slider. The left panel shows the original hologram, while the right panel displays the reconstructed image based on the current slider value.
'''

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from PIL import Image
import tkinter as tk
from tkinter import filedialog
from scipy.fft import fft2, ifft2, fftshift, ifftshift

def load_image():
    """Opens a file dialog to select an image from disk."""
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title="Select Hologram Image",
                                         filetypes=[("Image files", "*.png *.jpg *.jpeg *.tif *.bmp")])
    if not file_path:
        print("No file selected. Exiting.")
        exit()
    
    img = Image.open(file_path)#
    # extract red channel if it's RGB, otherwise use the image as is
    if img.mode == 'RGB':
        img = img.getchannel('R')
    elif img.mode == 'RGBA':
        img = img.getchannel('R')  # or you could average RGB channels if needed    
    else:
        img = img.convert('L')  # convert to grayscale if not already
    return np.array(img, dtype=float)

def get_fresnel_kernel(nx, ny, ps, wavelength, dz):
    """Calculates the Fresnel propagation kernel in Fourier space."""
    grid_size_x = ps * nx
    grid_size_y = ps * ny

    # Frequency grids
    fx = np.linspace(-(nx-1)/2*(1/grid_size_x), (nx-1)/2*(1/grid_size_x), nx)
    fy = np.linspace(-(ny-1)/2*(1/grid_size_y), (ny-1)/2*(1/grid_size_y), ny)
    FX, FY = np.meshgrid(fx, fy)

    # Fresnel phase factor: exp(j * pi * lambda * dz * f^2)
    phase = 1j * np.pi * wavelength * dz
    kernel = np.exp(phase * (FX**2 + FY**2))
    return kernel

# --- Parameters ---
PIXEL_SIZE = 3.45e-6  # meters
WAVELENGTH = 650e-9   # meters
INITIAL_DZ = 0.0      # meters

# Load and prepare image
img_data = load_image()
ny, nx = img_data.shape
E0 = np.sqrt(img_data)  # Amplitude from intensity
E0_fft = fftshift(fft2(E0)) # Pre-calculate FFT for speed

# --- Setup Plot ---
fig, ax = plt.subplots(1, 2, figsize=(12, 6))
plt.subplots_adjust(bottom=0.25)

ax[0].imshow(img_data, cmap='gray')
ax[0].set_title("Original Hologram (Sensor Plane)")
ax[0].axis('off')

# Initial reconstruction
kernel = get_fresnel_kernel(nx, ny, PIXEL_SIZE, WAVELENGTH, INITIAL_DZ)
Ef = ifft2(ifftshift(E0_fft * kernel))
recon_im = np.abs(Ef)**2

display = ax[1].imshow(recon_im, cmap='gray')
ax[1].set_title(f"Reconstruction (dz = {INITIAL_DZ:.2e} m)")
ax[1].axis('off')

# --- Interactive Slider ---
ax_slider = plt.axes([0.2, 0.1, 0.6, 0.03])
slider_dz = Slider(
    ax=ax_slider,
    label='Distance (m) ',
    valmin=0,
    valmax=1e-2,
    valinit=INITIAL_DZ,
    valfmt='%.2e'
)

def update(val):
    dz = slider_dz.val
    # Apply kernel to pre-calculated FFT
    k = get_fresnel_kernel(nx, ny, PIXEL_SIZE, WAVELENGTH, dz)
    Ef_new = ifft2(ifftshift(E0_fft * k))
    
    # Update display
    new_intensity = np.abs(Ef_new)**2
    display.set_data(new_intensity)
    
    # Auto-scale contrast for better visibility during propagation
    display.set_clim(np.percentile(new_intensity, 1), np.percentile(new_intensity, 99))
    
    ax[1].set_title(f"Reconstruction (dz = {dz:.2e} m)")
    fig.canvas.draw_idle()

slider_dz.on_changed(update)

print(f"Loaded image: {nx}x{ny}")
print("Adjust the slider to change reconstruction distance.")
plt.show()