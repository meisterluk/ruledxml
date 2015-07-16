#!/usr/bin/env python3

"""
    ruledxml.fs
    -----------

    File system functionalities for ruledxml.

    (C) 2015, meisterluk, BSD 3-clause license
"""

import shutil
import string
import os.path
import pathlib
import itertools
import lxml.etree


def create_unique_filepath(folder, prefix='', suffix='', alphabet=string.digits):
    """Create a filepath to a file which does not exist in `folder` yet.
    The filepath starts with `prefix` and ends with `suffix`.

    :param folder:      folder in which return value shall be unique
    :type folder:       str
    :param prefix:      prefix of the filename
    :type prefix:       str
    :param suffix:      suffix of the filename
    :type suffix:       str
    :param alphabet:    the alphabet to use if additional characters are required
    :type alphabet:     set
    :return:            the new filepath
    :rtype:             str
    """
    def candidates():
        for i in itertools.count(1):
            for variation in itertools.product(alphabet, repeat=i):
                yield ''.join(variation)

    candidate = os.path.join(folder, prefix + suffix)
    for cand in candidates():
        if not os.path.exists(candidate):
            return candidate
        candidate = os.path.join(folder, prefix + '_' + cand + suffix)

    return candidate


def create_base_directories(path: str, *, wholepath=False):
    """Given a filepath, make sure all base directories exist.
    Eg. "/root/sub/file.py", make sure "/root" and "/root/sub" exists.

    :param path:        A filepath
    :type path:         str
    :param wholepath:   If True, all path elements must exist as folders;
                        in the example: also "file.py" must exist as folder
    :type wholepath:    bool
    """
    if wholepath:
        basedir = path
    else:
        basedir = os.path.split(path)[0]

    pathinst = pathlib.Path(basedir)
    if not pathinst.exists():
        pathinst.mkdir(parents=True)


def copy_files(src: list([str]), dest: str):
    """Copy files `src` to a destination folder `dest`.

    This function creates unique file paths if files with
    the same name already exist. If `dest` does not exist,
    the requested folder structure is created.

    :param src:     an iterable of source filepaths
    :type str:      list
    :param dest:    a filepath to a folder where to write files to
    :type dest:     str
    """
    create_base_directories(dest, wholepath=True)
    assert os.path.isdir(dest), "Destination path must be folder"

    for s in src:
        basename = os.path.basename(s)
        root, ext = os.path.splitext(basename)
        target = create_unique_filepath(dest, root, ext)
        shutil.copy(s, target)


def copy_file(src: str, dest: str):
    """Copy a file `src` to a destination `dest`.

    This function creates unique file paths if files with
    the same name already exist. If `dest` does not exist,
    the requested folder structure is created.

    :param src:     source filepath
    :type str:      list
    :param dest:    destination filepath
    :type dest:     str
    """
    folders, filename = os.path.split(dest)

    # create parent directories
    create_base_directories(folders, wholepath=True)

    # create unique filename
    root, ext = os.path.splitext(filename)
    target = create_unique_filepath(folders, root, ext)

    shutil.copy(src, target)
