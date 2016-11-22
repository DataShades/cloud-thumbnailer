import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "cloud-thumbnailer",
    version = "0.0.1",
    author = "Gleb Rudenko",
    author_email = "gleb.rudenko@linkdigital.com.au",
    description = ("Cloud thumbnails uploader from external urls"),
    license = "BSD",
    keywords = "cloud thumbnail thumbnails uploader s3 libcloud link-digital",
    url = "http://packages.python.org/s3-thumbs-saver",
    packages=['cloudthumbnailer'],
    zip_safe=False,
    package_dir={
        'cloudthumbnailer': 'cloudthumbnailer',
    },
)