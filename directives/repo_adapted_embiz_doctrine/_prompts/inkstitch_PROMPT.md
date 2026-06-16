Read this local source bundle and create complete EMBIZ-specific operational doctrine.

Repository: inkstitch
Local source: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch
Bundle: /root/embroidery_business_agent_system/directives/repo_adapted_embiz_doctrine/_prompts/inkstitch_SOURCE_BUNDLE.md

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
# inkstitch EMBIZ ADAPTED DOCTRINE
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


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/dbus/select_elements.py =====

# Authors: see git history
#
# Copyright (c) 2022 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.
#
# The original Source can be found here:
# https://gitlab.com/inkscape/inkscape/uploads/ca84fa1092f8d6e81e49b99e659cd025/dbus_test.py

import sys
from time import sleep

import gi
from gi.repository import Gio, GLib

gi.require_version("Gio", "2.0")


class DBusActions:
    def __init__(self):
        try:
            bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        except BaseException:
            exit()

        name = 'org.inkscape.Inkscape'
        appGroupName = "/org/inkscape/Inkscape"
        self.applicationGroup = Gio.DBusActionGroup.get(
            bus,
            name,
            appGroupName)

    def run_action(self, action, param):
        self.applicationGroup.activate_action(action, param)


# start dbus
dbus = DBusActions()
# give it some time to start
sleep(0.5)
# clear previous selection
dbus.run_action('select-clear', None)
# select with the list of ids
dbus.run_action('select-by-id', GLib.Variant.new_string(sys.argv[1]))


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/inkstitch.py =====

# Authors: see git history
#
# Copyright (c) 2010 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.

import os
import sys
from pathlib import Path  # to work with paths as objects
from argparse import ArgumentParser  # to parse arguments and remove --extension

if sys.version_info >= (3, 11):
    import tomllib      # built-in in Python 3.11+
else:
    import tomli as tomllib

import logging

import lib.debug.utils as debug_utils
import lib.debug.logging as debug_logging
from lib.debug.utils import safe_get    # mimic get method of dict with default value

# --------------------------------------------------------------------------------------------

SCRIPTDIR = Path(__file__).parent.absolute()

logger = logging.getLogger("inkstitch")   # create module logger with name 'inkstitch'

# TODO --- temporary --- catch old DEBUG.ini file and inform user to reformat it to DEBUG.toml
old_debug_ini = SCRIPTDIR / "DEBUG.ini"
if old_debug_ini.exists():
    print("ERROR: old DEBUG.ini exists, please reformat it to DEBUG.toml and remove DEBUG.ini file", file=sys.stderr)
    sys.exit(1)
# --- end of temporary ---

debug_toml = SCRIPTDIR / "DEBUG.toml"
if debug_toml.exists():
    with debug_toml.open("rb") as f:
        ini = tomllib.load(f)  # read DEBUG.toml file if exists, otherwise use default values in ini object
else:
    ini = {}
# --------------------------------------------------------------------------------------------

running_as_frozen = getattr(sys, 'frozen', None) is not None  # check if running from pyinstaller bundle

if not running_as_frozen:  # override running_as_frozen from DEBUG.toml - for testing
    if safe_get(ini, "DEBUG", "force_frozen", default=False):
        running_as_frozen = True

