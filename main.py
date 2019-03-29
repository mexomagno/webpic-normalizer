""" Main file, everything happens here!"""

import sys
import argparse
import os
from PIL import Image as im
from PIL import ImageFilter as imf
from PIL import ImageEnhance as ime


SUPPORTED_IMAGE_FORMATS = ['png', 'jpeg', 'jpg', 'bmp']


class ImageProcessor:
    def __init__(self, img_path, output_size, bg_blur=10):
        self.img_path = img_path
        self.output_size = output_size
        self.bg_blur = bg_blur
        self.bg_upscale = 1.1

    def process(self):
        opened_img = im.open(self.img_path)
        aspect_ratio_in = opened_img.size[0]*1.0 / opened_img.size[1]
        aspect_ratio_out = self.output_size[0]*1.0 / self.output_size[1]
        # make sure new size gets inside output size
        if aspect_ratio_in < aspect_ratio_out:
            # output is wider, we must match heights
            in_height = self.output_size[1]
            in_width = in_height * aspect_ratio_in
            bg_width = self.output_size[0] * self.bg_upscale
            bg_height = bg_width / aspect_ratio_in * self.bg_upscale
            bgxpos = 0
            bgypos = in_height/2 - bg_height/2
            xpos = self.output_size[0]/2 - in_width/2
            ypos = 0
        else:
            # output is narrower, we must match widths
            in_width = self.output_size[0]
            in_height = in_width / aspect_ratio_in
            bg_height = self.output_size[1] * self.bg_upscale
            bg_width = bg_height * aspect_ratio_in * self.bg_upscale
            bgxpos = in_width/2 - bg_width/2
            bgypos = 0
            xpos = 0
            ypos = self.output_size[1]/2 - in_height/2
        in_img = opened_img.resize((int(in_width), int(in_height)))
        # Create large copy of image
        bg_fill = opened_img.resize((int(bg_width), int(bg_height)))
        # Blur
        bg_fill = bg_fill.filter(imf.GaussianBlur(self.bg_blur))
        # Opacity
        enhancer = ime.Brightness(bg_fill)
        bg_fill = enhancer.enhance(0.5)
        # Put in background
        out_img = im.new('RGB', self.output_size, 'black')
        out_img.paste(bg_fill, (int(bgxpos), int(bgypos)))
        out_img.paste(in_img, (int(xpos), int(ypos)))
        out_img.show(title="Processed")


    def save(self, output_dir=None):
        if output_dir is None:
            output_dir = os.path.curdir
        print("Saving...")



def is_image_file(file_path):
    _, ext = os.path.splitext(os.path.basename(file_path))
    if not ext.lower().replace('.', '') in SUPPORTED_IMAGE_FORMATS:
        return False
    return True

def parse_args():
    """Parses console args."""
    def _existing_image_or_directory(path):
        error = None
        if not os.path.isfile(path) and not os.path.isdir(path):
            error = "No such file or directory"
        if os.path.isfile(path) and not is_image_file(path):
            error = "Not a supported picture format"
        if error is not None:
            raise argparse.ArgumentTypeError("Error loading '{}': {}".format(path, error))
        return path

    arg_parser = argparse.ArgumentParser(description="A picture processor for mom's web!")
    arg_parser.add_argument("--output", "-o", help="Existing directory where to store the generated image(s)")
    arg_parser.add_argument("input", help="Existing image or directory with images to process",
                            type=_existing_image_or_directory)
    args = arg_parser.parse_args()
    return args

def main():
    options = parse_args()
    print("options: {}".format(options))
    # Process one image
    new_img = ImageProcessor(options.input, (800, 600))
    new_img.process()
    new_img.save()



"""
usage example:

main.py image_name.ext
-- Image processed, output saved in same folder
main.py image_name.ext -o outdir
-- image processed, output to specified dir
main.py folder_with_pics
-- All images in folder processed and stored in new output folder
main.py folder_with_pics -o outdir
-- Same but outputed to specified dir

"""


if __name__ == "__main__":
    main()
