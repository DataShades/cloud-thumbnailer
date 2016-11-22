
=================
Cloud Thumbnailer
=================

This Python plugin allows to imort resized images with their thumbnails into you cloud service from External urls, creates 1 resized image and 1 thumbnail of it.
	
	Now supports:
		
	S3_AP_SOUTHEAST2 Buckets.

------------
Requirements
------------

The plugin requires apache-libcloud version 1.4.0 and later just for the S3 Bucket region fix.
	Added S3_AP_SOUTHEAST2 Region.


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

Test are now in progress...

-----
Usage
-----

1. Import CloudConnector class::
	
	from cloudthumbnailer.cloud_connector import CloudConnector

2. Import ThumbsGenerator class::

	from cloudthumbnailer import ThumbsGenerator

3. Create a driver instance::
	
	driver = CloudConnector('s3', 'ACCESS_KEY, 'SECRET_KEY', 'bucket-name')

4. Create a thumbnailer instance::

	thumbnailer = ThumbsGenerator(scale_size, crop_size, driver, threads_num)

**scale_size** - tuple with two integer values e.g. (600, 800);

**crop_size** - tuple with two integer values e.g. (300, 300);

**driver**- our generated driver connector; *Default*: None

**threads_num** - number of running threads at the same time. *Default*: 3

5. Run the method you need::

	thumbnailer.download_from_csv('path-to-csv-file', args)
		OR
	thumbnailer.download_from_dict([data_dicts], args)

	Additional Optional args:

	key - recieve a key by which to find image url from csv/datadict
	callback - function that recieves 1 argument of tuple that contains 2 objects 
	which containe response from S3 ( Information about uploaded files ) 

-------------
Usage Example
-------------

Code sample::

	from cloudthumbnailer.cloud_connector import CloudConnector
	from cloudthumbnailer import ThumbsGenerator

	driver = CloudConnector('s3', 'ACCESS_KEY, 'SECRET_KEY', 'bucket-name')

	thumbnailer = ThumbsGenerator((600, 800), (300, 300), driver, 2)

	thumbnailer.download_from_csv('/home/user/some-user/sample.csv', key='url', my_func_callback)

	def my_func_callback(response):
		
		return response