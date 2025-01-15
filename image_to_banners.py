import base64
import math
import os
from concurrent.futures import as_completed, ProcessPoolExecutor
from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw
from skimage.color import rgb2lab
from skimage.metrics import structural_similarity as ssim

from utils import print_with_flush, get_assets_folder

# colors = {
#     "white": [189, 193, 193],
#     "orange": [189, 97, 22],
#     "magenta": [151, 59, 143],
#     "light_blue": [44, 136, 165],
#     "yellow": [192, 163, 46],
#     "lime": [97, 150, 23],
#     "pink": [183, 105, 128],
#     "gray": [54, 60, 62],
#     "light_gray": [118, 118, 114],
#     "cyan": [17, 118, 118],
#     "purple": [104, 38, 139],
#     "blue": [45, 51, 129],
#     "brown": [99, 64, 38],
#     "green": [71, 94, 17],
#     "red": [133, 35, 29],
#     "black": [22, 22, 25]
# }

colors = {
    "white": [77.76, -1.38, -0.48],
    "orange": [51.19, 32.5, 54.3],
    "magenta": [40.72, 49.31, -28.2],
    "light_blue": [52.79, -16.86, -23.11],
    "yellow": [67.72, -1.38, 60.65],
    "lime": [56.5, -36.48, 54.94],
    "pink": [53.74, 33.97, 0.94],
    "gray": [24.84, -2.02, -2.09],
    "light_gray": [49.52, -0.79, 2.2],
    "cyan": [44.78, -26.1, -7.73],
    "purple": [29.9, 46.29, -43.39],
    "blue": [25.29, 23.59, -44.92],
    "brown": [30.54, 12.2, 21.97],
    "green": [36.72, -20.65, 38.22],
    "red": [30.11, 41.16, 28.34],
    "black": [7.36, 0.78, -2.09],
}

pattern_items = ["cre", "sku", "flo", "moj", "glb", "pig", "flw", "gus"]

executor = None

