#!/usr/bin/env python3

import matplotlib.pyplot as plt
# import matplotlib.image as mpimg
from precip.cli import get_precipitation_lalo
from precip.cli.get_precipitation_lalo import create_parser
import sys
import argparse
import os
# import tempfile
# import glob


def parse_args(args):
    # Get the existing parser
    inps = create_parser()

    cmd = ['get_precipitation_lalo.py']
    cmd.extend(inps.positional)
    cmd.append('--no-show')

    if inps.start_date:
        cmd.append('--start-date')
        cmd.append(str(inps.start_date).replace('-', ''))

    if inps.end_date:
        cmd.append('--end-date')
        cmd.append(str(inps.end_date).replace('-', ''))

    if inps.roll:
        cmd.append('--roll')
        cmd.append(str(inps.roll))

    if inps.bins:
        cmd.append('--bins')
        cmd.append(str(inps.bins))

    if inps.log:
        cmd.append('--log')

    if inps.save is not None:
        cmd.append('--save')
        
        if inps.save:
            cmd.append(str(inps.save))

    if inps.interpolate:
        cmd.append('--interpolate')
        cmd.append(str(inps.interpolate))

    return cmd
    

def main():

    cmd = parse_args(sys.argv[1:])

    styles = ['map','bar', 'annual', 'strength']
    # styles = ['bar','strength']

# with tempfile.TemporaryDirectory() as tmpdir:
    for i, style in enumerate(styles):
        
        cmd = parse_args(sys.argv[1:])
        cmd.append('--style')
        cmd.append(style)
        # cmd.append('--save')
        # cmd.append(tmpdir)

        sys.argv = cmd
        fig, ax = get_precipitation_lalo.main()

    # image_paths = glob.glob(os.path.join(tmpdir, '*.png'))

    # # Create a new figure with subplots
    # fig, axs = plt.subplots(len(styles))

    # # Load each image from file and display it on a different subplot
    # for i, image_path in enumerate(image_paths):
    #     img = mpimg.imread(image_path)
    #     axs[i].imshow(img, aspect='auto')  # Adjust the aspect ratio
    #     axs[i].axis('off')

    plt.show(block=True)

if __name__ == '__main__':
    main()