Read this local source bundle and create complete EMBIZ-specific operational doctrine.

Repository: inkscape
Local source: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape
Bundle: /root/embroidery_business_agent_system/directives/repo_adapted_embiz_doctrine/_prompts/inkscape_SOURCE_BUNDLE.md

EMBIZ context:
- Root: /root/embroidery_business_agent_system
- Local corpus: /root/web-archive/ai_agents_skills_library
- OpenClaw: /root/.openclaw/workspace
- Agent bus: /usr/local/bin/agent-msg
- Slack mirror outbound-only; no secrets.
- Human approval required before customer contact.
- Human approval required before digitizing.
- Never claim SVG/PES/DST/EXP/INF/BMP exists unless file exists on disk.
- Named agents: Maya, Madeline, Morgan, Mila, Melanie, Mackenzie, Marina, Monica, Meredith, Mckenna, Margaret, Miranda, Michaela, Maeve, Matilda, Melody, Miriam, Mallory

You must adapt this repo into EMBIZ doctrine, not summarize it.

Write these sections:
# inkscape EMBIZ ADAPTED DOCTRINE
## Source Material Read
## What This Repo Contributes To EMBIZ
## EMBIZ-Specific Adaptation
## Assigned Agent Ownership
## Local Skill / Knowledge Library Integration
## Runtime Rules
## Required Files / Configs
## Commands / Checks
## Security Restrictions
## Verification Checklist
## Build Tasks
## What Not To Use
## Integration Status

Now use this source bundle:


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/src/extension/plugins/grid2/libgrid2.inx =====

<?xml version="1.0" encoding="UTF-8" ?>
<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
<inkscape-extension xmlns="http://www.inkscape.org/namespace/inkscape/extension">
<_name>Grid2</_name>
<id>org.inkscape.effect.grid2</id>
<param name="lineWidth" _gui-text="Line Width:" type="float">1.0</param>
<param name="xspacing" _gui-text="Horizontal Spacing:" type="float" min="0.1" max="1000">10.0</param>
<param name="yspacing" _gui-text="Vertical Spacing:" type="float" min="0.1" max="1000">10.0</param>
<param name="xoffset" _gui-text="Horizontal Offset:" type="float" min="0.0" max="1000">0.0</param>
<param name="yoffset" _gui-text="Vertical Offset:" type="float" min="0.0" max="1000">0.0</param>
<effect>
    <object-type>all</object-type>
        <effects-menu>
          <submenu _name="Render" >
                <submenu _name="Grids" />
          </submenu>
        </effects-menu>
<_menu-tip>Draw a path which is a grid</_menu-tip>
</effect>
<plugin name="libgrid2" />
</inkscape-extension>


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/CMakeScripts/cmake_consistency_check.py =====

#!/usr/bin/env python3

# $Id: cmake_consistency_check.py 38869 2011-07-31 03:15:37Z campbellbarton $
# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Contributor(s): Campbell Barton
#
# ***** END GPL LICENSE BLOCK *****

# <pep8 compliant>

import sys
if not sys.version.startswith("3"):
    print("\nPython3.x needed, found %s.\nAborting!\n" %
          sys.version.partition(" ")[0])
    sys.exit(1)

from cmake_consistency_check_config import (
    IGNORE,
    UTF8_CHECK,
    SOURCE_DIR,
)


import os
from os.path import join, dirname, normpath, splitext

global_h = set()
global_c = set()
global_refs = {}


def replace_line(f, i, text, keep_indent=True):
    file_handle = open(f, 'r')
    data = file_handle.readlines()
    file_handle.close()

    l = data[i]
    ws = l[:len(l) - len(l.lstrip())]

    data[i] = "%s%s\n" % (ws, text)

    file_handle = open(f, 'w')
    file_handle.writelines(data)
    file_handle.close()


def source_list(path, filename_check=None):
    for dirpath, dirnames, filenames in os.walk(path):

        # skip '.git'
        if dirpath.startswith("."):
            continue

        for filename in filenames:
            if filename_check is None or filename_check(filename):
                yield os.path.join(dirpath, filename)


# extension checking
def is_cmake(filename):
    ext = splitext(filename)[1]
    return (ext == ".cmake") or (filename == "CMakeLists.txt")


def is_c_header(filename):
    ext = splitext(filename)[1]
    return (ext in {".h", ".hpp", ".hxx", ".hh"})


def is_c(filename):
    ext = splitext(filename)[1]
    return (ext in {".c", ".cpp", ".cxx", ".m", ".mm", ".rc", ".cc", ".inl"})


def is_c_any(filename):
    return is_c(filename) or is_c_header(filename)


def cmake_get_src(f):

    sources_h = []
    sources_c = []

    filen = open(f, "r", encoding="utf8")
    it = iter(filen)
    found = False
    i = 0
    # print(f)

    def is_definition(l, f, i, name):
        if l.startswith("unset("):
            return False

        if ('set(%s' % name) in l or ('set(' in l and l.endswith(name)):
            if len(l.split()) > 1:
                raise Exception("strict formatting not kept 'set(%s*' %s:%d" % (name, f, i))
            return True

        if ("list(APPEND %s" % name) in l or ('list(APPEND ' in l and l.endswith(name)):
            if l.endswith(")"):
                raise Exception("strict formatting not kept 'list(APPEND %s...)' on 1 line %s:%d" % (name, f, i))
            return True

    while it is not None:
        context_name = ""
        while it is not None:
            i += 1
            try:
                l = next(it)
            except StopIteration:
                it = None
                break
            l = l.strip()
            if not l.startswith("#"):
                found = is_definition(l, f, i, "SRC")
                if found:
                    context_name = "SRC"
                    break
                found = is_definition(l, f, i, "INC")
                if found:
                    context_name = "INC"
                    break

        if found:
            cmake_base = dirname(f)

            while it is not None:
                i += 1
                try:
                    l = next(it)
                except StopIteration:
                    it = None
                    break

                l = l.strip()

                if not l.startswith("#"):

                    if ")" in l:
                        if l.strip() != ")":
                            raise Exception("strict formatting not kept '*)' %s:%d" % (f, i))
                        break

                    # replace dirs
                    l = l.replace("${CMAKE_CURRENT_SOURCE_DIR}", cmake_base)
                    l = l.strip('"')

                    if not l:
                        pass
                    elif l.startswith("$"):
                        if context_name == "SRC":
                            # assume if it ends with context_name we know about it
                            if not l.split("}")[0].endswith(context_name):
                                print("Can't use var '%s' %s:%d" % (l, f, i))
                    elif len(l.split()) > 1:
                        raise Exception("Multi-line define '%s' %s:%d" % (l, f, i))
                    else:
                        new_file = normpath(join(cmake_base, l))

                        if context_name == "SRC":
                            if is_c_header(new_file):
                                sources_h.append(new_file)
                                global_refs.setdefault(new_file, []).append((f, i))
                            elif is_c(new_file):
                                sources_c.append(new_file)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/CMakeScripts/cmake_consistency_check_config.py =====

import os

IGNORE = (
    # dirs
    "/cxxtest/",
    "/dom/work/",
    "/src/extension/dxf2svg/",
    "/test/",

    # files
    "buildtool.cpp",
    "src/inkscape-x64.rc",
    "src/inkview-x64.rc",
    "packaging/macosx/ScriptExec/main.c",
    "share/ui/keybindings.rc",
    "src/deptool.cpp",
    "src/display/nr-filter-skeleton.cpp",
    "src/display/testnr.cpp",
    "src/dom/io/httpclient.cpp",
    "src/dom/odf/SvgOdg.cpp",
    "src/dom/xmlwriter.cpp",
    "src/inkview.cpp",
    "src/inkview.rc",
    "src/io/streamtest.cpp",
    "src/libcola/cycle_detector.cpp",
    "src/libnr/nr-compose-reference.cpp",
    "src/libnr/testnr.cp",
    "src/live_effects/lpe-skeleton.cpp",
    "src/svg/test-stubs.cpp",
    "src/winconsole.cpp",

    # header files
    "share/filters/filters.svg.h",
    "share/palettes/palettes.h",
    "share/paint/patterns.svg.h",
    "share/templates/templates.h",
    "share/symbols/symbols.h",
    "src/libcola/cycle_detector.h",
    "src/libnr/in-svg-plane-test.h",
    "src/libnr/nr-point-fns-test.h",
    "src/libnr/nr-translate-test.h",
    "src/svg/test-stubs.h",

    # generated files, created by an in-source build
    "CMakeFiles/CompilerIdC/CMakeCCompilerId.c",
    "CMakeFiles/CompilerIdCXX/CMakeCXXCompilerId.cpp",
    "src/helper/sp-marshal.cpp",
    "src/helper/sp-marshal.h",
    "src/inkscape-version.cpp",
    "config.h",
    )

UTF8_CHECK = False

SOURCE_DIR = os.path.normpath(os.path.abspath(os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))))


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/buildtools/check_license_headers.py =====

#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# License checker: test that files have a proper SPDX license header.
# Author: Max Gaukler <development@maxgaukler.de>
# Licensed under GPL version 2 or any later version, read the file "COPYING" for more information.

from __future__ import print_function

import fnmatch
import os
import sys
import subprocess
license = {}
hasSPDX = {}

if sys.version_info[0] < 3:
    from io import open

# do not check licenses in these subdirectories:
# TODO: have look at the libraries' licenses
IGNORE_PATHS = [
    ".git*",
    "CMakeScripts",
    "LICENSES",
    "ccache",
    "build*",
    "doc",
    "inst",
    "man",
    "packaging",
    "patches",
    "po",
    "share",
    "src/3rdparty",
    "testfiles/cli_tests/testcases",
    "testfiles/data/example-FEXTRA-FCOMMENT.gz",
    "testfiles/rendering_tests/fonts/LICENSES",
]

# do not check licenses for the following file endings:
IGNORE_FILE_ENDINGS = [
    ".bmp",
    ".bz2",
    ".conf",
    ".dia",
    ".dll",
    ".eps",
    ".icc",
    ".kate-swp",
    ".ods",
    ".pdf",
    ".png",
    ".po",
    ".ps",
    ".rc",
    ".suppression",
    ".svg",
    ".ttf",
    ".ttc",
    ".otf",
    ".xml",
    ".xpm",
    ".COPYRIGHT",
    "AUTHORS",
    "BUILD_YOUR_OWN",
    "CONTRIBUTING.md",
    "COPYING",
    "HACKING",
    "INSTALL.md",
    "NEWS",
    "NEWS.md",
    "Notes.txt",
    "README",
    "README.md",
    "TRANSLATORS",
    "todo.txt",
]

# permitted licenses (MUST BE compatible with licensing the compiled product as GPL3).
# IF YOU CHANGE THIS, also update the list of licenses in COPYING!
PERMITTED_LICENSES = [
    "GPL-2.0-or-later",
    "GPL-3.0-or-later",
    "LGPL-2.1-or-later",
    "LGPL-3.0-or-later",
    "CC0",
]


class LicenseCheckError(Exception):
    pass


if not os.path.exists("./LICENSES"):
    print("this script must be run from the main git directory", file=sys.stderr)
    sys.exit(1)


def files_all():
    ignore_paths = [('./' + p) for p in IGNORE_PATHS]
    ignore_paths += [(p + '/*') for p in ignore_paths]

    for root, dirs, files in os.walk("."):
        for name in files:
            p = os.path.join(root,name)
            if any(p.endswith(i) for i in IGNORE_FILE_ENDINGS):
                continue
            if any(fnmatch.fnmatch(p, i) for i in ignore_paths):
                continue
            if subprocess.call(["git", "check-ignore", "-q", "--", p]) == 0:
                # file is in .gitignore
                continue
            yield p


def main(filenames):
    for p in filenames:
        license[p] = None
        hasSPDX[p] = False
        
        
        try:
            for line in open(p, encoding='utf-8').readlines():
                line = line.strip(' */#<>-!;\r\n')
                if line.startswith("SPDX-License-Identifier: "):
                    hasSPDX[p] = True
                    license[p] = line[len("SPDX-License-Identifier: "):]
        except IOError:
            print("Cannot open {} (ignored)".format(p), file=sys.stderr)
            continue
        except UnicodeDecodeError:
            raise LicenseCheckError(
                "Encoding of {} is damaged (should be UTF8), cannot check license"
                .format(p))

        if not hasSPDX[p]:
            raise LicenseCheckError(
                "File '{}' does not have a SPDX-License-Identifier: header.\n"
                "Please have a look at the coding style: https://inkscape.org/en/develop/coding-style/\n"
                "This is required so that we can make sure all files have compatible licenses."
                .format(p))

        if not any(lic in PERMITTED_LICENSES for lic in license[p].split(' OR ')):
            raise LicenseCheckError(
                "File '{}' has an incompatible or unknown license '{}' in the SPDX-License-Identifier header.\n"
                "Allowed licenses are:\n"
                "{}".format(p, license[p], "\n".join(PERMITTED_LICENSES)))


if __name__ == '__main__':
    try:
        main(files_all())
    except LicenseCheckError as e:
        print(e, file=sys.stderr)
        print("If you think this message is wrong, edit buildtools/check_license_headers.py", file=sys.stderr)
        sys.exit(1)

# vi:sw=4:expandtab:


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/buildtools/lpetest-parse.py =====

#!/usr/bin/env python3
# coding=utf-8
# SPDX-License-Identifier: GPL-2.0-or-later
#
# Script to evaluate LPE test output and update reference files.
# 
# Copyright (C) 2023-2024 Authors
# 
# Authors:
#   PBS <pbs3141@gmail.com>
#   Martin Owens <doctormo@gmail.com>
#
# Released under GNU GPL v2+, read the file 'COPYING' for more information.

import os, re, sys, argparse

