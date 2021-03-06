#! py -3
# Utilities
import shutil
import sys
import textwrap
import pprint

import atomic_kotlin_builder.config as config


def create_markdown_filename(h1):
    fn = h1.replace(": ", "_")
    fn = fn.replace(" ", "_") + ".md"
    fn = fn.replace("&", "and")
    fn = fn.replace("?", "")
    fn = fn.replace("+", "P")
    fn = fn.replace("/", "")
    fn = fn.replace("-", "_")
    fn = fn.replace("(", "")
    fn = fn.replace(")", "")
    fn = fn.replace("`", "")
    fn = fn.replace(",", "")
    fn = fn.replace("!", "")
    return fn


def create_numbered_markdown_filename(h1, n):
    return "%02d_" % n + create_markdown_filename(h1)


def clean(dir_to_remove):
    "Remove directory"
    try:
        if dir_to_remove.exists():
            shutil.rmtree(str(dir_to_remove))
            return "Removed: {}".format(dir_to_remove)
        else:
            return "Doesn't exist: {}".format(dir_to_remove)
    except Exception as e:
        print("""Removal failed: {}
        Are you inside that directory, or using a file inside it?
        """.format(dir_to_remove))
        print(e)


def check_for_existence(extension):
    files_with_extension = list(config.example_dir.rglob(extension))
    if len(files_with_extension) < 1:
        print("Error: no " + extension + " files found")
        sys.exit(1)
    return files_with_extension


def find_end(text_lines, n):
    """
    n is the index of the code listing title line,
    searches for closing ``` and returns that index
    """
    for i, line in enumerate(text_lines[n:]):
        if line.rstrip() == "```":
            return n + i
        if line.rstrip() == "```kotlin":
            assert False, "```kotlin before closing ```"
    else:
        assert False, "closing ``` not found"


def replace_code_in_text(generated, text):
    """
    Returns 'text' after replacing code listing matching 'generated'
    Both generated and text are NOT lists, but normal chunks of text
    returns new_text, starting_index so an editor can be opened at that line
    """
    code_lines = generated.splitlines()
    title = code_lines[0].strip()
    assert title in text, "{} not in text".format(title)
    text_lines = text.splitlines()
    for n, line in enumerate(text_lines):
        if line.strip() == title:
            end = find_end(text_lines, n)
            # print("n: {}, end: {}".format(n, end))
            # pprint.pprint(text_lines[n:end])
            # print("=" * 60)
            # pprint.pprint(code_lines)
            # print("-" * 60)
            text_lines[n:end] = code_lines
            new_text = ("\n".join(text_lines)).strip()
            return new_text, n
    assert False, "{} not found in text".format(title)




def create_new_status_file():
    "Create STATUS.md"
    status_file = config.root_path / "STATUS.md"
    if status_file.exists():
        return "STATUS.md already exists; new one not created"
    md_files = sorted([md.name for md in config.markdown_dir.glob("[0-9][0-9]_*.md")])
    status = ""
    def checkbox(item):
        nonlocal status
        status += "+ [ ] {}\n".format(item)
    for md in md_files:
        status += "#### {}\n".format(md)
        checkbox("Examples Replaced")
        checkbox("Rewritten")
        checkbox("Tech Checked")
        status += "+ Notes:\n"
    status_file.write_text(status)



# Format output:
# (0) Do first/last lines before formatting to width
# (1) Combine output and error (if present) files
# (2) Format all output to width limit
# (3) Add closing '*/'


def adjust_lines(text):
    text = text.replace("\0", "NUL")
    lines = text.splitlines()
    slug = lines[0]
    if "(First and Last " in slug:
        num_of_lines = int(slug.split()[5])
        adjusted = lines[:num_of_lines + 1] +\
            ["...________...________...________...________..."] +\
            lines[-num_of_lines:]
        return "\n".join(adjusted)
    elif "(First " in slug:
        num_of_lines = int(slug.split()[3])
        adjusted = lines[:num_of_lines + 1] +\
            ["                  ..."]
        return "\n".join(adjusted)
    else:
        return text


def fill_to_width(text):
    result = ""
    for line in text.splitlines():
        result += textwrap.fill(line, width=config.code_width - 1) + "\n"
    return result.strip()


def reformat_runoutput_files():
    for outfile in check_for_existence("*.out"):
        kotlin = outfile.with_suffix(".kt")
        if kotlin.exists():
            if "{VisuallyInspectOutput}" in kotlin.read_text():  # Don't create p1 file
                print("{} Excluded".format(kotlin.name))
                continue
        out_text = adjust_lines(outfile.read_text())
        phase_1 = outfile.with_suffix(".p1")
        with phase_1.open('w') as phs1:
            phs1.write(fill_to_width(out_text) + "\n")
            errfile = outfile.with_suffix(".err")
            if errfile.exists():
                phs1.write("___[ Error Output ]___\n")
                phs1.write(fill_to_width(errfile.read_text()) + "\n")
            phs1.write("*/\n")
