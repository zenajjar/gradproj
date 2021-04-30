import os.path
from collections.abc import Iterable
from typing import Union

import PIL.Image as Image
import matplotlib.pyplot as plt
import numpy as np

IMAGE_EXTENSIONS = ['png', 'jpeg', 'tiff', 'bmp', 'jpg', 'gif']
COMPRESSED_DATA_LENGTH_BITS = 16
MAX_PIXEL_VALUE = 255
HEADER_SIZE = 17
EPS = 0.00000005


def integer_to_binary(number: int, bits=8):
    return np.array([x == '1' for x in format(number, f'0{bits}b')])


def binary_to_string(binary):
    if binary:
        return '1'
    else:
        return '0'


def binary_to_integer(binary):
    return int.from_bytes(bits_to_bytes(binary), byteorder='big', signed=False)


def get_lsb(values):
    lsb = []
    for pixel in values:
        lsb.append(integer_to_binary(pixel)[-1])

    return lsb


def set_lsb(value, lsb):
    if lsb:
        value |= 1
    else:
        value &= ~1

    return value


def bytes_to_bits(buffer):
    return np.where(np.unpackbits(np.frombuffer(buffer, np.uint8)) == 1, True, False)


def bits_to_bytes(buffer):
    return np.packbits(buffer).tobytes()


def get_header_and_body(image: np.ndarray, header_size: int = HEADER_SIZE) -> (np.ndarray, np.ndarray):
    image = image.ravel().copy()
    return image[:int(header_size)], image[int(header_size):]


def scale_to(image: np.ndarray, r: Union[np.ndarray, Iterable, int, str]) -> np.ndarray:
    try:
        scaled_min, scaled_max = r
    except TypeError:
        scaled_max = r
        scaled_min = 0

    scaled_min = int(scaled_min)
    scaled_max = int(scaled_max)

    image -= np.min(image)
    original_range = np.max(image)
    scaled_range = scaled_max - scaled_min

    image = image.astype(np.float64)
    scale_factor = scaled_range / original_range

    image *= scale_factor

    if scaled_range <= original_range:  # TODO make sure this always works
        image -= EPS
        image = np.ceil(image)
    else:
        image += EPS
        image = np.floor(image)

    image += scaled_min

    return image.astype(np.uint8)


def get_mapped_values(original_max: int, scaled_max: int) -> np.ndarray:
    original_max = int(original_max)
    scaled_max = int(scaled_max)

    og_values = np.arange(original_max + 1)
    scaled_values = scale_to(og_values, scaled_max)
    recovered_values = scale_to(scaled_values, original_max)
    mapped_values = scaled_values[np.where(recovered_values - og_values != 0)]

    if not len(mapped_values):
        mapped_values = np.array([-1])

    return mapped_values


def read_image(path: str) -> np.ndarray:
    return np.uint8(Image.open(path).getchannel(0)).copy()


def get_peaks(pixels, n=2):
    hist = np.bincount(pixels)
    return np.sort(hist.argsort()[-n:])


def show_hist(image):
    bins = np.bincount(image.ravel())
    hist = np.zeros((MAX_PIXEL_VALUE + 1,))
    hist[:len(bins)] = bins
    plt.figure()
    plt.xlabel('Intensity Value')
    plt.ylabel('Count')
    plt.hist(np.arange(MAX_PIXEL_VALUE + 1), MAX_PIXEL_VALUE + 1, weights=hist)
    plt.show()


def assemble_image(header, pixels, shape):
    image = np.append(header, pixels)
    return image.reshape(shape)


def get_minimum_closest_right(hist, pixel_value):
    hist_right = (np.roll(hist, 1) + hist)[pixel_value + 2:]
    candidates = np.flatnonzero(hist_right == hist_right.min()) + pixel_value + 2
    candidates = candidates[np.flatnonzero(hist[candidates - 1] == hist[candidates - 1].min())]
    return candidates[np.abs(candidates - pixel_value).argmin()]


def get_minimum_closest_left(hist, pixel_value):
    hist_left = (np.roll(hist, -1) + hist)[:pixel_value - 2 + 1]
    candidates = np.flatnonzero(hist_left == hist_left.min())
    candidates = candidates[np.flatnonzero(hist[candidates + 1] == hist[candidates + 1].min())]
    return candidates[np.abs(candidates - pixel_value).argmin()]


def get_minimum_closest(hist, pixel_value):
    closest_right = get_minimum_closest_right(hist, pixel_value)
    closest_left = get_minimum_closest_left(hist, pixel_value)
    min_right_value = hist[closest_right] + hist[closest_right - 1]
    min_left_value = hist[closest_left] + hist[closest_left + 1]
    if min_right_value < min_left_value:
        return closest_right
    elif min_right_value > min_left_value:
        return closest_left
    else:
        if abs(closest_right - pixel_value) < abs(closest_left - pixel_value):
            return closest_right
        else:
            return closest_left


def get_shift_direction(P_L, P_H):
    if P_L < P_H:
        return -1
    else:
        return 1


def get_peaks_from_header(header_pixels: np.ndarray, peak_size: int = 8) -> (np.ndarray, np.ndarray):
    LSB = get_lsb(header_pixels)
    return binary_to_integer(LSB[0:peak_size]), binary_to_integer(LSB[peak_size:2 * peak_size])


def is_image(image_path: str) -> bool:
    return os.path.isfile(image_path) and os.path.splitext(image_path)[1][1:] in IMAGE_EXTENSIONS