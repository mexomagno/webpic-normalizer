""" Main file, everything happens here!"""

import sys
import argparse
import os
from PIL import Image as im
from PIL import ImageFilter as imf
from PIL import ImageEnhance as ime


SUPPORTED_IMAGE_FORMATS = ['png', 'jpeg', 'jpg', 'bmp']
DEFAULT_OUTPUT_FORMAT = 'jpg'


class ImageProcessor:
    def __init__(self, img_path, output_size, bg_blur, bg_opacity, bg_upscale):
        self.img_path = img_path
        self.output_size = output_size
        self.bg_blur = bg_blur
        self.bg_opacity = bg_opacity
        self.bg_upscale = bg_upscale
        self.output_image = None

    def process(self):
        opened_img = self._fix_jpeg_rotation(im.open(self.img_path))
        aspect_ratio_in = opened_img.size[0]*1.0 / opened_img.size[1]
        aspect_ratio_out = self.output_size[0]*1.0 / self.output_size[1]
        # make sure new size gets inside output size
        if aspect_ratio_in < aspect_ratio_out:
            # output is wider, we must match heights
            in_height = self.output_size[1]
            in_width = in_height * aspect_ratio_in
            bg_width = self.output_size[0]
            bg_height = bg_width / aspect_ratio_in
            bg_width *= self.bg_upscale
            bg_height *= self.bg_upscale
            bgxpos = self.output_size[0]/2 - bg_width/2
            bgypos = in_height/2 - bg_height/2
            xpos = self.output_size[0]/2 - in_width/2
            ypos = 0
        else:
            # output is narrower, we must match widths
            in_width = self.output_size[0]
            in_height = in_width / aspect_ratio_in
            bg_height = self.output_size[1]
            bg_width = bg_height * aspect_ratio_in
            bg_width *= self.bg_upscale
            bg_height *= self.bg_upscale
            bgxpos = in_width/2 - bg_width/2
            bgypos = self.output_size[1]/2 - bg_height/2
            xpos = 0
            ypos = self.output_size[1]/2 - in_height/2
        in_img = opened_img.resize((int(in_width), int(in_height)))
        # Create large copy of image
        bg_fill = opened_img.resize((int(bg_width), int(bg_height)))
        # Blur
        bg_fill = bg_fill.filter(imf.GaussianBlur(self.bg_blur))
        # Opacity
        enhancer = ime.Brightness(bg_fill)
        bg_fill = enhancer.enhance(self.bg_opacity)
        # Put in background
        out_img = im.new('RGB', self.output_size, 'black')
        out_img.paste(bg_fill, (int(bgxpos), int(bgypos)))
        out_img.paste(in_img, (int(xpos), int(ypos)))
        self.output_image = out_img

    def save(self, out_name):
        if not self.output_image:
            raise RuntimeError("You must first call '{}'".format(self.process.__name__))
        if os.path.isfile(out_name):
            raise RuntimeError("File '{}' already exists! Would've overriden".format(out_name))
        input_size_bytes = os.stat(self.img_path).st_size
        # Choose quality based on image size
        if input_size_bytes < 512*1024:
            quality = 90
            optimize = False
        elif input_size_bytes < 1024*1024:
            quality = 90
            optimize = False
        elif input_size_bytes < 2*1024*1024:
            quality = 90
            optimize = False
        else:
            quality = 85
            optimize = True
        print("Will compress with quality {}".format(quality))
        self.output_image.save(out_name,
                               format='JPEG',
                               quality=quality,
                               optimize=optimize)

    @staticmethod
    def _fix_jpeg_rotation(img_object):
        if hasattr(img_object, '_getexif'):
            orientation = 0x0112
            exif = img_object._getexif()
            if exif:
                orientation = exif[orientation]
                rotations = {
                    3: (im.ROTATE_180, 180),
                    6: (im.ROTATE_270, 270),
                    8: (im.ROTATE_90, 90)
                }
                print("Rotating image by {}° in compliance to exif metadata".format(rotations[orientation][1]))
                img_object = img_object.transpose(rotations[orientation][0])
        return img_object


def is_image_file(file_path):
    _, ext = os.path.splitext(os.path.basename(file_path))
    if not ext.lower().replace('.', '') in SUPPORTED_IMAGE_FORMATS:
        print("Warning: file '{}' not a supported image file".format(os.path.basename(file_path)))
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
    arg_parser.add_argument("--output-dir", '-o', help="Existing directory where to store the generated image(s)")
    arg_parser.add_argument("input", help="Existing image or directory with images to process",
                            type=_existing_image_or_directory)
    arg_parser.add_argument("--bgblur", "-b", help="Background fill blur ammount", default=10, type=int)
    arg_parser.add_argument("--bgopacity", "-p", help="Background fill opacity from 0 to 1", default=0.7, type=float)
    arg_parser.add_argument("--bgupscale", "-u", help="Background fill over size from 1", default=1.1, type=float)
    args = arg_parser.parse_args()
    return args


def main():
    options = parse_args()
    print("options: {}".format(options))
    # Process one image
    image_paths = list()
    out_dir = os.path.curdir
    if options.output_dir:
        out_dir = options.output_dir
    input_is_directory = os.path.isdir(options.input)
    if input_is_directory:
        files_in_dir = os.listdir(options.input)
        for img_file_path in [x for x in files_in_dir if is_image_file(x)]:
            image_paths.append(os.path.join(options.input, img_file_path))
        # Create output directory
        new_folder = "{}_processed".format(os.path.basename(os.path.abspath(options.input)))
        os.mkdir(new_folder)
        out_dir = os.path.join(out_dir, new_folder)
    else:
        # input was a single file
        image_paths.append(options.input)

    print("Files to process: {}. Dir to store: {}".format(len(image_paths), out_dir))
    print("Options: ")
    for opt in vars(options):
        print("\t- {}: {}".format(opt, getattr(options, opt)))
    counter = 0
    for img_path in image_paths:
        counter += 1
        print("Processing {} of {}... ({}%)".format(counter, len(image_paths), int(counter/len(image_paths)*100)))
        img_processor = ImageProcessor(img_path,
                                       output_size=(1160, 655),
                                       bg_blur=options.bgblur,
                                       bg_opacity=options.bgopacity,
                                       bg_upscale=options.bgupscale)
        img_processor.process()
        name, ext = os.path.splitext(os.path.basename(img_path))
        if input_is_directory:
            out_filename = "{}{}".format(name, DEFAULT_OUTPUT_FORMAT)
        else:
            out_filename = "{}_processed.{}".format(name, DEFAULT_OUTPUT_FORMAT)
        img_processor.save(out_name=os.path.join(out_dir, out_filename))
    print("Done. Saved to '{}'".format(out_dir))


if __name__ == "__main__":
    main()
