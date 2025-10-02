import gzip
import struct
import re
from pathlib import Path


def nbt_gen(file_name, width, height, blocks, banners, banners_blocks, coords):
    Path("generated/nbt").mkdir(parents=True, exist_ok=True)
    if f"{width}x{height}" in file_name:
        name = f'generated/nbt/{file_name}.nbt'
    else:
        name = f'generated/nbt/{file_name}_{width}x{height}.nbt'
    with gzip.open(name.replace(" ", "_"), 'w') as f:
        # Root
        f.write(struct.pack(">B", 10))
        f.write(struct.pack(">h", 0))

        # size
        f.write(struct.pack(">B", 9))  # TAG_list
        f.write(struct.pack(">h", 4))  # name length
        f.write(b"size")
        f.write(struct.pack(">B", 3))  # contains TAG_Int
        f.write(struct.pack(">i", 3))  # list length
        f.write(struct.pack(">i", width if width<32 else 32))  # x
        f.write(struct.pack(">i", height if height<32 else 32))  # y
        f.write(struct.pack(">i", 2))  # z

        # entities
        f.write(struct.pack(">B", 9))  # TAG_list
        f.write(struct.pack(">h", 8))  # name length
        f.write(b"entities")
        f.write(struct.pack(">B", 10))  # contains TAG_Compound
        f.write(struct.pack(">i", 0))  # list length

        # blocks
        f.write(struct.pack(">B", 9))  # TAG_list
        f.write(struct.pack(">h", 6))  # name length
        f.write(b"blocks")
        f.write(struct.pack(">B", 10))  # contains TAG_Compound
        f.write(struct.pack(">i", len(coords) * 2))  # list length

        # block compound (block)
        for coord in coords:
            coord_r = re.findall(r"\d+", coord)

            f.write(struct.pack(">B", 9))  # TAG_list
            f.write(struct.pack(">h", 3))  # name length
            f.write(b"pos")
            f.write(struct.pack(">B", 3))  # contains TAG_Int
            f.write(struct.pack(">i", 3))  # list length
            f.write(struct.pack(">i", width - int(coord_r[0]) - 1))  # x
            f.write(struct.pack(">i", height - int(coord_r[1]) - 1))  # y
            f.write(struct.pack(">i", 1))  # z

            f.write(struct.pack(">B", 3))  # TAG_Int
            f.write(struct.pack(">h", 5))  # name length
            f.write(b"state")
            f.write(struct.pack(">i", 1 + blocks.index(banners_blocks[coord]['block'])))

            f.write(struct.pack(">B", 0))

        # block compound (banner)
        for coord in coords:
            coord_r = re.findall(r"\d+", coord)

            if "banner" in banners_blocks[coord].keys():
                # nbt
                f.write(struct.pack(">B", 10))  # TAG_Compound
                f.write(struct.pack(">h", 3))  # name length
                f.write(b"nbt")

                # patterns
                f.write(struct.pack(">B", 9))  # TAG_list
                f.write(struct.pack(">h", 8))  # name length
                f.write(b"patterns")
                f.write(struct.pack(">B", 10))  # contains TAG_Compound
                f.write(struct.pack(">i", len(banners_blocks[coord]['banner'][1:])))  # list length
                for pattern in banners_blocks[coord]['banner'][1:]:
                    f.write(struct.pack(">B", 8))  # TAG_String
                    f.write(struct.pack(">h", 5))  # name length
                    f.write(b"color")
                    f.write(struct.pack(">h", len(f"{pattern.split('#')[0]}")))
                    f.write(f"{pattern.split('#')[0]}".encode("utf-8"))

                    f.write(struct.pack(">B", 8))  # TAG_String
                    f.write(struct.pack(">h", 7))  # name length
                    f.write(b"pattern")
                    f.write(struct.pack(">h", len(f"minecraft:{pattern.split('#')[1]}")))
                    f.write(f"minecraft:{pattern.split('#')[1]}".encode("utf-8"))

                    f.write(struct.pack(">B", 0))

                # id
                f.write(struct.pack(">B", 8))  # TAG_String
                f.write(struct.pack(">h", 2))  # name length
                f.write(b"id")
                f.write(struct.pack(">h", 16))
                f.write(b"minecraft:banner")
                f.write(struct.pack(">B", 0))

            f.write(struct.pack(">B", 9))  # TAG_list
            f.write(struct.pack(">h", 3))  # name length
            f.write(b"pos")
            f.write(struct.pack(">B", 3))  # contains TAG_Int
            f.write(struct.pack(">i", 3))  # list length
            f.write(struct.pack(">i", width - int(coord_r[0]) - 1))  # x
            f.write(struct.pack(">i", height - int(coord_r[1]) - 1))  # y
            f.write(struct.pack(">i", 0))  # z

            f.write(struct.pack(">B", 3))  # TAG_Int
            f.write(struct.pack(">h", 5))  # name length
            f.write(b"state")
            if "banner" in banners_blocks[coord].keys():
                f.write(struct.pack(">i", 1 + len(blocks) + banners.index(
                    banners_blocks[coord]['banner'][0].replace('#', '_'))))
            else:
                f.write(struct.pack(">i", 0))

            f.write(struct.pack(">B", 0))

        # palette
        f.write(struct.pack(">B", 9))  # TAG_list
        f.write(struct.pack(">h", 7))  # name length
        f.write(b"palette")
        f.write(struct.pack(">B", 10))  # contains TAG_Compound
        f.write(struct.pack(">i", len(blocks) + len(banners) + 1))  # list length

        # palette compound (air)
        f.write(struct.pack(">B", 8))  # TAG_String
        f.write(struct.pack(">h", 4))  # name length
        f.write(b"Name")
        f.write(struct.pack(">h", len(f"minecraft:air")))
        f.write(f"minecraft:air".encode("utf-8"))

        f.write(struct.pack(">B", 0))

        # palette compound (block)
        for block in blocks:
            if '-' in block:
                component = block.split("-")[1]
                block = block.split("-")[0]

                # properties
                f.write(struct.pack(">B", 10))  # TAG_Compound
                f.write(struct.pack(">h", 10))  # name length
                f.write(b"Properties")
                if component == 'top':
                    f.write(struct.pack(">B", 8))  # TAG_String
                    f.write(struct.pack(">h", 4))  # name length
                    f.write(b"axis")
                    f.write(struct.pack(">h", 1))
                    f.write(b"z")
                elif component == 'side':
                    f.write(struct.pack(">B", 8))  # TAG_String
                    f.write(struct.pack(">h", 6))  # name length
                    f.write(b"facing")
                    f.write(struct.pack(">h", 4))
                    f.write(b"east")
                elif component == 'front':
                    f.write(struct.pack(">B", 8))  # TAG_String
                    f.write(struct.pack(">h", 6))  # name length
                    f.write(b"facing")
                    f.write(struct.pack(">h", 5))
                    f.write(b"north")
                elif component == 'up':
                    f.write(struct.pack(">B", 8))  # TAG_String
                    f.write(struct.pack(">h", 6))  # name length
                    f.write(b"facing")
                    f.write(struct.pack(">h", 2))
                    f.write(b"up")
                elif component == 'lit':
                    f.write(struct.pack(">B", 8))  # TAG_String
                    f.write(struct.pack(">h", 3))  # name length
                    f.write(b"lit")
                    f.write(struct.pack(">h", 4))
                    f.write(b"true")
                elif component == 'inside':
                    f.write(struct.pack(">B", 8))  # TAG_String
                    f.write(struct.pack(">h", 5))  # name length
                    f.write(b"north")
                    f.write(struct.pack(">h", 5))
                    f.write(b"false")
                elif component == 'east' and "crafter" in block:
                    f.write(struct.pack(">B", 8))  # TAG_String
                    f.write(struct.pack(">h", 11))  # name length
                    f.write(b"orientation")
                    f.write(struct.pack(">h", 7))
                    f.write(b"west_up")
                elif component == 'east' and "crafter" in block:
                    f.write(struct.pack(">B", 8))  # TAG_String
                    f.write(struct.pack(">h", 11))  # name length
                    f.write(b"orientation")
                    f.write(struct.pack(">h", 7))
                    f.write(b"west_up")
                elif component == 'bottom' and "crafter" in block:
                    f.write(struct.pack(">B", 8))  # TAG_String
                    f.write(struct.pack(">h", 11))  # name length
                    f.write(b"orientation")
                    f.write(struct.pack(">h", 8))
                    f.write(b"up_south")
                elif component == 'south' and "crafter" in block:
                    f.write(struct.pack(">B", 8))  # TAG_String
                    f.write(struct.pack(">h", 11))  # name length
                    f.write(b"orientation")
                    f.write(struct.pack(">h", 8))
                    f.write(b"south_up")
                elif component == 'top' and "crafter" in block:
                    f.write(struct.pack(">B", 8))  # TAG_String
                    f.write(struct.pack(">h", 11))  # name length
                    f.write(b"orientation")
                    f.write(struct.pack(">h", 10))
                    f.write(b"down_north")
                elif component == 'west' and "crafter" in block:
                    f.write(struct.pack(">B", 8))  # TAG_String
                    f.write(struct.pack(">h", 11))  # name length
                    f.write(b"orientation")
                    f.write(struct.pack(">h", 7))
                    f.write(b"east_up")
                f.write(struct.pack(">B", 0))

            else:
                # properties
                f.write(struct.pack(">B", 10))  # TAG_Compound
                f.write(struct.pack(">h", 10))  # name length
                f.write(b"Properties")
                if 'trapdoor' in block:
                    f.write(struct.pack(">B", 8))  # TAG_String
                    f.write(struct.pack(">h", 6))  # name length
                    f.write(b"facing")
                    f.write(struct.pack(">h", 5))
                    f.write(b"south")
                    f.write(struct.pack(">B", 8))  # TAG_String
                    f.write(struct.pack(">h", 4))  # name length
                    f.write(b"open")
                    f.write(struct.pack(">h", 4))
                    f.write(b"true")
                elif 'shulker' in block:
                    f.write(struct.pack(">B", 8))  # TAG_String
                    f.write(struct.pack(">h", 6))  # name length
                    f.write(b"facing")
                    f.write(struct.pack(">h", 5))
                    f.write(b"north")
                elif 'smooth_stone_slab' in block:
                    f.write(struct.pack(">B", 8))  # TAG_String
                    f.write(struct.pack(">h", 4))  # name length
                    f.write(b"type")
                    f.write(struct.pack(">h", 6))
                    f.write(b"double")
                f.write(struct.pack(">B", 0))

            f.write(struct.pack(">B", 8))  # TAG_String
            f.write(struct.pack(">h", 4))  # name length
            f.write(b"Name")
            f.write(struct.pack(">h", len(f"minecraft:{block}")))
            f.write(f"minecraft:{block}".encode("utf-8"))

            f.write(struct.pack(">B", 0))

        # palette compound (banner)
        for banner in banners:
            # properties
            f.write(struct.pack(">B", 10))  # TAG_Compound
            f.write(struct.pack(">h", 10))  # name length
            f.write(b"Properties")
            f.write(struct.pack(">B", 8))  # TAG_String
            f.write(struct.pack(">h", 6))  # name length
            f.write(b"facing")
            f.write(struct.pack(">h", 5))
            f.write(b"north")
            f.write(struct.pack(">B", 0))

            f.write(struct.pack(">B", 8))  # TAG_String
            f.write(struct.pack(">h", 4))  # name length
            f.write(b"Name")
            f.write(struct.pack(">h", len(f"minecraft:{banner}")))
            f.write(f"minecraft:{banner}".encode("utf-8"))

            f.write(struct.pack(">B", 0))

        # version
        f.write(struct.pack(">B", 3))  # TAG_Int
        f.write(struct.pack(">h", 11))  # name length
        f.write(b"DataVersion")
        f.write(struct.pack(">i", 4440))

        # end root
        f.write(struct.pack(">B", 0))


def process_data(banners_blocks, file_name):
    coords = list(banners_blocks.keys())[:-1]
    resolution = banners_blocks['resolution']
    width = int(resolution[0])
    height = int(resolution[1])
    blocks = []
    for banner_block in list(banners_blocks.values())[:-1]:
        block = banner_block['block']
        if block not in blocks:
            blocks.append(block)

    banners = []
    for banner_block in list(banners_blocks.values())[:-1]:
        if 'banner' in banner_block.keys():
            banner = banner_block['banner'][0].replace('#', '_')
            if banner not in banners:
                banners.append(banner)

    nbt_gen(file_name, width, height, blocks, banners, banners_blocks, coords)
