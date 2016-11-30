import os
import requests
import mimetypes
import cStringIO
import csv
import uuid
from PIL import Image
from io import BytesIO
from Queue import Queue
from threading import Thread, Semaphore
from time import sleep
import json

import sys
import logging
logging.basicConfig()

log = logging.getLogger(__name__)

from pprint import pprint

ALLOWED_TYPES = ['jpg', 'jpeg', 'gif', 'png']

class ThumbsGenerator():
	def __init__(self, scale_size, crop_size, connector, check_exists=None, threads_num=3):
		self.queue = Queue()
		self.semaphore = Semaphore(threads_num)
		self.driver = connector.driver
		self.uploader = connector.uploader
		self.crop_size = crop_size
		self.scale_size = scale_size
		self.check_exists = check_exists
		self.stop_threading = False

	def get_file_name(self, image_url):
		filename = os.path.basename(image_url)
		name_and_ext = os.path.splitext(filename)

		return name_and_ext


	def scale_image_by_width(self, image, width):
		width = min(width, image.size[0])
		scaled_image = image.resize((width, width * image.size[1] / image.size[0]), Image.NEAREST)

		return scaled_image


	def scale_image_by_height(self, image, height):
		height = min(height, image.size[1])
		scaled_image = image.resize((height * image.size[0] / image.size[1], height), Image.NEAREST)

		return scaled_image

	
	def crop_image(self, image, size, crop_type):
		
		# Crop in the top, middle or bottom
		if crop_type == 'top':
			box = (0, 0, size[0], size[1])
		
		elif crop_type == 'middle':
			box = (round((image.size[0] - size[0]) / 2), 0,
			round((image.size[0] + size[0]) / 2), size[1])
		
		elif crop_type == 'bottom':
			box = (0, (image.size[1] - size[1]), size[0], image.size[1])
		
		else :
			raise ValueError('ERROR: invalid value for crop_type')
		
		croped_image = image.crop(box)

		return croped_image


	def scale_and_crop(self, image, crop_type):

		# Get current and desired ratio for the images
		image_ratio = image.size[0] / float(image.size[1])
		ratio = self.scale_size[0] / float(self.scale_size[1])

		if ratio >= image_ratio:
			
			#Resize the image
			image_resized = self.scale_image_by_width(image, self.scale_size[0])
			image_cropped = self.crop_image(image_resized, self.crop_size, crop_type)

		elif ratio < image_ratio:
			
			#Resize the image
			image_resized = self.scale_image_by_height(image, self.scale_size[1])
			image_cropped = self.crop_image(image_resized, self.crop_size, crop_type)

		else:
			raise ValueError('ERROR: invalid sizes. Image ratio is: ' + str(image_ratio) + ' Desired ratio is: ' + str(ratio))

		return image_resized, image_cropped

	
	def generate_thumbnail(self, image_url, image_data, callback, crop_type='middle'):
		images_callback = [image_data]
		
		# Retrieve our source image from a URL
		try:
			res = requests.get(image_url)
		
		except requests.exceptions.ConnectionError:
			log.error('{0}: {1}'.format(requests.exceptions.ConnectionError, image_url))

			return
			
		# Load the URL data into an image
		image_bytes = BytesIO(res.content)

		if 'content-type' in res.headers and 'image/x' in res.headers.get('content-type'):
			log.warn('This type of image is not allowed: ' + res.headers.get('content-type'))
			
			return
		
		
		try:
			image = Image.open(image_bytes)
			
			# Resize the image
			image_transformed = self.scale_and_crop(image, crop_type)
			
			# NOTE, we're saving the image into a cStringIO object to avoid writing to disk
			image_name = self.get_file_name(image_url)
			
			# Now we connect to our s3 bucket and upload from memory
			if self.driver is None:
				return 
			
			driver = self.driver()
			
			# s3_folders = (str(self.scale_size[0]) + 'x' + str(self.scale_size[1]) + '_scale', str(self.crop_size[0]) + 'x' + str(self.crop_size[1]) + '_scalecrop')
			s3_folders = ('{0}x{1}_scale'.format(self.scale_size[0], self.scale_size[1]),
						'{0}x{1}_scalecrop'.format(self.crop_size[0], self.crop_size[1]))

			# Generate UUID for file name
			file_uuid = uuid.uuid4()

			for index, img in enumerate(image_transformed):
				ibytes = BytesIO()
				img.save(ibytes, 'JPEG')
				ibytes.seek(0)
				object_name = '{0}/{1}_{2}.jpg'.format(s3_folders[index], image_name[0], file_uuid)
				s3_img_obj = self.uploader(driver, ibytes, object_name)
				
				images_callback.append(s3_img_obj)
			
			if callback is not None:
				callback(images_callback)
			
		except ValueError as e:
			log.error('{0}: {1}'.format(e, image_bytes))
		except IOError as e:
			log.error('{0}: {1}'.format(e, res.headers.get('content-type')))

	def get_dict_csv(self, csv_path):
		csvfile = open(csv_path)
		reader = csv.DictReader(csvfile)

		return reader

	def get_urls_from_dict(self, key, callback):
		
		# Suspend execution of the calling thread for the given number of seconds
		sleep(0.1)
		
		try:
			image_data = self.queue.get()
			image_url = image_data[key]
			split_image = image_url.split('.')
			image_type = split_image.pop().lower()

			if image_type in ALLOWED_TYPES:
				in_storage = self.check_file_in_storage(image_url, image_data)
				if not in_storage:
					log.info('Before Thumbnail generation: {0}'.format(image_url))

					self.generate_thumbnail(image_url, image_data, callback)
			else:
				log.warn("File type is not an image.")
		finally:
			self.queue.task_done()
			self.semaphore.release()
			log.info('Thread finished')


	def check_file_in_storage(self, image_url, image_data):
		
		if self.check_exists is not None and isinstance(self.check_exists, dict):
				
			if self.check_exists['key'] in image_data:
				
				data_loaded = image_data[self.check_exists['key']]
				if self.check_exists['json'] and isinstance(data_loaded, basestring):
					data_loaded = json.loads(data_loaded)
				
				check_head = requests.head(image_url)
				
				if 'etag' in check_head.headers:
					etag = check_head.headers.get('etag')
					
					if self.check_exists['sub_key'] and self.check_exists['sub_key'] in data_loaded:
						
						if data_loaded[self.check_exists['sub_key']] == etag.strip('"'):
							log.info('Image already in storage.')

							return True
					else:

						if image_data[self.check_exists['key']] == etag.strip('"'):
							log.info('Image already in storage.')

							return True

		return False


	def generate_items_queue(self, data_dict):

		for row in data_dict:
			self.queue.put(row)

		log.info('Queue was generated!')


	def run_multithreading_download(self, key, callback):
		queue_size = self.queue.qsize()
		
		# Generating multiple Threads for downloading images from cloud and upload to bucket
		for i in range(queue_size):
			try:
				if not self.stop_threading:
					thread_image = Thread(target=self.get_urls_from_dict, args=(key, callback))
					thread_image.deamon = True
					self.semaphore.acquire()
					log.info('Thread started: {0}'.format(thread_image.name))
					thread_image.start()
			except self.queue.Empty:
				log.info("The Queue ended.")
				break
			except KeyboardInterrupt:
				log.info("Ctrl-c received! Sending kill to threads...")
				self.stop_threading = True

		self.queue.join()

	def download_from_csv(self, csv_path, key='url', callback=None):

		# Reading CSV data and converting it to data_dict
		reader = self.get_dict_csv(csv_path)
		self.download_from_dict(reader, key, callback)


	def download_from_dict(self, data_dict, key='url', callback=None):

		self.generate_items_queue(data_dict)
		self.run_multithreading_download(key, callback)
