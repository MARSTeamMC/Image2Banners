import base64
import json
import multiprocessing
import sys
import urllib.parse
from io import BytesIO
from pathlib import Path

from PIL import Image

import image_to_banners
import json_to_banners
import list_to_banner
from utils import print_with_flush, get_assets_folder

file_name = None
image_banner = None
dict_banner = None

human_names = {
    'b':   '',
    'bs':  'Base',
    'ts':  'Chief',
    'ls':  'Pale Dexter',
    'rs':  'Pale Sinister',
    'cs':  'Pale',
    'ms':  'Fess',
    'drs': 'Bend',
    'dls': 'Bend Sinister',
    'ss':  'Paly',
    'cr':  'Saltire',
    'sc':  'Cross',
    'ld':  'Per Bend Siniste',
    'rud': 'Per Bend',
    'lud': 'Per Bend Inverted',
    'rd':  'Per Bend Sinister Inverted',
    'vh':  'Per Pale',
    'vhr': 'Per Pale Inverted',
    'hh':  'Per Fess',
    'hhb': 'Per Fess Inverted',
    'bl':  'Base Dexter Canton',
    'br':  'Base Sinister Canton',
    'tl':  'Chief Dexter Canton',
    'tr':  'Chief Sinister Canton',
    'bt':  'Chevron',
    'tt':  'Inverted Chevron',
    'bts': 'Base Indented',
    'tts': 'Chief Indented',
    'mc':  'Roundel',
    'mr':  'Lozenge',
    'bo':  'Bordure',
    'cbo': 'Bordure Indented',
    'bri': 'Field Masoned',
    'gra': 'Gradient',
    'gru': 'Base Gradient',
    'cre': 'Creeper Charge',
    'sku': 'Skull Charge',
    'flo': 'Flower Charge',
    'moj': 'Thing',
    'glb': 'Globe',
    'pig': 'Snout',
    'flw': 'Flow',
    'gus': 'Guster'
}

resource_names = {
    'background': 'base',
    'bs':  'stripe_bottom',
    'ts':  'stripe_top',
    'ls':  'stripe_left',
    'rs':  'stripe_right',
    'cs':  'stripe_center',
    'ms':  'stripe_middle',
    'drs': 'stripe_downright',
    'dls': 'stripe_downleft',
    'ss':  'small_stripes',
    'cr':  'cross',
    'sc':  'straight_cross',
    'ld':  'diagonal_left',
    'rud': 'diagonal_right',
    'lud': 'diagonal_up_left',
    'rd':  'diagonal_up_right',
    'vh':  'half_vertical',
    'vhr': 'half_vertical_right',
    'hh':  'half_horizontal',
    'hhb': 'half_horizontal_bottom',
    'bl':  'square_bottom_left',
    'br':  'square_bottom_right',
    'tl':  'square_top_left',
    'tr':  'square_top_right',
    'bt':  'triangle_bottom',
    'tt':  'triangle_top',
    'bts': 'triangles_bottom',
    'tts': 'triangles_top',
    'mc':  'circle',
    'mr':  'rhombus',
    'bo':  'border',
    'cbo': 'curly_border',
    'bri': 'bricks',
    'gra': 'gradient',
    'gru': 'gradient_up',
    'cre': 'creeper',
    'sku': 'skull',
    'flo': 'flower',
    'moj': 'mojang',
    'glb': 'globe',
    'pig': 'piglin',
    'flw': 'flow',
    'gus': 'guster'
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

    image_banner, dict_banner, file_name = image_to_banners.banner_gen(image_path, resolution, generate_blocks, generate_layered_banners, generate_big_banners,
                                            use_pattern_items, threads_count)

    print_with_flush(f"Generated_{resolution[0]}.{resolution[1]}")


def jsn(data):
    global image_banner, dict_banner, file_name

    json_path = urllib.parse.unquote(data['filePath'])
    threads_count = int(data['threadsCount'])

    image_banner, dict_banner, file_name, resolution = json_to_banners.banner_gen(json_path, threads_count)

    print_with_flush(f"Generated_{resolution[0]}.{resolution[1]}")


def save_as_image():
    global image_banner, file_name
    Path("generated/images").mkdir(parents=True, exist_ok=True)
    image_banner.save(f"generated/images/{file_name}.png")


def save_as_json():
    global dict_banner, file_name
    Path("generated/json").mkdir(parents=True, exist_ok=True)
    with open(f'generated/json/{file_name}.json', 'w', encoding='utf-8') as f:
        json.dump(dict_banner, f, ensure_ascii=False, indent=4)


def steps(data):
    global dict_banner
    print_with_flush("RemoveSteps")

    id = data['id']

    buffer = BytesIO()
    block = Image.open(f"{get_assets_folder()}/block/{dict_banner[id]['block']}.png")
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

    patterns = ','.join(['{color: "'+i.split('-')[0]+'", pattern: "'+resource_names[i.split('-')[1]]+'"}' for i in banner_lst[1:]])
    command = f'/give @p minecraft:{banner_lst[0].replace("-background", "_banner")}[minecraft:banner_patterns=['+patterns+']]'


    print_with_flush(f"StepsResult|data:image/png;base64,{banner_result}|{dict_banner[id]['block'].replace('_', ' ')}|data:image/png;base64,{block_result}|{command}")

    for c, i in enumerate(banner_steps):
        buffer = BytesIO()
        i.save(buffer, format="PNG")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')

        buffer = BytesIO()
        pattern = Image.open(f'{get_assets_folder()}/banner_patterns/'+banner_lst[c]+'.png')
        color_code = banner_lst[c].replace('-', ' ')

        if 'background' not in banner_lst[c]:
            pattern_name = f"{color_code.split(' ')[0].title()} {human_names[color_code.split(' ')[1]]}"
        else:
            pattern_name = color_code.title()

        pattern.save(buffer, format="PNG")
        buffer.seek(0)
        image_base64_pattern = base64.b64encode(buffer.read()).decode('utf-8')

        print_with_flush(f"Steps_{c}_data:image/png;base64,{image_base64}_data:image/png;base64,{image_base64_pattern}_{pattern_name}")


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
                save_as_image()

            elif data['operation'] == 'save_as_json':
                save_as_json()

            elif data['operation'] == 'steps':
                steps(data)


        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