def banner_gen(image_path, resolution, gen_blocks, gen_layering, gen_big, use_pattern_items, threads_count):
    FULL_WIDTH, FULL_HEIGHT = 22, 44

    image = Image.open(image_path).convert('RGBA')

    resolution_width = int(resolution[0])
    resolution_height = int(resolution[1])
    
    image = image.resize((resolution_width*22, resolution_height*22))
    OW, OH = image.size

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    print_with_flush(f"imagePreview_data:image/png;base64,{image_base64}")

    images = [image.crop((w * FULL_WIDTH, h * FULL_HEIGHT-22, (w + 1) * FULL_WIDTH, (h + 1) * FULL_HEIGHT))
              for h in range(math.ceil(OH / FULL_HEIGHT))
              for w in range(OW // FULL_WIDTH)]
    image.close()

    full = Image.new("RGB", (OW, OH))

    best_banners = [i for i in range(len(images))]

    banner_json = {f'({i%resolution_width},{i//resolution_width})':{} for i in range(resolution_width*resolution_height)}
    banner_json['resolution'] = resolution

    banner_bar = 0
    global executor
    executor = ProcessPoolExecutor(max_workers=threads_count)
    futures = [executor.submit(process_image, c, img, gen_blocks, (gen_layering and c>=int(resolution[0])), gen_big, use_pattern_items)
               for c, img in enumerate(images)]

    for future in as_completed(futures):
        banner_num = int(future.result()[0])
        banner_bar += 1
        banner = future.result()[1]
        best_banners[banner_num] = banner
        buffer = BytesIO()
        banner.save(buffer, format="PNG")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        section = future.result()[2]
        x = banner_num%resolution_width
        y = banner_num//resolution_width*2
        banner_json[f"({x},{y})"]["banner"] = section[0]
        banner_json[f"({x},{y})"]["block"] = section[1]
        if y+1<resolution_height:
            banner_json[f"({x},{y+1})"]["block"] = section[2]

        if len(section)==4:
            banner_json[f"({x},{y-1})"]["banner"] = section[3]

        print_with_flush(f"bannerPreview{banner_num}_data:image/png;base64,{image_base64}")
        print_with_flush(f'progressBar_data:{banner_bar}/{len(images)}')

    executor.shutdown()

    for idx, (w, h) in enumerate(((w, h) for h in range(math.ceil(OH / FULL_HEIGHT)) for w in range(OW // FULL_WIDTH))):
        full.paste(best_banners[idx],
                   (w * FULL_WIDTH, h * FULL_HEIGHT-3, (w + 1) * FULL_WIDTH, (h + 1) * FULL_HEIGHT),
                   best_banners[idx])

        best_banners[idx].close()

    file_name = Path(image_path).stem

    buffer = BytesIO()
    full.save(buffer, format="PNG")
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    print_with_flush(f"imagePreview_data:image/png;base64,{image_base64}")

    return full, banner_json, file_name

def process_image(c, img, gen_blocks, gen_layering, gen_big, use_pattern_items):
    section = []

    main_img = img.crop((0, 22, 22, 66))

    img_banner = main_img.crop((1, 2, 21, 41))

    img_banner_rgb = np.array(img_banner.convert('RGB'))
    img_banner.close()

    main_patterns, main_banner = generate_banner(img_banner_rgb, gen_big, use_pattern_items)
    section.append(main_patterns)

    if gen_blocks:
        img_up = main_img.crop((0, 0, 22, 22))
        draw = ImageDraw.Draw(img_up)
        draw.rectangle((1, 2, 20, 22), fill=(0, 0, 0, 255))

        img_down = main_img.crop((0, 22, 22, 44))
        draw = ImageDraw.Draw(img_down)
        draw.rectangle((1, 0, 20, 18), fill=(0, 0, 0, 255))

        img_up_rgb = np.array(img_up.convert('RGB'))
        img_down_rgb = np.array(img_down.convert('RGB'))

        img_up.close()
        img_down.close()

        block_up_name, block_up = generate_blocks(img_up_rgb, "up")
        block_down_name, block_down = generate_blocks(img_down_rgb, "down")
    else:
        block_up_name, block_up = generate_blocks(None, "up")
        block_down_name, block_down = generate_blocks(None, "down")

    section.append(block_up_name)
    section.append(block_down_name)

    full = Image.new("RGBA", (22, 47))
    full.paste(block_up, (0,3))
    full.paste(block_down, (0, 25))
    full.paste(main_banner, (1,5))

    if gen_layering:
        second_img = img.crop((0, 0, 22, 44))

        img_second_banner = second_img.crop((1, 2, 21, 41))
        second_img.close()

        img_second_banner_rgb = np.array(img_second_banner.convert('RGB'))
        img_second_banner.close()

        second_patterns, second_banner = generate_banner(img_second_banner_rgb, gen_big, use_pattern_items)
        second_banner = second_banner.crop((0, 18, 20, 39))

        second_full = full.copy()
        second_full.paste(second_banner, (1,0))
        better, full = compare_main_second(full, second_full, main_img)
        if better:
            section.append(second_patterns)

    img.close()
    main_img.close()

    return [c, full, section]

def generate_blocks(image_rgb, part):
    path = f"{get_assets_folder()}/blocks/"

    block_name = "polished_andesite"

    if image_rgb is None:
        return block_name, Image.open(path+part+"-polished_andesite.png")

    best_similarity_score = 0

    bvs = os.listdir(path)

    best_block = Image.open(path + bvs[0])

    for bv in bvs:
        if bv.split("-")[0]==part:
            bv_image = Image.open(path + bv)

            similarity_score = compare_images(bv_image, image_rgb)
            if similarity_score > best_similarity_score:
                best_similarity_score = similarity_score
                best_block = bv_image.copy()
                block_name = bv.split("-")[1].split(".")[0]

            bv_image.close()

    return block_name, best_block

def generate_banner(image2_rgb, gen_big, use_pattern_items):
    path = f"{get_assets_folder()}/banner_patterns/"

    patterns = []

    colors_in_img1 = get_colors(image2_rgb, colors)

    biggest_color = None
    biggest_color_count = 0
    for i in set(colors_in_img1):
        count = colors_in_img1.count(i)
        if biggest_color_count<count:
            biggest_color = i
            biggest_color_count=count

    patterns.append(f"{biggest_color}-background")
    if len(colors_in_img1) == 1:
        return patterns, Image.open(f"{path}{biggest_color}-background.png")

    new_colors = colors.copy()
    for i in set(colors_in_img1):
        new_colors.pop(i)

    colors_in_img2 = get_colors(image2_rgb, new_colors)
    colors_in_img = set(colors_in_img1+colors_in_img2)

    best_similarity_score = 0
    last_best_similarity_score = -1

    bvs = os.listdir(path)

    best_banner = Image.open(f"{path}{biggest_color}-background.png")
    best_banner_copy = best_banner.copy()

    layer = 0
    while last_best_similarity_score != best_similarity_score and (layer<6 or gen_big):
        last_best_similarity_score = best_similarity_score
        layer += 1
        for bv in bvs:
            if bv.split('-')[0] in colors_in_img and bv.split('-')[1].split(".")[0]!="background":
                if use_pattern_items or not (bv.split('-')[1].split(".")[0] in pattern_items):
                    bv_image = Image.open(path + bv)
                    temp_banner = best_banner_copy.copy()
                    temp_banner.alpha_composite(bv_image, (0, 0))
                    bv_image.close()

                    similarity_score = compare_images(temp_banner, image2_rgb)
                    if similarity_score > best_similarity_score:
                        best_similarity_score = similarity_score
                        best_banner = temp_banner.copy()
                        best_banner_name = bv.split(".")[0]

                    temp_banner.close()

        best_banner_copy = best_banner.copy()
        patterns.append(best_banner_name)

    return patterns, best_banner_copy

def compare_images(img1, image2_rgb):
    image1_rgb = np.array(img1.convert('RGB'))

    if image1_rgb.shape != image2_rgb.shape:
        image2_rgb = cv2.resize(image2_rgb, (image1_rgb.shape[1], image1_rgb.shape[0]))

    ssim_value = ssim(image1_rgb, image2_rgb, multichannel=True, full=False, channel_axis=2)

    return ssim_value

def compare_main_second(main_img, second_img, img):
    main_img_crop = main_img.crop((0,3,22,47))
    second_img_crop = second_img.crop((0,3,22,47))

    main_img_rgb = np.array(main_img_crop.convert('RGB'))
    second_img_rgb = np.array(second_img_crop.convert('RGB'))
    img_rgb = np.array(img.convert('RGB'))

    main_ssim_value = ssim(main_img_rgb, img_rgb, multichannel=True, full=False, channel_axis=2)
    second_ssim_value = ssim(second_img_rgb, img_rgb, multichannel=True, full=False, channel_axis=2)

    main_img_crop.close()
    second_img_crop.close()

    if second_ssim_value>main_ssim_value:
        main_img.close()
        return True, second_img
    
    second_img.close()
    return False, main_img

def get_colors(img, color_lst):
    colors_in_img = []
    for i in img:
        for px_color in i:
            lab_px_color = rgb_to_lab(px_color)
            dist = -1
            dist_name = None
            for name, lab_color in color_lst.items():
                color_dist = np.linalg.norm(lab_px_color - lab_color)
                if dist == -1 or color_dist < dist:
                    dist = color_dist
                    dist_name = name
            colors_in_img.append(dist_name)
    return colors_in_img

def rgb_to_lab(rgb_color):
    rgb_color = np.array([[rgb_color]]) / 255.0
    lab_color = rgb2lab(rgb_color)
    return lab_color[0][0]
