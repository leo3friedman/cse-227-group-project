import re
import lib.diff_util as DIFF_UTIL
import argparse

parser = argparse.ArgumentParser(description="Script that takes diff file path and output file path")
parser.add_argument("inputs", nargs=1, type=str, help="1 input string")
parser.add_argument("outputs", nargs=1, type=str, help="1 output string")
args = parser.parse_args()
input_path, output_path = args.inputs
print(input_path)
# diff_file_path = input1
# with open(diff_file_path, 'r') as f:
#     diff_content = f.read()

DIFF_UTIL.parse_diffoscope_output(input_path, output_path)