description = '''Evaluate LPE test output and update reference files.

Instructions:
 1. Download the "complete raw" job log from one of the test pipelines and place it in the same directory as this script, named joblog.txt. Alternatively, collect the output from running the test suite.
 2. Run the script and examine the output.
 3. If there are no regressions, say yes when it offers to update the testfiles/lpe_tests/* files.
 
Output format:
  The output consists of the old paths 'a.txt', new paths 'b.txt', and visual comparison 'path-comparison.svg'.
  For each LPE test failure,
  - The old path is written on a single line to 'a.txt'.
  - The new path is written on a single line to 'b.txt'.
  - A group is written to 'path-comparison.svg' containing the old path in yellow and the new path in cyan,
    with additive blend mode. Non-matching areas therefore appear in either yellow or cyan.'''

open_testfiles = {}

def yesnoprompt():
    while True:
        txt = input("[y/n]: ").lower()
        if txt in ('y', 'yes'): return True
        if txt in ('n', 'no'): return False
        sys.stdout.write("\nPlease specify yes or no.\n")

def update_reference_files(path, a, b, svg, id):
    id = id.split("(")[0]
    m = re.search("testfiles", svg)
    if m is None:
        sys.stderr.write(f"Warning: Ignoring file '{svg}'\n")
        return

    # Open and cache the contents of the file
    name = os.path.join(path, svg[m.start():])
    if name not in open_testfiles:
        with open(name, "r") as tmpf:
            open_testfiles[name] = tmpf.read()

    contents = open_testfiles[name]
    m = re.search(fr'\bid *= *"{id}"', contents)
    if m is None:
        sys.stderr.write(f"Warning: Ignoring id {id}\n")
        return

    i = max(
        contents.rfind("<path", 0, m.start()),
        contents.rfind("<ellipse", 0, m.start())
    )
    if i < 0:
        sys.stderr.write(f"Warning: Couldn't find start of path for {id}\n")
        return

    m = re.compile(r'\bd *= *"').search(contents, i)
    if m is None:
        sys.stderr.write(f"Warning: Couldn't find d attribute for {id}\n")
        return

    i = m.end()
    j = contents.find('"', i)
    if j == -1:
        sys.stderr.write(f"Warning: Couldn't find end of d attribute for {id}\n")
        return

    contents = contents[:i] + b + contents[j:]
    open_testfiles[name] = contents

def found(cmpf, af, bf, inkscape, count, a, b, svg, id):
    cmpf.write(f"""  <g>
    <path style="fill:#ffff00;stroke:none" d="{a}" id="good{count}" />
    <path style="fill:#00ffff;stroke:none;mix-blend-mode:lighten" d="{b}" id="bad{count}" />
  </g>
""")
    af.write(f"{a}\n")
    bf.write(f"{b}\n")
    update_reference_files(inkscape, a, b, svg, id)

