#!/usr/bin/env python
# coding: utf-8

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function


#-----------------------------------------------------------------------------
# Minimal Python version sanity check
#-----------------------------------------------------------------------------

import sys

v = sys.version_info
if v[:2] < (2,7) or (v[0] >= 3 and v[:2] < (3,3)):
    error = "ERROR: this package requires Python version 2.7 or 3.3 or above."
    print(error, file=sys.stderr)
    sys.exit(1)

PY3 = (sys.version_info[0] >= 3)

#-----------------------------------------------------------------------------
# get on with it
#-----------------------------------------------------------------------------

import os
from distutils import log
from distutils.core import setup, Command
from distutils.command.build_py import build_py
from distutils.command.sdist import sdist
from os.path import join as pjoin
from subprocess import check_call


repo_root = os.path.dirname(os.path.abspath(__file__))
is_repo = os.path.exists(pjoin(repo_root, '.git'))

npm_path = os.pathsep.join([
    pjoin(repo_root, 'node_modules', '.bin'),
    os.environ.get("PATH", os.defpath),
])

def mtime(path):
    """shorthand for mtime"""
    return os.stat(path).st_mtime

try:
    from shutil import which
except ImportError:
    ## which() function copied from Python 3.4.3; PSF license
    def which(cmd, mode=os.F_OK | os.X_OK, path=None):
        """Given a command, mode, and a PATH string, return the path which
        conforms to the given mode on the PATH, or None if there is no such
        file.

        `mode` defaults to os.F_OK | os.X_OK. `path` defaults to the result
        of os.environ.get("PATH"), or can be overridden with a custom search
        path.

        """
        # Check that a given file can be accessed with the correct mode.
        # Additionally check that `file` is not a directory, as on Windows
        # directories pass the os.access check.
        def _access_check(fn, mode):
            return (os.path.exists(fn) and os.access(fn, mode)
                    and not os.path.isdir(fn))

        # If we're given a path with a directory part, look it up directly rather
        # than referring to PATH directories. This includes checking relative to the
        # current directory, e.g. ./script
        if os.path.dirname(cmd):
            if _access_check(cmd, mode):
                return cmd
            return None

        if path is None:
            path = os.environ.get("PATH", os.defpath)
        if not path:
            return None
        path = path.split(os.pathsep)

        if sys.platform == "win32":
            # The current directory takes precedence on Windows.
            if not os.curdir in path:
                path.insert(0, os.curdir)

            # PATHEXT is necessary to check on Windows.
            pathext = os.environ.get("PATHEXT", "").split(os.pathsep)
            # See if the given file matches any of the expected path extensions.
            # This will allow us to short circuit when given "python.exe".
            # If it does match, only test that one, otherwise we have to try
            # others.
            if any(cmd.lower().endswith(ext.lower()) for ext in pathext):
                files = [cmd]
            else:
                files = [cmd + ext for ext in pathext]
        else:
            # On other platforms you don't have things like PATHEXT to tell you
            # what file suffixes are executable, so just pass on cmd as-is.
            files = [cmd]

        seen = set()
        for dir in path:
            normdir = os.path.normcase(dir)
            if not normdir in seen:
                seen.add(normdir)
                for thefile in files:
                    name = os.path.join(dir, thefile)
                    if _access_check(name, mode):
                        return name
        return None

def js_prerelease(command):
    """decorator for building minified js/css prior to another command"""
    class DecoratedCommand(command):
        def run(self):
            print('inner runnn.....')
            try:
                self.distribution.run_command('jsdeps')
            except Exception as e:
                log.warn("rebuilding js and css failed")
                log.warn(str(e))
            command.run(self)
            update_package_data(self.distribution)
    return DecoratedCommand


def update_package_data(distribution):
    """update package_data to catch changes during setup"""
    build_py = distribution.get_command_obj('build_py')
    # distribution.package_data = find_package_data()
    # re-init build_py options which load package_data
    build_py.finalize_options()


class NPM(Command):
    description = "install package,json dependencies using npm"

    user_options = []
    
    node_modules = pjoin(repo_root, 'node_modules')

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def should_run_npm(self):
        if not which('npm'):
            print("npm unavailable", file=sys.stderr)
            return False
        return True
    
    def run(self):
        if self.should_run_npm():
            print("installing build dependencies with npm")
            check_call(['npm', 'install'], cwd=repo_root)
            os.utime(self.node_modules, None)

        env = os.environ.copy()
        env['PATH'] = npm_path

        # update package data in case this created new files
        update_package_data(self.distribution)

pjoin = os.path.join
here = os.path.abspath(os.path.dirname(__file__))
pkg_root = pjoin(here, 'vegaexplore')




setup_args = dict(
    name            = 'vegaexplore',
    version         = '0.0.1',
    packages        = ['vegaexplore'],
    package_data    = {'': ['lib/*.js']},
    description     = '',
    long_description = '',
    author          = 'Brian E. Granger',
    author_email    = 'ellisonbg@gmail.com',
    license         = 'BSD',
    cmdclass        = {
        'build_py': js_prerelease(build_py),
        'sdist': js_prerelease(sdist),
        'jsdeps': NPM,
    },
)

# For some commands, use setuptools.  Note that we do NOT list install here!
# If you want a setuptools-enhanced install, just run 'setupegg.py install'
needs_setuptools = set(('develop', 'release', 'bdist_egg', 'bdist_rpm',
           'bdist', 'bdist_dumb', 'bdist_wininst', 'bdist_wheel',
           'egg_info', 'easy_install', 'upload', 'install_egg_info',
            ))

if len(needs_setuptools.intersection(sys.argv)) > 0:
    import setuptools

if 'setuptools' in sys.modules:
    # setup.py develop should check for submodules
    from setuptools.command.develop import develop
    setup_args['cmdclass']['develop'] = js_prerelease(develop)

setuptools_args = {}
install_requires = setuptools_args['install_requires'] = [
    'traitlets',
]



if 'setuptools' in sys.modules:
    setup_args.update(setuptools_args)

if __name__ == '__main__':
    setup(**setup_args)