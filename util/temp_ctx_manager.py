from contextlib import contextmanager
import os
import tempfile

@contextmanager
def make_tempfile(path):
    try:
        _, tempFileDir = tempfile.mkstemp(suffix=".ogg", dir=path)
        f = open(tempFileDir, "r")
        yield tempFileDir
    finally:
        f.close()


@contextmanager
def make_tempdir(path):
    try:
        tempDir = tempfile.mkdtemp(dir=path)
        print(tempDir)
        yield tempDir
    finally:
        # shutil.rmtree(tempDir)
        print("Done with makeTempdir")