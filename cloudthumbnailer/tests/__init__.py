from nose import tools
from s3thumbssaver.s3_cloud_connector import S3CloudConnector
from s3thumbssaver import ThumbsGenerator

class TestCloudThumbnailer():
	def setup_class(self):
		print('Creating connector instance before tests run')
		self.driver = S3CloudConnector('s3', 'ACCESS_KEY', 'SECRET_ACCESS_KEY', 'bucket-name')

	def setup(self):
		self.tg = ThumbsGenerator((600, 800), (300, 300), self.driver, 3)
