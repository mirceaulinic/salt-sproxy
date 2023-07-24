# -*- coding: utf-8 -*-
#
# salt-sproxy documentation build configuration file, created by
# sphinx-quickstart on Wed Aug  9 16:31:45 2017.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import json
import logging
from shutil import copyfile

import jinja2

sys.path.insert(0, os.path.abspath("../"))
sys.path.insert(0, os.path.abspath("../salt_sproxy"))
sys.path.insert(0, os.path.abspath("_themes"))

log = logging.getLogger(__name__)

# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.coverage",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "salt-sproxy"
copyright = "2019-2020, Mircea Ulinic"
author = "Mircea Ulinic"

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
# version = salt_sproxy.__version__
# The full version, including alpha/beta/rc tags.
# release = salt_sproxy.__version__

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "flask_theme_support.FlaskyStyle"

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False

# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "alabaster"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
html_theme_options = {
    "show_powered_by": False,
    "github_user": "mirceaulinic",
    "github_repo": "salt-sproxy",
    "github_banner": True,
    "show_related": False,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# This is required for the alabaster theme
# refs: http://alabaster.readthedocs.io/en/latest/installation.html#sidebars
html_sidebars = {
    "**": [
        "about.html",
        "navigation.html",
        "links.html",
        "relations.html",  # needs 'show_related': True theme option to display
        "searchbox.html",
        "donate.html",
    ]
}

# If true, links to the reST sources are added to the pages.
html_show_sourcelink = False

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
html_show_sphinx = False

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
html_show_copyright = True

# -- Options for HTMLHelp output ------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = "salt-sproxy"


# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',
    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',
    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',
    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (
        master_doc,
        "salt-sproxy.tex",
        "salt-sproxy Documentation",
        "Mircea Ulinic",
        "manual",
    )
]


# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, "salt-sproxy", "salt-sproxy Documentation", [author], 1),
    ("salt_sapi", "salt-sapi", "salt-sapi Documentation", [author], 1),
]


# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        master_doc,
        "salt-sproxy",
        "salt-sproxy Documentation",
        author,
        "salt-sproxy",
        "Salt plugin for interacting with network devices, without running Minions",
        "Miscellaneous",
    )
]

# -- Options for Epub output ----------------------------------------------

# Bibliographic Dublin Core info.
epub_title = project
epub_author = author
epub_publisher = author
epub_copyright = copyright

# The unique identifier of the text. This can be a ISBN number
# or the project homepage.
#
# epub_identifier = ''

# A unique identification for the text.
#
# epub_uid = ''

# A list of files that should not be packed into the epub file.
epub_exclude_files = ["search.html"]

curdir = os.path.abspath(os.path.dirname(__file__))
doc_examples_dir = os.path.join(curdir, "examples")
try:
    os.mkdir(doc_examples_dir)
except OSError:
    pass
examples_path = os.path.abspath(os.path.join(curdir, os.path.pardir, "examples"))
examples_dirs = [
    name
    for name in os.listdir(examples_path)
    if os.path.isdir(os.path.join(examples_path, name))
]
examples = []

for example_dir in examples_dirs:
    example_readme = os.path.join(examples_path, example_dir, "README.rst")
    example_doc = os.path.join(doc_examples_dir, "{}.rst".format(example_dir))
    if os.path.exists(example_readme):
        copyfile(example_readme, example_doc)
        examples.append(example_dir)

env = jinja2.Environment(loader=jinja2.FileSystemLoader("."))
examples_template = env.get_template("examples_index.jinja")
rendered_template = examples_template.render(examples=examples)
examples_index = os.path.join(doc_examples_dir, "index.rst")
with open(examples_index, "w") as rst_fh:
    rst_fh.write(rendered_template)
