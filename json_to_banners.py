import base64
import json
import math
import re
from concurrent.futures import as_completed, ProcessPoolExecutor
from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

import list_to_banner
from utils import print_with_flush, get_assets_folder

executor = None

def banner_gen(json_path, threads_count):
    with open(json_path, 'r', encoding='utf-8') as f:
        banner_json = json.load(f)

    banner_json = replace_old_texture_names(banner_json)

    resolution = banner_json['resolution']
    resolution_width = int(resolution[0])
    resolution_height = int(resolution[1])

    only_banners = banner_json.copy()
    only_banners.pop('resolution')

    full = Image.new("RGBA", (resolution_width*22, resolution_height*22))

    blocks = [i for i in range(resolution_width*math.ceil(resolution_height))]
    banners = [i for i in range(resolution_width*math.ceil(resolution_height))]

    section_bar = 0
    global executor
    executor = ProcessPoolExecutor(max_workers=threads_count)
    futures = [executor.submit(process_section, c, section)
               for c, section in enumerate(only_banners.items())]

    for future in as_completed(futures):
        section_bar += 1

        section_num = int(future.result()[0])
        coords = future.result()[1]
        banner = future.result()[2]
        block = future.result()[3]

        blocks[section_num] = [section_num, coords, block]
        banners[section_num] = [section_num, coords, banner ]

    for section_num, coords, block in blocks:
        coords = re.sub(r"[()]", "", coords).split(",")
        x = int(coords[0])*22
        y = int(coords[1])*22

        full.paste(block, (x, y, x+22, y+22))

        block.close()

        if (section_num+1)%resolution_width==0:
            buffer = BytesIO()
            full.save(buffer, format="PNG")
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            print_with_flush(f"imagePreview|data:image/png;base64,{image_base64}")
            print_with_flush(f'progressBar:{section_num}/{len(blocks)+len(banners)}')

    executor.shutdown()

    for section_num, coords, banner in banners[::-1]:
        if banner:
            coords = re.sub(r"[()]", "", coords).split(",")
            x = int(coords[0]) * 22
            y = int(coords[1]) * 22

            full.paste(banner, (x+1, y+2, x+21, y+41))

            banner.close()

        if (section_num+1) % resolution_width == 0:
            buffer = BytesIO()
            full.save(buffer, format="PNG")
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            print_with_flush(f"imagePreview|data:image/png;base64,{image_base64}")
            print_with_flush(f'progressBar:{len(blocks)+len(banners)-section_num}/{len(blocks)+len(banners)}')

    buffer = BytesIO()
    full.save(buffer, format="PNG")
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    print_with_flush(f"imagePreview|data:image/png;base64,{image_base64}")
    print_with_flush(f"update-resolution:{resolution_width}|{resolution_height}")

    file_name = Path(json_path).stem

    return full, banner_json, file_name, resolution


def process_section(c, section):
    path = f"{get_assets_folder()}/blocks/"

    coords = section[0]
    section = section[1]

    if "banner" in section:
        banner = list_to_banner.convert(section['banner'])
    else:
        banner = None

    block = Image.open(path+section['block']+".png").convert("RGBA")
    block_np = np.array(block)
    block_np = cv2.resize(block_np, (22, 22))
    block = Image.fromarray(block_np, "RGBA")

    return [c, coords, banner, block]


def replace_old_texture_names(banner_json):
    old_texture_names = {
        "dried_kelp": "dried_kelp_block",
        "powder_snow": "snow_block",
        "magma": "magma_block",
        "pale_moss_carpet": "pale_moss_block"
    }

    for part in banner_json.values():
        if "block" in part:
            block = part["block"]

            if block in old_texture_names.keys():
                part["block"] = old_texture_names[block]

    return banner_json