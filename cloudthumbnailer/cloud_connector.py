from libcloud.storage.types import Provider
from libcloud.storage.providers import get_driver

class CloudConnector():
	def __init__(self, provider="s3", region=None, api_key=None, secret_key=None, bucket=None):
		self.api_key = api_key
		self.secret_key = secret_key
		self.bucket = bucket
		self.region = region
		self.driver = self.select_storage_provider(provider)
		self.uploader = self.driver_data_upload


	def select_storage_provider(self, provider):
		try:
			driver = {
				's3': self.get_connected_driver_to_s3bucket,
			}.get(provider)

			return driver

		except ValueError:
			raise ValueError('Provider doesn\'t exists')

	
	def get_driver_container(self, driver):
		container = driver.get_container(container_name=self.bucket)

		return container
	
	
	def get_connected_driver_to_s3bucket(self):
		cls = get_driver(getattr(Provider, self.region))
		driver = cls(self.api_key, self.secret_key)

		return driver


	def driver_data_upload(self, driver, iterator, object_name):
		container = self.get_driver_container(driver)

		image_obj = driver.upload_object_via_stream(
			iterator=iterator,
			container=container,
			object_name=object_name
		)

		return image_obj