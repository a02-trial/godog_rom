#!/usr/bin/env python3
"""
simg2sdat.py - Convert sparse image to sdat format
Standalone script, no AOSP dependencies required
Based on the Android sparse image format specification
"""

import os
import sys
import struct
import argparse

# Sparse image constants
SPARSE_HEADER_MAGIC = 0xED26FF3A
SPARSE_HEADER_SIZE = 28
SPARSE_CHUNK_HEADER_SIZE = 12
CHUNK_TYPE_RAW = 0xCAC1
CHUNK_TYPE_FILL = 0xCAC2
CHUNK_TYPE_DONT_CARE = 0xCAC3
CHUNK_TYPE_CRC32 = 0xCAC4

BLOCK_SIZE = 4096

def read_sparse_header(f):
    data = f.read(SPARSE_HEADER_SIZE)
    if len(data) < SPARSE_HEADER_SIZE:
        raise ValueError("File too small to be a sparse image")
    magic, major, minor, file_hdr_sz, chunk_hdr_sz, blk_sz, total_blks, total_chunks, image_checksum = \
        struct.unpack('<I2H4H2I', data)
    if magic != SPARSE_HEADER_MAGIC:
        raise ValueError(f"Not a sparse image (magic={hex(magic)})")
    return {
        'major': major, 'minor': minor,
        'file_hdr_sz': file_hdr_sz, 'chunk_hdr_sz': chunk_hdr_sz,
        'blk_sz': blk_sz, 'total_blks': total_blks,
        'total_chunks': total_chunks
    }

def sparse_to_raw(sparse_file, raw_file):
    with open(sparse_file, 'rb') as f_in, open(raw_file, 'wb') as f_out:
        hdr = read_sparse_header(f_in)
        blk_sz = hdr['blk_sz']

        # Skip extra header bytes if any
        f_in.seek(hdr['file_hdr_sz'])

        for _ in range(hdr['total_chunks']):
            chunk_data = f_in.read(SPARSE_CHUNK_HEADER_SIZE)
            if len(chunk_data) < SPARSE_CHUNK_HEADER_SIZE:
                break
            chunk_type, reserved, chunk_sz, total_sz = struct.unpack('<HHI I', chunk_data)

            data_sz = total_sz - SPARSE_CHUNK_HEADER_SIZE

            if chunk_type == CHUNK_TYPE_RAW:
                data = f_in.read(data_sz)
                f_out.write(data)
            elif chunk_type == CHUNK_TYPE_FILL:
                fill_val = f_in.read(4)
                fill_data = fill_val * (chunk_sz * blk_sz // 4)
                f_out.write(fill_data)
            elif chunk_type == CHUNK_TYPE_DONT_CARE:
                f_out.write(b'\x00' * (chunk_sz * blk_sz))
            elif chunk_type == CHUNK_TYPE_CRC32:
                f_in.read(data_sz)
            else:
                f_in.read(data_sz)

def raw_to_transfer(img_file, out_dir, prefix):
    """Convert raw ext4 img to .new.dat + .transfer.list"""
    img_size = os.path.getsize(img_file)
    total_blocks = img_size // BLOCK_SIZE

    dat_file = os.path.join(out_dir, f"{prefix}.new.dat")
    transfer_file = os.path.join(out_dir, f"{prefix}.transfer.list")

    with open(img_file, 'rb') as f_in, open(dat_file, 'wb') as f_out:
        block_ranges = []
        start = 0
        block = 0

        while True:
            chunk = f_in.read(BLOCK_SIZE)
            if not chunk:
                break
            if len(chunk) < BLOCK_SIZE:
                chunk += b'\x00' * (BLOCK_SIZE - len(chunk))
            f_out.write(chunk)
            block += 1

        block_ranges.append(f"0,0,{block}")

    with open(transfer_file, 'w') as f:
        f.write("4\n")
        f.write(f"{total_blocks}\n")
        f.write(f"{total_blocks}\n")
        f.write(f"new {block_ranges[0]}\n")

    print(f"Output: {dat_file} ({os.path.getsize(dat_file) // 1024 // 1024} MB)")
    print(f"Output: {transfer_file}")
    return dat_file, transfer_file

def convert_img_to_sdat(input_img, out_dir, prefix):
    os.makedirs(out_dir, exist_ok=True)
    
    # Check if input is sparse
    with open(input_img, 'rb') as f:
        magic = struct.unpack('<I', f.read(4))[0]
    
    if magic == SPARSE_HEADER_MAGIC:
        print(f"Input is sparse image, converting to raw first...")
        raw_img = os.path.join(out_dir, f"{prefix}_raw.img")
        sparse_to_raw(input_img, raw_img)
        raw_to_transfer(raw_img, out_dir, prefix)
        os.remove(raw_img)
    else:
        print(f"Input is raw ext4 image...")
        raw_to_transfer(input_img, out_dir, prefix)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert ext4 image to sdat format')
    parser.add_argument('input', help='Input .img file')
    parser.add_argument('-o', '--output', default='.', help='Output directory')
    parser.add_argument('-p', '--prefix', required=True, help='Output prefix (system/product)')
    args = parser.parse_args()

    print(f"Converting {args.input} -> {args.prefix}.new.dat + {args.prefix}.transfer.list")
    convert_img_to_sdat(args.input, args.output, args.prefix)
    print("Done!")