def main():
    parser = argparse.ArgumentParser(prog='lpetest-parse.py', description=description, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--log', default='joblog.txt', metavar='FILE', help='Input file containing test log')
    parser.add_argument('--cmp', default='path-comparison.svg', metavar='FILE', help='Output file for visualisation of path differences')
    parser.add_argument('--a', default='a.txt', metavar='FILE', help='Output file for original paths')
    parser.add_argument('--b', default='b.txt', metavar='FILE', help='Output file for new paths')
    parser.add_argument('--inkscape', default=None, metavar='DIR', help='Inkscape project root directory')
    args = parser.parse_args()

    path = args.inkscape
    if not path:
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    if not os.path.isdir(os.path.join(path, '.git')):
        sys.stderr.write(f"Project not found in '{path}'\n\n")
        sys.stderr.write("Please run this from the Inkscape project root directory, or pass it as --inkscape\n")
        sys.exit(-1)

    if not os.path.isfile(args.log):
        sys.stderr.write(f"Test log not found in '{args.log}'\n\n")
        sys.stderr.write("Please run the suite or download log file from a CI pipeline first\n")
        sys.exit(-2)

    with open(args.log, "r") as logf:
        log = logf.read()

    with open(args.cmp, "w") as cmpf, open(args.a, "w") as af, open(args.b, "w") as bf:
        cmpf.write("<svg>\n")
        
        data = {}
        count = 0
        for tag, value in re.findall(r"\s*\d+:\s+(?P<name>svg|id|a|b):\s*\d+:\s+(?P<value>.+)", log):
            data[tag] = value
            if tag == "b":
                count += 1
                found(cmpf, af, bf, path, count, **data)

        cmpf.write("</svg>\n")

    if len(open_testfiles) > 0:
        print("Overwrite these files?")
        for name in open_testfiles.keys():
            print(name)

        if yesnoprompt():
            for name, contents in open_testfiles.items():
                with open(name, "w") as out:
                    out.write(contents)

if __name__ == "__main__":
    main()


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/buildtools/media-check-icons.py =====

#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# Icon checker: test that icon themes contain all needed icons
# Author: Martin Owens <doctormo@geek-2.com>
# Licensed under GPL version 2 or any later version, read the file "COPYING" for more information.

import fnmatch
import os
import sys

from collections import defaultdict

THEME_PATH = os.path.join('.', 'share', 'icons')
IGNORE_THEMES = [
    'application',
]
FALLBACK_THEME = 'hicolor'
# These are hard coded as symbolic in the gtk source code
SYMBOLIC_ONLY_ICONS = {
    'list-add',
    'list-remove',
    'applications-graphics',
    'edit-find',
    'dialog-warning',
    'edit-clear',
    'view-refresh',
    'pan-down',
    'pan-right',
    'pan-left',
    'pan-end',
    'pan-start',
    'pan-up',
    'window-close',
    'application-exit',
    'document-save-as',
    'open-menu',
}
# These should never appear in a symbolic theme, because they always need to have color
SCALABLE_ONLY_ICONS = {
    'color-selector-hsx',
    'color-selector-hsl',
    'color-selector-hsv',
    'color-selector-oklch',
    'color-selector-named',
    'color-selector-hsluv',
    'color-selector-cms',
    'color-selector-cmyk',
    'color-selector-okhsl',
    'color-selector-rgb',
    'color-wheel',
    'out-of-gamut-icon',
}
# Those are illustrations rather than icons
IGNORE_ILLUSTRATIONS = {
    'feBlend-icon',
    'feColorMatrix-icon',
    'feComponentTransfer-icon',
    'feComposite-icon',
    'feConvolveMatrix-icon',
    'feDiffuseLighting-icon',
    'feDisplacementMap-icon',
    'feFlood-icon',
    'feGaussianBlur-icon',
    'feImage-icon',
    'feMerge-icon',
    'feMorphology-icon',
    'feOffset-icon',
    'feSpecularLighting-icon',
    'feTile-icon',
    'feTurbulence-icon',
}
# Those are UI elements in form of icons; themes may define them, but they shouldn't have to
IGNORE_UI = {
    'resizing-handle-horizontal',
    'resizing-handle-vertical',
}

NO_PROBLEM,\
BAD_SYMBOLIC_NAME,\
BAD_SCALABLE_NAME,\
MISSING_FROM,\
ONLY_FOUND_IN,\
SCALABLE_ONLY,\
SYMBOLIC_ONLY = range(7)

def icon_themes():
    for name in os.listdir(THEME_PATH):
        filename = os.path.join(THEME_PATH, name)
        if name in IGNORE_THEMES or not os.path.isdir(filename):
            continue
        yield name, filename

def theme_to_string(name, kind):
    return f"{name}-{kind}"

def find_errors_in(themes):
    errors = []
    warnings = []

    data = defaultdict(set)
    bad_symbolic = []
    bad_scalable = []
    all_symbolics = set()

    for name, path in themes:
        for root, dirs, files in os.walk(path):
            orig = root
            root = root[len(path)+1:]
            if '/' not in root:
                continue
            (kind, root) = root.split('/', 1)
            if kind not in ("symbolic", "scalable"):
                continue # Not testing cursors, maybe later.

            theme_name = (name, kind)
            if kind == "symbolic":
                all_symbolics.add(name)

            for fname in files:
                if not fname.endswith('.svg'):
                    continue

                if kind == "symbolic":
                    if not fname.endswith('-symbolic.svg'):
                        bad_symbolic.append(os.path.join(orig, fname))
                        continue
                    else:
                        # Make filenames consistant for comparison
                        fname = fname.replace('-symbolic.svg', '.svg')
                elif kind == "scalable" and fname.endswith('-symbolic.svg'):
                    bad_scalable.append(os.path.join(orig, fname))
                    continue

                if fname in IGNORE_ILLUSTRATIONS or fname in IGNORE_UI:
                    continue

                filename = os.path.join(root, fname)
                data[filename].add(theme_name)

    if bad_symbolic:
        errors.append((BAD_SYMBOLIC_NAME, bad_symbolic))
    if bad_scalable:
        errors.append((BAD_SCALABLE_NAME, bad_scalable))

    only_found_in = defaultdict(list)
    missing_from = defaultdict(list)
    warn_missing_from = defaultdict(list)
    symbolic_found = defaultdict(list)
    scalable_found = defaultdict(list)

    for filename in sorted(data):
        datum = data[filename]

        symbolics = set(name for (name, kind) in datum if kind == 'symbolic')
        scalables = set(name for (name, kind) in datum if kind == 'scalable')

        # Color icons should NEVER be in the symbolic sets
        short_name = filename.split("/")[-1].replace(".svg", "")
        if short_name in SCALABLE_ONLY_ICONS:
            for theme in symbolics:
                symbolic_found[theme].append(filename)
        if short_name in SYMBOLIC_ONLY_ICONS:
            for theme in scalables:
                scalable_found[theme].append(filename)

        # Ignore a bunch of hard coded things
        if short_name in (SCALABLE_ONLY_ICONS | SYMBOLIC_ONLY_ICONS | IGNORE_ILLUSTRATIONS | IGNORE_UI):
            continue

        # For every scalable, there must be a symbolic
        diff = scalables - symbolics
        if len(diff) > 0:
            for name in diff:
                missing_from[f"{name}-symbolic"].append(filename)
            continue

        # Icon present in all themes => no error
        if symbolics == all_symbolics:
            continue



===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/buildtools/media-check-keys.py =====

#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# Keys checker:
#
#  * Are there bad xml elements / parsing
#  * Does it contain non-key xml elements
#  * Does the keys file reference something unknown
#  * Does it repeat empty actions
#  * Are there keys formatted as verbs
#  * Are some of the keys missing
#  * Does it include the default xml
#
# Author: Martin Owens <doctormo@geek-2.com>
# Licensed under GPL version 2 or any later version, read the file "COPYING" for more information.

import fnmatch
import os
import sys

from collections import defaultdict

from lxml import etree

KEYS_PATH = os.path.join('.', 'share', 'keys')
DEFAULT = 'inkscape.xml'

IGNORE_MISSING_KEYS = ['org.']

class Keys:
    """Open and parse a keys xml file"""
    def __init__(self, filename):
        self.filename = filename
        self.mods = set()
        self.keys = set()
        self.olds = set()
        self.ticks = defaultdict(list)
        self.errors = False
        self.parse(etree.parse(filename))

    def parse(self, doc):
        """Parse the document into checkable concerns"""
        for child in doc.getroot().getchildren():
            try:
                if child.tag == "modifier":
                    name = child.attrib['action']
                    self.mods.add(name)
                    self.ticks[name].append(child.attrib.get('modifiers'))
                elif child.tag == "bind":
                    name = child.attrib['gaction']
                    self.keys.add(name)
                    self.ticks[name].append(child.attrib.get('keys'))
                    if 'key' in child.attrib or 'modifiers' in child.attrib:
                        self.olds.add(name)
                elif child.tag == "{http://www.w3.org/2001/XInclude}include":
                    self.parse_include(child.attrib['href'])
                elif isinstance(child.tag, str):
                    sys.stderr.write(f"Unrecognised tag in keys file {child.tag}\n")
                    self.errors = True
            except KeyError as err:
                sys.stderr.write(f"Missing attribute g/action in {self.filename}\n")
                self.errors = True

    def parse_include(self, file):
        """Parse in the linked file"""
        other = Keys(os.path.join(os.path.dirname(self.filename), file))
        self.mods = self.mods.union(other.mods)
        self.keys = self.keys.union(other.keys)

    @classmethod
    def others(cls):
        """Load all non default keys"""
        for name in os.listdir(KEYS_PATH):
            filename = os.path.join(KEYS_PATH, name)
            if name == DEFAULT:
                continue
            if not os.path.isfile(filename) or not filename.endswith('.xml'):
                continue
            yield name, cls(filename)

    @classmethod
    def default(cls):
        """Load default keys"""
        return cls(os.path.join(KEYS_PATH, DEFAULT))


if __name__ == '__main__':
    sys.stderr.write("\n\n==== CHECKING KEYBOARD FILES ====\n\n")
    data = defaultdict(set)
    names = set()

    errors = False
    that = Keys.default()


    for name, this in Keys.others():
        sys.stderr.write(f"Checking '{name}'\n")

        for old in this.olds:
            sys.stderr.write(f" ! Old formatted key binding {old}\n")

        add = []
        if '-' not in sys.argv:
            for key in this.keys ^ (that.keys & this.keys):
                sys.stderr.write(f" + Unknown extra key {key}\n")
                errors = True

            for mod in this.mods ^ (that.mods & this.mods):
                sys.stderr.write(f" + Unknown extra modifier {mod}\n")
                errors = True

            for tick, lst in this.ticks.items():
                if len(lst) > 1 and None in lst:
                    sys.stderr.write(f" * Multiple empty references to {tick}\n")

        if '+' not in sys.argv:
            for key in that.keys ^ (that.keys & this.keys):
                if [ig for ig in IGNORE_MISSING_KEYS if key.startswith(ig)]:
                    continue
                if '-' in sys.argv:
                    add.append(f"<bind gaction=\"{key}\" />")
                else:
                    sys.stderr.write(f" - Missing key {key}\n")
                errors = True

            for mod in that.mods ^ (that.mods & this.mods):
                if '-' in sys.argv:
                    add.append(f"<modifier action=\"{mod}\" />")
                else:
                    sys.stderr.write(f" - Missing modifier {mod}\n")
                errors = True

        for item in sorted(add):
            sys.stderr.write(f"  {item}\n")
        sys.stderr.write("\n")

    if errors:
        sys.exit(5)

# vi:sw=4:expandtab:


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/buildtools/media-check-ui.py =====

#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
# UI Policy consistancy
#
# Author: Martin Owens <doctormo@geek-2.com>
# Licensed under GPL version 2 or any later version, read the file "COPYING" for more information.

import fnmatch
import os
import sys

from glob import glob
from copy import deepcopy
from collections import defaultdict

from lxml import etree

UI_PATH = os.path.join(os.path.dirname(__file__), '..', 'share', 'ui')

class Glade:
    """Open and parse a glade/ui file"""
    def __init__(self, filename):
        self.filename = filename
        self.fn = os.path.basename(filename)
        self.objects = []
        self.chain = []

    def parse(self):
        """Parse the document into checkable concerns"""
        self.parse_child(etree.parse(self.filename).getroot())

    def parse_child(self, elem):
        template = {'class': None, 'properties': {}, 'id': "NOID"}
        if elem.tag == "object":
            name = elem.attrib['class']
            self.chain.append(deepcopy(template))
            self.chain[-1]['class'] = elem.attrib['class']
            self.chain[-1]['id'] = elem.attrib.get('id', None)
            self.objects.append(self.chain[-1])
        elif elem.tag == "property" and self.chain and self.chain[-1]:
            name = elem.attrib['name']
            if name in self.chain[-1]['properties']:
                self.chain[-1]['error'] = f"Duplicate property '{name}'"
            name = name.replace('-', '_')
            self.chain[-1]['properties'][name] = elem.text
            self.chain.append(None)
        else:
            self.chain.append(None)

        for child in elem.getchildren():
            self.parse_child(child)

        self.chain.pop()


class PolicyChecker:
    name = None
    search = None
    ignore = []
    errors = {
        'parse': ("Parser Error", "Found something unusual in the XML"),
    }

    def __init__(self):
        self._e = defaultdict(list)
        self.policies = [f for n, f in type(self).__dict__.items() if n.startswith("policy_")]

    def check(self):
        for file in glob(os.path.join(UI_PATH, self.search)):
            ui = Glade(file)
            if ui.fn in self.ignore:
                continue
            ui.parse()

            for obj in ui.objects:
                if 'error' in obj:
                    self.report(ui, 'parse', obj, obj['error'])
                self.repair_id(obj)
                for f in self.policies:
                    for err in f(self, obj['class'], **obj['properties']):
                        self.violation(ui, err, obj, f.__code__.co_varnames)
        return self.print_report()

    def repair_id(self, obj):
        if not obj['id']:
            obj['id'] = obj['properties'].get('action-name', None)
            if obj['id'] and 'action-target' in obj['properties']:
                obj['id'] = f"{obj['id']}{{{obj['properties']['action-target']}}}"

    def print_report(self):
        ret = 0
        sys.stderr.write(f"\n\n==== CHECKING {self.name} FILES ====\n\n")
        for code, instances in self._e.items():
            name, desc = self.errors[code]
            sys.stderr.write(f"\n == {name} ==\n\n  {desc}\n\n")
            for _id, props in instances:
                sys.stderr.write(f" * {_id}: {props}\n")
                ret += 1
        return ret

    def report(self, ui, key, obj, msg):
        self._e[key].append((f"{ui.fn}: {obj['class']}:{obj['id']}", msg))

    def violation(self, ui, key, obj, props):
        self.report(ui, key, obj, " ".join([p + "=" + obj['properties'].get(p, 'N/A') for p in props if p not in ('self', 'cls', 'props')]))
        

class PolicyCheckerToolbars(PolicyChecker):
    name = "TOOLBAR"
    search = "toolbar-*.ui"
    ignore = ['toolbar-tool-prefs.ui']
    errors = {
        'button-focus1': ("Button Takes Focus", "A toolbar button can have focus and will take that focus when clicked. Add focus-on-click=False to fix this."),
        'button-focus2': ("Button Refuses Focus", "A toolbar button is refusing focus, which makes it inaccessable to keyboard navigation. Remove focusable=False"),
        'entry-focus': ("Entry Refuses Focus", "A toolbar entry doesn't allow itself to be in focus, stopping text from being entered. Change focusable to True and focus-on-click to True (or remove them)"),
}

    def policy_01_entries(self, cls, focusable="True", focus_on_click="True", **props):
        # Policy 1. All Buttons should have focusable: False
        if cls in ("GtkButton", "GtkMenuButton", "GtkToggleButton", "GtkRadioButton"):
            if focusable == "False":
                yield 'button-focus2'
            elif focus_on_click != "False":
                yield 'button-focus1'

    def policy_02_entries(self, cls, focusable="True", focus_on_click="True", **props):
        # Policy 2. All Entries, SpinButtons should have focusable: True
        if cls in ("GtkEntry", "GtkSpinButton", "GtkComboBoxText"):
            if focus_on_click == "False" or focusable == "False":
                yield 'entry-focus'



if __name__ == '__main__':
    errors = 0
    errors += PolicyCheckerToolbars().check()

    if errors:
        sys.exit(-5)
    else:
        sys.stderr.write("COMPLETE, NO PROBLEMS FOUND\n")

# vi:sw=4:expandtab:


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/buildtools/msys2checkdeps.py =====

#!/usr/bin/env python
# ------------------------------------------------------------------------------------------------------------------
# list or check dependencies for binary distributions based on MSYS2 (requires the package mingw-w64-ntldd)
#
# run './msys2checkdeps.py --help' for usage information
# ------------------------------------------------------------------------------------------------------------------

from __future__ import print_function


import argparse
import os
import subprocess
import sys


SYSTEMROOT = os.environ['SYSTEMROOT']


class Dependency:
    def __init__(self):
        self.location = None
        self.dependents = set()


def warning(msg):
    print("Warning: " + msg, file=sys.stderr)


def error(msg):
    print("Error: " + msg, file=sys.stderr)
    exit(1)


def call_ntldd(filename):
    try:
        output = subprocess.check_output(['ntldd', '-R', filename], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        error("'ntldd' failed with '" + str(e) + "'")
    except WindowsError as e:
        error("Calling 'ntldd' failed with '" + str(e) + "' (have you installed 'mingw-w64-ntldd-git'?)")
    except Exception as e:
        error("Calling 'ntldd' failed with '" + str(e) + "'")
    return output.decode('utf-8')


def get_dependencies(filename, deps):
    raw_list = call_ntldd(filename)

    skip_indent = float('Inf')
    parents = {}
    parents[0] = os.path.basename(filename)
    for line in raw_list.splitlines():
        line = line[1:]
        indent = len(line) - len(line.lstrip())
        if indent > skip_indent:
            continue
        else:
            skip_indent = float('Inf')

        # if the dependency is not found in the working directory ntldd tries to find it on the search path
        # which is indicated by the string '=>' followed by the determined location or 'not found'
        if ('=>' in line):
            (lib, location) = line.lstrip().split(' => ')
            if lib == "OPENGL32.dll": #ignored since it's a system library but is absent from the CI (no display)
                skip_indent = indent
                continue
            elif location == 'not found':
                location = None
            else:
                location = location.rsplit('(', 1)[0].strip()
        else:
            lib = line.rsplit('(', 1)[0].strip()
            location = os.getcwd()

        parents[indent+1] = lib

        # we don't care about Microsoft libraries and their dependencies
        if location and SYSTEMROOT in location:
            skip_indent = indent
            continue

        if lib not in deps:
            deps[lib] = Dependency()
            deps[lib].location = location
        deps[lib].dependents.add(parents[indent])
    return deps


def collect_dependencies(path):
    # collect dependencies
    #   - each key in 'deps' will be the filename of a dependency
    #   - the corresponding value is an instance of class Dependency (containing full path and dependents)
    deps = {}
    if os.path.isfile(path):
        deps = get_dependencies(path, deps)
    elif os.path.isdir(path):
        extensions = ['.exe', '.pyd', '.dll']
        exclusions = ['distutils/command/wininst']  # python
        for base, dirs, files in os.walk(path):
            for f in files:
                filepath = os.path.join(base, f)
                (_, ext) = os.path.splitext(f)
                if (ext.lower() not in extensions) or any(exclusion in filepath for exclusion in exclusions):
                    continue
                deps = get_dependencies(filepath, deps)
    return deps


if __name__ == '__main__':
    modes = ['list', 'list-compact', 'check', 'check-missing', 'check-unused']

    # parse arguments from command line
    parser = argparse.ArgumentParser(description="List or check dependencies for binary distributions based on MSYS2.\n"
                                                 "(requires the package 'mingw-w64-ntldd')",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('mode', metavar="MODE", choices=modes,
                        help="One of the following:\n"
                             "  list          - list dependencies in human-readable form\n"
                             "                  with full path and list of dependents\n"
                             "  list-compact  - list dependencies in compact form (as a plain list of filenames)\n"
                             "  check         - check for missing or unused dependencies (see below for details)\n"
                             "  check-missing - check if all required dependencies are present in PATH\n"
                             "                  exits with error code 2 if missing dependencies are found\n"
                             "                  and prints the list to stderr\n"
                             "  check-unused  - check if any of the libraries in the root of PATH are unused\n"
                             "                  and prints the list to stderr")
    parser.add_argument('path', metavar='PATH',
                        help="full or relative path to a single file or a directory to work on\n"
                             "(directories will be checked recursively)")
    parser.add_argument('-w', '--working-directory', metavar="DIR",
                        help="Use custom working directory (instead of 'dirname PATH')")
    args = parser.parse_args()

    # check if path exists
    args.path = os.path.abspath(args.path)
    if not os.path.exists(args.path):
        error("Can't find file/folder '" + args.path + "'")

    # get root and set it as working directory (unless one is explicitly specified)
    if args.working_directory:
        root = os.path.abspath(args.working_directory)
    elif os.path.isdir(args.path):
        root = args.path
    elif os.path.isfile(args.path):
        root = os.path.dirname(args.path)
    os.chdir(root)

    # get dependencies for path recursively
    deps = collect_dependencies(args.path)

    # print output / prepare exit code
    exit_code = 0
    for dep in sorted(deps):
        location = deps[dep].location
        dependents = deps[dep].dependents

        if args.mode == 'list':
            if (location is None):
                location = '---MISSING---'
            print(dep + " - " + location + " (" + ", ".join(dependents) + ")")
        elif args.mode == 'list-compact':
            print(dep)
        elif args.mode in ['check', 'check-missing']:
            if ((location is None) or (root not in os.path.abspath(location))):
                warning("Missing dependency " + dep + " (" + ", ".join(dependents) + ")")
                exit_code = 2

    # check for unused libraries
    if args.mode in ['check', 'check-unused']:
        installed_libs = [file for file in os.listdir(root) if file.endswith(".dll")]
        deps_lower = [dep.lower() for dep in deps]
        top_level_libs = [lib for lib in installed_libs if lib.lower() not in deps_lower]
        for top_level_lib in top_level_libs:
            warning("Unused dependency " + top_level_lib)

    exit(exit_code)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/packaging/android/copylibs.py =====

#! /bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later

description = 'Recursively copy dependencies of a library or executable'

import os, subprocess, shutil, argparse
from elftools.elf.elffile import ELFFile

# Get the library search paths from pkg-config.
def get_pkgconfig_search_paths():
    out = subprocess.run('pkg-config --libs-only-L `pkg-config --list-package-names --env-only`', shell=True, check=True, capture_output=True).stdout
    return [x[2:] for x in out.decode('utf-8').split() if x.startswith('-L')]

# Find all libraries in the given search paths.
# Returns the result as a mapping from library names to full paths.
def find_libs(search_paths):
    libs = {}
    for search_path in search_paths:
        for path, dirs, files in os.walk(search_path):
            for f in files:
                if f.endswith('.so'):
                    libs[f] = os.path.join(path, f)
    return libs

# Given a library or executable, return the names of its library dependencies.
def get_imported_libs(path):
    with open(path, 'rb') as f:
        e = ELFFile(f)
        s = e.get_section_by_name('.dynamic')
        return [t.needed for t in s.iter_tags() if t.entry['d_tag'] == 'DT_NEEDED']

# Given a library or executable, recursively add the names of its library dependencies to imported_libs.
def get_imported_libs_recursive(path, all_libs, imported_libs):
    for lib in get_imported_libs(path):
        if lib in imported_libs: continue
        imported_libs.append(lib)
        loc = all_libs.get(lib)
        if loc != None:
            get_imported_libs_recursive(loc, all_libs, imported_libs)

def main():
    parser = argparse.ArgumentParser(prog='copylibs.py', description=description)
    parser.add_argument('-o', '--outputdir', metavar='DIR', help='Directory to copy the libraries to (default: don\'t copy, just list)')
    parser.add_argument('-s', '--search', metavar='DIR', default=[], action='append', help='Specify an additional library search path')
    parser.add_argument('-l', '--link', help='Create symlinks instead of copying', action='store_true')
    parser.add_argument('file', nargs='+', help='The input executable or library')
    args = parser.parse_args()

    # Find all libraries in the search paths.
    search_paths = get_pkgconfig_search_paths() + args.search
    all_libs = find_libs(search_paths)

    # Find all libraries needed by the input files.
    needed_libs = []
    for f in args.file:
        get_imported_libs_recursive(f, all_libs, needed_libs)

    # For each needed lib, find its actual location and copy/symlink to output directory, or report not found
    for lib in needed_libs:
        loc = all_libs.get(lib)
        print(lib, '->', loc)
        if loc != None and args.outputdir != None:
            if args.link:
                os.symlink(loc, os.path.join(args.outputdir, lib))
            else:
                shutil.copy(loc, args.outputdir)

if __name__ == "__main__":
    main()


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/packaging/android/genicons.py =====

#! /bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later

description = 'Generate android app icons from an SVG.'

import os, subprocess, argparse

data = (
    ('m', 48),
    ('h', 72),
    ('xh', 96),
    ('xxh', 144),
    ('xxxh', 192)
)

def generate(svg, outputdir, name):
    for sizecode, _ in data:
        try:
            os.mkdir(os.path.join(outputdir, f'mipmap-{sizecode}dpi'))
        except FileExistsError:
            pass

    subprocess.run([
        'inkscape',
        svg,
        '--batch-process',
        '--actions=' + '; '.join([f'export-filename:{os.path.join(outputdir, f'mipmap-{sizecode}dpi', f'{name}.png')}; export-width:{size}; export-do' for sizecode, size in data])
    ], check = True)

def main():
    parser = argparse.ArgumentParser(prog='genicons.py', description=description, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-o', '--outputdir', default='.', metavar='DIR', help='Directory to place the output')
    parser.add_argument('-n', '--name', default='ic_launcher', metavar='STRING', help='What to call the icon')
    parser.add_argument('svg', help='The input SVG file')
    args = parser.parse_args()
    
    generate(svg=args.svg, outputdir=args.outputdir, name=args.name)

if __name__ == "__main__":
    main()


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/share/filters/i18n.py =====

#!/usr/bin/env python3

from xml.dom import minidom
import sys

doc = minidom.parse(sys.argv[1])

filters = doc.getElementsByTagName('filter')

sys.stdout.write("char * stringlst = [")

for filter in filters:
    label = "N_(\"" + filter.getAttribute('inkscape:label') + "\")"
    menu = "N_(\"" + filter.getAttribute('inkscape:menu') + "\")"
    if (filter.getAttribute('inkscape:menu-tooltip')):
        desc = "N_(\"" + filter.getAttribute('inkscape:menu-tooltip') + "\")"
    else:
        desc = ""
    comment = ""

    if "NR" in label:
        comment = '/* TRANSLATORS: NR means non-realistic. See menu Filters > Non realistic shaders */\n'
    
    sys.stdout.write(comment + "\n" + label + ",\n" + menu + ",\n" + desc + ",\n")

sys.stdout.write("];")


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/share/filters/samplify.py =====

# This script produces a sample SVG demonstrating all filters in a filters file.
#
# It takes two inputs: the sample file with the object that will be cloned and filtered, and
# the file with filters (such as Inkscape's share/filters/filters.svg).
#
# Run it thus:
#
#    python3 samplify.py sample.svg filters.svg > out.svg
#
# It requires 'inkscape' in executable path for dimension queries.

import sys, os, string, subprocess
from lxml import etree

if len(sys.argv) < 3:
    sys.stderr.write ("Usage: python3 samplify.py sample.svg filters.svg > out.svg\n")
    sys.exit(1)

# namespaces we need to be aware of
NSS = {
u'sodipodi' :u'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd',
u'cc'       :u'http://web.resource.org/cc/',
u'svg'      :u'http://www.w3.org/2000/svg',
u'dc'       :u'http://purl.org/dc/elements/1.1/',
u'rdf'      :u'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
u'inkscape' :u'http://www.inkscape.org/namespaces/inkscape',
u'xlink'    :u'http://www.w3.org/1999/xlink',
u'xml'      :u'http://www.w3.org/XML/1998/namespace'
}

# helper function to add namespace URI to a name
def addNS(tag, ns=None):
    val = tag
    if ns!=None and len(ns)>0 and ns in NSS and len(tag)>0 and tag[0]!='{':
        val = "{%s}%s" % (NSS[ns], tag)
    return val

# attributes and elements we will use, prepared with their namespace
a_href = addNS('href', 'xlink')
a_menu = addNS('menu', 'inkscape')
a_tooltip = addNS('menu-tooltip', 'inkscape')
a_label = addNS('label', 'inkscape')
e_text = addNS('text', 'svg')
e_tspan = addNS('tspan', 'svg')
e_flowRoot = addNS('flowRoot', 'svg')
e_flowPara = addNS('flowPara', 'svg')
e_flowSpan = addNS('flowSpan', 'svg')
e_g = addNS('g', 'svg')
e_use = addNS('use', 'svg')
e_defs = addNS('defs', 'svg')
e_filter = addNS('filter', 'svg')
e_rect = addNS('rect', 'svg')
e_svg = addNS('svg', 'svg')
e_switch = addNS('switch', 'svg')


tstream = open(sys.argv[1], 'rb')
tdoc = etree.parse(tstream)

fstream = open(sys.argv[2], 'rb')
fdoc = etree.parse(fstream)

menus = []

for defs in fdoc.getroot().getchildren():
    for fi in defs.getchildren():
        if fi.tag == e_filter and fi.attrib[a_menu] not in menus:
            menus.append(fi.attrib[a_menu])

menu_shifts = {}
for m in menus:
    menu_shifts[m] = 0

menus.sort()

#print menus

def copy_element (a):
    b = etree.Element(a.tag, nsmap=NSS)
    for i in a.items():
        b.set(i[0], i[1])
    b.text = a.text
    b.tail = a.tail
    return b

#query inkscape about the bounding box of obj
q = {'x':0,'y':0,'width':0,'height':0}
file = sys.argv[1]
id = tdoc.getroot().attrib["id"]
for query in q.keys():
    f = subprocess.Popen(["inkscape", "--query-%s"%query, "--query-id=%s"%id, "%s"%file], stdout=subprocess.PIPE)
    q[query] = float(f.stdout.read())

# add some margins
q['width'] = q['width'] * 1.3
q['height'] = q['height'] * 1.3

#print q    

root = tdoc.getroot()
tout = etree.ElementTree(copy_element(root))
newroot = tout.getroot()
for ch in root.getchildren():
    chcopy = ch.__deepcopy__(-1)
    newroot.append(chcopy)
    if ch.tag == e_defs:
        for defs in fdoc.getroot().getchildren():
            for fi in defs.getchildren():
                ficopy = fi.__deepcopy__(-1)
                newroot.getchildren()[-1].append(ficopy)
    if ch.tag == e_g:
        newroot.getchildren()[-1].attrib["id"] = "original"
        for menu in menus:
            text = etree.Element(e_text, nsmap=NSS)
            text.attrib['x']=str(q['x'] - q['width'] * 0.2)
            text.attrib['y']=str( q['y'] + q['height'] * (menus.index(menu) + 1.4) )
            text.attrib['style']="font-size:%d;text-anchor:end;" % (q['height']*0.2)
            text.text = menu
            newroot.append(text)
        for defs in fdoc.getroot().getchildren():
            for fi in defs.getchildren():
                if fi.tag != e_filter:
                    continue
                clone = etree.Element(e_use, nsmap=NSS)
                clone.attrib[a_href]='#original'
                clone.attrib["style"]='filter:url(#'+fi.attrib["id"]+')'
                menu = fi.attrib[a_menu]
                clone.attrib["transform"] = 'translate('+str( q['width'] * menu_shifts[menu] )+', '+str( q['height'] * (menus.index(menu) + 1) )+')'
                newroot.append(clone)

                text = etree.Element(e_text, nsmap=NSS)
                text.attrib['x']=str( q['x'] + q['width'] * (menu_shifts[menu] + 0.5) )
                text.attrib['y']=str( q['y'] + q['height'] * (menus.index(menu) + 1.86) )
                text.attrib['style']="font-size:%d;text-anchor:middle;" % (q['height']*0.08)
                text.text = fi.attrib[a_label]
                newroot.append(text)

                if a_tooltip not in fi.keys():
                    print("no menu-tooltip for", fi.attrib["id"])
                    sys.exit()

                text = etree.Element(e_text, nsmap=NSS)
                text.attrib['x']=str( q['x'] + q['width'] * (menu_shifts[menu] + 0.5) )
                text.attrib['y']=str( q['y'] + q['height'] * (menus.index(menu) + 1.92) )
                text.attrib['style']="font-size:%d;text-anchor:middle;" % (q['height']*0.04)
                text.text = fi.attrib[a_tooltip]
                newroot.append(text)

                menu_shifts[menu] = menu_shifts[menu] + 1
        break

total_width = max(menu_shifts.values()) * q['width']    
total_height = (len(menus) + 1) * q['height']
tout.getroot().attrib['width'] = str(total_width)
tout.getroot().attrib['height'] = str(total_height)

print(etree.tostring(tout, encoding='UTF-8'))



===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/share/markers/i18n.py =====

#!/usr/bin/env python3

from xml.dom import minidom
import sys

doc = minidom.parse(sys.argv[1])
markers = doc.getElementsByTagName('marker')

stockids = []
for m in markers:
    stockids.append("N_(\"" + m.getAttribute('inkscape:stockid') + "\")")

sys.stdout.write("const char **stringlst = {\n    " + ",\n    ".join(stockids) + "\n};\n")



===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/share/paint/i18n.py =====

#!/usr/bin/env python3

from xml.dom import minidom
import sys


sys.stdout.write("char * stringlst = [")

for rawdoc in sys.argv[1:]:
    doc = minidom.parse(rawdoc)

    for title in doc.getElementsByTagName('title'):
        ret = ""
        for child in title.childNodes:
            if child.nodeType == child.TEXT_NODE:
                ret += child.data
        if ret:
            ret = ret.replace("\n", "").replace("\"", "'")
            sys.stdout.write("N_(\"" + ret + "\"),")

    for filter in doc.getElementsByTagName('pattern'):
        stockid = filter.getAttribute('inkscape:stockid')
        if stockid == "":
            stockid = filter.getAttribute('inkscape:label')
        if stockid != "":
            sys.stdout.write("N_(\"" + stockid + "\"),")

sys.stdout.write("];")


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/share/palettes/PaletteGen.py =====

import colorsys

print '''GIMP Palette
Name: Inkscape default
Columns: 3
# generated by PaletteGen.py'''


# grays

g_steps = 10
g_step_size = 1.0 / g_steps

for i in range(0, g_steps + 1):
    level = i * g_step_size
    r, g, b = colorsys.hls_to_rgb(0, level, 0)
    
    rval = int(round(r * 255))
    gval = int(round(g * 255))
    bval = int(round(b * 255))
    
    if i == 0:
        line = "%3s %3s %3s  Black" % (rval, gval, bval)
    elif i == g_steps:
        line = "%3s %3s %3s  White" % (rval, gval, bval)
    else:
        line = "%3s %3s %3s  %s%% Gray" % (rval, gval, bval, 100 - int(level * 100))
    print line

    # add three more steps near white
    if i == g_steps - 1:
        level_m = level + 0.25 * g_step_size
        r, g, b = colorsys.hls_to_rgb(0, level_m, 0)
        rval = int(round(r * 255))
        gval = int(round(g * 255))
        bval = int(round(b * 255))
        print "%3s %3s %3s  %s%% Gray" % (rval, gval, bval, 100 - (level_m * 100))

        level_m = level + 0.5 * g_step_size
        r, g, b = colorsys.hls_to_rgb(0, level_m, 0)
        rval = int(round(r * 255))
        gval = int(round(g * 255))
        bval = int(round(b * 255))
        print "%3s %3s %3s  %s%% Gray" % (rval, gval, bval, 100 - int(level_m * 100))

        level_mm = level + 0.75 * g_step_size
        r, g, b = colorsys.hls_to_rgb(0, level_mm, 0)
        rval = int(round(r * 255))
        gval = int(round(g * 255))
        bval = int(round(b * 255))
        print "%3s %3s %3s  %s%% Gray" % (rval, gval, bval, 100 - (level_mm * 100))


# standard HTML colors
print '''128   0   0  Maroon (#800000)
255   0   0  Red (#FF0000)
128 128   0  Olive (#808000)
255 255   0  Yellow (#FFFF00)
  0 128   0  Green (#008000)
  0 255   0  Lime (#00FF00)
  0 128 128  Teal (#008080)
  0 255 255  Aqua (#00FFFF)
  0   0 128  Navy (#000080)
  0   0 255  Blue (#0000FF)
128   0 128  Purple (#800080)
255   0 255  Fuchsia (#FF00FF)'''

# HSL palette
h_steps = 15
s_steps = 3
l_steps = 14
h_step_size = 1.0 / h_steps
s_step_size = 1.3 / s_steps

for h in range(0, h_steps):
    for s in range(0, s_steps):
        l_range = int(round(l_steps - (s*6/s_steps))) - 2
        l_step_size = 1.0 / l_range
        for l in range(1, l_range):
            hval = h * h_step_size
            sval = 1 - (s * s_step_size)
            lval = l * l_step_size
            
            r, g, b = colorsys.hls_to_rgb(hval, lval, sval)
            
            rval = int(round(r * 255))
            gval = int(round(g * 255))
            bval = int(round(b * 255))
            
            line = "%3s %3s %3s  #%02X%02X%02X" % (rval, gval, bval, rval, gval, bval)
            print line


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/share/palettes/i18n.py =====

#!/usr/bin/env python3

import sys
import glob
import re

sys.stdout.write("char * stringlst = [")

# Gimp palette format: R   G   B  Label (255   0   0  Red)

regex = re.compile(r'^\s*\d{1,3}\s+\d{1,3}\s+\d{1,3}\s+([^#\s].*)')
regexnoc = re.compile(r'%')

for filename in sys.argv[1:]:
    file = open (filename, 'r')
    for line in file:
        match = regex.match(line)
        if match:
            sys.stdout.write('\n/* Palette: ' + filename + ' */')
            search = regexnoc.search(match.group(1))
            if search:
                sys.stdout.write("/* xgettext:no-c-format */")
            sys.stdout.write("NC_(\"Palette\", \"" + match.group(1) + "\"),")

sys.stdout.write("];")


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/share/palettes/soc2gpl.py =====

#!/usr/bin/env python3
#
# Copyright 2018 (c) Martin Owens
#
"""
Convert LibreOffice SOC Palette into a GIMP Palette file
"""

import os
import sys
import logging

from argparse import ArgumentParser

import lxml.etree

def write_palette(nom, filename, colors):
    """Write colours to a GIMP palette format"""
    print('''GIMP Palette
Name: {name}
Columns: 3
# generated by {prog}
# original file {filename}'''.format(name=nom, filename=filename, prog=sys.argv[0]))
    for color_name, color in colors:
        print("{red: >3} {green: >3} {blue: >3}\t{name}".format(red=color[0], green=color[1], blue=color[2], name=color_name))

def process_soc(filename):
    """Generator that returns each colour as a tuple of colours and names"""
    with open(filename, 'r') as fhl:
        doc = lxml.etree.parse(fhl)
        root = doc.getroot()
    for color in root:
        attr = dict([(attr.split('}')[-1], value) for attr, value in color.attrib.items()])
        if 'name' in attr and 'color' in attr:
            color = attr['color']
            color = (int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))
            yield (attr['name'], color)

def main():
    """Main"""
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('-n', '--name', help='Name of the palette', default=None)
    parser.add_argument('socfile', help='The soc file to convert')
    arg = parser.parse_args()

    if not os.path.isfile(arg.socfile):
        logging.error("Cannot find file %s", arg.socfile)
        sys.exit(1)

    if arg.name:
        name = arg.name
    else:
        name = os.path.basename(arg.socfile).rsplit('.')[0]

    write_palette(name, arg.socfile, process_soc(arg.socfile))

if __name__ == '__main__':
    main()


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/share/symbols/i18n.py =====

#!/usr/bin/env python3

from xml.dom import minidom
import sys

sys.stdout.write("char * stringlst = [")

for filename in sys.argv[1:]:
    doc = minidom.parse(filename)
    symbols = doc.getElementsByTagName('title')
    
    if symbols:
        for symbol in symbols:
            sys.stdout.write("\n/* Symbols: " + filename + " */  NC_(\"Symbol\", \"" + symbol.firstChild.nodeValue + "\"),")

sys.stdout.write("];")


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/share/templates/create_default_templates.py =====

#!/usr/bin/env python3
#
# Creates localized default templates
# (uses default.svg as base and reads localized strings directly from .po/.gmo files)
#

from __future__ import print_function
from __future__ import unicode_literals  # make all literals unicode strings by default (even in Python 2)

import gettext
import glob
import os
import shutil
import sys
from io import open  # needed for support of encoding parameter in Python 2


LAYER_STRING = 'Layer'


if len(sys.argv) != 3:
    sys.exit("Usage:\n  %s ${CMAKE_SOURCE_DIR} ${CMAKE_BINARY_DIR}" % sys.argv[0])

source_dir = sys.argv[1]
binary_dir = sys.argv[2]


# get available languages (should match the already created .gmo files)
gmofiles = glob.glob(binary_dir + '/po/*.gmo')

languages = gmofiles
languages = [os.path.basename(language) for language in languages]  # split filename from path
languages = [os.path.splitext(language)[0] for language in languages]  # split extension


# process each language sequentially
for language in languages:
    # copy .gmo file into a location where gettext can find and use it
    source = binary_dir + '/po/' + language + '.gmo'
    destination_dir = binary_dir + '/po/locale/' + language + '/LC_MESSAGES/'
    destination = destination_dir + 'inkscape.mo'

    if not os.path.isdir(destination_dir):
        os.makedirs(destination_dir)
    shutil.copy(source, destination)

# do another loop to ensure we've copied all the translations before using them
for language in languages:
    # get translation with help of gettext
    translation = gettext.translation('inkscape', localedir=binary_dir + '/po/locale', languages=[language])
    translated_string = translation.gettext(LAYER_STRING)

    if type(translated_string) != type(LAYER_STRING):  # python2 compat (make sure translation is a Unicode string)
        translated_string = translated_string.decode('utf-8')

    # now create localized version of English template file (if we have a translation)
    template_file = source_dir + '/share/templates/default.svg'
    output_file = binary_dir + '/share/templates/default.' + language + '.svg'

    if os.path.isfile(output_file):
        os.remove(output_file)
    if translated_string != LAYER_STRING:
        with open(template_file, 'r', encoding='utf-8', newline='\n') as file:
            filedata = file.read()
        filedata = filedata.replace('Layer', translated_string)
        with open(output_file, 'w', encoding='utf-8', newline='\n') as file:
            file.write(filedata)


# create timestamp file (indicates last successful creation for build system)
timestamp_file = binary_dir + '/share/templates/default_templates.timestamp'
if os.path.exists(timestamp_file):
    os.utime(timestamp_file, None)
else:
    open(timestamp_file, 'a').close()


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/share/templates/i18n.py =====

#!/usr/bin/env python3

from xml.dom import minidom
import sys

elements = ["inkscape:_name", "inkscape:_shortdesc", "inkscape:_keywords", "inkscape:category", "inkscape:label"]

sys.stdout.write("char * stringlst = [")

for filename in sys.argv[1:]:
    doc = minidom.parse(filename)
    templates = doc.getElementsByTagName('inkscape:_templateinfo')
    
    if templates:
        for element in elements:
            lines = templates[0].getElementsByTagName(element)
            if lines:
                sys.stdout.write("N_(\"" + lines[0].firstChild.nodeValue + "\"),")

sys.stdout.write("];")


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/testfiles/cli_tests/get-pages.py =====

#!/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
#
# Author: Martin Owens
# Copyright: 2025
#
"""
Parse an SVG file for it's inkscape paages and output page numbers in stderr 
and the page labels in stdout. This is used by CMake to contruct tests.
"""

import os
import sys

def main(filename):
    if not os.path.isfile(filename):
        sys.stderr.write(f"Can't find file: '{filename}'")
        sys.exit(1)
    parse = None
    with open(filename, 'r') as fhl:
        for line in fhl:
            if "<defs" in line:
                parse = ""
            if parse is not None:
                parse += line
            if "</defs>" in line:
                break
    if not parse:
        return

    parse = parse.replace("\n", "").replace(">", "\n").split("<view")

    labels = []
    for i, page in enumerate(parse[1:]):
        attrs = dict([tuple(a.replace("\"", "").strip().split("=", 1)) for a in page.split("\" ") if "=" in a])
        label = attrs.get("inkscape:label", attrs.get("label", f"badpage{i+1}"))
        label = label.encode('ascii', 'replace').decode("ascii").lower()
        label = label.strip().replace(" ", "-").replace("_", "-").replace(";", "-")
        if label in labels or not label:
            label = f"badpage{i+1}"
        labels.append(label)

    if not labels:
        labels = ["page0"]

    sys.stderr.write(";".join([str(i) for i in range(len(labels))]))
    sys.stdout.write(";".join(labels))

if __name__ == "__main__":
    for f in sys.argv[1:]:
        main(f)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/testfiles/cli_tests/testcases/regression-1364_script.py =====

from lxml import etree

def d_cmp(orig, new):
    """ Compares the original d attribute to the new one. """
    orig_list = orig.split()
    new_list = new.split()

    if len(orig_list) != len(new_list):
        return False

    # Normalize the final 'z' to uppercase:
    orig_list[-1] = orig_list[-1].upper()
    new_list[-1] = new_list[-1].upper()

    for (o, n) in zip(orig_list, new_list):
        if o == n:
            continue
        numeric = "{:.0f}".format(float(n))
        if o != numeric:
            return False

    return True

document = etree.parse("regression-1364_output.svg")
layer = document.find('{http://www.w3.org/2000/svg}g[@id="layer1"]')
boolop_result = layer.find('{http://www.w3.org/2000/svg}path[@id="small"]')

assert boolop_result.attrib.get("transform") == "scale(2)"

assert d_cmp("M 0 0 L 0 50 A 50 50 0 0 0 50 0 L 0 0 z", boolop_result.attrib.get("d"))



===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/testfiles/cli_tests/testcases/regression-2602_script.py =====

from lxml import etree

document = etree.parse("regression-2602_output.svg")

parent = document.find('{http://www.w3.org/2000/svg}g[@id="parent"]')
paths = parent.findall('{http://www.w3.org/2000/svg}path')

assert parent.attrib.get("style") == "fill:#0000ff"
assert paths[0].attrib.get("style") == "fill:#ff0000"
assert paths[1].attrib.get("style") is None


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/testfiles/cli_tests/testcases/regression-2797_script.py =====

from lxml import etree

document = etree.parse("regression-2797_output.svg")

parent = document.find('{http://www.w3.org/2000/svg}text[@id="parent"]')
tspan1, = parent.findall('{http://www.w3.org/2000/svg}tspan')
tspan2s = tspan1.findall('{http://www.w3.org/2000/svg}tspan')

# Expect outer tspan added as SVG 1.1 fallback with x/y position.
# Expect no inner tspan with incorrect "font-size:medium".

assert len(tspan2s) == 0

assert parent.attrib.get("style") == "font-size:4px;shape-inside:url(#theshape)"
assert tspan1.attrib.get("style") is None
assert tspan1.attrib.get("x") == "2"
assert tspan1.attrib.get("y") is not None


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/testfiles/rendering_tests/svginotf/build.py =====

# SPDX-License-Identifier: GPL-2.0-or-later

#  Requirements and build instructions
# setup venv (consult with python docs for non Linux OS):
#
# python -m venv venv
# source ./venv/bin/activate
# pip install fonttools defcon ufo2ft ufoLib2

# glyph indexes/order in config and ids in SVG files are important

import defcon
import fontTools
import ufo2ft
import fontTools.svgLib.path
from fontTools.ttLib import newTable
from pathlib import Path
from fontTools.ttLib.tables.S_V_G_ import SVGDocument

OUTPUT = "svginotf_testfont1.otf"
EM_SIZE = 1000

ufo_font = defcon.Font()
ufo_font.info.unitPerEm = EM_SIZE
ufo_font.info.familyName = "SVGinOTF testfont1"
ufo_font.info.xHeight = 500
ufo_font.info.capHeight = 800
ufo_font.info.ascender = 1000
ufo_font.info.descender = -200

DEFAULT_WIDTH = 500

FALLBACK_BOX = 'M 0,0 L 0,800 800,800 800,0 z'
glyphs = [
    # somewhat normal
    {'unicode': 0x61, 'name': 'a', 'svg': 'glyphs/a.svg'},
    # tall
    {'unicode': 0x62, 'name': 'b',
     'fallback_shape': 'M 0,-1400 L 0,2331 500,2331 500,-1400 z',
     'width': 502,
     'svg': 'glyphs/b.svg'},
    # wide
    {'unicode': 0x63, 'name': 'c',
     'fallback_shape': 'M -1276,0 L -1276,920 1750,920 500,0 z',
     'svg': 'glyphs/c.svg'},
    # viewport offset
    {'unicode': 0x64, 'name': 'd',
     'fallback_shape': 'M 0,0 L 0,800 500,800 500,0 z',
     'svg': 'glyphs/d.svg'},
]

for info in glyphs:
    glyph = ufo_font.newGlyph(info['name'])
    glyph.unicodes = [info['unicode']]
    glyph.width = info.get('width', DEFAULT_WIDTH)
    pen = glyph.getPen()
    non_color_shape = info.get('fallback_shape', FALLBACK_BOX)
    fontTools.svgLib.parse_path(non_color_shape, pen)

otf = ufo2ft.compileOTF(ufo_font)
svg_table = newTable("SVG ")
svg_table.docList = []
glyph_order = otf.getGlyphOrder()
print(glyph_order)
index_map = {name: i for i, name in enumerate(glyph_order)}
for info in glyphs:
    svg_file_path = info.get('svg', None)
    if not svg_file_path:
        continue
    group_range = info.get('group', None)
    svg_text = Path(svg_file_path).read_text()
    gid = index_map[info['name']]
    gid_min = gid
    gid_max = gid

    if group_range:
        gid_min = group_range[0]
        gid_max = group_range[1]

    svg_table.docList.append(SVGDocument(svg_text, gid_min, gid_max, info.get('compressed', True)))
svg_table.docList.sort(key=lambda x: x.startGlyphID)
otf[svg_table.tableTag] = svg_table
otf.save(OUTPUT)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/doc/vscode/c_cpp_properties.json =====

{
    "configurations": [
        {
            "name": "Win32",
            "compileCommands": "${workspaceFolder}/build/compile_commands.json",
            // compile_commands.json overrides these next two settings.
            "compilerPath": "C:/msys64/ucrt64/bin/g++.exe",
            "cppStandard": "c++20",
            "intelliSenseMode": "windows-gcc-x64",
            "browse": {
                "path": ["${workspaceFolder}/**"],
                "limitSymbolsToIncludedHeaders": true
            }
        }
    ],
    "version": 4
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/doc/vscode/launch.json =====

{
    // Use IntelliSense to learn about possible attributes.
    // Hover to view descriptions of existing attributes.
    // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
    "version": "0.2.0",
    "configurations": [
        {
            "name": "(gdb) Launch",
            "type": "cppdbg",
            "request": "launch",
            "preLaunchTask": "Ninja Install",
            // The .com file is necessary to get command line output to GDB. https://gitlab.com/inkscape/inbox/-/issues/4495
            "program": "${workspaceFolder}/build/install_dir/bin/inkscape.com",
            "cwd": "${workspaceFolder}",
            // Fails if false unless terminal.integrated.automationProfile.windows is PS or cmd,
            // or if it's absent and terminal.integrated.defaultProfile.windows is one of those.
            // Those can be set in the user settings.json, in a workspace file, or in .vscode/settings.json.
            "externalConsole": false,
            "MIMode": "gdb",
            "miDebuggerPath": "C:/msys64/ucrt64/bin/gdb.exe",
            "filterStdout": true,
            "filterStderr": false
        }
    ]
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/doc/vscode/tasks.json =====

{
    // See https://go.microsoft.com/fwlink/?LinkId=733558
    // for the documentation about the tasks.json format
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Ninja Install",
            "type": "shell",
            "command": "cd \"${workspaceFolder}\" && ninja -C build install",
            "options": {
                "shell": {
                    "executable": "C:\\msys64\\usr\\bin\\bash.exe",
                    "args": ["-lc"]
                },
                "env": {
                    "MSYSTEM": "UCRT64",
                    "CHERE_INVOKING": "1"
                }
            },
            "group": {
                "kind": "build",
                "isDefault": true
            },
            "problemMatcher": []
        },
        {
            "label": "CMake",
            "type": "shell",
            "command": "cd \"${workspaceFolder}/build\" && cmake -DCMAKE_INSTALL_PREFIX=\"${workspaceFolder}/build/install_dir\" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_BUILD_TYPE=Debug -DWITH_INTERNAL_2GEOM=ON -DBUILD_SHARED_LIBS=OFF -G Ninja ..",
            "options": {
                "shell": {
                    "executable": "C:\\msys64\\usr\\bin\\bash.exe",
                    "args": ["-lc"]
                },
                "env": {
                    "MSYSTEM": "UCRT64",
                    "CHERE_INVOKING": "1"
                }
            },
            "group": {
                "kind": "build",
                "isDefault": false
            },
            "problemMatcher": []
        }
    ]
}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/.gitlab-ci.yml =====

# Dependencies are managed in the Dockerfile in the inkscape-ci-docker
# Git repository. Change them there, wait a bit, and then we'll use
# the new ones here in these builds.
image: registry.gitlab.com/inkscape/inkscape-ci-docker/master


# This file is structured in four parts:
# I) definitions
# II) build jobs
# III) checks that are run on merge requests
# IV) building inkscape.gitlab.io/inkscape (doc and scan)
#


#######################
#                     #
#     Definitions     #
#                     #
#######################

# all jobs are safe to interrupt
default:
  interruptible: true
  artifacts:
    name: "$CI_JOB_NAME-$CI_COMMIT_REF_NAME"
  timeout: 3h


#speedup git on runners
variables:
  GIT_DEPTH: "50"
  GIT_SUBMODULE_STRATEGY: recursive

#reusable templates
.ccache_init: &ccache_init
  before_script:
    - mkdir -p ccache
    - export CCACHE_BASEDIR=${PWD}
    - export CCACHE_DIR=${PWD}/ccache

# basic workflow setup:
# - run pipelines for all branches without an open MR
# - run MR pipeline only as soon as an MR is opened
workflow:
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS'
      when: never
    - if: '$CI_COMMIT_BRANCH'

.run_MR: &run_for_MR
  if: '$CI_MERGE_REQUEST_ID'

.run_no_MR: &do_not_run_for_MR
  if: '$CI_MERGE_REQUEST_ID'
  when: never

.run_no_schedules: &do_not_run_for_schedules
  if: '$CI_PIPELINE_SOURCE == "schedule"'
  when: never

.run_otherwise: &run_otherwise
  when: on_success


#######################
#                     #
#  Building inkscape  #
#                     #
#######################
# Linux, Appimage, macOS, Windows.


inkscape:linux:
  stage: build
  timeout: 3h
  rules:
    - *do_not_run_for_schedules
    - *run_otherwise
  cache:
    key: "cache-linux"
    paths:
      - ccache/
  <<: *ccache_init
  script:
    - mkdir build
    - cd build
    - cmake .. -GNinja -DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX:PATH=/usr
    - ninja all tests
  artifacts:
    expire_in: 1 year
    paths:
      - build/


appimage:linux:
  stage: build
  timeout: 3h
  rules:
    - *do_not_run_for_schedules
    - *run_otherwise
  needs: ["inkscape:linux"]
  script:
    - bash -ex packaging/appimage/generate.sh
  artifacts:
    expire_in: 1 year
    paths:
      - Inkscape*.AppImage


.macos:
  stage: build
  rules:
    - *do_not_run_for_schedules
    # Create macOS jobs only for the "inkscape" namespace as the runner is
    # restricted to that group. ("dehesselle" namespace has its own runner)
    - if: $CI_PROJECT_NAMESPACE != "inkscape" && $CI_PROJECT_NAMESPACE != "dehesselle"
      when: never
    - *run_otherwise
  cache:
    - key: ccache-$CI_JOB_NAME_SLUG-$CI_COMMIT_REF_SLUG
      fallback_keys:
        - ccache-$CI_JOB_NAME_SLUG-master
      paths:
        - ccache
  tags:
    - macos
    - arm64
  variables:
    CCACHE_DIR: $CI_PROJECT_DIR/ccache
    # ICM = inkscape ci macos
    # https://gitlab.com/inkscape/infra/inkscape-ci-macos
    ICM_REPO_REF: c722fc920cecc5c348fbf20f44ada169661412a0
    ICM_REPO_URL: https://gitlab.com/inkscape/infra/inkscape-ci-macos.git
    # build number
    INK_BUILD: $CI_PIPELINE_IID
    # build host
    ORKA_RUNNER: sequoia-4
    # package registry to upload dependencies
    PACKAGE_REGISTRY_URL: $CI_API_V4_URL/projects/$CI_PROJECT_ID/packages/generic
    PACKAGE_URL_PREFIX: ${PACKAGE_REGISTRY_URL}/icm/${ICM_REPO_REF}
    # directory and SDK settings for ICM
    REP_DIR: $CI_PROJECT_DIR
    WRK_DIR: /Users/Shared/work
  before_script:
    # Clone the repo containing all the build scripts.
    - |
      git clone $ICM_REPO_URL icm
      git -C icm checkout $ICM_REPO_REF
      git -C icm submodule update --init --recursive


deps:macos:
  extends: .macos
  variables:
    CCACHE_MAXSIZE: "500Mi"
    SDKROOT: /opt/sdks/MacOSX11.3.sdk
  script:
    # Build dependencies and upload to the package registry.
    - |
      VER_DIR=$(icm/jhb/usr/bin/config get VER_DIR)
      PACKAGE_URL=${PACKAGE_URL_PREFIX}/$(basename $VER_DIR)_$(uname -m).dmg
      if curl --max-filesize 1M -H "JOB-TOKEN: $CI_JOB_TOKEN" -sLO $PACKAGE_URL 2>/dev/null; then
        # rc=0 as GitLab returns a 404 page
        icm/110-bootstrap_jhb.sh
        icm/120-build_gtk4.sh
        icm/130-build_inkdeps.sh
        rm $VER_DIR/var/cache/pkg/.skip
        icm/jhb/usr/bin/jhb run rustup self uninstall -y || true
        icm/jhb/usr/bin/archive remove_nonessentials
        icm/jhb/usr/bin/archive create_dmg
        curl --fail-with-body -H "JOB-TOKEN: $CI_JOB_TOKEN" --upload-file $(basename $PACKAGE_URL) $PACKAGE_URL
        rm -rf ${VER_DIR:?}
      else
        # rc=56 because the artifact size exceeds the specified max-filesize
        echo "Found dependencies in package registry."
      fi


inkscape:macos:


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/snap/snapcraft.yaml =====

# SPDX-License-Identifier: GPL-2.0-or-later
name: inkscape
adopt-info: inkscape
contact: https://inkscape.org/contribute
license: GPL-3.0
confinement: strict
base: core24
compression: lzo

# ----
# hacks to make `evince` work for the print preview
layout:
  /usr/lib/$CRAFT_ARCH_TRIPLET_BUILD_FOR/evince/4/backends:
    bind: $SNAP/usr/lib/$CRAFT_ARCH_TRIPLET_BUILD_FOR/evince/4/backends
  /usr/lib/$CRAFT_ARCH_TRIPLET_BUILD_FOR/glib-2.0:
    bind: $SNAP/usr/lib/$CRAFT_ARCH_TRIPLET_BUILD_FOR/glib-2.0
# ----

plugs:
  dot-config-inkscape:
    interface: personal-files
    write: [ $HOME/.config/inkscape ]
  gtk-3-themes:
    interface: content
    target: $SNAP/data-dir/themes
    default-provider: gtk-common-themes
  icon-themes:
    interface: content
    target: $SNAP/data-dir/icons
    default-provider: gtk-common-themes
# ----
# hack needed to ensure that the "cups" slot is available on the host, see https://snapcraft.io/docs/cups-interface
  foo-install-cups:
    interface: content
    content: foo
    default-provider: cups
    target: $SNAP_DATA/foo
# ----

slots:
  inkscape-dbus:
    interface: dbus
    bus: session
    name: org.inkscape.Inkscape

# commented out due to bug https://github.com/canonical/snapcraft/issues/4931
# will be added automatically by snapcraft anyway
# assumes: [ command-chain ]

parts:
  inkscape:
    plugin: cmake
    source: .
    cmake-generator: Ninja
    cmake-parameters:
      - '-DCMAKE_INSTALL_PREFIX='
    build-packages:
#       NOTE: Most dependencies are already provided by "extension: gnome" (see later).
      - cython3
      - libart-2.0-dev
      - libboost-all-dev
      - libcdr-dev
      - libdouble-conversion-dev
      - libgc-dev
      - libgsl-dev
      - libgtest-dev
      - libmagick++-dev
      - libpoppler-glib-dev
      - libpoppler-private-dev
      - libpotrace-dev
      - librevenge-dev
      - libreadline-dev
      - libspelling-1-dev
      - libvisio-dev
      - libwpg-dev
      - libxml-parser-perl
      - libxslt1-dev
      - ragel
      - libgmock-dev
    stage-packages:
#       NOTE: Most dependencies are already provided by "extension: gnome" (see later).
      - libboost-filesystem1.83.0
      - libcdr-0.1-1
      - libgc1
      - libgsl27
      - libgslcblas0
      - libmagick++-6.q16-9
      - libpotrace0
      - libproxy1v5
      - librevenge-0.0-0
      - libspelling-1-1
      - libvisio-0.1-1
      - libwpg-0.3-3
      - imagemagick
      - libimage-magick-perl
      - libwmf-bin
      - transfig
      - libsvg-perl
      - libxml-xql-perl
# ----
# needed by the print preview feature
      - evince
      - libglib2.0-0t64
# ----
    prime:
      - -lib/inkscape/*.a
      - -*canberra*so* # We don't have sound permissions anyway
# HACK: remove all libraries that are already provided by the snap gnome extension
# The list can be generated with:
# snap run --shell inkscape
# $ cd /snap/inkscape/current/usr/lib/; for i in **/lib*.so*; do if [ -e /snap/gnome-46-2404/current/usr/lib/$i ]; then echo $i; fi; done
# and some manual string modifications.
# (note that the string "gnome-46-2404" may need to be updated in the future, check $GTK_PATH within the snap environment.)
      - -usr/lib/*/gtk-*/
      - -usr/lib/*/libICE.*
      - -usr/lib/*/libLerc.*
      - -usr/lib/*/libSM.*
      - -usr/lib/*/libXcursor.*
      - -usr/lib/*/libXcomposite.*
      - -usr/lib/*/libXi.*
      - -usr/lib/*/libXinerama.*
      - -usr/lib/*/libXrandr.*
      - -usr/lib/*/libXrender.*
      - -usr/lib/*/libXt.*
      - -usr/lib/*/libarchive.*
      - -usr/lib/*/libatk.*
      - -usr/lib/*/libatk-bridge.*
      - -usr/lib/*/libatspi.*
      - -usr/lib/*/libaom.*
      - -usr/lib/*/libaspell.*
      - -usr/lib/*/libavahi-client.*
      - -usr/lib/*/libavahi-common.*
      - -usr/lib/*/libcairo-gobject.*
      - -usr/lib/*/libcairo-script-interpreter.*
      - -usr/lib/*/libcairo.*
      - -usr/lib/*/libcolord.*
      - -usr/lib/*/libcolordprivate.*
      - -usr/lib/*/libcups.*
      - -usr/lib/*/libcurl-gnutls.*
      - -usr/lib/*/libdatrie.*
      - -usr/lib/*/libdconf.*
      - -usr/lib/*/libde265.*
      - -usr/lib/*/libdeflate.*
      - -usr/lib/*/libenchant-2.*
      - -usr/lib/*/libepoxy.*
      - -usr/lib/*/libexslt.*
      - -usr/lib/*/libfontconfig.*
      - -usr/lib/*/libfreebl3.*
      - -usr/lib/*/libfreeblpriv3.*
      - -usr/lib/*/libfribidi.*
      - -usr/lib/*/libgdbm.*
      - -usr/lib/*/libgdbm_compat.*
      - -usr/lib/*/libgdk_pixbuf-2.0.*
      - -usr/lib/*/libgomp.*
      - -usr/lib/*/libgraphene-1.0.*
      - -usr/lib/*/libgraphite2.*
      - -usr/lib/*/libgtk-4.*
      - -usr/lib/*/libgtksourceview-5.*
      - -usr/lib/*/libharfbuzz.*
      - -usr/lib/*/libheif.*
      - -usr/lib/*/libhunspell-1.7.*
      - -usr/lib/*/libjbig.*
      - -usr/lib/*/libjpeg.*
      - -usr/lib/*/liblber.*
      - -usr/lib/*/liblcms2.*
      - -usr/lib/*/libldap.*
      - -usr/lib/*/libltdl.*
      - -usr/lib/*/libmpfr.*
      - -usr/lib/*/libmpfr.*
      - -usr/lib/*/libnghttp2.*
      - -usr/lib/*/libnspr4.*
      - -usr/lib/*/libnss3.*
      - -usr/lib/*/libnssckbi.*
      - -usr/lib/*/libnssdbm3.*
      - -usr/lib/*/libnssutil3.*
      - -usr/lib/*/libopenjp2.*
      - -usr/lib/*/libopenjp2.*
      - -usr/lib/*/libpango-1.0.*
      - -usr/lib/*/libpangocairo-1.0.*
      - -usr/lib/*/libpangoft2-1.0.*


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/.gitlab/issue_templates/Default.md =====

Do not report issues here!

Use https://gitlab.com/inkscape/inbox/-/issues/ instead . 



See https://inkscape.org/contribute/report-bugs/ for more instructions. If you notice this after creating an issue, don't do anything, don't create a second issue, let the bug wranglers move it to appropriate section.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/.gitlab/merge_request_templates/release.md =====


# Releasing a new Inkscape Version

Please complete this checklist in order to make a new release.

Unless specified every item should be considered for every type of release. i.e. Alpha, beta, RC and final

## Coordination

 * [ ] Plan a schedule for the release
 * [ ] Tell the other teams about the schedule
   * [ ] Testing team
   * [ ] Translations team
   * [ ] Vectors team
 * [ ] Check release notes are up to date
 * [ ] Translations merge requests all submitted

## Issues

 * [ ] There are no blocker issues in the milestone for this release (RC and Final)
 * [ ] The developer team is happy with the remaining issues

## Code

 * [ ] Inkscape version is updated
 * [ ] Update Man pages and Tutorials
 * [ ] Syncronise extensions repository (look for same branch name)
 * [ ] Check all the CI builders are passing correctly

## Graphics (RC and Final only)

 * [ ] About screens
 * [ ] Windows install graphics nsis
 * [ ] Windows install graphics wix



===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/CONTRIBUTING.md =====

[Inkscape Developer Documentation](doc/readme.md) /

Contributing to Inkscape - Getting started with Inkscape Development
====================================================================

Inkscape welcomes your contributions to make it an even better
drawing program for the Open Source community.

You can help improve Inkscape with and without programming knowledge. We need both to get a good result.

As a **non-programmer**, you can e.g. help with support, testing, documentation, translations or outreach.
Please see our [Contributing page](https://inkscape.org/contribute/).

If you want to help as a **programmer**, then please follow the rest of this page. We suggest the following steps:

1. Know how to contact us
2. Get the source code
3. Compile and run
4. Look at the developer documentation
5. Set up a GitLab account
6. Make changes
7. Submit as Merge Request

Contact
-------

Feel free to reach out to us.

- Chat: The development team channel is available via [Web Chat](https://chat.inkscape.org/channel/team_devel) or via IRC: irc://irc.libera.chat/#inkscape-devel
- Mailing list: [inkscape-devel@lists.inkscape.org](mailto:inkscape-devel@lists.inkscape.org). Most of the developers are subscribed to the mailing list.
- Bug tracker:
  - Report issues in the [inbox](https://gitlab.com/inkscape/inbox/-/issues).
  - Once issues are confirmed, the developers move them to the [development issue tracker](https://gitlab.com/inkscape/inkscape/-/issues)
- Video conference: We regularly meet by video. Please ask in the chat for details.
- Real life: About once a year there is an Inkscape summit. We also take part in events like Libre Graphics Meeting. This is announced in the chat and mailing list.



Source Code
-----------

Inkscape uses the Git version control system, with the code hosted on GitLab.

 * Inkscape core: https://gitlab.com/inkscape/inkscape
 * Further tools and parts: https://gitlab.com/inkscape/

How to get the sourcode is described in the next step.

Get the Source, Compile and Install
-----------------------------------

[Compile Inkscape from source](doc/building/readme.md).

(If you only want to run Inkscape, but not modify the code, you can also [download a prebuilt Inkscape version](INSTALL.md).)


Developer Documentation
-----------------------

This page is part of the [Inkscape Developer Documentation](doc/readme.md). Here you should find everything you need for programming Inkscape. If not, please contact us or submit a merge request for improvement.


Setting up a GitLab account
---------------------------

To report bugs and submit changes, you need an account for GitLab. This is free. [Sign up on gitlab.com](https://gitlab.com/users/sign_up). You can find more information in the [Gitlab user tutorial](https://docs.gitlab.com/ee/user/profile/account/create_accounts.html).


Submitting Improvements
-----------------------

Changes to Inkscape can be submitted as merge requests on GitLab. If you know how to use GitLab, you can skip this section, *except* for the part about "Changes to CI settings".

The following sections are a rough guide to introduce you to the topic. They should get you started, but are no in-depth guide and provide only some indications of the required steps. If you are new to Git you will likely need to lookup some of the commands and terms on your own. Feel free to ask in the chat and look at [GitLab's tutorials](https://docs.gitlab.com/tutorials/learn_git/).

### Workflow

Once you have implemented new features or fixed bugs, you may want to contribute the changes back to the official Inkscape source code, such that other people can also benefit from your efforts.

Our motto for changes to the codebase is "Patch first, ask questions
later". When someone has an idea, rather than endlessly debating it, we
encourage folks to go ahead and code something up (even prototypish).

You would make this change in your own fork of Inkscape (see GitLab docs about
how to fork the repository), in a development branch of the code, which can be
submitted to GitLab as a merge request (MR). Once in an MR it is convenient for other
folks to try out, poke and prod, and tinker with. We figure, the best
way to see if an idea fits is to try it on for size.

So if you have an idea, go ahead:

### Creating a fork

A *fork* is your own copy of a GitLab repository on GitLab. Contrary to the official repository of Inkscape, you can push changes to your fork (you have write access) and thereby make them publicly available.

Fork the inkscape project (https://gitlab.com/inkscape/inkscape): Create a fork by clicking the Fork icon in the upper right corner of [Inkscape's main GitLab page](https://gitlab.com/inkscape/inkscape). See the [GitLab documentation](https://docs.gitlab.com/ee/user/project/repository/forking_workflow.html#creating-a-fork) on this topic for more information. You then work with your fork instead of the official repository, i.e. clone it to your local storage.

### Changes to CI settings
When you push changes, automatic builds and tests on the GitLab servers are initiated. The default timeout of GitLab is too short for the Inkscape build.

**Important**:
Go to your fork > Settings > CI/CD > General Pipelines > Timeout. Change the Pipeline Timeout to `3 hours`. If you can not find the setting, check the [GitLab documentation](https://docs.gitlab.com/ci/pipelines/settings/#set-a-limit-for-how-long-jobs-can-run).

### Creating a branch

Merge requests operate on branches, so it necessary to create a new branch for the changes you want to contribute. Use a separate branch for each bug/feature you want to work on. Assume you are going to fix a nasty bug. Create a branch with an appropriate name, e.g., `fix-for-bug-xyz`, by running
```
git checkout -b fix-for-bug-xyz
```
on the local clone of your fork. Make your changes (the bugfix) and commit them.

Find more information in the [GitLab documentation](https://docs.gitlab.com/topics/git/branch/).

### Commiting changes

Make the changes and `git commit` them.

See the [Commit Style](#commit-style) for how to write good commit messages.

### Pushing changes

When you are done with your changes, it is usually a good idea to take a few moments and review the status of your local Git repository and your work to make sure everything is the way you want. Pushing the branch to your GitLab fork repository will make it publicly available.

To push the branch to your fork of Inkscape on GitLab, run

```
git push origin fix-for-bug-xyz
```

This also produces a notification like

```
remote: To create a merge request for fix-for-bug-xyz, visit:
remote:   https://gitlab.com/userxxx/inkscape/-/merge_requests/new?merge_request%5Bsource_branch%5D=fix-for-bug-xyz
```

with a link for creating a merge request (where `userxxx` is your username). This message is only output for newly created branches.

### Creating a merge request

There are multiple ways to create a merge request. For example, you can use the above link printed by git push to create a merge request. Alternatively, you can select your branch on the GitLab web interface and click Create merge request in the upper right corner. See the GitLab documentation for more information on creating merge requests.

In GitLab's merge request form, enter a title, a meaningful description and attach pictures or files if appropriate.

It is recommended to tick the *Allow commits from members who can merge to the target branch* checkbox. This allows the core developers to push changes directly to your branch and thereby simplifies the integration of your code into Inkscape.

Try to keep your MR current instead of creating a new one. You can always push new changes to your branch to update the existing MR.

Rebase your MR sometimes.


### Merge request review

Merge requests are reviewed. Other developers will look at your MR and give feedback. Please check regularly if there were new comments on your MR.

Once everyone is happy, the MR is approved.

Repository access
-----------------

Any change (MR) to Inkscape must be approved by at least one other person with write access.
We give write access out to people with proven interest in helping develop
the codebase. Proving your interest is straightforward:  Make two
contributions and request access.

Coding Style
------------

Please refer to the [Coding Style Guidelines](https://inkscape.org/en/develop/coding-style/) if you have specific questions
on the style to use for code. If reading style guidelines doesn't interest
you, just follow the general style of the surrounding code, so that it is at
least consistent.

Before making big changes, we recommend to discuss your idea with us. Someone else might already have plans you can build upon and we will try to guide you!

Commit Style
------------

Write informative commit messages ([check this](https://chris.beams.io/posts/git-commit/)).



===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/INSTALL.md =====

[Inkscape Developer Documentation](doc/readme.md) /

Building and Installing Inkscape
================================

# Download prebuilt Inkscape

To download ready made Inkscape versions, see:
- [Stable version](https://inkscape.org/download)
- [Latest development version](https://inkscape.org/release/inkscape-dev/)

# Compile it yourself

To build Inkscape on your own, please see [Compiling Inkscape](doc/building/readme.md) in the developer documentation.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/NEWS.md =====

Inkscape 1.2-alpha

Release highlights

Released on 2022-02-05

    Inkscape documents can now hold multiple pages, which are managed by the new Page tool
    Editable markers and dash patterns
    On-canvas alignment snapping
    Selectable origin for numerical scaling and moving
    All alignment options in a single dialog
    Gradient editing in the Fill and Stroke dialog
    Layers and objects dialog merged
    Snap settings refactored
    Configurable Tool bar, continuous icon scaling and many more new customization options
    Performance improvements for many parts of the interface and many different functions
    Many crash & bug fixes


==================================================================
===                                                            ===
===     The authoritative version of the changelog is at       ===
=== https://wiki.inkscape.org/wiki/index.php/Release_notes/1.2 ===
===                                                            ===
==================================================================

General user interface
Color palette

The overall look and options of the Color palette and the Swatches dialog got a massive overhaul (MR #2881):

    When switching the color palette, the switcher shows a colorful preview line for each palette
    Between 1 and 5 palette rows that can be displayed all at once, or scrolled through vertically / using the arrow buttons
    Improved and reliably working settings for padding, tile size and tile shape / auto-stretching

Status Bar

    The layer selection dropdown has been replaced by a layer indicator. Clicking on the indicator opens the new Layers and object dialog. This change improves Inkscape's performance for documents with many layers (MR #3648).
    The status bar contents is now configurable, see Customization section.

Tool bar

    The tool bar width can now be resized and also wraps into multiple columns automatically if the screen height is too small for all icons to fit.
    You can customize which tools will be part of the tool bar in the preferences, see Customization section

Dithering


Inkscape's gradients sometimes suffered from visible steps between colors, a phenomenon also known as gradient banding. Gradient banding is caused by the difference between how many different colors are available for the selected image file format and how many colors a human eye can discern. The effect becomes especially prominent when exporting a gradient that only spans a small color range to a high-resolution image. There just aren't enough colors available for a smooth transition.

Dithering softens these steps by scattering pixels of the different adjacent colors along the gradient, a little bit like a blur.

Dithering is now used both for Export of raster images as well as for displaying gradients on canvas(MR #3812). This functionality requires a special version of Cairo, our rendering engine. This means that it will only be available in the pre-packaged builds (for macOS, Windows and for the Linux AppImage).

For standard Linux package formats (deb, rpm, …), it depends upon your Linux distribution maintainers whether they will patch up the version of Cairo they want to distribute. We hope that this change will one day also be included in the official Cairo packages (Link to ongoing discussion).

Canvas
Page

    The page shadow now has a more realistic, blurry, fade-out look (MR #3128). [TODO: add a small screenshot]
    Settings for the page background / decoration were refactored, see section about Document properties dialog.
    Inkscape documents can now hold multiple pages! Learn more in the section about the new Page tool.

Snapping
Snap bar is now Snap popover
The snap bar has been replaced with a new 'popover'-type dialog, which will unfold when you click on the little arrow symbol in the top right corner, next to the snap symbol. Snap options now have always-visible descriptions, to make them easier to understand (MR #3323).

To activate / deactivate snapping globally, click on the snap symbol in the top right corner or press %.

The popover dialog has two different modes:

    Simple: Only 3 options: snap bounding boxes and paths, activate / deactivate the new alignment snapping). This provides a simple preset for many use cases.
    Advanced: Gives the familiar granular control over every snapping option. Switching from 'Advanced' back to 'Simple' is not merely a visual change, but will reset snap settings to defaults.


Snapping preferences globalized

Snap settings are no longer saved with the document, but are set globally for all documents in the preferences and in the snap popover dialog. The option for enabling snapping in new documents has been removed, as it no longer makes sense.

The options for snapping perpendicularly and tangentially to paths or guidelines have been moved from the document preferences to the snap popover to make them more discoverable. The other snap options from the document settings dialog were removed. [TODO: check whether this is still true at the time of release] 

Alignment and Distribution snapping
During Google Summer of Code 2021, GSOC student Parth Pant worked on adding on-canvas alignment and distribution snapping, with support of the mentors Thomas Holder and Marc Jeanmougin. As a result, three new modes of on-canvas snapping have been added. These new modes make aligning and distributing objects a very easy drag-and-drop operation (MR #3294)..

When on-canvas alignment is active, Inkscape will display horizontal or vertical temporary guidelines that indicate when the selected object can be aligned relative to another object on the canvas. It connects the points of the objects that are in alignment. With distribution snapping, multiple objects close by are taken into account, making it possible to align objects in a grid, with very little effort.

The temporary guidelines only appear while editing / moving objects on the canvas. Once a guide shows up, the movement of the selection is loosely constrained in the direction of the guide.

Alignment and Distribution snapping guidelines display the distance(s) between objects as a little label per default. This can be disabled from Edit → Preferences → Snapping: Show snap distance in case of alignment or distribution snap.

The 'Simple' mode of the snapping popover dialog allows you to simply activate or deactivate Alignment snapping. The 'Advanced' mode gives you additional control by allowing you to en-/disable:

    Self snapping: Toggle alignment snapping for nodes in the same path while editing nodes or node handles
    Distribution snapping: Toggle distribution snapping

Tools
Page tool

The new Page tool (lowest button in the tool bar) allows you to create multi-page Inkscape documents, and to import as well as export multi-page PDF documents. (MR #3486, MR #3785, MR #3821). It supports overlapping pages and pages of different sizes in a single document.

Tool usage:

    To create a new page either:
        click-and-drag on the canvas
        or click on the 'Create a new page' button in the tool controls
    To delete a page, click on the page to select it, then click on the button Delete selected page or use the Del or Backspace keys.
    To move a page on the canvas, click-and-drag it to the desired new position. If the option to Move overlapping objects is active, this will also move any objects that touch the page along with it.
    To change a page's size:
        click on a page whose size you want to change to select it, then drag the square-shaped handle in its bottom right corner
        click on the page, and then choose one of the predefined sizes in the page size dropdown, or enter your size values for the 'Custom' option, by typing them into the field in the form of 10cm x 15cm
    To fit a page to:
        the size of the drawing: make sure to have no object selected before you switch to the Page tool. Then select a page by clicking on it, then click on the button 'Fit page to drawing or selection' in the tool controls
        a selected object: first select the object(s) with the selection tool, then switch to the Page tool, click on a page to select it, then press the the button 'Fit page to drawing or selection' in the tool controls
    To add a label to your page, select the page by clicking on it, then enter a name or label for it into the text field in the page tool's tool controls. Labels are always visible, no matter which tool is currently selected.
    To export a multi-page PDF file, use File → Save a copy … → PDF. This will automatically include all pages.
    To open or import a multi-page PDF or (pdf-based) AI file, use File → Open/Import → select file name → choose to import 'All' pages [Known issue: 'import' moves content of some pages to some far out place in the drawing]

Note: Multi-page SVG files are an Inkscape-specific concept. Web browsers will only display the first page of your document, which corresponds to the 'viewbox' area of the SVG file.
Selector Tool

The tool now allows to set the origin of the selection for precise numerical positioning:

    Click on one of the 9 object handles to select your desired origin for the scaling, or select and then drag the middle handle to the desired position
    A small red circle now indicates the new origin and the x/y position in the tool controls will adjust to the new origin.
    Now edit the x, y, width or height values to move and scale your object using the new origin (MR #2700)
Text Tool

    Kerning options are now symbolized by a button between the subscript and text direction selectors. Clicking on it will open a so-called pop-over, where all previously available options can be found. This change saves space in the Text tool's toolbar.
    Negative kerning values can now be as little as -1000 (previously -100), making them symmetrical to their positive counterparts (MR #2569, MR #3434)
    Padding: Text that is flowed into a shape and standard flowed text now have an additional square-shaped handle in the top right corner. Move the handle to adjust the text padding inside the frame (MR #2769) [Currently broken]
    Exclusion zones: Text can now flow around one or more movable objects:
        Select all object(s) (use only shapes and paths on the same object hierarchy level as the text; no groups / clones / images supported) and the text.
        Set the exclusion zone by going to Text → Set subtraction frames.
        Now you can move the exclusion objects around or edit their shape, and the text will adjust automatically.
        If you want to change the exclusion zones again at a later point, repeat the process with all objects that the text should flow around.

Background info: SVG 2.0 flowed text allows for shape-padding and shape-subtract attributes. shape-padding lets the text flow into a shape and leave some space between its edges and w where the text will start to flow. shape-subtract subtracts shapes with margin, so text can flow around other objects in the scene. These attributes were supported in Inkscape 1.0, but not exposed to the user. This version of Inkscape includes both an adjustable on-canvas knot for changing the padding as well as a Text menu item for setting text subtraction properties with a further knot to adjust it's margins.

[See merge request for animated gifs to add here]
Path Operations

    New Split path operation, available from Path → Split path:
    The function separates a path object that consists of multiple subpaths into a set of path objects that 'belong together'. This means that parts of a path that have holes in them are kept as whole objects. The function works by splitting up a path into non-intersecting bits, keeping intersecting bits together.
    Example: A path that consists of a word, like 'Inkscape' will be split into 8 parts, one for each letter. With the familiar 'Break apart' function, there would be 12 parts, because of the holes in the letters that would be split off as their own objects, too (MR #3738).[TODO: add animation]
    On-Canvas Boolean operations [TODO: fill in if merged, seems to have low probability, lots of work to be done] https://gitlab.com/inkscape/inkscape/-/merge_requests/3357 Osama Ahmad with mentors Thomas Holder, Marc Jeanmougin, Martin Owens

Dialogs
General

    A mini-menu (downward pointing arrow symbol) was added into the title bar of every multi-dialog panel (also called 'notebook'). You can use it to close the current tab, to undock it, or to close the whole panel. It also shows a list of available dialogs, sorted by purpose, allowing you to open them with a click ((MR #3728)
    Open dialogs are now less costly for performance, because they do not update when it's not needed (MR #3369), or when they are hidden (MR #3761)
    Docking zones now expand and flash slowly when a dialog is dragged close to them. This makes it easier to see where docking is possible (MR #3729)
    The text labels of docked dialogs are now more responsive to the width of dialog (MR #3627)

Align and distribute

    The formerly separate Arrange dialog is now integrated with the Align and Distribute dialog. With its three tabs, more user-friendly names and some small visual tweaks, the dialog now holds everything that is needed for aligning, distributing and arranging objects in your drawing (MR #3382, MR #3667).
    The icons inside this dialog are now smaller.
    Node alignment and distribution is nolonger shown on first run Just when you use node editing tool
Document Properties

The 'Snapping' tab was removed in favor of a global snapping preference, see Snapping section.

The first tab of the Document properties dialog was refactored thoroughly to make it easier to use:

    It's now labelled 'Display' instead of 'Page'
    The long list of different document formats is now available from a dropdown
    There is a preview available of the page format and colors [TODO: needs screenshot]
    The page area(s) in a document can now have a different color than the underlying 'desk' area [TODO: mention in highlights?]
    The other options have been rearranged to look tidier
    The option to add margins to a document when resizing it is currently unavailable [TODO: hopefully get that back before the release]

(MR #3700).

(MR #3400, MR #3403)
Fill and Stroke dialog
Color selector

    The more intuitive HSL mode (hue, saturation, lightness) is now the default mode of the color selector.
    All color selection modes (e.g. HSL, HSV, RGB, CMYK, color wheel, CMS) have been moved into drop-down menu, with icons. You can get the old, tabbed look back by disabling the option in Edit → Preferences → Interface: Use compact color selector mode switch (MR #3443).


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/README.md =====

Inkscape. Draw Freely.
======================

[https://inkscape.org/](https://inkscape.org/)

Inkscape is a Free and open source vector graphics editor. It offers a rich set
of features and is widely used for both artistic and technical illustrations
such as cartoons, clip art, logos, typography, diagramming and flowcharting.
It uses vector graphics to allow for sharp printouts and renderings at
unlimited resolution and is not bound to a fixed number of pixels like raster
graphics. Inkscape uses the standardized SVG file format as its main format,
which is supported by many other applications including web browsers.

SVG Features include basic shapes, paths, text, markers, clones,
alpha blending, transforms, gradients, and grouping.
In addition, Inkscape supports Creative Commons meta-data, node-editing,
layers, complex path operations, text-on-path, and SVG XML editing.
It also imports several formats like EPS, Postscript,
JPEG, PNG, BMP, and TIFF and exports PNG as well as multiple vector-based
formats.

Inkscape's main motivations are to provide the Open Source community
with a fully W3C compliant XML, SVG, and CSS2 drawing tool emphasizing a
lightweight core with powerful features added as extensions, and the
establishment of a friendly, open, community-oriented development
processes.

[![build status](https://gitlab.com/inkscape/inkscape/badges/master/pipeline.svg)](https://gitlab.com/inkscape/inkscape/-/commits/master)

## More information

- [Download](https://inkscape.org/download)
- [User Documentation](https://inkscape.org/learn/)
- [Developer Documentation](doc/readme.md)
- [Report Bugs](https://inkscape.org/contribute/report-bugs/)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/doc/building/general_advanced.md =====

[Developer documentation](../readme.md) / [Compiling Inkscape](./readme.md) /


# Advanced build options valid for all operating systems

This page lists detailed options for building Inkscape. They are valid for all operating systems.

Before this you should already have read the basic instructions for building on your operating system - see [Compiling Inkscape](./readme.md).


Build Options
-------------

A number of configuration settings can be overridden through CMake. To
see a list of the options available for Inkscape, run:

```sh
cmake -L
```
or, for more advanced cmake settings:

```sh
cmake --help
```

For example, to build Inkscape with only SVG 1 support, and no SVG 2, do:

```sh
cmake .. -DWITH_SVG2=OFF
```

# Ninja Build vs. Ninja Install

There are two variants of building:

1. Ninja Build (`ninja`): Only compile Inkscape. The resulting binary `bin/inkscape` (Windows: `bin/inkscape.exe`) does not yet work because it is missing the necessary files like UI layout, icons etc. (`share`) and translations (`po`).
2. Ninja Install (`ninja install`): Compile Inkscape (as in 1.) and copy the binary and all needed files into one folder `build/install_dir`. The location of that `install_dir` is set in the option`CMAKE_INSTALL_PREFIX` when calling `cmake`.

Here in the documentation we recommend `ninja install` to simplify the explanations.

If you want to keep multiple compiled versions of Inkscape, you can copy the `install_dir` of each version to another folder and run them from there.


## Faster build without "Ninja install"

This section describes a possibility to slightly improve build time that is, however, only recommended for advanced developers.

You can save a few seconds if you only run `ninja` instead of `ninja install`. This needs a workaround to set up and some caution when using.


In the following we will set up a directory named `dev_share` used as`CMAKE_INSTALL_PREFIX`.
```
cd build

mkdir -p dev_share
ln -s ../../share dev_share/inkscape
ln -s ../po/locale dev_share/locale
```

Run CMake with the new `CMAKE_INSTALL_PREFIX`: `cmake -DCMAKE_INSTALL_PREFIX=./dev_share .....`, where for "....." you insert all other options as in the normal (e.g., [Linux](./linux.md)) build instructions.

Build Inkscape using `ninja` instead of `ninja install`.

Run Inkscape using `./bin/inkscape` instead of `./install_dir/bin/inkscape`.

When using these workarounds, it is recommended that you **do not run `ninja install`** or any commands that depend on it (e.g., packaging for Linux DEB or `ninja dist-win-msi` for Windows EXE format). Else, some files may unexpectedly appear in the `share` folder of your repository and your Git status will show these unwanted changes.


# CMake Build Type (Debug or Release)

The standard for development is to create a debug build (`-DCMAKE_BUILD_TYPE=Debug`) that includes debugging symbols and enables stricter compiler settings and assertion checks at runtime.

For a Release build without debug information, use `-DCMAKE_BUILD_TYPE=Release`.

# Internal lib2geom

The standard for development is to use the latest development version of lib2geom (`-DWITH_INTERNAL_2GEOM=ON`). This version is included in the Inkscape source tree as a submodule (`src/3rdparty/2geom`).

If you want to use the system version instead, use `-DWITH_INTERNAL_2GEOM=OFF`.

# Make vs Ninja

Inkscape can also be built with Make instead of Ninja. This has no real benefit except if you are used to calling `make`.

If you use the suggested CMake commands but without `-G Ninja` then you will need to run `make` instead of `ninja`.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/doc/building/linux.md =====

[Developer documentation](../readme.md) / [Compiling Inkscape](./readme.md) /

# Compiling Inkscape on Linux


**TODO** - this is currently being merged with instructions on the [Website](https://inkscape.org/develop/getting-started/) and [wiki](https://wiki.inkscape.org/wiki/index.php?title=Compiling_Inkscape).


## Getting Dependencies

For common linux-distributions (Ubuntu, Debian, Fedora, Arch and more) you can use
[a bash-script](https://gitlab.com/inkscape/inkscape-ci-docker/-/raw/master/install_dependencies.sh?inline=false) 
for getting required libraries:

```bash
wget -v https://gitlab.com/inkscape/inkscape-ci-docker/-/raw/master/install_dependencies.sh -O install_dependencies.sh
bash install_dependencies.sh --recommended
```

For a detailed list of all dependencies see [Tracking Dependencies](https://wiki.inkscape.org/wiki/Tracking_Dependencies).

## Getting Inkscape Source


To obtain the latest source code, use the following command (downloads into a subdirectory of your current working directory called "inkscape" by default):
```bash
git clone --recurse-submodules https://gitlab.com/inkscape/inkscape.git
```

Then change into that directory:
```bash
cd inkscape
```

To update the code later use:
```bash
git pull --recurse-submodules && git submodule update --recursive
```

## Compiling

Inkscape is built using CMake and Ninja.

To compile and run Inkscape, run the following in the Inkscape code directory:
```sh
# Create build subdirectory
mkdir build
# Change to it
cd build
# run CMake for initial setup
cmake -DCMAKE_INSTALL_PREFIX="${PWD}/install_dir" -DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache -DCMAKE_BUILD_TYPE=Debug -DWITH_INTERNAL_2GEOM=ON -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -G Ninja ..
# compile
ninja install
# run
./install_dir/bin/inkscape
```

To compile again after making changes, you can re-run the `ninja install` command. Make sure you are in the `build` subdirectory.


## Problems

☎ _If you can't solve your issue with the information above, please [ask in the chat](https://chat.inkscape.org/channel/team_devel) or [report a bug](https://inkscape.org/report)_.

## See also
- [Contributing and Developing](../../CONTRIBUTING.md)
- [Advanced Information on Compiling Inkscape](doc/build/general_advanced.md)
- [Packaging for Ubuntu Snap](../../snap/README.md)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkscape/doc/building/mac.md =====

[Developer documentation](../readme.md) / [Compiling Inkscape](./readme.md) /

# Compiling Inkscape on MacOS

Inkscape on MacOS can be built with either Homebrew or MacPorts.

## Using Homebrew

### Dependencies

Prerequisites:

- Xcode (AppStore)
- Xcode command line tools (`xcode-select --install`)
- [HomeBrew](https://brew.sh/)

Make sure you don't have any MacPorts stuff in your PATH. <!-- TODO - how? -->

Install packages:
```
brew install \
    adwaita-icon-theme \
    bdw-gc \
    boost \
    cairomm \
    ccache \
    cmake \
    double-conversion \
    gettext \
    gsl \
    gtkmm4 \
    gtksourceview5 \
    icu4c \
    imagemagick \
    intltool \
    lcms2 \
    libxslt \
    ninja \
    pkg-config \
    poppler \
    potrace
```

You may substitute `imagemagick` with `graphicsmagick`.

If you want to include a spell checker, also install `libspelling` using `brew`.

To build version 1.4.x you need `gtkmm3` instead of `gtkmm4` and also install libraries `gspell`, `libomp` and `libsoup@2`.

### Get Inkscape Source
Check out the source if you haven't already:

```
git clone --recurse-submodules https://gitlab.com/inkscape/inkscape.git
cd inkscape
```

### Build Inkscape

Inside the Inkscape directory, run the following c
