import os
import tempfile
import subprocess
import re
from pathlib import Path

def compare_dirs_with_diffoscope(path1, path2):
    with tempfile.NamedTemporaryFile(delete=False) as diff_file:
        result = subprocess.run(
            ['diffoscope', '--exclude-directory-metadata=recursive',
             '--text', diff_file.name, path1, path2],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        with open(diff_file.name, 'r') as f:
            diff_content = f.read()
        os.unlink(diff_file.name)
        return diff_content, len(diff_content)

def compare_dirs_with_diffoscope_recorded_text(path1, path2, output_path):
    # Run diffoscope and write its output directly to output_path
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    result = subprocess.run(
        ['diffoscope', '--exclude-directory-metadata=recursive',
         '--text', output_path, path1, path2],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

def compare_dirs_with_diffoscope_recorded_html(path1, path2, output_path):
    # Run diffoscope and write its output directly to output_path
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    result = subprocess.run(
        ['diffoscope', '--exclude-directory-metadata=recursive',
         '--html', output_path, path1, path2],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    # print(result)

# def parse_diffoscope_output(diff_text, output_file_path):
#     diff_info = []
#     current_file = None
#     current_diffs = []
#     current_chunk_is_ordering = False
#     ordering_only_file = True

#     lines = diff_text.splitlines()

#     # line[4:].strip() removes "+++ " or "--- " from the beginning (so we just get file location)
#     for raw_line in lines:
#         # Normalize line by removing diffoscope UI characters like │ ├ etc.
#         line = re.sub(r'^[\s│├┄─]*', '', raw_line)

#         # Detect start of file diff
#         if line.startswith('--- '):
#             # Save previous file's real diffs if any
#             if current_file and current_diffs and not ordering_only_file:
#                 current_file['diffs'] = current_diffs
#                 diff_info.append(current_file)

#             # Begin new file diff
#             current_file = {'file1': line[4:].strip(), 'file2': '', 'diffs': []}
#             current_diffs = []
#             ordering_only_file = False  # default false; will set to True if detected
#             current_chunk_is_ordering = False

#         elif line.startswith('+++ ') and current_file:
#             current_file['file2'] = line[4:].strip()

#         elif "Ordering differences only" in line:
#             ordering_only_file = True
#             current_chunk_is_ordering = True

#         elif line.startswith('@@') and current_file:
#             if not current_chunk_is_ordering:
#                 match = re.match(r'@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@', line)
#                 if match:
#                     line_from = int(match.group(1))
#                     line_to = int(match.group(2))
#                     current_diffs.append((line_from, line_to))
#             current_chunk_is_ordering = False  # Reset after chunk is parsed

#     # Final file block check
#     if current_file and current_diffs and not ordering_only_file:
#         current_file['diffs'] = current_diffs
#         diff_info.append(current_file)

#     # Write output
#     with open(output_file_path, 'w') as out:
#         for diff in diff_info:
#             out.write(f"{diff['file1']} <-> {diff['file2']}\n")
#             for from_line, to_line in diff['diffs']:
#                 out.write(f"  - Original line: {from_line}, Modified line: {to_line}\n")
#             out.write("\n")

def write_ranges_with_update_url(out, orig_lines, update_url_lines):
    """
    orig_lines: sorted list of changed original line numbers
    update_url_lines: set of lines that are update_url lines
    """
    if not orig_lines:
        return

    start = prev = orig_lines[0]
    for line in orig_lines[1:] + [None]:  # Add None to flush last range
        if line is None or line != prev + 1 or prev in update_url_lines:
            # Close off the current range before the new line or after update_url line
            if start == prev:
                # Single line range
                if start in update_url_lines:
                    out.write(f"  - Original: {start}–{prev} -> Update URL\n")
                else:
                    out.write(f"  - Original: {start}–{prev}\n")
            else:
                # Multi-line range
                # If update_url lines inside this range, we have split earlier,
                # so none should be inside here.
                out.write(f"  - Original: {start}–{prev}\n")

            start = line
        prev = line

def parse_diffoscope_output(input_path: str, output_path: str):
    # Ensure the output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(input_path, 'r') as f:
        diff_content = f.read()
    lines = diff_content.splitlines()

    current_file = None
    current_diffs = None
    output = []
    ordering_only = False
    line_end_only = False
    file_list = False

    old_line_num = new_line_num = 0

    for rawline in lines:
        line = re.sub(r'^[\s│├┄─]*', '', rawline)

        if line.startswith('--- '):
            if current_diffs and current_file:
                if not (ordering_only and line_end_only):
                    if file_list:
                        current_file['flag'] = 1
                    current_file['diffs'] = current_diffs
                elif ordering_only:
                    current_file['flag'] = 2
                elif line_end_only:
                    current_file['flag'] = 3
                output.append(current_file)

            current_file = {'file1': line[4:].strip(), 'file2': '', 'flag': 0, 'diffs': []}
            current_diffs = []
            ordering_only = False
            line_end_only = False
            file_list = False

        elif line.startswith('+++ '):
            current_file['file2'] = line[4:].strip()

        elif "Ordering differences only" in line:
            ordering_only = True
        elif "Line-ending differences only" in line:
            line_end_only = True
        elif "file list" in line:
            file_list = True

        elif file_list:
            if line.startswith("+"):
                current_diffs.append(("+", line[1:].strip()))
            elif line.startswith("-"):
                current_diffs.append(("-", line[1:].strip()))

        elif line.startswith('@@') and current_file:
            if not ordering_only:
                match = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
                if match:
                    old_line_num = int(match.group(1))
                    old_count = int(match.group(2)) if match.group(2) else 1
                    new_line_num = int(match.group(3))
                    new_count = int(match.group(4)) if match.group(4) else 1

                    current_diffs.append({
                        "orig_start": old_line_num,
                        "mod_start": new_line_num,
                        "orig_changes": [],
                        "mod_changes": [],
                        "update_url_lines": []
                    })

        elif current_file and current_diffs and isinstance(current_diffs[-1], dict):
            if line.startswith('-'):
                current_diffs[-1]["orig_changes"].append(old_line_num)
                if "update_url" in line:
                    current_diffs[-1]["update_url_lines"].append(old_line_num)
                old_line_num += 1
            elif line.startswith('+'):
                current_diffs[-1]["mod_changes"].append(new_line_num)
                new_line_num += 1
            else:
                old_line_num += 1
                new_line_num += 1

    # Final file
    if current_diffs and current_file:
        if not (ordering_only and line_end_only):
            if file_list:
                current_file['flag'] = 1
            current_file['diffs'] = current_diffs
        elif ordering_only:
            current_file['flag'] = 2
        elif line_end_only:
            current_file['flag'] = 3
        output.append(current_file)

    # Output to file
    with open(output_path, 'w') as out:
        for diff in output:
            out.write(f"---{diff['file1']} <-> +++{diff['file2']}")
            out_check = diff['file1'].split(".")
            if len(out_check) > 1:
                out.write(f"; File type: {out_check[-1]}\n")
            else:
                out.write("\n")

            if diff['flag'] == 1:
                minus_file = []
                plus_file = []
                for pm, fname in diff['diffs']:
                    if pm == '+':
                        plus_file.append(fname)
                    else:
                        minus_file.append(fname)

                out.write("  - files: " + ", ".join(minus_file) + "\n")
                out.write("  + files: " + ", ".join(plus_file) + "\n\n")

            elif diff['flag'] == 2:
                out.write("Ordering differences only\n")
            elif diff['flag'] == 3:
                out.write("Line-ending differences only\n")
            else:
                for hunk in diff['diffs']:
                    if not isinstance(hunk, dict):
                        continue
                    orig = sorted(hunk["orig_changes"])
                    mod = sorted(hunk["mod_changes"])
                    update_lines = set(hunk.get("update_url_lines", []))

                    # Use helper to print original ranges with special update_url lines
                    write_ranges_with_update_url(out, orig, update_lines)

                    # Print modified ranges normally as before
                    if mod:
                        start = mod[0]
                        end = mod[-1]
                        out.write(f"  + Modified: {start}–{end}\n")

                out.write("\n")

    return