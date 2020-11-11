class MemrError(Exception):
    """ Base error class for Memr related errors. """

class TimecodeError(MemrError):
    """ Base error class for Timecode related errors. """

class StorageError(MemrError):
    """ Base error class for Storage related errors. """

class GCSError(MemrError):
    """ Base error class for Storage related errors. """

class MongoError(MemrError):
    """ Base error class for MongoDB related errors. """

class YTDownloadError(MemrError):
    """ Base error class for Audio Download related errors. """

class AudioConversionError(MemrError):
    """ Base error class for Audio Conversion related errors. """

class AudioDownloadError(MemrError):
    """ Base error class for Audio Download related errors. """

class MissingArguments(MemrError):
    """ Base error class for Missing Arguments related errors. """