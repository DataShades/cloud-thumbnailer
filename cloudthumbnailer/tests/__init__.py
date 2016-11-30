from nose import tools
from PIL import Image
import unittest
import os

from cloudthumbnailer.cloud_connector import CloudConnector
from cloudthumbnailer import ThumbsGenerator

class TestCloudThumbnailer(unittest.TestCase):
	# def setup_class(self):
	# 	print('Creating connector instance before tests run')
	# 	self.driver = S3CloudConnector('s3', 'ACCESS_KEY', 'SECRET_ACCESS_KEY', 'bucket-name')

	def setUp(self):
		self.driver = CloudConnector('s3', 'ACCESS_KEY', 'SECRET_ACCESS_KEY', 'bucket-name')
		self.tg = ThumbsGenerator((600, 800), (300, 300), self.driver, None, 3)
		self.image_name = 'test-image.jpeg'
		self.image_path = os.path.dirname(os.path.abspath(__file__)) + '/' + self.image_name


	def test_get_file_name(self):
		tools.assert_tuple_equal(self.tg.get_file_name(self.image_name), ('test-image', '.jpeg'))


	def test_scale_image_by_width(self):
		image = Image.open(self.image_path)
		width = 600
		tools.assert_is_instance(self.tg.scale_image_by_width(image, width), Image.Image)

	
	def test_scale_image_by_height(self):
		image = Image.open(self.image_path)
		height = 800
		tools.assert_is_instance(self.tg.scale_image_by_height(image, height), Image.Image)