if len(sys.argv) < 2:
    # no arguments - prevent accidentally running this script
    msg = "No arguments given, exiting!"  # without gettext localization see _()
    msg += "\n\n"
    msg += "Ink/Stitch is an Inkscape extension."
    msg += "\n\n"
    msg += "Please enter arguments or run Ink/Stitch through the Inkscape extensions menu."
    if running_as_frozen:  # we show dialog only when running from pyinstaller bundle - using wx
        try:
            import wx
            app = wx.App()
            dlg = wx.MessageDialog(None, msg, "Inkstitch", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
        except ImportError:
            print(msg, file=sys.stderr)
    else:
        print(msg, file=sys.stderr)
    sys.exit(1)

# activate logging - must be done before any logging is done
debug_logging.activate_logging(running_as_frozen, ini, SCRIPTDIR)
# --------------------------------------------------------------------------------------------

# check if running from inkscape, given by environment variable
if os.environ.get('INKSTITCH_OFFLINE_SCRIPT', '').lower() in ['true', '1', 'yes', 'y']:
    running_from_inkscape = False
else:
    running_from_inkscape = True

# initialize debug and profiler type
debug_active = bool((gettrace := getattr(sys, 'gettrace')) and gettrace())  # check if debugger is active on startup
debug_type = 'none'
profiler_type = 'none'

if not running_as_frozen:  # debugging/profiling only in development mode
    # specify debugger type
    #   but if script was already started from debugger then don't read debug type from ini file or cmd line
    if not debug_active:
        debug_type = debug_utils.resolve_debug_type(ini)  # read debug type from ini file or cmd line

    profiler_type = debug_utils.resolve_profiler_type(ini)  # read profile type from ini file or cmd line

    if running_from_inkscape:
        # process creation of the Bash script - should be done before sys.path is modified, see below in prefer_pip_inkex
        if safe_get(ini, "DEBUG", "create_bash_script", default=False):  # create script only if enabled in DEBUG.toml
            debug_utils.write_offline_debug_script(SCRIPTDIR, ini)

        # disable debugger when running from inkscape
        disable_from_inkscape = safe_get(ini, "DEBUG", "disable_from_inkscape", default=False)
        if disable_from_inkscape:
            debug_type = 'none'  # do not start debugger when running from inkscape

    # prefer pip installed inkex over inkscape bundled inkex, pip version is bundled with Inkstitch
    # - must be be done before importing inkex
    prefer_pip_inkex = safe_get(ini, "LIBRARY", "prefer_pip_inkex", default=True)
    if prefer_pip_inkex and 'PYTHONPATH' in os.environ:
        debug_utils.reorder_sys_path()

# enabling of debug depends on value of debug_type in DEBUG.toml file
if debug_type != 'none':
    from lib.debug.debugger import init_debugger
    init_debugger(debug_type, ini)
    # check if debugger is really activated
    debug_active = bool((gettrace := getattr(sys, 'gettrace')) and gettrace())

# activate logging for svg
# we need to import only after possible modification of sys.path, we disable here flake8 E402
from lib.debug.debug import debug  # noqa: E402  # import global variable debug - don't import whole module
debug.enable()  # perhaps it would be better to find a more relevant name; in fact, it's about logging and svg creation.

# log startup info
debug_logging.startup_info(logger, SCRIPTDIR, running_as_frozen, running_from_inkscape, debug_active, debug_type, profiler_type)

# --------------------------------------------------------------------------------------------

# pop '--extension' from arguments and generate extension class name from extension name
#   example:  --extension=params will instantiate Params() class from lib.extensions.

# we need to import only after possible modification of sys.path, we disable here flake8 E402
from lib import extensions  # noqa: E402  # import all supported extensions of institch

# TODO: if we run this earlier the warnings ignore filter for releases will not work properly
if running_as_frozen and not debug_logging.frozen_debug_active():
    debug_logging.disable_warnings()

parser = ArgumentParser()
parser.add_argument("--extension")
my_args, remaining_args = parser.parse_known_args()

extension_name = my_args.extension

# example: foo_bar_baz -> FooBarBaz
extension_class_name = extension_name.title().replace("_", "")

extension_class = getattr(extensions, extension_class_name)
extension = extension_class()  # create instance of extension class - call __init__ method

# extension run(), we differentiate between debug and normal mode
# - in debug or profile mode we debug or profile extension.run() method
# - in normal mode we run extension.run() in try/except block to catch all exceptions and hide GTK spam
if debug_active or profiler_type != "none":  # if debug or profile mode
    if profiler_type == 'none':             # only debugging
        extension.run(args=remaining_args)
    else:                                  # do profiling
        debug_utils.profile(profiler_type, SCRIPTDIR, ini, extension, remaining_args)

else:   # if not debug nor profile mode
    from lib.exceptions import InkstitchException, format_uncaught_exception
    from inkex import errormsg  # to show error message in inkscape
    from lxml.etree import XMLSyntaxError  # to catch XMLSyntaxError from inkex
    from lib.i18n import _      # see gettext translation function _()
    from lib.utils import restore_stderr, save_stderr  # to hide GTK spam

    save_stderr()  # hide GTK spam
    exception = None
    try:
        extension.run(args=remaining_args)
    except (SystemExit, KeyboardInterrupt):
        raise
    except XMLSyntaxError:
        msg = _("Ink/Stitch cannot read your SVG file. "
                "This is often the case when you use a file which has been created with Adobe Illustrator.")
        msg += "\n\n"
        msg += _("Try to import the file into Inkscape through 'File > Import...' (Ctrl+I)")
        errormsg(msg)
    except InkstitchException as exc:
        errormsg(str(exc))
    except Exception:
        errormsg(format_uncaught_exception())
        sys.exit(1)
    finally:


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/lib/__init__.py =====




===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/lib/commands.py =====

# Authors: see git history
#
# Copyright (c) 2010 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.

import os
import sys
from copy import deepcopy
from random import random
from typing import List, Optional, cast

import inkex
from shapely import geometry as shgeo
from shapely import get_coordinates

from .i18n import N_, _
from .svg import (apply_transforms, generate_unique_id,
                  get_correction_transform, get_document, get_node_transform)
from .svg.svg import copy_no_children, point_upwards
from .svg.tags import (CONNECTION_END, CONNECTION_START, CONNECTOR_TYPE,
                       INKSCAPE_LABEL, SVG_SYMBOL_TAG, SVG_USE_TAG, XLINK_HREF)
from .utils import Point, cache, get_bundled_dir
from .utils.geometry import ensure_multi_polygon

COMMANDS = {
    # L10N command attached to an object
    "starting_point": N_("Starting position"),

    # L10N command attached to an object
    "ending_point": N_("Ending position"),

    # L10N command attached to an object
    "target_point": N_("Target position"),

    # L10N command attached to an object
    "autoroute_start": N_("Auto-route starting position"),

    # L10N command attached to an object
    "autoroute_end": N_("Auto-route ending position"),

    # L10N command attached to an object
    "stop": N_("Stop (pause machine) after sewing this object"),

    # L10N command attached to an object
    "trim": N_("Trim thread after sewing this object"),

    # L10N command attached to an object
    "ignore_object": N_("Ignore this object (do not stitch)"),

    # L10N command attached to an object
    "satin_cut_point": N_("Satin cut point (use with Cut Satin Column)"),

    # L10N command that affects a layer
    "ignore_layer": N_("Ignore layer (do not stitch any objects in this layer)"),

    # L10N command that affects entire document
    "origin": N_("Origin for exported embroidery files"),

    # L10N command that affects entire document
    "stop_position": N_("Jump destination for Stop commands (a.k.a. \"Frame Out position\")."),
}

OBJECT_COMMANDS = ["starting_point", "ending_point", "target_point", "autoroute_start", "autoroute_end",
                   "stop", "trim", "ignore_object", "satin_cut_point"]
HIDDEN_CONNECTOR_COMMANDS = ["starting_point", "ending_point", "autoroute_start", "autoroute_end", "satin_cut_point"]
FREE_MOVEMENT_OBJECT_COMMANDS = ["autoroute_start", "autoroute_end"]
LAYER_COMMANDS = ["ignore_layer"]
GLOBAL_COMMANDS = ["origin", "stop_position"]


class CommandParseError(Exception):
    pass


class BaseCommand(object):
    @property
    @cache
    def description(self):
        return get_command_description(self.command)

    def parse_symbol(self):
        if self.symbol.tag != SVG_SYMBOL_TAG:
            raise CommandParseError("use points to non-symbol")

        self.command = self.symbol.get('id')

        if self.command.startswith('inkstitch_'):
            self.command = self.command[10:]
            # It is possible that through copy paste or whatever user action a command is defined multiple times
            # in the defs section. In this case the id will be altered with an additional number (e.g. inkstitch_trim-5)
            # Let's make sure to remove the number part to recognize the command correctly
            self.command = self.command.split("-")[0]
        else:
            raise CommandParseError("symbol is not an Ink/Stitch command")

    def get_node_by_url(self, url):
        # url will be #path12345.  Find the corresponding object.
        if url is None:
            raise CommandParseError("url is None")

        if not url.startswith('#'):
            raise CommandParseError("invalid connection url: %s" % url)

        id = url[1:]

        try:
            return self.svg.xpath(".//*[@id='%s']" % id)[0]
        except (IndexError, AttributeError):
            raise CommandParseError("could not find node by url %s" % id)


class Command(BaseCommand):
    def __init__(self, connector: inkex.PathElement) -> None:
        self.connector = connector
        self.svg = self.connector.getroottree().getroot()

        self.parse_command()

    def parse_connector_path(self) -> inkex.Path:
        path = inkex.paths.Path(self.connector.get('d')).to_superpath()
        return apply_transforms(path, self.connector)

    def parse_command(self) -> None:
        path = self.parse_connector_path()
        if len(path) == 0:
            raise CommandParseError("connector has no path information")

        neighbors = [
            self.get_node_by_url(self.connector.get(CONNECTION_START)),
            self.get_node_by_url(self.connector.get(CONNECTION_END))
        ]

        self.symbol_is_end = neighbors[0].tag != SVG_USE_TAG
        if self.symbol_is_end:
            neighbors.reverse()

        if neighbors[0].tag != SVG_USE_TAG:
            raise CommandParseError("connector does not point to a use tag")

        self.use = neighbors[0]

        self.symbol = self.get_node_by_url(neighbors[0].get(XLINK_HREF))
        self.parse_symbol()

        self.target: inkex.BaseElement = neighbors[1]

        pos = (float(self.use.get("x", 0)), float(self.use.get("y", 0)))
        transform = get_node_transform(self.use)
        target = inkex.Transform(transform).apply_to_point(pos)
        self.target_point = target

    def __repr__(self):
        return "Command('%s', %s)" % (self.command, self.target_point)

    def clone(self, new_target: inkex.BaseElement) -> inkex.BaseElement:
        """
        Clone this command and point it to the new target, positioning it relative to the new target the same as the target
        """
        group: Optional[inkex.BaseElement] = cast(Optional[inkex.BaseElement], self.connector.getparent())
        assert group is not None, "The connector should be part of a group."
        transform_relative_to_target: inkex.Transform = -self.target.composed_transform() @ group.composed_transform()

        # Clone group
        cloned_group = copy_no_children(group)
        cloned_group.transform = new_target.transform @ transform_relative_to_target
        new_target_parent = new_target.getparent()
        assert new_target_parent is not None, "The target should be a non-root element."
        new_target_parent.append(cloned_group)

        symbol = copy_no_children(self.use)
        cloned_group.append(symbol)
        point_upwards(symbol)

        # Copy connector
        connector = copy_no_children(self.connector)
        cloned_group.insert(0, connector)
        if self.symbol_is_end:
            symbol_attr = CONNECTION_END
            target_attr = CONNECTION_START
        else:


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/lib/debug/__init__.py =====

# Authors: see git history
#
# Copyright (c) 2010 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/lib/debug/debug.py =====

# Authors: see git history
#
# Copyright (c) 2010 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.

import atexit  # to save svg file on exit
import time    # to measure time of code block, use time.monotonic() instead of time.time()
import traceback
from datetime import datetime
from typing import TypeVar, Callable, Any, cast

from contextlib import contextmanager  # to measure time of with block
from pathlib import Path  # to work with paths as objects

import inkex
from lxml import etree   # to create svg file

from ..svg import line_strings_to_path
from ..svg.tags import INKSCAPE_GROUPMODE, INKSCAPE_LABEL

from .utils import safe_get
from ..utils.paths import get_ini

import logging
logger = logging.getLogger("inkstitch.debug")   # create module logger with name 'inkstitch.debug'

# See https://mypy.readthedocs.io/en/stable/generics.html#declaring-decorators
F = TypeVar('F', bound=Callable[..., Any])

# to log messages if previous debug logger is not enabled
logger_inkstich = logging.getLogger("inkstitch")   # create module logger with name 'inkstitch'

sew_stack_enabled = safe_get(get_ini(), "DEBUG", "enable_sew_stack", default=False)


# --------------------------------------------------------------------------------------------
# decorator to check if debugging is enabled
# - if debug is not enabled then decorated function is not called
def check_enabled(func):
    def decorated(self, *args, **kwargs):
        if self.enabled:
            return func(self, *args, **kwargs)

    return decorated


# unwrapping = provision for functions as arguments
# - if argument is callable then it is called and return value is used as argument
#   otherwise argument is returned as is
def _unwrap(arg):
    if callable(arg):
        return arg()
    else:
        return arg


# decorator to unwrap arguments if they are callable
#   eg: if argument is lambda function then it is called and return value is used as argument
def unwrap_arguments(func):
    def decorated(self, *args, **kwargs):
        unwrapped_args = [_unwrap(arg) for arg in args]
        unwrapped_kwargs = {name: _unwrap(value) for name, value in kwargs.items()}

        return func(self, *unwrapped_args, **unwrapped_kwargs)

    return decorated


class Debug(object):
    """Tools to help debug Ink/Stitch

    This class contains methods to log strings and SVG elements.  Strings are
    logged to debug.log, and SVG elements are stored in debug.svg to aid in
    debugging stitch algorithms.

    All functionality is gated by self.enabled.  If debugging is not enabled,
    then debug calls will consume very few resources.  Any method argument
    can be a callable, in which case it is called and the return value is
    logged instead.  This way one can log potentially expensive expressions
    by wrapping them in a lambda:

    debug.log(lambda: some_expensive_function(some_argument))

    The lambda is only called if debugging is enabled.
    """

    def __init__(self):
        self.enabled = False
        self.last_log_time = None
        self.current_layer = None
        self.group_stack = []
        self.svg_filename = None

    def enable(self):
        # determine svg filename from logger
        if len(logger.handlers) > 0 and isinstance(logger.handlers[0], logging.FileHandler):
            # determine filename of svg file from logger
            filename = Path(logger.handlers[0].baseFilename)
            self.svg_filename = filename.with_suffix(".svg")
            self.svg_filename.unlink(missing_ok=True)      # remove existing svg file

        # self.log is activated by active logger
        # - enabled only if logger first handler is FileHandler
        #   to disable "inkstitch.debug" simply set logging level to CRITICAL
        if logger.isEnabledFor(logging.INFO) and self.svg_filename is not None:
            self.enabled = True
            self.log(f"Logging enabled with svg file: {self.svg_filename}")
            self.init_svg()

        else:
            # use alternative logger to log message if logger has no handlers
            logger_inkstich.info("No handlers in logger, cannot enable logging and svg file creation")

    def init_svg(self):
        self.svg = etree.Element("svg", nsmap=inkex.NSS)
        atexit.register(self.save_svg)

    def save_svg(self):
        if self.enabled and self.svg_filename is not None:
            self.log(f"Writing svg file: {self.svg_filename}")
            tree = etree.ElementTree(self.svg)
            tree.write(str(self.svg_filename))    # lxml <5.0.0 does not support Path objects, requires string
        else:
            # use alternative logger to log message if logger has no handlers
            logger_inkstich.info(f"Saving to svg file is not activated {self.svg_filename=}")

    @check_enabled
    @unwrap_arguments
    def add_layer(self, name="Debug"):
        layer = etree.Element("g", {
            INKSCAPE_GROUPMODE: "layer",
            INKSCAPE_LABEL: name,
            "style": "display: none"
        })
        self.svg.append(layer)
        self.current_layer = layer

    @check_enabled
    @unwrap_arguments
    def open_group(self, name="Group"):
        group = etree.Element("g", {
            INKSCAPE_LABEL: name
        })

        self.log_svg_element(group)
        self.group_stack.append(group)

    @check_enabled
    @unwrap_arguments
    def close_group(self):
        if self.group_stack:
            self.group_stack.pop()

    @check_enabled
    @unwrap_arguments
    def log(self, message, *args):
        if self.last_log_time:
            message = "(+%s) %s" % (datetime.now() - self.last_log_time, message)

        self.raw_log(message, *args)

    def raw_log(self, message, *args):
        now = datetime.now()
        self.last_log_time = now

        msg = message % args
        logger.info(msg)

    # decorator to measure time of function
    def time(self, func: F) -> F:
        def decorated(*args, **kwargs):
            if self.enabled:
                self.raw_log("entering %s()", func.__name__)
                start = time.monotonic()

            result = func(*args, **kwargs)

            if self.enabled:
                end = time.monotonic()
                self.raw_log("leaving %s(), duration = %s", func.__name__, round(end - start, 6))


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/lib/debug/debugger.py =====

# Authors: see git history
#
# Copyright (c) 2024 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.


# ### General debugging notes:
# 1. to enable debugging or profiling copy DEBUG_template.toml to DEBUG.toml and edit it

# ### How create bash script for offline debugging from console
# 1. in DEBUG.toml set create_bash_script = true
# 2. call inkstitch.py extension from inkscape to create bash script named by bash_file_base in DEBUG.toml
# 3. run bash script from console

# ### Enable debugging
# 1. set debug_type to one of  - vscode, pycharm, pydev, see below for details
#      debug_type = vscode    - 'debugpy' for vscode editor
#      debug_type = pycharm   - 'pydevd-pycharm' for pycharm editor
#      debug_type = pydev     - 'pydevd' for eclipse editor
# 2. set debug_enable = true in DEBUG.toml
#    or use command line argument -d in bash script
#    or set environment variable INKSTITCH_DEBUG_ENABLE = True or 1 or yes or y

# ### Enable profiling
# 1. set profiler_type to one of - cprofile, profile, pyinstrument
#      profiler_type = cprofile    - 'cProfile' profiler
#      profiler_type = profile     - 'profile' profiler
#      profiler_type = pyinstrument- 'pyinstrument' profiler
# 2. set profile_enable = true in DEBUG.toml
#    or use command line argument -p in bash script
#    or set environment variable INKSTITCH_PROFILE_ENABLE = True or 1 or yes or y

# ### Miscelaneous notes:
# - to disable debugger when running from inkscape set disable_from_inkscape = true in DEBUG.toml
# - to change various output file names see DEBUG.toml
# - to prefer inkscape version of inkex module over pip version set prefer_pip_inkex = false in DEBUG.toml

# ###

# ### How to debug Ink/Stitch with LiClipse:
#
# 1. Install LiClipse (liclipse.com) -- no need to install Eclipse first
# 2. Start debug server as described here: http://www.pydev.org/manual_adv_remote_debugger.html
#    * follow the "Note:" to enable the debug server menu item
# 3. Copy and edit a file named "DEBUG.toml" from "DEBUG_template.toml" next to inkstitch.py in your git clone
#    and set debug_type = pydev
# 4. Run any extension and PyDev will start debugging.

# ###

# ### To debug with PyCharm:

# You must use the PyCharm Professional Edition and _not_ the Community
# Edition. Jetbrains has chosen to make remote debugging a Pro feature.
# To debug Inkscape python extensions, the extension code and Inkscape run
# independently of PyCharm, and only communicate with the debugger via a
# TCP socket. Thus, debugging is "remote," even if it's on the same machine,
# connected via the loopback interface.
#
# 1.     pip install pydev_pycharm
#
#    pydev_pycharm is versioned frequently. Jetbrains suggests installing
#    a version at least compatible with the current build. For example, if your
#    PyCharm build, as found in menu PyCharm -> About Pycharm is 223.8617.48,
#    you could do:
#        pip install pydevd-pycharm~=223.8617.48
#
# 2. From the Pycharm "Run" menu, choose "Edit Configurations..." and create a new
#    configuration. Set "IDE host name:" to  "localhost" and "Port:" to 5678.
#    You can leave the default settings for all other choices.
#
# 3. Touch a file named "DEBUG.toml" at the top of your git repo, as above
#    set debug_type = pycharm
#
# 4. Create a symbolic link in the Inkscape extensions directory to the
#    top-level directory of your git repo. On a mac, for example:
#        cd ~/Library/Application\ Support/org.inkscape.Inkscape/config/inkscape/extensions/
#        ln -s <full path to the top level of your Ink/Stitch git repo>
#    On other architectures it may be:
#        cd ~/.config/inkscape/extensions
#        ln -s <full path to the top level of your Ink/Stitch git repo>
#    Remove any other Ink/Stitch files or references to Ink/Stitch from the
#    extensions directory, or you'll see duplicate entries in the Ink/Stitch
#    extensions menu in Inkscape.
#
# 5. In Pycharm, either click on the green "bug" icon if visible in the upper
#    right or press Ctrl-D to start debugging.The PyCharm debugger pane will
#    display the message "Waiting for process connection..."
#
# 6. Do some action in Inkscape which invokes Ink/Stitch extension code, and the
#    debugger will be triggered. If you've left "Suspend after connect" checked
#    in the Run configuration, PyCharm will pause in the "self.log("Enabled
#    PyDev debugger.)" statement, below. Uncheck the box to have it continue
#    automatically to your first set breakpoint.

# ###

# ### To debug with VS Code
# see: https://code.visualstudio.com/docs/python/debugging#_command-line-debugging
#      https://code.visualstudio.com/docs/python/debugging#_debugging-by-attaching-over-a-network-connection
#
# 1. Install the Python module to debug in VS Code
#      pip install debugpy
# 2. Install the Python and Python Debugger extensions in VS Code
# 3. Copy and edit a file named "DEBUG.toml" from "DEBUG_template.toml" next to inkstitch.py in your git clone:
#    debug_type = vscode
# 4. Start the debug server in VS Code by clicking on the debug icon in the left pane
#    select "Python: Attach" from the dropdown menu and click on the green arrow.
# 5. Run Ink/Stitch and it should connect to VS Code's debugger automatically.
#
# Notes:
#   to see flask server url routes:
#      - comment out the line self.disable_logging() in run() of lib/api/server.py

# We have some ignores so you don't see errors if you don't have one or more of the debugger libraries installed.
# But in turn those ignores will cause unused-ignore errors if those libraries aren't installed...
# mypy: disable-error-code="unused-ignore"

import os
import sys

import socket  # to check if debugger is running

from .utils import safe_get  # mimic get method of dict with default value

import logging

logger = logging.getLogger("inkstitch")

# we intentionally disable flakes C901 - function is too complex, beacuse it is used only for debugging
# currently complexity is set 10 see 'make style', this means that function can have max 10 nested blocks, here we have more
# flake8: noqa: C901
def init_debugger(debug_type:str,  ini: dict):
    if debug_type == 'none':
        return

    debugger = debug_type

    try:
        if debugger == 'vscode':
            import debugpy  # type: ignore[import-untyped, import-not-found]
        elif debugger == 'pycharm':
            import pydevd_pycharm  # type: ignore[import-untyped, import-not-found]
        elif debugger == 'pydev':
            import pydevd  # type: ignore[import-untyped, import-not-found]
        elif debugger == 'file':
            pass
        else:
            raise ValueError(f"unknown debugger: '{debugger}'")

    except ImportError:
        logger.info(f"importing debugger failed (debugger disabled) for {debugger}")

    # pydevd likes to shout about errors to stderr whether I want it to or not
    with open(os.devnull, 'w') as devnull:
        stderr = sys.stderr
        sys.stderr = devnull

        try:
            if debugger == 'vscode':
                debugpy.connect(("localhost", 5678))
                debugpy.breakpoint()
            elif debugger == 'pycharm':
                pydevd_pycharm.settrace('localhost', port=5678, stdoutToServer=True,
                                        stderrToServer=True)
            elif debugger == 'pydev':
                pydevd.settrace()
            elif debugger == 'file':
                pass
            else:
                raise ValueError(f"unknown debugger: '{debugger}'")

        except socket.error as error:
            logger.info(f"Debugging: connection to {debugger} failed: %s", error)
            logger.info(f"Be sure to run 'Start debugging server' in {debugger} to enable debugging.")
        else:
            logger.info(f"Enabled '{debugger}' debugger.")

        sys.stderr = stderr


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/lib/debug/logging.py =====

# Authors: see git history
#
# Copyright (c) 2024 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.

# basic info for inkstitch logging:
# ---------------------------------
# some idea can be found in: Modern Python logging - https://www.youtube.com/watch?v=9L77QExPmI0
#
# logging vs warnings
# -------------------
# warnings - see https://docs.python.org/3/library/warnings.html
# logging  - see https://docs.python.org/3/library/logging.html
#
# In simplified terms, use "warning" to alert that a specific function is deprecated, and in all other cases, use "logging".
# Warnings are primarily intended for libraries where there's a newer solution available, but for backward compatibility
# reasons, the old functionality is retained.
#
# In complex applications like Inkstitch, it might be sensible to exclusively use one method, namely "logging",
# to unify and simplify the messaging system of such a system.
#
#
# root logger:
# ------------
# - The primary logger orchestrates all other loggers through logging.xxx() calls.
# - It should only be utilized at the application's highest level to manage the logging of all loggers.
# - It can easily disable all loggers by invoking logging.disable() and channel all warnings to logging
#   by setting logging.captureWarnings(True) with the level WARNING.
# - The configuration of all loggers can be achieved via a file, and logging.config.dictConfig(logging_dict).
#

# module logger:
# --------------
#  - Instantiate the logger by invoking logger=getLogger(name).
#      Avoid using __name__ as the name, as it generates numerous loggers per application.
#      The logger name persists globally throughout the application.
#  - Avoid configuring the module logger within the module itself;
#      instead, utilize the top-level application configuration with logging.config.
#      This allows users of the application to customize it according to their requirements.

# example of module logger:
# -------------------------
# import logging
# logger = logging.getLogger('inkstitch')  # create module logger with name 'inkstitch', but configure it at top level of app
# ...
#   logger.debug('debug message')          # example of using module logger
# ...

# top level of the application:
# ----------------------------
# - configure root and other loggers
#   - best practice is to configure from a file: eg logging.config.fileConfig('logging.conf')
#     - consider toml format for logging configuration (json, yaml, xml, dict are also possible)
#

# list of loggers in inkstitch (not complete):
# -------------------------------------------
# - root             - main logger that controls all other loggers
# - inkstitch        - suggested name for inkstitch
# - inkstitch.debug  - uses in debug module with svg file saving
#
# third-party loggers:
# --------------------
# - werkzeug         - is used by flask
# - shapely.geos     - was used by shapely but currently replaced by exceptions and warnings
#

# --------------------------------------------------------------------------------------------
import os
import sys
from pathlib import Path
from typing import Dict, Any

if sys.version_info >= (3, 11):
    import tomllib      # built-in in Python 3.11+
else:
    import tomli as tomllib

import warnings          # to control python warnings
import logging           # to configure logging
import logging.config    # to configure logging from dict

from .utils import safe_get     # mimic get method of dict with default value

logger = logging.getLogger('inkstitch')


# --------------------------------------------------------------------------------------------
# activate_logging - configure logging for inkstitch application
def activate_logging(running_as_frozen: bool, ini: dict, SCRIPTDIR: Path):
    if running_as_frozen:                          # in release mode
        activate_for_frozen()
    else:                                          # in development
        activate_for_development(ini, SCRIPTDIR)


# Configure logging in frozen (release) mode of application:
# in release mode normally we want to ignore all warnings and logging, but we can enable it by setting environment variables
#  - INKSTITCH_LOGLEVEL - logging level:
#       'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
#  - PYTHONWARNINGS, -W - warnings action controlled by python
#       actions: 'error', 'ignore', 'always', 'default', 'module', 'once'
def activate_for_frozen():
    if frozen_debug_active():
        loglevel = os.environ.get('INKSTITCH_LOGLEVEL')  # read log level from environment variable or None
        docpath = os.environ.get('DOCUMENT_PATH')  # read document path from environment variable (set by inkscape) or None

        # The end user enabled logging and warnings are redirected to the input_svg.inkstitch.log file.

        vars = {
            'loglevel': loglevel.upper(),
            'logfilename': Path(docpath).with_suffix('.inkstitch.log')  # log file is created in document path
        }
        config = expand_variables(frozen_config, vars)

        # dictConfig has access to top level variables, dict contains: ext://__main__.var
        #   - restriction: variable must be last token in string - very limited functionality, avoid using it

        # After this operation, logging will be activated, so we can use the logger.
        logging.config.dictConfig(config)  # configure root logger from dict

        logging.captureWarnings(True)                           # capture all warnings to log file with level WARNING
    else:
        logging.disable()                # globally disable all logging of all loggers
        disable_warnings()


def frozen_debug_active():
    loglevel = os.environ.get('INKSTITCH_LOGLEVEL')  # read log level from environment variable or None
    docpath = os.environ.get('DOCUMENT_PATH')  # read document path from environment variable (set by inkscape) or None
    if docpath is not None and loglevel is not None and loglevel.upper() in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        return True
    return False


def disable_warnings():
    warnings.simplefilter('ignore')  # ignore all warnings


# in development mode we want to use configuration from some LOGGING.toml file
def activate_for_development(ini: dict, SCRIPTDIR: Path):
    logging_config_file = safe_get(ini, "LOGGING", "log_config_file", default=None)
    vars: Dict[str, Any] = {'SCRIPTDIR': SCRIPTDIR}        # dynamic data for logging configuration

    if logging_config_file is not None:
        logging_config_file = Path(logging_config_file)
        if logging_config_file.exists():
            with open(logging_config_file, "rb") as f:
                devel_config = tomllib.load(f)   # -> dict
        else:
            raise FileNotFoundError(f"{logging_config_file} file not found")
    else:                                   # if LOGGING.toml file does not exist, use default logging configuration
        vars['loglevel'] = 'DEBUG'          # set log level to DEBUG
        vars['logfilename'] = SCRIPTDIR / "inkstitch.log"  # log file is created in current directory
        devel_config = development_config   # get TOML configuration from module

    configure_logging(devel_config, ini, vars)  # initialize and activate logging configuration

    logger.info("Running in development mode")
    logger.info(f"Using logging configuration from file: {logging_config_file}")
    logger.debug(f"Logging configuration: {devel_config=}")


# --------------------------------------------------------------------------------------------
# configure logging from dictionary:
#  - capture all warnings to log file with level WARNING - depends on warnings_capture
#  - set action for warnings: 'error', 'ignore', 'always', 'default', 'module', 'once' - depends on warnings_action
def configure_logging(config: dict, ini: dict, vars: dict):
    config = expand_variables(config, vars)

    # After this operation, logging will be activated, so we can use the logger.
    logging.config.dictConfig(config)  # configure loggers from dict - using loglevel, logfilename

    warnings_capture = config.get('warnings_capture', True)
    logging.captureWarnings(warnings_capture)  # capture warnings to log file with level WARNING
    warnings_action = config.get('warnings_action', 'default').lower()
    warnings.simplefilter(warnings_action)      # set action for warnings: 'error', 'ignore', 'always', ...

    disable_logging = safe_get(ini, "LOGGING", "disable_logging", default=False)
    if disable_logging:


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/lib/debug/utils.py =====

# Authors: see git history
#
# Copyright (c) 2024 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.

# this file is without: import inkex
# - we need dump argv and sys.path as is on startup from inkscape
#   - later sys.path may be modified that influences importing inkex (see prefer_pip_inkex)

import os
import sys
from pathlib import Path  # to work with paths as objects
import logging
from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from ..extensions.base import InkstitchExtension

logger = logging.getLogger("inkstitch")

# We have some ignores so you don't see errors if you don't have one or more of the profiling libraries installed.
# But in turn those ignores will cause unused-ignore errors if those libraries aren't installed...
# mypy: disable-error-code="unused-ignore"


# safe_get - get value from nested dictionary, return default if key does not exist
# - to read nested values from dict - mimic get method of dict with default value
#   example: safe_get({'a': {'b': 1}},   'a', 'b') -> 1
#            safe_get({'a': {'b': 1}},   'a', 'c', default=2) -> 2
def safe_get(dictionary: dict, *keys, default=None):
    for key in keys:
        if key not in dictionary:
            return default
        dictionary = dictionary[key]
    return dictionary


def write_offline_debug_script(debug_script_dir: Path, ini: dict) -> None:
    '''
    prepare Bash script for offline debugging from console
        arguments:
        - debug_script_dir - Path object, absolute path to directory of inkstitch.py
        - ini       - see DEBUG.toml
    '''

    # define names of files used by offline Bash script
    bash_file_base = safe_get(ini, "DEBUG", "bash_file_base", default="debug_inkstitch")
    bash_name = Path(bash_file_base).with_suffix(".sh")  # Path object
    bash_svg = Path(bash_file_base).with_suffix(".svg")  # Path object

    # check if input svg file exists in arguments, take argument that not start with '-' as file name
    svgs = [arg for arg in sys.argv[1:] if not arg.startswith('-')]
    if len(svgs) != 1:
        print(f"WARN: {len(svgs)} svg files found, expected 1, [{svgs}]. No script created in write debug script.", file=sys.stderr)
        return

    svg_file = Path(svgs[0])
    if svg_file.exists() and bash_svg.exists() and bash_svg.samefile(svg_file):
        print("WARN: input svg file is same as output svg file. No script created in write debug script.", file=sys.stderr)
        return

    import shutil  # to copy svg file
    bash_file = debug_script_dir / bash_name

    with open(bash_file, 'w') as f:  # "w" text mode, automatic conversion of \n to os.linesep
        f.write('#!/usr/bin/env bash\n')

        # cmd line arguments for debugging and profiling
        f.write(bash_parser())  # parse cmd line arguments: -d -p

        f.write(f'# python version: {sys.version}\n')   # python version

        myargs = " ".join(sys.argv[1:])
        f.write(f'# script: {sys.argv[0]}  arguments: {myargs}\n')  # script name and arguments

        # environment PATH
        f.write('# PATH:\n')
        f.write(f'#   {os.environ.get("PATH", "")}\n')
        # for p in os.environ.get("PATH", '').split(os.pathsep): # PATH to list
        #     f.write(f'#   {p}\n')

        # python module path
        f.write('# python sys.path:\n')
        for p in sys.path:
            f.write(f'#   {p}\n')

        # see static void set_extensions_env() in inkscape/src/inkscape-main.cpp
        f.write('# PYTHONPATH:\n')
        for p in os.environ.get('PYTHONPATH', '').split(os.pathsep):  # PYTHONPATH to list
            f.write(f'#   {p}\n')

        f.write(f'# copy {svg_file} to {bash_svg}\n#\n')
        shutil.copy(svg_file, debug_script_dir / bash_svg)  # copy file to bash_svg
        myargs = myargs.replace(str(svg_file), str(bash_svg))  # replace file name with bash_svg

        # see void Extension::set_environment() in inkscape/src/extension/extension.cpp
        f.write('# Export inkscape environment variables:\n')
        notexported = ['SELF_CALL']  # if an extension calls inkscape itself
        exported = ['INKEX_GETTEXT_DOMAIN', 'INKEX_GETTEXT_DIRECTORY',
                    'INKSCAPE_PROFILE_DIR', 'DOCUMENT_PATH', 'PYTHONPATH']
        for k in notexported:
            if k in os.environ:
                f.write(f'#   export {k}="{os.environ[k]}"\n')
        for k in exported:
            if k in os.environ:
                f.write(f'export {k}="{os.environ[k]}"\n')

        f.write('# signal inkstitch.py that we are running from offline script\n')
        f.write('export INKSTITCH_OFFLINE_SCRIPT="True"\n')

        f.write('# call inkstitch\n')
        f.write(f'python3 inkstitch.py {myargs}\n')
    bash_file.chmod(0o0755)  # make file executable, hopefully ignored on Windows


def bash_parser() -> str:
    return r'''
set -e   #  exit on error

# parse cmd line arguments:
#   -d enable debugging
#   -p enable profiling
#             ":..." - silent error reporting
while getopts ":dp" opt; do
  case $opt in
    d)
        export INKSTITCH_DEBUG_ENABLE="True"
        ;;
    p)
        export INKSTITCH_PROFILE_ENABLE="True"
        ;;
    \?)
        echo "Invalid option: -$OPTARG" >&2
        exit 1
        ;;
    :)
        echo "Option -$OPTARG requires an argument." >&2
        exit 1
        ;;
  esac
done

'''


def reorder_sys_path() -> None:
    '''
    change sys.path to prefer pip installed inkex over inkscape bundled inkex
    '''
    # see static void set_extensions_env() in inkscape/src/inkscape-main.cpp
    # what we do:
    # - move inkscape extensions path to the end of sys.path
    # - we compare PYTHONPATH with sys.path and move PYTHONPATH to the end of sys.path
    #   - also user inkscape extensions path is moved to the end of sys.path - may cause problems?
    #   - path for deprecated-simple are removed from sys.path, will be added later by importing inkex

    # PYTHONPATH to list
    pythonpath = os.environ.get('PYTHONPATH', '').split(os.pathsep)
    # remove pythonpath from sys.path
    sys.path = [p for p in sys.path if p not in pythonpath]
    # remove deprecated-simple, it will be added later by importing inkex
    pythonpath = [p for p in pythonpath if not p.endswith('deprecated-simple')]
    # remove nonexisting paths
    pythonpath = [p for p in pythonpath if os.path.exists(p)]
    # add pythonpath to the end of sys.path
    sys.path.extend(pythonpath)


# -----------------------------------------------------------------------------
# try to resolve debugger type from ini file or cmd line of bash
def resolve_debug_type(ini: dict) -> str:
    # enable/disable debugger from bash: -d
    if os.environ.get('INKSTITCH_DEBUG_ENABLE', '').lower() in ['true', '1', 'yes', 'y']:
        debug_enable = True
    else:
        debug_enable = safe_get(ini, "DEBUG", "debug_enable", default=False)  # enable debugger on startup from ini

    debug_type = safe_get(ini, "DEBUG", "debug_type", default="none")  # debugger type vscode, pycharm, pydevd
    if not debug_enable:
        debug_type = 'none'



===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/lib/elements/__init__.py =====

# Authors: see git history
#
# Copyright (c) 2010 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.

from .clone import Clone
from .element import EmbroideryElement
from .empty_d_object import EmptyDObject
from .fill_stitch import FillStitch
from .image import ImageObject
from .satin_column import SatinColumn
from .stroke import Stroke
from .text import TextObject
from .utils.nodes import iterate_nodes, node_to_elements, nodes_to_elements


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/lib/elements/clone.py =====

# Authors: see git history
#
# Copyright (c) 2010 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.

from contextlib import contextmanager
from math import degrees
from typing import Dict, Generator, List, Optional, Tuple, Any, cast

from inkex import BaseElement, Title, Transform, Vector2d
from lxml.etree import _Comment
from shapely import Geometry, MultiLineString, Point as ShapelyPoint

from ..commands import (find_commands, is_command_symbol,
                        point_command_symbols_up)
from ..i18n import _
from ..stitch_plan.stitch_group import StitchGroup
from ..svg.path import get_node_transform
from ..svg.svg import copy_no_children
from ..svg.tags import (CONNECTION_END, CONNECTION_START, EMBROIDERABLE_TAGS,
                        INKSTITCH_ATTRIBS, SVG_GROUP_TAG, SVG_SYMBOL_TAG,
                        SVG_USE_TAG)
from ..utils import cache
from .element import EmbroideryElement, param
from .validation import ValidationWarning


class CloneWarning(ValidationWarning):
    name = _("Clone Object")
    description = _("There are one or more clone objects in this document.  "
                    "Ink/Stitch can work with clones, but you are limited to set a very few parameters. ")
    steps_to_solve = [
        _("If you want to convert the clone into a real element, follow these steps:"),
        _("* Select the clone"),
        _("* Run: Extensions > Ink/Stitch > Edit > Unlink Clone")
    ]


class Clone(EmbroideryElement):
    name = "Clone"
    element_name = _("Clone")

    def __init__(self, node: BaseElement) -> None:
        super(Clone, self).__init__(node)

    @property
    @param('clone', _("Clone"), type='toggle', inverse=False, default=True)
    def clone(self) -> bool:
        return self.get_boolean_param("clone", True)

    @property
    @param('angle',
           _('Custom fill angle'),
           tooltip=_("This setting will apply a custom fill angle for the clone."),
           unit='deg',
           type='float')
    @cache
    def clone_fill_angle(self) -> float:
        return self.get_float_param('angle')

    @property
    @param('flip_angle',
           _('Flip angle'),
           tooltip=_(
               "Flip automatically calculated angle if it appears to be wrong."),
           type='boolean',
           default=False)
    @cache
    def flip_angle(self) -> bool:
        return self.get_boolean_param('flip_angle', False)

    def get_cache_key_data(self, previous_stitch: Any, next_element: EmbroideryElement) -> List[str]:
        source_node = self.node.href
        source_elements = self.clone_to_elements(source_node)
        return [element.get_cache_key(previous_stitch, next_element) for element in source_elements]

    def clone_to_elements(self, node: BaseElement) -> List[EmbroideryElement]:
        # Only used in get_cache_key_data, actual embroidery uses nodes_to_elements+iterate_nodes
        from .utils.nodes import node_to_elements
        elements = []
        if node.tag in EMBROIDERABLE_TAGS:
            elements = node_to_elements(node, True)
        elif node.tag == SVG_GROUP_TAG:
            for child in node.iterdescendants():
                elements.extend(self.clone_to_elements(child))
        return elements

    def to_stitch_groups(self, last_stitch_group: Optional[StitchGroup], next_element: Optional[EmbroideryElement] = None) -> List[StitchGroup]:
        if not self.clone:
            return []

        with self.clone_elements() as elements:
            if not elements:
                return []
            stitch_groups = []

            next_elements = [next_element]
            if len(elements) > 1:
                next_elements = cast(List[Optional[EmbroideryElement]], elements[1:]) + next_elements
            for element, next_element in zip(elements, next_elements):
                # Using `embroider` here to get trim/stop after commands, etc.
                element_stitch_groups = element.embroider(last_stitch_group, next_element)
                if len(element_stitch_groups):
                    last_stitch_group = element_stitch_groups[-1]
                    stitch_groups.extend(element_stitch_groups)

            return stitch_groups

    @property
    def first_stitch(self) -> Optional[ShapelyPoint]:
        first, last = self.first_and_last_element()
        if first:
            return first.first_stitch
        return None

    def uses_previous_stitch(self) -> bool:
        first, last = self.first_and_last_element()
        if first:
            return first.uses_previous_stitch()
        return False

    def uses_next_element(self) -> bool:
        first, last = self.first_and_last_element()
        if last:
            return last.uses_next_element()
        return False

    @cache
    def first_and_last_element(self) -> Tuple[Optional[EmbroideryElement], Optional[EmbroideryElement]]:
        with self.clone_elements() as elements:
            if len(elements):
                return elements[0], elements[-1]
        return None, None

    @contextmanager
    def clone_elements(self) -> Generator[List[EmbroideryElement], None, None]:
        """
        A context manager method which yields a set of elements representing the cloned element(s) href'd by this clone's element.
        Cleans up after itself afterwards.
        This is broken out from to_stitch_groups for testing convenience, primarily.
        Could possibly be refactored into just a generator - being a context manager is mainly to control the lifecycle of the elements
        that are cloned (again, for testing convenience primarily)
        """
        from .utils.nodes import iterate_nodes, nodes_to_elements

        cloned_nodes = self.resolve_clone()
        try:
            # In a try block so we can ensure that the cloned_node is removed from the tree in the event of an exception.
            # Otherwise, it might be left around on the document if we throw for some reason.
            yield nodes_to_elements(iterate_nodes(cloned_nodes[0]))
        finally:
            # Remove the "manually cloned" tree.
            for cloned_node in cloned_nodes:
                cloned_node.delete()

    def resolve_clone(self, recursive: bool = True) -> List[BaseElement]:
        """
        "Resolve" this clone element by copying the node it hrefs as if unlinking the clone in Inkscape.
        The node will be added as a sibling of this element's node, with its transform and style applied.
        The fill angles for resolved elements will be rotated per the transform and clone_fill_angle properties of the clone.

        :param recursive: Recursively "resolve" all child clones in the same manner
        :returns: A list where the first element is the "resolved" node, and zero or more commands attached to that node
        """
        parent: Optional[BaseElement] = self.node.getparent()
        assert parent is not None, f"Element {self.node.get_id()} should have a parent"
        source_node: Optional[BaseElement] = self.node.href
        assert source_node is not None, f"Target of {self.node.get_id()} was None!"
        source_parent: Optional[BaseElement] = source_node.getparent()
        assert source_parent is not None, f"Target {source_node.get_id()} of {self.node.get_id()} should have a parent"
        cloned_node = clone_with_fixup(parent, source_node)

        if recursive:
            # Recursively resolve all clones as if the clone was in the same place as its source
            source_parent.add(cloned_node)

            if is_clone(cloned_node):
                cloned_node = cloned_node.replace_with(Clone(cloned_node).resolve_clone()[0])
            else:
                clones: List[BaseElement] = [n for n in cloned_node.iterdescendants() if is_clone(n)]


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/lib/elements/element.py =====

# Authors: see git history
#
# Copyright (c) 2010 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.
from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from copy import deepcopy
from typing import Any, Callable, List, Optional, TypeVar

import inkex
import numpy as np
from inkex import BaseElement, Color, bezier
from shapely import Point as ShapelyPoint
from shapely.ops import nearest_points

from ..commands import Command, find_commands
from ..debug.debug import debug
from ..exceptions import InkstitchException, format_uncaught_exception
from ..i18n import _
from ..marker import get_marker_elements_cache_key_data
from ..metadata import InkStitchMetadata
from ..patterns import apply_patterns, get_patterns_cache_key_data
from ..stitch_plan import StitchGroup
from ..stitch_plan.lock_stitch import (LOCK_DEFAULTS, AbsoluteLock, CustomLock,
                                       LockStitch, SVGLock)
from ..svg import (PIXELS_PER_MM, apply_transforms, convert_length,
                   get_node_transform)
from ..svg.clip import get_clip_path
from ..svg.tags import INKSCAPE_LABEL, INKSTITCH_ATTRIBS
from ..utils import DotDict, Point, cache
from ..utils.cache import (CacheKeyGenerator, get_stitch_plan_cache,
                           is_cache_disabled)


class Param(object):
    def __init__(self, name, description, unit=None, values=[], type=None, group=None, inverse=False,
                 options=[], default=None, tooltip=None, sort_index=0, select_items=None, enables=None):
        self.name = name
        self.description = description
        self.unit = unit
        self.values = values or [""]
        self.type = type
        self.group = group
        self.inverse = inverse
        self.options = options
        self.default = default
        self.tooltip = tooltip
        self.sort_index = sort_index
        self.select_items = select_items
        self.enables = enables

    def __repr__(self):
        return "Param(%s)" % vars(self)


# See https://mypy.readthedocs.io/en/stable/generics.html#declaring-decorators
F = TypeVar('F', bound=Callable[..., Any])


# Decorate a member function or property with information about
# the embroidery parameter it corresponds to
def param(*args, **kwargs) -> Callable[[F], F]:
    p = Param(*args, **kwargs)

    def decorator(func: F) -> F:
        # Functions don't have the `param` attribute defined, but we tack it on anyway
        func.param = p  # type:ignore[attr-defined]
        return func

    return decorator


class EmbroideryElement(object):
    def __init__(self, node: BaseElement):
        self.node = node

    @property
    def id(self):
        return self.node.get('id')

    @classmethod
    def get_params(cls):
        params = []
        for attr in dir(cls):
            prop = getattr(cls, attr)
            if isinstance(prop, property):
                # The 'param' attribute is set by the 'param' decorator defined above.
                fget = prop.fget
                if fget is not None and hasattr(fget, 'param'):
                    params.append(fget.param)
        return params

    @cache
    def get_param(self, param, default):
        value = self.node.get(INKSTITCH_ATTRIBS[param], "").strip()
        return value or default

    @cache
    def get_boolean_param(self, param, default=None):
        value = self.get_param(param, default)

        if isinstance(value, bool):
            return value
        else:
            return value and (value.lower() in ('yes', 'y', 'true', 't', '1'))

    @cache
    def get_float_param(self, param, default=None):
        try:
            value = float(self.get_param(param, default))
        except (TypeError, ValueError):
            value = default

        if value is None:
            return value

        if param.endswith('_mm'):
            value = value * PIXELS_PER_MM

        return value

    @cache
    def get_int_param(self, param, default=None):
        try:
            value = int(self.get_param(param, default))
        except (TypeError, ValueError):
            return default

        if param.endswith('_mm'):
            value = int(value * PIXELS_PER_MM)

        return value

    # returns 2 float values as a numpy array
    # if a single number is given in the param, it will apply to both returned values.
    # Not cached the cache will crash if the default is a numpy array.
    # The ppoperty calling this will need to cache itself and can safely do so since it has no parameters
    def get_split_float_param(self, param, default=(0, 0)):
        default = np.array(default)  # type coersion in case the default is a tuple

        raw = self.get_param(param, "")
        parts = raw.split()
        try:
            if len(parts) == 0:
                return default
            elif len(parts) == 1:
                a = float(parts[0])
                return np.array([a, a])
            else:
                a = float(parts[0])
                b = float(parts[1])
                return np.array([a, b])
        except (TypeError, ValueError):
            return default

    # not cached
    def get_split_mm_param_as_px(self, param, default):
        return self.get_split_float_param(param, default) * PIXELS_PER_MM

    # returns an array of multiple space separated int values
    @cache
    def get_multiple_int_param(self, param, default="0"):
        params = self.get_param(param, default).split(" ")
        try:
            params = [int(param) for param in params if param]
        except (TypeError, ValueError):
            params = [int(default)]

        if param.endswith('_mm'):
            params = [value * PIXELS_PER_MM for value in params]

        return params

    # returns an array of multiple space separated float values
    @cache
    def get_multiple_float_param(self, param, default="0"):
        params = self.get_param(param, default).split(" ")


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/lib/elements/empty_d_object.py =====

# Authors: see git history
#
# Copyright (c) 2010 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.

from ..i18n import _
from ..svg.tags import INKSCAPE_LABEL
from .element import EmbroideryElement
from .validation import ObjectTypeWarning


class EmptyD(ObjectTypeWarning):
    name = _("EmptyD")
    description = _("There is an invalid object in the document without geometry information.")
    steps_to_solve = [
        _('* Run Extensions > Ink/Stitch > Troubleshoot > Cleanup Document...')
    ]


class EmptyDObject(EmbroideryElement):
    name = "EmtpyD"
    element_name = _("Empty Path")

    def validation_warnings(self):
        label = self.node.get(INKSCAPE_LABEL) or self.node.get("id")
        yield EmptyD((0, 0), label)

    @property
    def shape(self):
        return

    @property
    def first_stitch(self):
        return None

    @property
    def color(self):
        # We are not able to sitch this element, but some method calling the element may require a color definition.
        # So let's simply define a black color
        return 'black'

    def to_stitch_groups(self, last_stitch_group, next_element=None):
        return []


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/lib/elements/fill_stitch.py =====

# Authors: see git history
#
# Copyright (c) 2010 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.

import math
import re

import numpy as np
from inkex import Color, ColorError, LinearGradient
from shapely import geometry as shgeo
from shapely import set_precision
from shapely.errors import GEOSException
from shapely.ops import nearest_points
from shapely.validation import explain_validity, make_valid

from .. import tiles
from ..i18n import _
from ..marker import get_marker_elements
from ..stitch_plan import StitchGroup
from ..stitches import (tatami_fill, circular_fill, contour_fill, cross_stitch,
                        guided_fill, legacy_fill, linear_gradient_fill,
                        meander_fill, tartan_fill)
from ..stitches.linear_gradient_fill import gradient_angle
from ..stitches.running_stitch import bean_stitch
from ..stitches.utils.cross_stitch import CrossGeometries
from ..svg import PIXELS_PER_MM
from ..svg.tags import INKSCAPE_LABEL
from ..tartan.utils import get_tartan_settings, get_tartan_stripes
from ..utils import cache
from ..utils.geometry import ensure_multi_polygon
from ..utils.param import ParamOption
from .element import EmbroideryElement, param
from .validation import ValidationError, ValidationWarning


class SmallShapeWarning(ValidationWarning):
    name = _("Small Fill")
    description = _("This fill object is so small that it would probably look better as running stitch or satin column. "
                    "For very small shapes, fill stitch is not possible, and Ink/Stitch will use running stitch around "
                    "the outline instead.")


class ExpandWarning(ValidationWarning):
    name = _("Expand")
    description = _("The expand parameter for this fill object cannot be applied. "
                    "Ink/Stitch will ignore it and will use original size instead.")


class UnderlayInsetWarning(ValidationWarning):
    name = _("Inset")
    description = _("The underlay inset parameter for this fill object cannot be applied. "
                    "Ink/Stitch will ignore it and will use the original size instead.")


class MissingGuideLineWarning(ValidationWarning):
    name = _("Missing Guideline")
    description = _('This object is set to "Guided Fill", but has no guide line.')
    steps_to_solve = [
        _('* Create a stroke object'),
        _('* Select this object and run Extensions > Ink/Stitch > Edit > Selection to guide line')
    ]


class DisjointGuideLineWarning(ValidationWarning):
    name = _("Disjointed Guide Line")
    description = _("The guide line of this object isn't within the object borders. "
                    "The guide line works best, if it is within the target element.")
    steps_to_solve = [
        _('* Move the guide line into the element')
    ]


class MultipleGuideLineWarning(ValidationWarning):
    name = _("Multiple Guide Lines")
    description = _("This object has multiple guide lines, but only the first one will be used.")
    steps_to_solve = [
        _("* Remove all guide lines, except for one.")
    ]


class UnconnectedWarning(ValidationWarning):
    name = _("Unconnected")
    description = _("Fill: This object is made up of unconnected shapes. "
                    "Ink/Stitch doesn't know what order to stitch them in.  Please break this "
                    "object up into separate shapes.")
    steps_to_solve = [
        _('* Extensions > Ink/Stitch > Fill Tools > Break Apart Fill Objects'),
    ]


class BorderCrossWarning(ValidationWarning):
    name = _("Border crosses itself")
    description = _("Fill: The border crosses over itself. This may lead into unconnected shapes. "
                    "Please break this object into separate shapes to indicate in which order it should be stitched in.")
    steps_to_solve = [
        _('* Extensions > Ink/Stitch > Fill Tools > Break Apart Fill Objects')
    ]


class StrokeAndFillWarning(ValidationWarning):
    name = _("Fill and Stroke color")
    description = _("Element has both a fill and a stroke color. It is recommended to use two separate elements instead.")
    steps_to_solve = [
        _('* Duplicate the element. Remove stroke color from the first and fill color from the second.'),
        _('* Adapt the shape of the second element to compensate for push and pull fabric distortion.')
    ]


class NoGradientWarning(ValidationWarning):
    name = _("No linear gradient color")
    description = _("Linear Gradient has no linear gradient color.")
    steps_to_solve = [
        _('* Open the Fill and Stroke dialog.'),
        _('* Set a linear gradient as a fill and adapt colors to your liking.')
    ]


class NoTartanStripeWarning(ValidationWarning):
    name = _("No stripes to render")
    description = _("Tartan fill: There is no active fill stripe to render")
    steps_to_solve = [
        _('Go to Extensions > Ink/Stitch > Fill Tools > Tartan and adjust stripe settings:'),
        _('* Check if stripes are active'),
        _('* Check the minimum stripe width setting and the scale factor')
    ]


class DefaultTartanStripeWarning(ValidationWarning):
    name = _("No customized pattern")
    description = _("Tartan fill: Using default pattern")
    steps_to_solve = [
        _('Go to Extensions > Ink/Stitch > Tools: Fill > Tartan and adjust stripe settings:'),
        _('* Customize your pattern')
    ]


class CrossPatternCoverageWarning(ValidationWarning):
    name = _("Cross stitch: shape too small")
    description = _('This shape is too small to fit a cross. Please adapt params and/or shape.')
    steps_to_solve = [
        _('* Change the pattern size'),
        _('* Or adapt the grid offset or move the shape'),
        _('* Or increase the expand value or increase shape size'),
        _('* Or decrease the fill coverage value'),
        _('* Or use Extensions > Ink/Stitch > Tools: Fill > Cross Stitch Assistant, adapt settings and pixelate the shape')
    ]


class InvalidShapeError(ValidationError):
    name = _("This shape is invalid")
    description = _('Fill: This shape cannot be stitched out. Please try to repair it with the "Break Apart Fill Objects" extension.')
    steps_to_solve = [
        _('* Extensions > Ink/Stitch > Fill Tools > Break Apart Fill Objects')
    ]


class FillStitch(EmbroideryElement):
    name = "FillStitch"
    element_name = _("FillStitch")

    @property
    @param('fill', _('Fill stitching'), type='toggle', default=True, sort_index=1)
    def fill(self):
        return self.get_boolean_param('fill', True)

    _fill_methods = [ParamOption('tatami_fill', _("Tatami Fill")),
                     ParamOption('circular_fill', _("Circular Fill")),
                     ParamOption('contour_fill', _("Contour Fill")),
                     ParamOption('cross_stitch', _("Cross Stitch")),
                     ParamOption('guided_fill', _("Guided Fill")),
                     ParamOption('linear_gradient_fill', _("Linear Gradient Fill")),
                     ParamOption('meander_fill', _("Meander Fill")),
                     ParamOption('tartan_fill', _("Tartan Fill")),
                     ParamOption('legacy_fill', _("Legacy Fill"))]

    @property
    @param('fill_method',
           _('Fill method'),
           type='combo',


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/lib/elements/image.py =====

# Authors: see git history
#
# Copyright (c) 2010 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.

from shapely import make_valid
from shapely.errors import GEOSException
from shapely.geometry import MultiPolygon, Polygon

from ..i18n import _
from ..svg.path import get_node_transform
from ..utils.geometry import ensure_multi_polygon
from .element import EmbroideryElement
from .validation import ObjectTypeWarning


class ImageTypeWarning(ObjectTypeWarning):
    name = _("Image")
    description = _("Ink/Stitch can't work with objects like images.")
    steps_to_solve = [
        _('* Redraw the image with the pen (P) or bezier (B) tool'),
        _('* Alternatively convert your image into a path: Path > Trace Bitmap... (Shift+Alt+B) '
          '(further steps might be required)'),
        _('* To convert the image for cross stitching, use Tools: Fill > Cross Stitch Assistant')
    ]


class ImageObject(EmbroideryElement):
    name = "Image"

    @property
    def shape(self):
        shape = self._get_clipped_path()

        if shape.is_valid:
            # set_precision to avoid FloatingPointErrors
            return ensure_multi_polygon(shape, 3)

        shape = make_valid(shape)

        return ensure_multi_polygon(shape, 3)

    def _get_clipped_path(self):
        if self.clip_shape is None:
            return self.original_shape

        # make sure clip path and shape are valid
        clip_path = make_valid(self.clip_shape)
        shape = make_valid(self.original_shape)

        try:
            intersection = clip_path.intersection(shape)
        except GEOSException:
            return self.original_shape

        return intersection

    @property
    def original_shape(self):
        # shapely's idea of "holes" are to subtract everything in the second set
        # from the first. So let's at least make sure the "first" thing is the
        # biggest path.
        paths = self.paths
        paths.sort(key=lambda point_list: Polygon(point_list).area, reverse=True)
        if len(paths) > 1:
            shape = MultiPolygon([(paths[0], paths[1:])])
        else:
            shape = MultiPolygon([paths])
        return shape

    def center(self):
        parent = self.node.getparent()
        assert parent is not None, "This should be part of a tree and therefore have a parent"
        transform = get_node_transform(parent)
        center = self.node.bounding_box(transform).center
        return center

    def validation_warnings(self):
        yield ImageTypeWarning(self.center())

    def to_stitch_groups(self, last_stitch_group, next_element):
        return []

    def first_stitch(self):
        return None


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/lib/elements/marker.py =====

# Authors: see git history
#
# Copyright (c) 2010 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.

import inkex

from ..i18n import _
from .element import EmbroideryElement
from .validation import ObjectTypeWarning


class MarkerWarning(ObjectTypeWarning):
    name = _("Marker Element")
    description = _("This element will not be embroidered. "
                    "It will be applied to objects in the same group. Objects in sub-groups will be ignored.")
    steps_to_solve = [
        _("Turn back to normal embroidery element mode, remove the marker:"),
        _('* Open the Fill and Stroke panel (Objects > Fill and Stroke)'),
        _('* Go to the Stroke style tab'),
        _('* Under "Markers" choose the first (empty) option in the first dropdown list.')
    ]


class MarkerObject(EmbroideryElement):
    name = "Marker"

    def validation_warnings(self):
        repr_point = next(inkex.Path(self.parse_path()).end_points)
        yield MarkerWarning(repr_point)

    def to_stitch_groups(self, last_stitch_group, next_element=None):
        return []

    def first_stitch(self):
        return None


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/lib/elements/satin_column.py =====

# Authors: see git history
#
# Copyright (c) 2010 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.

import itertools
from copy import deepcopy
from itertools import chain
from typing import List, Tuple

import numpy as np
from inkex import Path
from shapely import affinity as shaffinity
from shapely import geometry as shgeo
from shapely import set_precision
from shapely.ops import nearest_points, substring

from ..debug.debug import debug
from ..i18n import _
from ..metadata import InkStitchMetadata
from ..stitch_plan import Stitch, StitchGroup
from ..stitches import running_stitch
from ..svg import line_strings_to_coordinate_lists
from ..svg.styles import get_join_style_args
from ..utils import Point, cache, cut, cut_multiple, offset_points, prng
from ..utils.param import ParamOption
from ..utils.threading import check_stop_flag
from .element import PIXELS_PER_MM, EmbroideryElement, param
from .utils.stroke_to_satin import convert_path_to_satin, set_first_node
from .validation import ValidationError, ValidationWarning


class NotStitchableError(ValidationError):
    name = _("Not stitchable satin column")
    description = _("A satin column can be build from a single stroke or consists of two rails and optional rungs. "
                    "This satin column has a different setup.")
    steps_to_solve = [
        _('Make sure your satin column is not a combination of multiple satin columns.'),
        _('Go to our website and read how a satin column should look like https://inkstitch.org/docs/stitches/satin-column/'),
    ]


rung_message = _("Each rung should intersect both rails once.")


class ClosedPathWarning(ValidationWarning):
    name = _("Rail is a closed path")
    description = _("Rail is a closed path without a definite starting and ending point.")
    steps_to_solve = [
        _('* Select the node where you want the satin to start.'),
        _('* Click on: Break path at selected nodes.')
    ]


class DanglingRungWarning(ValidationWarning):
    name = _("Rung doesn't intersect rails")
    description = _("Satin column: A rung doesn't intersect both rails.") + " " + rung_message


class NoRungWarning(ValidationWarning):
    name = _("Satin has no rungs")
    description = _("Rungs control the stitch direction in satin columns. It is best pratice to use them.")
    steps_to_solve = [
        _('* With the selected object press "P" to activate the pencil tool.'),
        _('* Hold "Shift" while drawing a rung.')
    ]


class TooManyIntersectionsWarning(ValidationWarning):
    name = _("Rung intersects too many times")
    description = _("Satin column: A rung intersects a rail more than once.") + " " + rung_message


class StrokeSatinWarning(ValidationWarning):
    name = _("Simple Satin")
    description = ("If you need more control over the stitch directions within this satin column, convert it to a real satin path")
    steps_to_solve = [
        _('* Select the satin path'),
        _('* Run Extensions > Ink/Stitch > Tools: Satin > Stroke to Satin')
    ]


class NarrowSatinWarning(ValidationWarning):
    name = _("Narrow Satin")
    description = _("This element renders as a satin, but it is too narrow.")
    steps_to_solve = [
        _("* Increase stroke width."),
        _("Ink/Stitch will not register elements with a stroke width underneath 0.3 mm as satin, but it is recommended to stay above 1mm."),
    ]


class TwoRungsWarning(ValidationWarning):
    name = _("Satin has exactly two rungs")
    description = _("There are exactly two rungs. This may lead to false rail/rung detection.")
    steps_to_solve = [
        _('* With the selected object press "P" to activate the pencil tool.'),
        _('* Hold "Shift" while drawing a rung.')
    ]


class UnequalPointsWarning(ValidationWarning):
    name = _("Unequal number of points")
    description = _("Satin column: There are no rungs and rails have an unequal number of points.")
    steps_to_solve = [
        _('The easiest way to solve this issue is to add one or more rungs. '),
        _('Rungs control the stitch direction in satin columns.'),
        _('* With the selected object press "P" to activate the pencil tool.'),
        _('* Hold "Shift" while drawing the rung.')
    ]


class SatinColumn(EmbroideryElement):
    name = "SatinColumn"
    element_name = _("Satin Column")

    def __init__(self, *args, **kwargs):
        super(SatinColumn, self).__init__(*args, **kwargs)

    @property
    @param('satin_column', _('Custom satin column'), type='toggle')
    def satin_column(self):
        return self.get_boolean_param("satin_column")

    _satin_methods = [ParamOption('satin_column', _('Satin Column')),
                      ParamOption('e_stitch', _('"E" Stitch')),
                      ParamOption('s_stitch', _('"S" Stitch')),
                      ParamOption('zigzag', _('Zig-zag'))]

    @property
    @param('satin_method',
           _('Method'),
           type='combo',
           default=0,
           options=_satin_methods,
           sort_index=0)
    def satin_method(self):
        return self.get_param('satin_method', 'satin_column')

    @property
    @param('random_width_decrease_percent',
           _('Random percentage of satin width decrease'),
           tooltip=_('shorten stitch across rails at most this percent. '
                     'Two values separated by a space may be used for an asymmetric effect.'),
           default=0, type='float', unit=_("% (each side)"), sort_index=91)
    @cache
    def random_width_decrease(self):
        return self.get_split_float_param("random_width_decrease_percent", (0, 0)) / 100

    @property
    @param('random_width_increase_percent',
           _('Random percentage of satin width increase'),
           tooltip=_('lengthen stitch across rails at most this percent. '
                     'Two values separated by a space may be used for an asymmetric effect.'),
           default=0, type='float', unit=_("% (each side)"), sort_index=90)
    @cache
    def random_width_increase(self):
        return self.get_split_float_param("random_width_increase_percent", (0, 0)) / 100

    @property
    @param('random_zigzag_spacing_percent',
           _('Random zig-zag spacing percentage'),
           tooltip=_('Amount of random jitter added to zigzag spacing.'),
           default=0, type='float', unit="± %", sort_index=92)
    def random_zigzag_spacing(self):
        # peak-to-peak distance between zigzags
        return max(self.get_float_param("random_zigzag_spacing_percent", 0), 0) / 100

    _split_methods = [ParamOption('default', _('Default')),
                      ParamOption('simple', _('Simple')),
                      ParamOption('staggered', _('Staggered'))]

    @property
    @param('split_method',
           _('Split Method'),
           type='combo',
           tooltip=_('Display needle penetration points in simulator to see the effect of each split method.'),
           default=0,
           options=_split_methods,
           sort_index=93)
    def split_method(self):


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/lib/elements/stroke.py =====

"""Module for Stroke element."""

# Authors: see git history
#
# Copyright (c) 2010 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.

from math import ceil

import shapely.geometry as shgeo
from shapely.errors import GEOSException

from ..i18n import _
from ..marker import get_marker_elements
from ..stitch_plan import StitchGroup
from ..stitches.ripple_stitch import ripple_stitch
from ..stitches.running_stitch import bean_stitch, running_stitch, zigzag_stitch
from ..threads import ThreadColor
from ..utils import Point, cache
from ..utils.param import ParamOption
from .element import EmbroideryElement, param
from .satin_column import SatinColumn
from .validation import ValidationWarning


class MultipleGuideLineWarning(ValidationWarning):
    """Warning for multiple guide lines."""

    name = _("Multiple Guide Lines")
    description = _("This object has multiple guide lines, but only the first one will be used.")
    steps_to_solve = [_("* Remove all guide lines, except for one.")]


class TooNarrowSatinWarning(ValidationWarning):
    """Stroke is too narrow to render as satin."""

    name = _("Too narrow satin")
    description = _("This element renders as running stitch while it has a satin column parameter.")
    steps_to_solve = [
        _("* Increase stroke width."),
        _("Whether or not a stroke can be rendered as a satin, depends on the stroke width and the preference value for the minimum satin stroke "
          "width. The stroke width has to be wider than the preference setting, otherwise this element will be treated as a running stitch. To not "
          "produce hard stitches, it is recommended to only use satins wider than 1mm."),
    ]


class Stroke(EmbroideryElement):
    """Stroke element."""

    name = "Stroke"
    element_name = _("Stroke")

    @property
    @param("satin_column", _("Running stitch along paths"), type="toggle", inverse=True)
    def satin_column(self):
        """Return True if satin column is enabled."""
        return self.get_boolean_param("satin_column")

    @property
    def color(self):
        """Return the color of the stroke."""
        color = self.stroke_color
        if self.cutwork_needle is not None:
            color = ThreadColor(color, description=self.cutwork_needle, chart=self.cutwork_needle)
        return color

    @property
    def cutwork_needle(self):
        """Return cutwork needle number."""
        needle = self.get_int_param("cutwork_needle") or None
        if needle is not None:
            needle = f"Cut {needle}"
        return needle

    _stroke_methods = [
        ParamOption("running_stitch", _("Running Stitch / Bean Stitch")),
        ParamOption("ripple_stitch", _("Ripple Stitch")),
        ParamOption("zigzag_stitch", _("ZigZag Stitch")),
        ParamOption("manual_stitch", _("Manual Stitch")),
    ]

    @property
    @param(
        "stroke_method",
        _("Method"),
        type="combo",
        default=0,
        options=_stroke_methods,
        sort_index=0,
    )
    def stroke_method(self):
        """Return the stroke method."""
        return self.get_param("stroke_method", "running_stitch")

    @property
    @param(
        "repeats",
        _("Repeats"),
        tooltip=_("Defines how many times to run down and back along the path."),
        type="int",
        select_items=[
            ("stroke_method", "running_stitch"),
            ("stroke_method", "ripple_stitch"),
            ("stroke_method", "zigzag_stitch"),
        ],
        default="1",
        sort_index=2,
    )
    def repeats(self):
        """Return the number of repeats."""
        return max(1, self.get_int_param("repeats", 1))

    @property
    @param(
        "bean_stitch_repeats",
        _("Bean stitch number of repeats"),
        tooltip=_(
            "Backtrack each stitch this many times.  "
            "A value of 1 would triple each stitch (forward, back, forward).  "
            "A value of 2 would quintuple each stitch, etc.\n\n"
            "A pattern with various repeats can be created with a list of values separated "
            "by a space."
        ),
        type="str",
        select_items=[
            ("stroke_method", "running_stitch"),
            ("stroke_method", "ripple_stitch"),
            ("stroke_method", "manual_stitch"),
            ("stroke_method", "zigzag_stitch"),
        ],
        default=0,
        sort_index=3,
    )
    def bean_stitch_repeats(self):
        """Return the number of bean stitch repeats."""
        return self.get_multiple_int_param("bean_stitch_repeats", "0")

    @property
    @param(
        "manual_pattern_placement",
        _("Manual stitch placement"),
        tooltip=_("No extra stitches will be added to the original ripple pattern and the running stitch length value will be ignored."),
        type="boolean",
        select_items=[("stroke_method", "ripple_stitch")],
        default=False,
        sort_index=3,
    )
    def manual_pattern_placement(self):
        """Return True if manual pattern placement is enabled."""
        return self.get_boolean_param("manual_pattern_placement", False)

    @property
    @param(
        "running_stitch_length_mm",
        _("Running stitch length"),
        tooltip=_(
            "Length of stitches. Stitches can be shorter according to the stitch tolerance "
            "setting.\n"
            "It is possible to create stitch length patterns by adding multiple values separately."
        ),
        unit="mm",
        type="string",
        select_items=[
            ("stroke_method", "running_stitch"),
            ("stroke_method", "ripple_stitch"),
        ],
        default="2.5",
        sort_index=4,
    )
    def running_stitch_length(self):
        """Return the running stitch length."""
        return [max(value, 0.01) for value in self.get_multiple_float_param("running_stitch_length_mm", "2.5")]

    @property
    @param(
        "running_stitch_tolerance_mm",
        _("Stitch tolerance"),
        tooltip=_(
            "All stitches must be within this distance from the path.  "
            + "A lower tolerance means stitches will be closer together.  "


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/lib/elements/text.py =====

# Authors: see git history
#
# Copyright (c) 2010 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.

from ..i18n import _
from ..svg.path import get_node_transform
from .element import EmbroideryElement
from .validation import ObjectTypeWarning


class TextTypeWarning(ObjectTypeWarning):
    name = _("Text")
    description = _("Ink/Stitch cannot work with objects like text.")
    steps_to_solve = [
        _('* Text: Create your own letters or try the lettering tool:'),
        _('- Extensions > Ink/Stitch > Lettering')
    ]


class TextObject(EmbroideryElement):
    name = "Text"
    element_name = _("Text")

    def pointer(self):
        parent = self.node.getparent()
        assert parent is not None, "This should be part of a tree and therefore have a parent"
        transform = get_node_transform(parent)
        point = self.node.bounding_box(transform).center

        return point

    def validation_warnings(self):
        yield TextTypeWarning(self.pointer())

    def to_stitch_groups(self, last_stitch_group, next_element=None):
        return []

    def first_stitch(self):
        return None


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/lib/elements/utils/nodes.py =====

# Authors: see git history
#
# Copyright (c) 2010 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.

from typing import Iterable, List, Optional

from inkex import BaseElement
from lxml.etree import Comment

from ...commands import is_command, layer_commands
from ...debug.debug import sew_stack_enabled
from ...marker import has_marker
from ...svg.tags import (CONNECTOR_TYPE, EMBROIDERABLE_TAGS,
                         INKSCAPE_GROUPMODE, NOT_EMBROIDERABLE_TAGS,
                         SVG_CLIPPATH_TAG, SVG_DEFS_TAG, SVG_GROUP_TAG,
                         SVG_IMAGE_TAG, SVG_MASK_TAG, SVG_TEXT_TAG)
from ..clone import Clone, is_clone
from ..element import EmbroideryElement
from ..empty_d_object import EmptyDObject
from ..fill_stitch import FillStitch
from ..image import ImageObject
from ..marker import MarkerObject
from ..satin_column import SatinColumn
from ..stroke import Stroke
from ..text import TextObject


def node_to_elements(node, clone_to_element=False) -> List[EmbroideryElement]:  # noqa: C901
    if node.style('display') == 'none':
        return []
    if is_clone(node) and not clone_to_element:
        # clone_to_element: get an actual embroiderable element once a clone has been defined as a clone
        return [Clone(node)]

    elif node.tag in EMBROIDERABLE_TAGS and not node.get_path():
        return [EmptyDObject(node)]

    elif has_marker(node):
        return [MarkerObject(node)]

    elif node.tag in EMBROIDERABLE_TAGS or is_clone(node):
        elements: List[EmbroideryElement] = []

        from ...sew_stack import SewStack
        sew_stack = SewStack(node)

        if not sew_stack.sew_stack_only:
            element = EmbroideryElement(node)
            if element.fill_color is not None and not element.get_style('fill-opacity', 1) == "0":
                elements.append(FillStitch(node))
            if element.stroke_color is not None:
                if element.get_boolean_param("satin_column", False) and (len(element.path) > 1 or element.stroke_width > element.satin_threshold):
                    elements.append(SatinColumn(node))
                elif not is_command(element.node):
                    elements.append(Stroke(node))
            if element.get_boolean_param("stroke_first", False):
                elements.reverse()

        if sew_stack_enabled:
            elements.append(sew_stack)

        return elements

    elif node.tag == SVG_IMAGE_TAG:
        return [ImageObject(node)]

    elif node.tag == SVG_TEXT_TAG:
        return [TextObject(node)]

    else:
        return []


def nodes_to_elements(nodes: Iterable[BaseElement]) -> List[EmbroideryElement]:
    elements = []
    for node in nodes:
        elements.extend(node_to_elements(node))

    return elements


def iterate_nodes(node: BaseElement,  # noqa: C901
                  selection: Optional[List[BaseElement]] = None,
                  troubleshoot=False) -> List[BaseElement]:
    # Postorder traversal of selected nodes and their descendants.
    # Returns all nodes if there is no selection.
    def walk(node: BaseElement, selected: bool) -> List[BaseElement]:
        nodes = []

        # lxml-stubs types are wrong, node.tag can be Comment.
        if node.tag is Comment:  # type:ignore[comparison-overlap]
            return []

        element = EmbroideryElement(node)

        if element.has_command('ignore_object'):
            return []

        if node.tag == SVG_GROUP_TAG and node.get(INKSCAPE_GROUPMODE) == "layer":
            if len(list(layer_commands(node, "ignore_layer"))):
                return []

        if (node.tag in EMBROIDERABLE_TAGS or node.tag == SVG_GROUP_TAG) and element.get_style('display', 'inline') is None:
            return []

        # defs, masks and clippaths can contain embroiderable elements
        # but should never be rendered directly.
        if node.tag in [SVG_DEFS_TAG, SVG_MASK_TAG, SVG_CLIPPATH_TAG]:
            return []

        # command connectors with a fill color set, will glitch into the elements list
        if is_command(node) or node.get(CONNECTOR_TYPE):
            return []

        if not selected:
            if selection:
                if node in selection:
                    selected = True
            else:
                # if the user didn't select anything that means we process everything
                selected = True

        for child in node:
            nodes.extend(walk(child, selected))

        if selected:
            if node.tag == SVG_GROUP_TAG:
                pass
            elif (node.tag in EMBROIDERABLE_TAGS or is_clone(node)) and not has_marker(node):
                nodes.append(node)
            # add images, text and elements with a marker for the troubleshoot extension
            elif troubleshoot and (node.tag in NOT_EMBROIDERABLE_TAGS or has_marker(node)):
                nodes.append(node)

        return nodes

    return walk(node, False)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/lib/elements/utils/stroke_to_satin.py =====

# Authors: see git history
#
# Copyright (c) 2025 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.

import sys
from math import acos, degrees

from inkex import errormsg
from numpy import convolve, diff, int32, setdiff1d, sign, zeros
from shapely import geometry as shgeo
from shapely.affinity import rotate, scale
from shapely.ops import substring

from ...i18n import _
from ...svg import PIXELS_PER_MM
from ...utils import Point, roll_linear_ring
from ...utils.geometry import remove_duplicate_points


class SelfIntersectionError(Exception):
    pass


def convert_path_to_satin(path, stroke_width, style_args, rungs_at_nodes=False):
    path = remove_duplicate_points(fix_loop(path))

    if len(path) < 2:
        # ignore paths with just one point -- they're not visible to the user anyway
        return None

    sections = list(convert_path_to_satins(path, stroke_width, style_args, rungs_at_nodes=rungs_at_nodes))

    if sections:
        joined_satin = list(sections)[0]
        for satin in sections[1:]:
            joined_satin = _merge(joined_satin, satin)
        return joined_satin
    return None


def convert_path_to_satins(path, stroke_width, style_args, rungs_at_nodes=False, depth=0):
    try:
        rails, rungs = path_to_satin(path, stroke_width, style_args, rungs_at_nodes)
        yield (rails, rungs)
    except SelfIntersectionError:
        # The path intersects itself.  Split it in two and try doing the halves
        # individually.

        if depth >= 20:
            # At this point we're slicing the path way too small and still
            # getting nowhere.  Just give up on this section of the path.
            return

        halves = split_path(path)

        for path in halves:
            for section in convert_path_to_satins(path, stroke_width, style_args, rungs_at_nodes=rungs_at_nodes, depth=depth + 1):
                yield section


def split_path(path):
    linestring = shgeo.LineString(path)
    halves = [
        list(substring(linestring, 0, 0.5, normalized=True).coords),
        list(substring(linestring, 0.5, 1, normalized=True).coords),
    ]

    return halves


def fix_loop(path):
    if path[0] == path[-1] and len(path) > 1:
        first = Point.from_tuple(path[0])
        second = Point.from_tuple(path[1])
        midpoint = (first + second) / 2
        midpoint = midpoint.as_tuple()

        return [midpoint] + path[1:] + [path[0], midpoint]
    else:
        return path


def path_to_satin(path, stroke_width, style_args, rungs_at_nodes):
    if Point(*path[0]).distance(Point(*path[-1])) < 1:
        raise SelfIntersectionError()

    path = shgeo.LineString(path)
    distance = stroke_width / 2.0

    try:
        left_rail = path.offset_curve(-distance, **style_args)
        right_rail = path.offset_curve(distance, **style_args)
    except ValueError:
        # TODO: fix this error automatically
        # Error reference: https://github.com/inkstitch/inkstitch/issues/964
        errormsg(_("Ink/Stitch cannot convert your stroke into a satin column. "
                   "Please break up your path and try again.") + '\n')
        sys.exit(1)

    if left_rail.geom_type != 'LineString' or right_rail.geom_type != 'LineString':
        # If the offset curve come out as anything but a LineString, that means the
        # path intersects itself, when taking its stroke width into consideration.
        raise SelfIntersectionError()

    rungs = generate_rungs(path, stroke_width, left_rail, right_rail, rungs_at_nodes)

    left_rail = list(left_rail.coords)
    right_rail = list(right_rail.coords)

    return (left_rail, right_rail), rungs


def get_scores(path):
    """Generate an array of "scores" of the sharpness of corners in a path

    A higher score means that there are sharper corners in that section of
    the path.  We'll divide the path into boxes, with the score in each
    box indicating the sharpness of corners at around that percentage of
    the way through the path.  For example, if scores[40] is 100 and
    scores[45] is 200, then the path has sharper corners at a spot 45%
    along its length than at a spot 40% along its length.
    """

    # need 101 boxes in order to encompass percentages from 0% to 100%
    scores = zeros(101, int32)
    path_length = path.length

    prev_point = None
    prev_direction = None
    length_so_far = 0
    for point in path.coords:
        point = Point(*point)

        if prev_point is None:
            prev_point = point
            continue

        direction = (point - prev_point).unit()

        if prev_direction is not None:
            # The dot product of two vectors is |v1| * |v2| * cos(angle).
            # These are unit vectors, so their magnitudes are 1.
            cos_angle_between = prev_direction * direction

            # Clamp to the valid range for a cosine.  The above _should_
            # already be in this range, but floating point inaccuracy can
            # push it outside the range causing math.acos to throw
            # ValueError ("math domain error").
            cos_angle_between = max(-1.0, min(1.0, cos_angle_between))

            angle = abs(degrees(acos(cos_angle_between)))

            # Use the square of the angle, measured in degrees.
            #
            # Why the square?  This penalizes bigger angles more than
            # smaller ones.
            #
            # Why degrees?  This is kind of arbitrary but allows us to
            # use integer math effectively and avoid taking the square
            # of a fraction between 0 and 1.
            scores[int(round(length_so_far / path_length * 100.0))] += angle ** 2

        length_so_far += (point - prev_point).length()
        prev_direction = direction
        prev_point = point

    return scores


def local_minima(array):
    # from: https://stackoverflow.com/a/9667121/4249120
    # This finds spots where the curvature (second derivative) is > 0.
    #
    # This method has the convenient benefit of choosing points around
    # 5% before and after a sharp corner such as in a square.
    return (diff(sign(diff(array))) > 0).nonzero()[0] + 1


def generate_rungs(path, stroke_width, left_rail, right_rail, rungs_at_nodes):


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/lib/elements/validation.py =====

# Authors: see git history
#
# Copyright (c) 2010 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.

from typing import Optional, List
from shapely.geometry import Point as ShapelyPoint

from ..utils import Point as InkstitchPoint


class ValidationMessage(object):
    '''Holds information about a problem with an element.

    Attributes:
      name - A short descriptor for the problem, such as "dangling rung"
      description - A detailed description of the problem, such as
        "One or more rungs does not intersect both rails."
      position - An optional position where the problem occurs,
        to aid the user in correcting it.  type: Point or tuple of (x, y)
      steps_to_solve - A list of operations necessary to solve the problem
    '''

    # Subclasses will fill these in.
    name: Optional[str] = None
    description: Optional[str] = None
    steps_to_solve: List[str] = []

    def __init__(self, position=None, label=""):
        if isinstance(position, ShapelyPoint):
            position = (position.x, position.y)

        self.position = InkstitchPoint(*position)
        self.label = label


class ValidationError(ValidationMessage):
    """A problem that will prevent the shape from being embroidered."""
    pass


class ValidationWarning(ValidationMessage):
    """A problem that won't prevent a shape from being embroidered.

    The user will almost certainly want to fix the warning, but if they
    don't, Ink/Stitch will do its best to process the object.
    """
    pass


class ObjectTypeWarning(ValidationMessage):
    """A shape is not a path and will not be embroidered.

    Ink/Stitch only works with paths and ignores everything else.
    The user might want the shape to be ignored, but if they
    don't, they receive information how to change this behaviour.
    """
    pass


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/lib/exceptions.py =====

# Authors: see git history
#
# Copyright (c) 2010 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.
import traceback
import sys
import platform
import subprocess
from glob import glob


class InkstitchException(Exception):
    pass


def get_os_version():
    if sys.platform == "win32":
        # To get the windows version, python functions are used
        # Using python subprocess with cmd.exe in windows is currently a security risk
        os_ver = "Windows " + platform.release() + " version: " + platform.version()
    if sys.platform == "darwin":
        # macOS command line progam provides accurate info than python functions
        mac_v1 = subprocess.run(["sw_vers"], capture_output=True, text=True)
        mac_v1 = str(mac_v1.stdout.strip())
        mac_v2 = subprocess.run(["uname",  "-m"], capture_output=True, text=True)
        mac_v2 = str(mac_v2.stdout.strip())
        os_ver = mac_v1 + "\nCPU:\t\t\t\t" + mac_v2
    if sys.platform == "linux":
        # Getting linux version method used here is for systemd and nonsystemd linux.
        try:
            ltmp = subprocess.run(["cat"] + glob("/etc/*-release"), capture_output=True, text=True)
            lnx_ver = ltmp.stdout.splitlines()
            lnx_ver = str(list(filter(lambda x: "PRETTY_NAME" in x, lnx_ver)))
            os_ver = lnx_ver[15:][:-3]
        except FileNotFoundError:
            os_ver = "Cannot get Linux distro version"

    return os_ver


def format_uncaught_exception():
    """Format the current exception as a request for a bug report.

    Call this inside an except block so that there is an exception that we can
    call traceback.format_exc() on.
    """

    # importing locally to avoid any possibility of circular import
    from lib.utils import version
    from .i18n import _

    message = ""
    message += _("Ink/Stitch experienced an unexpected error. This means it is a bug in Ink/Stitch.")
    message += "\n\n"
    # L10N this message is followed by a URL: https://github.com/inkstitch/inkstitch/issues/new
    message += _("If you'd like to help please\n"
                 "- copy the entire error message below\n"
                 "- save your SVG file and\n"
                 "- create a new issue at")
    message += " https://github.com/inkstitch/inkstitch/issues/new\n\n"
    message += _("Include the error description and also (if possible) the svg file.")
    message += '\n\n'
    message += get_os_version()
    message += '\n\n'
    message += version.get_inkstitch_version() + '\n'
    message += traceback.format_exc()

    return message


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/lib/extensions/__init__.py =====

# Authors: see git history
#
# Copyright (c) 2010 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.

from .about import About
from .apply_attribute import ApplyAttribute
from .apply_palette import ApplyPalette
from .apply_threadlist import ApplyThreadlist
from .auto_run import AutoRun
from .auto_satin import AutoSatin
from .batch_lettering import BatchLettering
from .break_apart import BreakApart
from .cleanup import Cleanup
from .commands_scale_symbols import CommandsScaleSymbols
from .cross_stitch_assistant import CrossStitchAssistant
from .cut_satin import CutSatin
from .cutwork_segmentation import CutworkSegmentation
from .density_map import DensityMap
from .display_stacking_order import DisplayStackingOrder
from .duplicate_params import DuplicateParams
from .element_info import ElementInfo
from .fill_to_satin import FillToSatin
from .fill_to_stroke import FillToStroke
from .flip import Flip
from .generate_palette import GeneratePalette
from .global_commands import GlobalCommands
from .gradient_blocks import GradientBlocks
from .input import Input
from .install import Install
from .install_custom_palette import InstallCustomPalette
from .jump_to_stroke import JumpToStroke
from .jump_to_trim import JumpToTrim
from .knockdown_fill import KnockdownFill
from .layer_commands import LayerCommands
from .lettering import Lettering
from .lettering_along_path import LetteringAlongPath
from .lettering_custom_font_dir import LetteringCustomFontDir
from .lettering_edit_json import LetteringEditJson
from .lettering_font_sample import LetteringFontSample
from .lettering_force_lock_stitches import LetteringForceLockStitches
from .lettering_generate_json import LetteringGenerateJson
from .lettering_organize_glyphs import LetteringOrganizeGlyphs
from .lettering_remove_kerning import LetteringRemoveKerning
from .lettering_set_color_sort_index import LetteringSetColorSortIndex
from .lettering_svg_font_to_layers import LetteringSvgFontToLayers
from .letters_to_font import LettersToFont
from .object_commands import ObjectCommands
from .object_commands_toggle_visibility import ObjectCommandsToggleVisibility
from .outline import Outline
from .output import Output
from .palette_split_text import PaletteSplitText
from .palette_to_text import PaletteToText
from .params import Params
from .png_realistic import PngRealistic
from .png_simple import PngSimple
from .preferences import Preferences
from .print_pdf import Print
from .redwork import Redwork
from .remove_duplicated_points import RemoveDuplicatedPoints
from .remove_embroidery_settings import RemoveEmbroiderySettings
from .reorder import Reorder
from .satin_multicolor import SatinMulticolor
from .satin_to_stroke import SatinToStroke
from .select_elements import SelectElements
from .selection_to_anchor_line import SelectionToAnchorLine
from .selection_to_guide_line import SelectionToGuideLine
from .selection_to_pattern import SelectionToPattern
from .sew_stack_editor import SewStackEditor
from .simulator import Simulator
from .stitch_plan_preview import StitchPlanPreview
from .stitch_plan_preview_undo import StitchPlanPreviewUndo
from .stroke_to_lpe_satin import StrokeToLpeSatin
from .stroke_to_satin import StrokeToSatin
from .tartan import Tartan
from .test_swatches import TestSwatches
from .thread_list import ThreadList
from .transform_elements import TransformElements
from .troubleshoot import Troubleshoot
from .unlink_clone import UnlinkClone
from .update_svg import UpdateSvg
from .zigzag_line_to_satin import ZigzagLineToSatin
from .zip import Zip

extensions = [
    About,
    ApplyAttribute,
    ApplyPalette,
    ApplyThreadlist,
    AutoRun,
    AutoSatin,
    BatchLettering,
    BreakApart,
    Cleanup,
    CommandsScaleSymbols,
    CrossStitchAssistant,
    CutSatin,
    CutworkSegmentation,
    DensityMap,
    DisplayStackingOrder,
    DuplicateParams,
    ElementInfo,
    FillToSatin,
    FillToStroke,
    Flip,
    GeneratePalette,
    GlobalCommands,
    GradientBlocks,
    Input,
    Install,
    InstallCustomPalette,
    JumpToStroke,
    JumpToTrim,
    KnockdownFill,
    LayerCommands,
    Lettering,
    LetteringAlongPath,
    LetteringCustomFontDir,
    LetteringEditJson,
    LetteringFontSample,
    LetteringForceLockStitches,
    LetteringGenerateJson,
    LetteringOrganizeGlyphs,
    LetteringRemoveKerning,
    LetteringSetColorSortIndex,
    LetteringSvgFontToLayers,
    LettersToFont,
    ObjectCommands,
    ObjectCommandsToggleVisibility,
    Outline,
    Output,
    PaletteSplitText,
    PaletteToText,
    Params,
    PngRealistic,
    PngSimple,
    Preferences,
    Print,
    Redwork,
    RemoveDuplicatedPoints,
    RemoveEmbroiderySettings,
    Reorder,
    SatinMulticolor,
    SatinToStroke,
    SelectElements,
    SelectionToAnchorLine,
    SelectionToGuideLine,
    SelectionToPattern,
    SewStackEditor,
    Simulator,
    StitchPlanPreview,
    StitchPlanPreviewUndo,
    StrokeToLpeSatin,
    StrokeToSatin,
    Tartan,
    TestSwatches,
    ThreadList,
    TransformElements,
    Troubleshoot,
    UnlinkClone,
    UpdateSvg,
    ZigzagLineToSatin,
    Zip
]


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/lib/extensions/about.py =====

# Authors: see git history
#
# Copyright (c) 2023 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.

from ..gui.about import AboutInkstitchApp
from .base import InkstitchExtension


class About(InkstitchExtension):

    def effect(self) -> None:
        app = AboutInkstitchApp()
        app.MainLoop()


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/lib/extensions/apply_attribute.py =====

# Authors: see git history
#
# Copyright (c) 2025 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.

from inkex import Boolean, errormsg

from ..i18n import _
from .base import InkstitchExtension


class ApplyAttribute(InkstitchExtension):
    '''
    Applies a given attribute to all selected elements
    '''
    def __init__(self, *args, **kwargs):
        InkstitchExtension.__init__(self, *args, **kwargs)
        self.arg_parser.add_argument("--notebook")
        self.arg_parser.add_argument("-n", "--namespace", dest="namespace", type=str, default='inkstitch')
        self.arg_parser.add_argument("-k", "--key", dest="key", type=str, default='')
        self.arg_parser.add_argument("-v", "--value", dest="value", type=str, default='')
        self.arg_parser.add_argument("-r", "--remove", dest="remove", type=Boolean, default=False)

    def effect(self):
        self.get_elements()
        if not self.elements:
            errormsg(_("Please select at least one element."))
            return

        if not self.options.key:
            errormsg(_("Please enter the attribute name."))
            return

        key = ''
        if self.options.namespace:
            key = f'{self.options.namespace}:'
        key += self.options.key

        if self.options.remove:
            for element in self.elements:
                element.node.pop(key)
        else:
            if not self.options.value:
                errormsg(_("Please enter a value."))
                return
            for element in self.elements:
                element.node.set(key, self.options.value)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/lib/extensions/apply_palette.py =====

# Authors: see git history
#
# Copyright (c) 2024 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.

from json import dumps

from ..elements import Clone, FillStitch
from ..gui.abort_message import AbortMessageApp
from ..gui.apply_palette import ApplyPaletteApp
from ..i18n import _
from ..tartan.palette import Palette
from ..tartan.utils import get_tartan_settings
from ..threads import ThreadCatalog, ThreadColor
from .base import InkstitchExtension


class ApplyPalette(InkstitchExtension):
    '''
    Applies colors of a color palette to elements
    '''

    def effect(self) -> None:
        # Remove selection, we want all the elements in the document
        self.svg.selection.clear()

        if not self.get_elements():
            app = AbortMessageApp(
                _("There is no stitchable element in the document."),
                _("https://inkstitch.org/")
            )
            app.MainLoop()
            return

        palette_choice = ApplyPaletteApp()
        if palette_choice.palette:
            self.apply_palette(palette_choice.palette)

    def apply_palette(self, palette_name: str) -> None:
        palette = ThreadCatalog().get_palette_by_name(palette_name)

        # Iterate through the color blocks to apply colors
        for element in self.elements:
            if isinstance(element, Clone):
                # clones use the color of their source element
                continue
            elif hasattr(element, 'gradient') and element.gradient is not None:
                # apply colors to each gradient stop
                for i, gradient_style in enumerate(element.gradient.stop_styles):
                    color = gradient_style['stop-color']
                    gradient_style['stop-color'] = palette.nearest_color(ThreadColor(color)).to_hex_str()
                continue

            nearest_color = palette.nearest_color(ThreadColor(element.color))
            if isinstance(element, FillStitch):
                element.node.style['fill'] = nearest_color.to_hex_str()

                # Apply palette to tartan color palette
                if element.node.get('inkstitch:tartan', None):
                    settings = get_tartan_settings(element.node)
                    tartan_palette = Palette()
                    tartan_palette.update_from_code(settings['palette'])
                    tartan_palette.apply_palette(palette)
                    settings['palette'] = tartan_palette.palette_code
                    element.node.set('inkstitch:tartan', dumps(settings))
            else:
                element.node.style['stroke'] = nearest_color.to_hex_str()

        metadata = self.get_inkstitch_metadata()
        metadata['thread-palette'] = palette_name


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/inkstitch/lib/extensions/apply_threadlist.py =====

# Authors: see git history
#
# Copyright (c) 2010 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.

import os
import re
import sys
from typing import List, Optional

import inkex

import pystitch

from ..i18n import _
from ..svg.tags import INKSTITCH_ATTRIBS
from ..threads import ThreadCatalog
from .base import InkstitchExtension


class ApplyThreadlist(InkstitchExtension):
    '''
    Applies colors of a thread list to elements
    Count of colors and elements should fit together
    Use case: reapply colors to e.g. a dst file
    '''
    def __init__(self, *args, **kwargs):
        InkstitchExtension.__init__(self, *args, **kwargs)
        self.arg_parser.add_argument("-o", "--options", type=str, default=None, dest="page_1")
        self.arg_parser.add_argument("-i", "--info", type=str, default=None, dest="page_2")
        self.arg_parser.add_argument("-f", "--filepath", type=str, default="", dest="filepath")
        self.arg_parser.add_argument("-m", "--method", type=int, default=1, dest="method")
        self.arg_parser.add_argument("-t", "--palette", type=str, default=None, dest="palette")

    def effect(self) -> None:
        # Remove selection, we want all the elements in the document
        self.svg.selection.clear()

        if not self.get_elements():
            return

        path = self.options.filepath
        self.verify_path(path)

        method = self.options.method

        # colors: [[color, cutwork_needle],[...]]
        if path.endswith(('col', 'inf', 'edr')):
            colors = self.parse_color_format(path)
        elif method == 1:
            colors = self.parse_inkstitch_threadlist(path)
        else:
            colors = self.parse_threadlist_by_catalog_number(path)

        self.verify_colors(colors, method)

        # Iterate through the color blocks to apply colors
        element_color = ""
        i = -1
        for element in self.elements:
            if element.color != element_color:
                element_color = element.color
                i += 1

            # No more colors in the list, stop here
            if i == len(colors):
                break

            style = element.node.get('style').replace("%s" % element_color, "%s" % colors[i][0])
            element.node.set('style', style)

            # apply cutwork
            if colors[i][1] is not None:
                element.node.set(INKSTITCH_ATTRIBS['cutwork_needle'], colors[i][1])

    def verify_path(self, path: str) -> None:
        if not os.path.exists(path):
            inkex.errormsg(_("File not found."))
            sys.exit(1)
        if os.path.isdir(path):
            inkex.errormsg(_("The filepath specified is not a file but a dictionary.\nPlease choose a threadlist file to import."))
            sys.exit(1)

    def verify_colors(self, colors: List[List[Optional[str]]], method: int) -> None:
        if all(c is None for c in colors):
            inkex.errormsg(_("Couldn't find any matching colors in the file."))
            if method == 1:
                inkex.errormsg(_('Please try to import as "other threadlist" and specify a color palette below.'))
            else:
                inkex.errormsg(_("Please chose an other color palette for your design."))
            sys.exit(1)

    def parse_inkstitch_threadlist(self, path: str) -> List[List[Optional[str]]]:
        colors = []
        with open(path
