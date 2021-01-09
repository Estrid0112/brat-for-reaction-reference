#!/usr/bin/env python



"""Simple interface to for importing files into the data directory.

Author:     Pontus Stenetorp    <pontus is s u-tokyo ac jp>
Version:    2011-02-21
"""

from os import W_OK, access
from os.path import join as join_path
from os.path import isdir, isfile, samefile
import os

from config import DATA_DIR

from annotation import JOINED_ANN_FILE_SUFF, TEXT_FILE_SUFFIX, open_textfile, TextAnnotations, \
    AnnotationsIsReadOnlyError
from annotator import ModificationTracker
from common import ProtocolError
from document import real_directory

# Constants
DEFAULT_IMPORT_DIR = 'import'
###


class InvalidDirError(ProtocolError):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return 'Invalid directory'

    def json(self, json_dic):
        json_dic['exception'] = 'invalidDirError'
        return json_dic


class InvalidInputError(ProtocolError):
    def __init__(self, input_text):
        self.input_text = input_text

    def __str__(self):
        if self.input_text == "negative":
            return 'Input number is negative'
        else:
            return 'The input number will remove the relation between {}'.format(self.input_text)

    def json(self, json_dic):
        json_dic['exception'] = 'invalidInputError'
        return json_dic


class FileExistsError(ProtocolError):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return 'File exists: %s' % self.path

    def json(self, json_dic):
        json_dic['exception'] = 'fileExistsError'
        return json_dic


class NoWritePermissionError(ProtocolError):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return 'No write permission to %s' % self.path

    def json(self, json_dic):
        json_dic['exception'] = 'noWritePermissionError'
        return json_dic


# TODO: Chop this function up
def save_import(text, docid, collection=None):
    '''
    TODO: DOC:
    '''

    directory = collection

    if directory is None:
        dir_path = DATA_DIR
    else:
        # XXX: These "security" measures can surely be fooled
        if (directory.count('../') or directory == '..'):
            raise InvalidDirError(directory)

        dir_path = real_directory(directory)

    # Is the directory a directory and are we allowed to write?
    if not isdir(dir_path):
        raise InvalidDirError(dir_path)
    if not access(dir_path, W_OK):
        raise NoWritePermissionError(dir_path)

    base_path = join_path(dir_path, docid)
    txt_path = base_path + '.' + TEXT_FILE_SUFFIX
    ann_path = base_path + '.' + JOINED_ANN_FILE_SUFF

    # Before we proceed, verify that we are not overwriting
    for path in (txt_path, ann_path):
        if isfile(path):
            raise FileExistsError(path)

    # Make sure we have a valid POSIX text file, i.e. that the
    # file ends in a newline.
    if text != "" and text[-1] != '\n':
        text = text + '\n'

    with open_textfile(txt_path, 'w') as txt_file:
        txt_file.write(text)
        txt_file.close()

        # Touch the ann file so that we can edit the file later
        with open(ann_path, 'w') as _:
            pass

    return {'document': docid}


def modify_reference_file(num_reactions, docid, collection=None, write_permission=True):
    num = int(num_reactions)
    if num <= 0:
        raise InvalidInputError("negative")

    directory = collection

    if directory is None:
        dir_path = DATA_DIR
    else:
        # XXX: These "security" measures can surely be fooled
        if (directory.count('../') or directory == '..'):
            raise InvalidDirError(directory)

        dir_path = real_directory(directory)
        if (not write_permission) or (write_permission == "false"):
            raise NoWritePermissionError(dir_path)

    # Is the directory a directory and are we allowed to write?
    if not isdir(dir_path):
        raise InvalidDirError(dir_path)
    if not access(dir_path, W_OK):
        raise NoWritePermissionError(dir_path)

    base_path = join_path(dir_path, docid)
    txt_path = base_path + '.' + TEXT_FILE_SUFFIX
    ann_path = base_path + '.' + JOINED_ANN_FILE_SUFF

    with TextAnnotations(base_path) as ann_obj:
        # bail as quick as possible if read-only
        if ann_obj._read_only:
            raise AnnotationsIsReadOnlyError(ann_obj.get_document())
        relations = list(ann_obj.get_relations())
        for rel in relations:
            if (int(rel.arg1[1:])) > num - 1 or (int(rel.arg2[1:])) > num - 1:  # Entity index starts from 0
                raise InvalidInputError("{} and {}".format(rel.arg1, rel.arg2))

    text = " ".join("T{}".format(i) for i in range(1, num + 1))
    with open_textfile(txt_path, 'w') as txt_file:
        txt_file.write(text)
        txt_file.close()

    with open(ann_path, 'w') as ann_file:
        for i in range(1, num+1):
            ann_id = "T{}".format(i)
            start = text.find(ann_id)
            end = start + len(ann_id)
            ann_file.write("{}\tREACTION_SPAN {} {}\t{}\n".format(ann_id, start, end, ann_id))
        for rel in relations:
            ann_file.write("{}\t{} Arg1:{} Arg2:{}\n".format(rel.id, rel.type, rel.arg1, rel.arg2))
    ann_file.close()
    return {'document': docid}


if __name__ == '__main__':
    # TODO: Update these to conform with the new API
    """from unittest import TestCase from tempfile import mkdtemp from shutil
    import rmtree from os import mkdir.

    class SaveImportTest(TestCase):
        test_text = 'This is not a drill, this is a drill *BRRR!*'
        test_dir = 'test'
        test_filename = 'test'

        def setUp(self):
            self.tmpdir = mkdtemp()
            mkdir(join_path(self.tmpdir, SaveImportTest.test_dir))
            mkdir(join_path(self.tmpdir, DEFAULT_IMPORT_DIR))

        def tearDown(self):
            rmtree(self.tmpdir)

        def test_import(self):
            save_import(SaveImportTest.test_text, SaveImportTest.test_filename,
                    relative_dir=SaveImportTest.test_dir,
                    directory=self.tmpdir)

        def test_default_import_dir(self):
            save_import(SaveImportTest.test_text, SaveImportTest.test_filename,
                    directory=self.tmpdir)


    import unittest
    unittest.main()
    """
