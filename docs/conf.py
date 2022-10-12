# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'stix2xspec'
copyright = '2022, Erica Lastufka'
author = 'Erica Lastufka'
release = '0.1.0-alpha'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
import sys
import os
sys.path.insert(0, os.path.abspath("../"))
#sys.path.insert(0, os.path.abspath("../.."))
#sys.path.insert(0, os.path.abspath("../stix2xspec"))

extensions = ['sphinx.ext.duration', 'sphinx.ext.autodoc', 'sphinx.ext.napoleon', 'sphinx.ext.autosummary', 'myst_parser', 'sphinxcontrib.apidoc']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

#from https://github.com/cherrypy/cheroot/blob/main/docs/conf.py
master_doc = 'index'

apidoc_excluded_paths = ['../stix2xspec/data']
apidoc_extra_args = [
    '--implicit-namespaces',
    '--private',  # include “_private” modules
]
apidoc_module_dir = '../stix2xspec'
apidoc_module_first = False
#apidoc_output_dir = 'pkg'
apidoc_separate_modules = True
apidoc_toc_file = None

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
#html_static_path = ['_static']
html_theme_options = {
#    'analytics_id': 'G-XXXXXXXXXX',  #  Provided by Google in your dashboard
#    'analytics_anonymize_ip': False,
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'vcs_pageview_mode': '',
    'style_nav_header_background': 'white',
    # Toc options
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}
