import argparse

def get_args():
    parser = argparse.ArgumentParser(
            description='API to download lectures off msc-mu.com')
    parser.add_argument(
            '-t', '--category', type=int, metavar='', help='to specify category number'
            )
    parser.add_argument(
            '-c', '--course', type=int, metavar='', help='to specify course number'
            )
    parser.add_argument(
            '-f', '--folder', type=str, metavar='', help='to specify destination folder'
            )
    parser.add_argument(
            '-v', '--verbose', action='store_true', help='Increase Verbosity'
            )
    return parser.parse_args()

