import base64
import json
import multiprocessing
import sys
import urllib.parse
from io import BytesIO
from pathlib import Path
from PIL import Image

import banners_to_nbt
import image_to_banners
import json_to_banners
import list_to_banner
from utils import print_with_flush, get_assets_folder

file_name = None
image_banner = None
dict_banner = None

readable_names = {
    'stripe_bottom':  'Base',
    'stripe_top':  'Chief',
    'stripe_left':  'Pale Dexter',
    'stripe_right':  'Pale Sinister',
    'stripe_center':  'Pale',
    'stripe_middle':  'Fess',
    'stripe_downright': 'Bend',
    'stripe_downleft': 'Bend Sinister',
    'small_stripes':  'Paly',
    'cross':  'Saltire',
    'straight_cross':  'Cross',
    'diagonal_left':  'Per Bend Siniste',
    'diagonal_right': 'Per Bend',
    'diagonal_up_left': 'Per Bend Inverted',
    'diagonal_up_right':  'Per Bend Sinister Inverted',
    'half_vertical':  'Per Pale',
    'half_vertical_right': 'Per Pale Inverted',
    'half_horizontal':  'Per Fess',
    'half_horizontal_bottom': 'Per Fess Inverted',
    'square_bottom_left':  'Base Dexter Canton',
    'square_bottom_right':  'Base Sinister Canton',
    'square_top_left':  'Chief Dexter Canton',
    'square_top_right':  'Chief Sinister Canton',
    'triangle_bottom':  'Chevron',
    'triangle_top':  'Inverted Chevron',
    'triangles_bottom': 'Base Indented',
    'triangles_top': 'Chief Indented',
    'circle':  'Roundel',
    'rhombus':  'Lozenge',
    'border':  'Bordure',
    'curly_border': 'Bordure Indented',
    'bricks': 'Field Masoned',
    'gradient': 'Gradient',
    'gradient_up': 'Base Gradient',
    'creeper': 'Creeper Charge',
    'skull': 'Skull Charge',
    'flower': 'Flower Charge',
    'mojang': 'Thing',
    'globe': 'Globe',
    'piglin': 'Snout',
    'flow': 'Flow',
    'guster': 'Guster'
}


def img(data):
    global image_banner, dict_banner, file_name

    image_path = urllib.parse.unquote(data['filePath'])
    resolution = data['resolution']
    generate_blocks = data['generateBlocks']
    generate_layered_banners = data['generateLayeredBanners']
    generate_big_banners = data['generateBigBanners']
    use_pattern_items = data['usePatternItems']
    threads_count = int(data['threadsCount'])
    compare_method = float(data['compareMethod'])/100

    image_banner, dict_banner, file_name = image_to_banners.banner_gen(image_path, resolution, generate_blocks, generate_layered_banners, generate_big_banners,
                                            use_pattern_items, threads_count, compare_method)

    print_with_flush(f"Generated_{resolution[0]}.{resolution[1]}")


def jsn(data):
    global image_banner, dict_banner, file_name

    json_path = urllib.parse.unquote(data['filePath'])
    threads_count = int(data['threadsCount'])

    image_banner, dict_banner, file_name, resolution = json_to_banners.banner_gen(json_path, threads_count)

    print_with_flush(f"Generated_{resolution[0]}.{resolution[1]}")


def save_as_image(data):
    global image_banner, file_name
    Path("generated/images").mkdir(parents=True, exist_ok=True)
    if f"{int(data['resolution'][0])}x{int(data['resolution'][1])}" in file_name:
        image_banner.save(f"generated/images/{file_name}.png")
    else:
        image_banner.save(f"generated/images/{file_name}_{int(data['resolution'][0])}x{int(data['resolution'][1])}.png")

