#!/usr/bin/env python

"""Go image recognition."""



### Global
import argparse, cStringIO, os, pickle, sys, time, urllib2
try:
    from PIL import Image, ImageDraw
except ImportError, msg:
    print >> sys.stderr, msg
    sys.exit(1)

### Local
import linef
import intrsc
import gridf
import output


class Logger:
    def __init__(self):
        self.t = 0

    def __call__(self, m):
        t_n = time.time()
        if self.t > 0:
            print >> sys.stderr, "\t" + str(t_n - self.t)
        print >> sys.stderr, m
        self.t = t_n


def argument_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    # parser.add_argument('url', metavar='url',
    #                     help="image url")
    parser.add_argument('urls', metavar='url', nargs='+',
                        help="image to analyse")
    parser.add_argument('-w', type=int, default=640,
                    help="scale image to the specified width before analysis")
    parser.add_argument('-m', '--manual', dest='manual_mode',
                        action='store_true',
                        help="manual grid selection")
    parser.add_argument('-d', '--debug', dest='show_all',
                        action='store_true',
                        help="show every step of the computation")
    parser.add_argument('-s', '--save', dest='saving', action='store_true',
                        help="save images instead of displaying them")
    parser.add_argument('-c', '--cache', dest='l_cache', action='store_true',
                        help="use cached lines")
    parser.add_argument('-t', '--timed_reopen', dest='timed_reopen', action='store_true',
                        help="reopen file in a loop based on a timer, cache is implicit")
    parser.add_argument('-S', '--sgf', dest='sgf_output', action='store_true',
                        help="output in SGF")
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                        help="report progress")
    return parser

# Debug vars may be global
show_all = False
verbose = False

def load_image_from_url(url, width):
    try:
        image_raw = cStringIO.StringIO(urllib2.urlopen(url).read())
        image = Image.open(image_raw)
        # Not sure what mode 'P' is. CMYK based image?
        if image.mode == 'P':
            image = image.convert('RGB')
        # Resize based on given width
        if image.size[0] > width:
            image = image.resize((width, int((float(width)/image.size[0]) *
                              image.size[1])), Image.ANTIALIAS)
    except IOError, msg:
        print >> sys.stderr, msg
        return 1

    return image

def get_board_for_image(image, do_something, logger, show_all, last_board):

    # cache_dir = "saved/cache"
    # filename = "%s/game_%s" % (cache_dir,str(image.size[0]))
    # if os.path.exists(filename):
    #     lines, l1, l2, bounds, hough = pickle.load(open(filename))
    #     print >> sys.stderr, "using cached results"
    # else:
    #     lines, l1, l2, bounds, hough = linef.find_lines(image, do_something, logger)
    #     if not os.path.isdir(cache_dir):
    #         os.makedirs(cache_dir)
    #     d_file = open(filename, 'wb')
    #     pickle.dump((lines, l1, l2, bounds, hough), d_file)
    #     d_file.close()


    # Find intersections
    if last_board:
        grid, lines, intersections = last_board['grid'], last_board['lines'], last_board['intersections']
    else:
        lines, l1, l2, bounds, hough = linef.find_lines(image, do_something, logger)
        grid, lines = gridf.find(lines, image.size, l1, l2, bounds, hough,
                             show_all, do_something, logger)
        intersections = intrsc.b_intersects(image, lines, show_all, do_something, logger)
    board = intrsc.board(image, intersections, show_all, do_something, logger)
    return {
        'state': board,
        'intersections': intersections,
        'grid': grid,
        'lines': lines
    }

### TODO: Centralise logging
def init_logger(verbose):
    if verbose:
        logger = Logger()
    else:
        def logger(m):
            pass

    return logger

### TODO: Find more elegant way to do this, global for this is not pretty
def init_show_all(show_all):
    if not show_all:
        def nothing(a, b):
            pass
        return nothing
    elif args.saving:
        return Imsave("saved/" + args.files[0][:-4] + "_" +
                               str(image.size[0]) + "/").save

def main():
    """Main function of the program."""

    parser = argument_parser()
    args = parser.parse_args()

    logger = init_logger(args.verbose)
    do_something = init_show_all(args.show_all)

    last_board = None
    game = None
    while 1:
        raw_input('Press a key')
        image = load_image_from_url(args.urls[0], args.w)

        if last_board:
            board = get_board_for_image(image, do_something, logger, show_all, last_board)
        else:
            board = get_board_for_image(image, do_something, logger, show_all, None)
            if args.sgf_output:
                game = output.Game(19, board['state'])
        last_board = board

        if args.sgf_output:
            game.addMove(board['state'])
            print game.asSGF()
        else:
            print board['state']




if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt: #TODO does this work?
        print >> sys.stderr, "Interrupted."
        sys.exit(1)
