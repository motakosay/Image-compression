from PIL import Image
import numpy as np
from scipy import fftpack

def process_image(input_path, output_path, component):
    # Open image and convert to YCbCr
    image = Image.open(input_path)
    ycbcr = image.convert('YCbCr')
    npmat = np.array(ycbcr, dtype=np.uint8)
    npmat = npmat - 128

    # Pad the image so rows and cols are multiples of 8
    rows, cols, _ = npmat.shape
    new_rows = (rows + 7) // 8 * 8  # Round up to the nearest multiple of 8
    new_cols = (cols + 7) // 8 * 8
    npmat = np.pad(npmat, ((0, new_rows - rows), (0, new_cols - cols), (0, 0)), mode='constant', constant_values=0)

    # Define the 2D DCT and IDCT functions
    def dct_2d(image):
        return fftpack.dct(fftpack.dct(image.T, norm='ortho').T, norm='ortho')

    def idct_2d(image):
        return fftpack.idct(fftpack.idct(image.T, norm='ortho').T, norm='ortho')

    # Load quantization tables
    def load_quantization_table(comp):
        if comp == 'lum':
            return np.array([
                [16, 11, 10, 16, 24, 40, 51, 61],
                [12, 12, 14, 19, 26, 58, 60, 55],
                [14, 13, 16, 24, 40, 57, 69, 56],
                [14, 17, 22, 29, 51, 87, 80, 62],
                [18, 22, 37, 56, 68, 109, 103, 77],
                [24, 35, 55, 64, 81, 104, 113, 92],
                [49, 64, 78, 87, 103, 121, 120, 101],
                [72, 92, 95, 98, 112, 100, 103, 99]
            ])
        elif comp == 'chrom':
            return np.array([
                [17, 18, 24, 47, 99, 99, 99, 99],
                [18, 21, 26, 66, 99, 99, 99, 99],
                [24, 26, 56, 99, 99, 99, 99, 99],
                [47, 66, 99, 99, 99, 99, 99, 99],
                [99, 99, 99, 99, 99, 99, 99, 99],
                [99, 99, 99, 99, 99, 99, 99, 99],
                [99, 99, 99, 99, 99, 99, 99, 99],
                [99, 99, 99, 99, 99, 99, 99, 99]
            ])
        else:
            raise ValueError("Component should be either 'lum' or 'chrom'")

    # Quantize and dequantize functions
    def quantize(block, comp):
        q = load_quantization_table(comp)
        return (block / q).round().astype(np.int32)

    def dequantize(block, comp):
        q = load_quantization_table(comp)
        return block * q

    # Perform DCT, quantization, and inverse operations on 8x8 blocks
    for i in range(0, new_rows, 8):
        for j in range(0, new_cols, 8):
            for k in range(3):
                if component == 'both' or (component == 'lum' and k == 0) or (component == 'chrom' and k != 0):
                    block = npmat[i:i+8, j:j+8, k]
                    dct_matrix = dct_2d(block)
                    quant_matrix = quantize(dct_matrix, 'lum' if k == 0 else 'chrom')
                    dequant_matrix = dequantize(quant_matrix, 'lum' if k == 0 else 'chrom')
                    idct_matrix = idct_2d(dequant_matrix)
                    npmat[i:i+8, j:j+8, k] = idct_matrix

    # Crop back to original size
    npmat = npmat[:rows, :cols, :]

    # Convert back to uint8 and add 128
    npmat = npmat + 128
    npmat = npmat.clip(0, 255).astype(np.uint8)

    # Convert back to RGB and save the image
    output_image = Image.fromarray(npmat, 'YCbCr').convert('RGB')
    output_image.save(output_path)
    output_image.show()

# Example usage
process_image("PathToYourImage.jpg", "output_image.jpg", component='chrom') #component = 'both' or 'lum' or 'chrom'