def save_as_json(data):
    global dict_banner, file_name
    Path("generated/json").mkdir(parents=True, exist_ok=True)
    if f"{int(data['resolution'][0])}x{int(data['resolution'][1])}" in file_name:
        with open(f"generated/json/{file_name}.json", 'w', encoding='utf-8') as f:
            json.dump(dict_banner, f, ensure_ascii=False, indent=4)
    else:
        with open(f"generated/json/{file_name}_{int(data['resolution'][0])}x{int(data['resolution'][1])}.json", 'w', encoding='utf-8') as f:
            json.dump(dict_banner, f, ensure_ascii=False, indent=4)


def save_as_nbt(data):
    global image_banner, dict_banner, file_name
    Path("generated/nbt").mkdir(parents=True, exist_ok=True)


def steps(data):
    global dict_banner
    print_with_flush("RemoveSteps")

    id = data['id']

    buffer = BytesIO()
    block = Image.open(f"{get_assets_folder()}/blocks/{dict_banner[id]['block']}.png")
    block.save(buffer, format="PNG")
    buffer.seek(0)
    block_result = base64.b64encode(buffer.read()).decode('utf-8')

    if 'banner' not in dict_banner[id]:
        buffer = BytesIO()
        Image.open(f'{get_assets_folder()}/banner.png').save(buffer, format="PNG")
        buffer.seek(0)
        banner_result = base64.b64encode(buffer.read()).decode('utf-8')

        print_with_flush(f"StepsResult|data:image/png;base64,{banner_result}|{dict_banner[id]['block']}|data:image/png;base64,{block_result}")
        return

    banner_lst = dict_banner[id]['banner']
    banner_steps = list_to_banner.convert_with_steps(banner_lst)

    buffer = BytesIO()
    banner_steps[-1].save(buffer, format="PNG")
    buffer.seek(0)
    banner_result = base64.b64encode(buffer.read()).decode('utf-8')
    print(banner_lst)
    patterns = ','.join(['{color: "' + i.split('#')[0] + '", pattern: "' + i.split('#')[1] + '"}' for i in banner_lst[1:]])
    command = f'/give @p minecraft:{banner_lst[0].replace("#wall_banner", "_banner")}[minecraft:banner_patterns=[' + patterns + ']]'

    print_with_flush(f"StepsResult|data:image/png;base64,{banner_result}|{dict_banner[id]['block'].replace('_', ' ').replace('-', ' ').title()}|data:image/png;base64,{block_result}|{command}")

    for c, i in enumerate(banner_steps):
        buffer = BytesIO()
        i.save(buffer, format="PNG")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')

        buffer = BytesIO()
        pattern = Image.open(f'{get_assets_folder()}/banner_patterns/'+banner_lst[c]+'.png')
        color_code = banner_lst[c].replace('#', ' ')

        if 'wall' not in banner_lst[c]:
            pattern_name = f"{color_code.split(' ')[0].title()} {readable_names[color_code.split(' ')[1]]}"
        else:
            pattern_name = color_code.title().replace('_', ' ')

        pattern.save(buffer, format="PNG")
        buffer.seek(0)
        image_base64_pattern = base64.b64encode(buffer.read()).decode('utf-8')

        print_with_flush(f"Steps|{c}|data:image/png;base64,{image_base64}|data:image/png;base64,{image_base64_pattern}|{pattern_name}")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    while True:
        try:
            input_data = sys.stdin.readline().strip()
            if not input_data:
                continue

            data = json.loads(input_data)
            print_with_flush(data)

            if data['operation'] == 'close':
                break

            if data['operation'] == 'generate':
                file_extension = data['filePath'].split(".")[1]
                if file_extension == 'json':
                    jsn(data)
                else:
                    img(data)

            elif data['operation'] == 'save_as_image':
                save_as_image(data)

            elif data['operation'] == 'save_as_json':
                save_as_json(data)

            elif data['operation'] == 'save_as_nbt':
                banners_to_nbt.process_data(dict_banner, file_name)

            elif data['operation'] == 'steps':
                steps(data)


        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
