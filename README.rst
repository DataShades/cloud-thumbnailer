
=================
Cloud Thumbnailer
=================

This Python plugin allows to import resized images with their thumbnails into your cloud service from external urls, creates 1 resized image and 1 thumbnail of it.
	
Now supports:
		
All S3 Bucket Regions.

------------
Requirements
------------

The plugin requires `apache-libcloud <https://github.com/apache/libcloud>`_ version 1.4.0 and later just for the S3 Bucket region fix.

About region information take a look at libcloud `documentation <https://libcloud.readthedocs.io/en/latest/supported_providers.html#id180>`_


------------
Installation
------------

1. Clone the repository::
	
	git clone https://github.com/DataShades/cloud-thumbnailer.git

3. Go into the folder and install requirements::
	
	pip install -r requirements.txt

2. In the same folder run::

	python setup.py develop

to install the plugin itself.

-------------
Running Tests
-------------

Tests are now in progress...

-----
Usage
-----

1. Import CloudConnector class:
::	
	from cloudthumbnailer.cloud_connector import CloudConnector


2. Import ThumbsGenerator class:
::
	from cloudthumbnailer import ThumbsGenerator


3. Create a driver instance:
::
	driver = CloudConnector('s3', 'S3_REGION', 'ACCESS_KEY, 'SECRET_KEY', 'bucket-name')


List of **S3_REGION** is provided in `libcloud docs <https://libcloud.readthedocs.io/en/latest/supported_providers.html#id180>`_

4. Create a thumbnailer instance:
::
	thumbnailer = ThumbsGenerator(scale_size, crop_size, driver, check_exists, threads_num)


**scale_size** - tuple with two integer values e.g. (600, 800);

**crop_size** - tuple with two integer values e.g. (300, 300);

**driver** - our generated driver connector;

**check_exits** - Optional dict with information where to look for image hash generated from S3 and save in our dict or db  *Example*: {'key': 'metadata', 'sub_key': 'resized_s3_hash', 'json': True}, *sub_key* and *json* are optional too. *Default*: None

**threads_num** - number of running threads at the same time. *Default*: 3

5. Run the method you need::

	thumbnailer.download_from_csv('path-to-csv-file', args)
		OR
	thumbnailer.download_from_dict([data_dicts], args)

	Additional Optional args:

	key - recieves a key by which to find image url from csv/datadict
	callback - function that recieves 1 argument of tuple that contains 2 objects 
	which containe response from S3 ( Information about uploaded files ) 

-------------
Usage Example
-------------

Code sample:
::
	from cloudthumbnailer.cloud_connector import CloudConnector
	from cloudthumbnailer import ThumbsGenerator

	driver = CloudConnector('s3', 'S3_REGION', 'ACCESS_KEY', 'SECRET_KEY', 'bucket-name')

	thumbnailer = ThumbsGenerator((600, 800), (300, 300), driver, None, 2)

	thumbnailer.download_from_csv('/home/user/some-user/sample.csv', key='url', my_func_callback)

	def my_func_callback(response):
		
		return response
