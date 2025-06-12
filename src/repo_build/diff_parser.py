import glob
import re
import lib.diff_util as DIFF_UTIL
import argparse
import os

# parser = argparse.ArgumentParser(description="Script that takes diff file path and output file path")
# parser.add_argument("inputs", nargs=1, type=str, help="1 input string")
# parser.add_argument("outputs", nargs=1, type=str, help="1 output string")
# args = parser.parse_args()
# input_path = args.inputs[0]
# output_path = args.outputs[0]


txt_files = glob.glob("/workspace/cse-227-group-project/pipeline_output/output_text/*.txt")
file_names = [os.path.basename(f) for f in txt_files]
# print(file_names[0])
# print(len(txt_files))
for file in file_names:
    # print(file)
    DIFF_UTIL.parse_diffoscope_output(f"/workspace/cse-227-group-project/pipeline_output/output_text/{file}",
                                      f"/workspace/cse-227-group-project/pipeline_output/output_parsed/{file}")
    

txt_files = glob.glob("/workspace/cse-227-group-project/pipeline_output/output_parsed/*.txt")
print(len(txt_files))

# DIFF_UTIL.parse_diffoscope_output(f"/workspace/cse-227-group-project/pipeline_output/output_text/zoehneto_chrome-rtf-viewer.txt",
#                                   f"/workspace/cse-227-group-project/src/repo_build/old_code/test.txt")
# DIFF_UTIL.parse_diffoscope_output(input_path, output_path)