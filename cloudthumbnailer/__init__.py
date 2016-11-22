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

import logging

log = logging.getLogger(__name__)

from pprint import pprint

class ThumbsGenerator():
	def __init__(self, scale_size, crop_size, driver=None, threads_num=3,):
		self.queue = Queue()
		self.semaphore = Semaphore(threads_num)
		self.driver = driver.driver
		self.bucket = driver.bucket
		self.crop_size = crop_size
		self.scale_size = scale_size
		self.stop_threading = False

	def get_file_name(self, image_url):
		split_url = image_url.split('/')
		get_fname = split_url.pop()
		split_name = get_fname.split('.')

		ext = split_name.pop()
		file_name = ''.join(split_name)

		return (file_name, ext)


	def scale_image_by_width(self, image, width):
		scaled_image = image.resize((width, int(round(width * image.size[1] / image.size[0]))), Image.NEAREST)

		return scaled_image


	def scale_image_by_height(self, image, height):
		scaled_image = image.resize((int(round(height * image.size[0] / image.size[1])), height), Image.NEAREST)

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

		if ratio > image_ratio:
			
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

	
	def generate_thumbnail(self, image_url, callback, crop_type='middle'):
		images_callback = []
		
		#Retrieve our source image from a URL
		try:
			fp = requests.get(image_url)
			
			#Load the URL data into an image
			image_bytes = BytesIO(fp.content)

			if 'content-type' in fp.headers and 'image/x' in fp.headers.get('content-type'):
				log.warn('This type of image is not allowed: ' + fp.headers.get('content-type'))
				
				return
		
		except requests.exceptions.ConnectionError:
			log.warn(image_url)
			log.error(requests.exceptions.ConnectionError)

			return
		
		try:
			image = Image.open(image_bytes)
			
			#Resize the image
			image_transformed = self.scale_and_crop(image, crop_type)

			#NOTE, we're saving the image into a cStringIO object to avoid writing to disk
			set_image_name = self.get_file_name(image_url);

			#Generate UUID for file name
			file_uuid = uuid.uuid4();

			#Now we connect to our s3 bucket and upload from memory
			if self.driver is None:
				return 
			
			driver_cred = self.driver()
			container = driver_cred.get_container(container_name=self.bucket)
			s3_folders = (str(self.scale_size[0]) + 'x' + str(self.scale_size[1]) + '_scale', str(self.crop_size[0]) + 'x' + str(self.crop_size[1]) + '_scalecrop')
			
			for index, img in enumerate(image_transformed):
				ibytes = BytesIO()
				img.save(ibytes, 'JPEG')
				ibytes.seek(0)
				s3_img_obj = driver_cred.upload_object_via_stream(iterator=ibytes,
													container=container,
													object_name= s3_folders[index] + '/' + set_image_name[0] + '_' + str(file_uuid) + '.jpg')
				images_callback.append(s3_img_obj)
			
			if callback is not None:
				callback(images_callback)
			
		except ValueError:
			log.error(ValueError)
		except IOError as e:
			log.warn(fp.headers.get('content-type'))
			log.error(e)

	def get_dict_csv(self, csv_path):
		csvfile = open(csv_path)
		reader = csv.DictReader(csvfile)

		return reader

	def get_urls_from_dict(self, url, callback):
		sleep(0.1)
		image_url = self.queue.get()
		self.generate_thumbnail(image_url, callback)
		print('===================================================================')
		print(image_url)
		print('===================================================================')
		self.semaphore.release()
		print('Thread finished')



	def generate_items_queue(self, data_dict, key):

		for row in data_dict:
			self.queue.put(row[key])

		print('Queue was generated!')


	def run_multithreading_download(self, key, callback):		
		
		# Generating multiple Threads for downloading images from cloud and upload to bucket
		while not self.queue.empty() and not self.stop_threading:
			try:			
				thread_image = Thread(target=self.get_urls_from_dict, args=(key, callback))
				
				self.semaphore.acquire()
				print('Thread started: {0}'.format(thread_image.name))
				thread_image.start()
			
			except KeyboardInterrupt:
				print "Ctrl-c received! Sending kill to threads..."
				self.stop_threading = True

	def download_from_csv(self, csv_path, key='url', callback=None):

		# Reading CSV data and converting it to data_dict
		reader = self.get_dict_csv(csv_path)
		self.generate_items_queue(reader, key)
		self.run_multithreading_download(key, callback)

	def download_from_dict(self, data_dict, key='url', callback=None):

		self.generate_items_queue(data_dict, key)
		self.run_multithreading_download(key, callback)