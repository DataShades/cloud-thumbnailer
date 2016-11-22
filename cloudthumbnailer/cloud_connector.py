from libcloud.storage.types import Provider
from libcloud.storage.providers import get_driver

class CloudConnector():
	def __init__(self, provider="s3", api_key=None, secret_key=None, bucket=None):
		self.api_key = api_key
		self.secret_key = secret_key
		self.bucket = bucket
		self.driver = {
			's3': self.connect_to_s3bucket,
		}.get(provider)


	def connect_to_s3bucket(self):
		cls = get_driver(Provider.S3_AP_SOUTHEAST2)
		driver = cls(self.api_key, self.secret_key)

		return driver