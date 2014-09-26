# pylint: skip-file
#
# This file helps to compute a version number in source trees obtained from:
#
# git-archive tarball (such as those provided by githubs download-from-tag feature).
#
# Distribution tarballs (built by setup.py sdist) and build directories (produced by setup.py build) will contain a much
# shorter file that just contains the computed version number.
#
# This file is released into the public domain.
# Generated by versioneer-0.11 (https://github.com/warner/python-versioneer)
#
#
# CHANGES: peter1000, https://github.com/peter1000
# ================================================
#
# 20140731:
#
# - addition to  __init__.py: use project import not relative imports
# - changed indent to projects 3 spaces style
# - changes: to fit a bit more the own Project style: example renamed ClassNames
# - changes: removed check for: win32
#
from errno import ENOENT
from os import sep as os_sep
from os.path import (
   abspath as path_abspath,
   basename as path_basename,
   dirname as path_dirname,
   exists as path_exists,
   join as path_join,
)
from re import search as re_search
from subprocess import (
   Popen as subprocess_Popen,
   PIPE,
)
from sys import (
   exc_info as sys_exc_info,
   version as sys_version,
)


# these strings will be replaced by git during git-archive
git_refnames = '$Format:%d$'
git_full = '$Format:%H$'

# these strings are filled in when 'setup.py versioneer' creates _version.py
tag_prefix = ''
parentdir_prefix = 'LCONF-'
versionfile_source = 'LCONF/_version.py'


def run_command(commands, args, cwd=None, verbose=False, hide_stderr=False):
   assert isinstance(commands, list)
   # noinspection PyUnusedLocal
   p = None
   for c in commands:
      try:
         p = subprocess_Popen([c] + args, cwd=cwd, stdout=PIPE, stderr=(PIPE if hide_stderr else None))
         break
      except EnvironmentError:
         e = sys_exc_info()[1]
         if e.errno == ENOENT:
            continue
         if verbose:
            print('unable to run {}'.format(args[0]))
            print(e)
         return None
   else:
      if verbose:
         print('unable to find command, tried {}'.format(commands))
      return None
   stdout = p.communicate()[0].strip()
   if sys_version >= '3':
      stdout = stdout.decode()
   if p.returncode != 0:
      if verbose:
         print('unable to run {} (error)'.format(args[0]))
      return None
   return stdout


def versions_from_parentdir(_parentdir_prefix, root, verbose=False):
   # Source tarballs conventionally unpack into a directory that includes both the project name and a version string.
   dirname = path_basename(root)
   if not dirname.startswith(_parentdir_prefix):
      if verbose:
         print('guessing rootdir is <{}>, but <{}> does not start with prefix <{}>'.format(root, dirname, _parentdir_prefix))
      return None
   return {'version': dirname[len(_parentdir_prefix):], 'full': ''}


def git_get_keywords(versionfile_abs):
   # the code embedded in _version.py can just fetch the value of these keywords. When used from setup.py, we don't want to
   # import _version.py, so we do it with a regexp instead. This function is not used from _version.py.
   keywords = {}
   try:
      f = open(versionfile_abs, 'r')
      for line in f.readlines():
         if line.strip().startswith('git_refnames ='):
            mo = re_search(r'=\s*"(.*)"', line)
            if mo:
               keywords['refnames'] = mo.group(1)
         if line.strip().startswith('git_full ='):
            mo = re_search(r'=\s*"(.*)"', line)
            if mo:
               keywords['full'] = mo.group(1)
      f.close()
   except EnvironmentError:
      pass
   return keywords


def git_versions_from_keywords(keywords, _tag_prefix, verbose=False):
   if not keywords:
      return {}  # keyword-finding function failed to find keywords
   refnames = keywords['refnames'].strip()
   if refnames.startswith('$Format'):
      if verbose:
         print('keywords are unexpanded, not using')
      return {}  # unexpanded, so not in an unpacked git-archive tarball
   refs = set([r.strip() for r in refnames.strip('()').split(',')])
   # starting in git-1.8.3, tags are listed as 'tag: foo-1.0' instead of just 'foo-1.0'. If we see a 'tag: ' prefix, prefer
   # those.

   # noinspection PyPep8Naming
   TAG = 'tag: '
   tags = set([r[len(TAG):] for r in refs if r.startswith(TAG)])
   if not tags:
      # Either we're using git < 1.8.3, or there really are no tags. We use a heuristic: assume all version tags have a
      # digit. The old git `percentage d` expansion behaves like git log --decorate=short and strips out the refs/heads/ and
      # refs/tags/ prefixes that would let us distinguish between branches and tags. By ignoring refnames without digits, we
      # filter out many common branch names like 'release' and 'stabilization', as well as 'HEAD' and 'master'.
      tags = set([r for r in refs if re_search(r'\d', r)])
      if verbose:
         print('discarding <{}>, no digits'.format(','.join(refs - tags)))
   if verbose:
      print('likely tags: {}'.format(','.join(sorted(tags))))
   for ref in sorted(tags):
      # sorting will prefer e.g. '2.0' over '2.0rc1'
      if ref.startswith(_tag_prefix):
         r = ref[len(_tag_prefix):]
         if verbose:
            print('picking {}'.format(r))
         return {'version': r, 'full': keywords['full'].strip()}
   # no suitable tags, so we use the full revision id
   if verbose:
      print('no suitable tags, using full revision id')
   return {'version': keywords['full'].strip(), 'full': keywords['full'].strip()}


def git_versions_from_vcs(_tag_prefix, root, verbose=False):
   # this runs 'git' from the root of the source tree. This only gets called if the git-archive 'subst' keywords were *not*
   # expanded, and _version.py hasn't already been rewritten with a short version string, meaning we're inside a checked out
   # source tree.
   if not path_exists(path_join(root, '.git')):
      if verbose:
         print('no .git in {}'.format(root))
      return {}

   # noinspection PyPep8Naming
   GITS = ['git']
   stdout = run_command(GITS, ['describe', '--tags', '--dirty', '--always'], cwd=root)
   if stdout is None:
      return {}
   if not stdout.startswith(_tag_prefix):
      if verbose:
         print('tag <{}> does not start with prefix <{}>'.format(stdout, _tag_prefix))
      return {}
   tag = stdout[len(_tag_prefix):]
   stdout = run_command(GITS, ['rev-parse', 'HEAD'], cwd=root)
   if stdout is None:
      return {}
   full = stdout.strip()
   if tag.endswith('-dirty'):
      full += '-dirty'
   return {'version': tag, 'full': full}


def get_versions(default=None, verbose=False):
   # I am in _version.py, which lives at ROOT/VERSIONFILE_SOURCE. If we have __file__, we can work backwards from there to
   # the root. Some py2exe/bbfreeze/non-CPython implementations don't do __file__, in which case we can only use expanded
   # keywords.
   if not default:
      default = {'version': 'unknown', 'full': ''}
   keywords = {'refnames': git_refnames, 'full': git_full}
   ver = git_versions_from_keywords(keywords, tag_prefix, verbose)
   if ver:
      return ver

   try:
      root = path_abspath(__file__)
      # versionfile_source is the relative path from the top of the source tree (where the .git directory might live) to this
      # file. Invert this to find the root from __file__.
      for i in range(len(versionfile_source.split(os_sep))):
         root = path_dirname(root)
   except NameError:
      return default

   return (
      git_versions_from_vcs(tag_prefix, root, verbose)
      or versions_from_parentdir(parentdir_prefix, root, verbose)
      or default
   )
