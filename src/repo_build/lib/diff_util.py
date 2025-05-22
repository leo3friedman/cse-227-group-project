import os
import tempfile
import subprocess
import re


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

def compare_dirs_with_diffoscope_recorded(path1, path2, output_path):
    # Run diffoscope and write its output directly to output_path
    result = subprocess.run(
        ['diffoscope', '--exclude-directory-metadata=recursive',
         '--text', output_path, path1, path2],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

def parse_diffoscope_output(diff_text, output_file_path):
    diff_info = []
    current_file = None
    current_diffs = []
    current_chunk_is_ordering = False
    ordering_only_file = True

    lines = diff_text.splitlines()

    for raw_line in lines:
        # Normalize line by removing diffoscope UI characters like │ ├ etc.
        line = re.sub(r'^[\s│├┄─]*', '', raw_line)

        # Detect start of file diff
        if line.startswith('--- '):
            # Save previous file's real diffs if any
            if current_file and current_diffs and not ordering_only_file:
                current_file['diffs'] = current_diffs
                diff_info.append(current_file)

            # Begin new file diff
            current_file = {'file1': line[4:].strip(), 'file2': '', 'diffs': []}
            current_diffs = []
            ordering_only_file = False  # default false; will set to True if detected
            current_chunk_is_ordering = False

        elif line.startswith('+++ ') and current_file:
            current_file['file2'] = line[4:].strip()

        elif "Ordering differences only" in line:
            ordering_only_file = True
            current_chunk_is_ordering = True

        elif line.startswith('@@') and current_file:
            if not current_chunk_is_ordering:
                match = re.match(r'@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@', line)
                if match:
                    line_from = int(match.group(1))
                    line_to = int(match.group(2))
                    current_diffs.append((line_from, line_to))
            current_chunk_is_ordering = False  # Reset after chunk is parsed

    # Final file block check
    if current_file and current_diffs and not ordering_only_file:
        current_file['diffs'] = current_diffs
        diff_info.append(current_file)

    # Write output
    with open(output_file_path, 'w') as out:
        for diff in diff_info:
            out.write(f"{diff['file1']} <-> {diff['file2']}\n")
            for from_line, to_line in diff['diffs']:
                out.write(f"  - Original line: {from_line}, Modified line: {to_line}\n")
            out.write("\n")