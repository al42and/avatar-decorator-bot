from PIL import Image, ImageColor, ImageDraw, ImageFilter
import io

from avatar_decorator_bot import config


AVATAR_SIZE = (640, 640)


def get_color(args):
    name = ' '.join(args)
    rgba = ImageColor.getrgb(name)
    return rgba[0], rgba[1], rgba[2]


def add_color_to_avatar(image_file, rgb):
    avatar = Image.open(image_file)
    avatar = avatar.resize(AVATAR_SIZE, resample=Image.LANCZOS)
    avatar_new = Image.new('RGB', AVATAR_SIZE, rgb)
    mask = _circular_mask(AVATAR_SIZE)
    avatar_new.paste(avatar, box=(0, 0), mask=mask)
    return _image_to_bytes(avatar_new)


def create_empty_avatar(rgb):
    image = Image.new('RGB', AVATAR_SIZE, rgb)
    return _image_to_bytes(image)


def _image_to_bytes(image):
    fd = io.BytesIO()
    image.save(fd, 'PNG')
    fd.seek(0)
    return fd


def _circular_mask(size, delta=None):
    if delta is None:
        delta = size[0] // 10

    mask = Image.new('L', size, 0)

    draw = ImageDraw.Draw(mask)
    draw.ellipse((delta, delta, size[0]-delta, size[1]-delta), 255)

    if config.IMAGE_BLUR and size[0] > 100:
        mask_blurred = mask.filter(ImageFilter.GaussianBlur(2))
        return mask_blurred
    else:
        return mask
