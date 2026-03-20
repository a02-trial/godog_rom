#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@ File Name    :   img2sdat.py
@ Author       :   Abdalrohman Alnasier
@ Created Time :   2022/11/10 19:09:36

OEM_ROM_Editor
Copyright (C) 2022 Abdalrohman Alnasier

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import argparse
import os
import tempfile
import time

# Import necessary modules
import common, images, sparse_img


def img2sdat(input_image, prefix, cache_size, out_dir, version):
    """
    Convert image to new.dat format.

    Args:
        input_image (str): Path to the input system image.
        prefix (str): Name of the image.
        cache_size (int): Cache size.
        out_dir (str): Output directory.
        version (int): Transfer list version number.

    Returns:
        None
    """

    start_time = time.time()

    # Create output directory if it doesn't exist
    os.makedirs(out_dir, exist_ok=True)

    # Construct output path
    path = os.path.join(out_dir, prefix)

    # Create SparseImage object
    image = sparse_img.SparseImage(input_image, tempfile.mkstemp()[1], "0")

    # Set cache size
    common.OPTIONS.cache_size = cache_size

    # Create EmptyImage object
    src = images.EmptyImage()

    # Compute block image diff
    block_image_diff = common.BiD(image, src, version)
    block_image_diff.Compute(path)

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time} seconds")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # Define command-line arguments
    parser.add_argument("image", help="input system image")

    parser.add_argument("-c", "--cachesize", type=int, default=402653184, help="cache size")

    parser.add_argument(
        "-o",
        "--outdir",
        default=".",
        help="output directory (current directory by default)",
    )

    parser.add_argument(
        "-v",
        "--version",
        default=4,
        type=int,
        help="transfer list version number (3,4 default=4)",
    )

    parser.add_argument("-p", "--prefix", default="system", help="name of image (prefix.new.dat)")

    args = parser.parse_args()

    # Call main function with command-line arguments
    img2sdat(args.image, args.prefix, args.cachesize, args.outdir, args.version)
