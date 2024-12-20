from PIL import Image

def convert(banner_lst):
    path = "assets/banner_patterns/"
    banner = Image.open(path+banner_lst[0]+".png")
    for bv in banner_lst[1:]:
        variant = Image.open(path+bv+".png")
        banner.alpha_composite(variant, (0, 0))
        variant.close()

    return banner

def convert_with_steps(banner_lst):
    path = "assets/banner_patterns/"

    banner_steps = []

    banner = Image.open(path + banner_lst[0] + ".png")
    banner_steps.append(banner.copy())
    for bv in banner_lst[1:]:
        variant = Image.open(path + bv + ".png")
        banner.alpha_composite(variant, (0, 0))
        variant.close()
        banner_steps.append(banner.copy())
        
    return banner_steps
