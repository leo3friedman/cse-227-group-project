import re
import lib.diff_util as DIFF_UTIL
import argparse

parser = argparse.ArgumentParser(description="Script that takes diff file name")
parser.add_argument("inputs", nargs=1, type=str, help="1 input string")
args = parser.parse_args()
input1 = args.inputs[0]
print(input1)
diff_file_path = input1
with open(diff_file_path, 'r') as f:
    diff_content = f.read()

DIFF_UTIL.parse_diffoscope_output(diff_content, "diff_summary.txt")