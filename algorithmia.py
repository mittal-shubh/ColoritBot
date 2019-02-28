import os
import time
import uuid
import mimetypes
import urllib
import requests
from PIL import Image
from io import BytesIO
import Algorithmia
import utilities
import ray

#@ray.remote
def waiting_message(user_id):
	if user_id:
		utilities.send_message(user_id, {"text": "It is coming!"})
		time.sleep(1.5)
		utilities.send_message(user_id, {"text": "I beg you few more seconds."})
	return

#@ray.remote
def runcoloritalgo(input):
	result = algo.pipe(input).result  # Outputs the image url
	print(result)
	#image_type = mimetypes.guess_type(urllib.parse.urlparse(result['output']).path)[0].split("/")[1]
	t800Bytes = client.file(result["output"]).getBytes()
	return t800Bytes

class parallel_processing:
	def __init__(self, user_id, input):
		self.user_id = user_id
		self.input = input

	def run(self):
		ray.init()
		result1 = waiting_message.remote(self.user_id)
		result2 = runcoloritalgo.remote(self.input)
		a, t800Bytes = ray.get([result1, result2])
		return t800Bytes

def if_color(local_file=None, image_url=None, get_response=None):
	if not (get_response or image_url or local_file):
		print("Provide atleast one of local_file, image_url or get_response attributes.")
		return
	if (get_response) and (not image_url) and (not local_file):
		im = Image.open(BytesIO(get_response)).convert('RGB')
	elif (local_file) and (not get_response) and (not image_url):
		im = Image.open(local_file).convert('RGB')
	elif (image_url) and (not local_file) and (not get_response):
		response = requests.get(image_url)
		im = Image.open(BytesIO(response.content)).convert('RGB')
	else:
		print("Provide only one of the local_file, image_url or get_response attributes.")
		return
	pix = im.load()
	image_size = im.size
	print(image_size)
	diff = 0
	for w in range(image_size[0]):
		for h in range(image_size[1]):
			r, g, b = pix[w, h]
			rg = abs(r-g)
			gb = abs(g-b)
			br = abs(b-r)
			diff += rg+gb+br
	print(diff)
	color_factor = float(diff)/(image_size[0]*image_size[1])
	print(color_factor)
	if round(color_factor) != 0:
		return True
	return False

def get_random_file_name(full_path=None, cwd_rsp_path=None, image_type='png'):
	if full_path and (not cwd_rsp_path):
		fp = full_path
	elif cwd_rsp_path and (not full_path):
		fp = cwd_rsp_path
	else:
		print("Please provide only one of these attributes: [full_path, cwd_rsp_path].")
		return
	if not os.path.exists(fp):
		os.mkdir(fp)
		print('Directory Created')
	else:
		print("Directory Exists")
	file_name = fp + '/' + uuid.uuid4().hex + '.%s' %image_type
	while os.path.isfile(file_name):
		print("File (%s) already exists" %file_name)
		file_name = fp + '/' + uuid.uuid4().hex + '.%s' %image_type
	return file_name

def colorit(algorithm='deeplearning/ColorfulImageColorization/1.1.5', local_file=None, algorithmia_file=None, 
	image_url=None, image_path=None, user_id=None):
	print("Coloring It")
	color = False
	if (local_file) and (not algorithmia_file) and (not image_url):
		input = bytearray(open(local_file, "rb").read())
		color = if_color(local_file=local_file)
	elif (algorithmia_file) and (not image_url) and (not local_file):
		input = {"image": algorithmia_file}
		color = if_color()
	elif (image_url) and (not local_file) and (not algorithmia_file):
		# Try this: https://scontent.xx.fbcdn.net/v/t1.15752-9/52297953_405991800162283_7056520676215095296_n.jpg?_nc_cat=111&_nc_ad=z-m&_nc_cid=0&_nc_zor=9&_nc_ht=scontent.xx&oh=4a1c6de3a6614aa21f5fe8e20e84f43b&oe=5CE4CA2D
		response = requests.get(image_url)
		input = bytearray(response.content)
		color = if_color(get_response=response.content)
	else:
		print("Provide only one of the local_file, algorithmia_file or image_url attributes.")
		return
	if color:
		return "It's not a black & white image. Provide a black & white one."
	try:
		client = Algorithmia.client(os.environ['ALGORITHMIA_KEY'])
		algo = client.algo(algorithm)
		if user_id and image_path:
			file_name = get_random_file_name(cwd_rsp_path="static/colored_images", image_type='png')
			image_path=os.path.join(os.path.realpath(os.path.join(os.getcwd(),os.path.dirname(__file__))),file_name)
			print(image_path)
			#processor = parallel_processing(user_id, input)
			#t800Bytes = processor.run()
			waiting_message(user_id)
			t800Bytes = runcoloritalgo(input)
			Image.open(BytesIO(t800Bytes)).save(image_path)
			return file_name
		else:
			file_name = algo.pipe(input).result  # Outputs the image url
		return file_name
	except Exception as e:
		print('[Error]: '+str(e))
		return

'''
# The .dir() method takes a Data URI path and returns an Algorithmia.datadirectory.DataDirectory object for the child directory.
client.dir("data://.my")
# Check if a specific directory exists
client.dir("data://.my/robots").exists()
# The .dirs() method returns a generator object of all the child directories.
for dir in client.dir("data://.my").dirs():
    # The .url is a convenience field that holds "/v1/data/" + dir.path
    # The .path is the path to the directory
    print "Directory " + dir.path + " at URL " + dir.url
# List files in the 'robots' directory
dir = client.dir("data://.my/robots")
# The .files() method returns a generator object of all the files in directory
for file in dir.files():
    print "File " + file.path + " at URL " + file.url + " last modified " + file.last_modified
# Creating a directory
robots = client.dir("data://.my/robots")
robots.create()
# You can also create a directory with different permissions
from Algorithmia.acl import ReadAcl
# Supports: ReadAcl.public, ReadAcl.private, ReadAcl.my_algos
robots.create(ReadAcl.public)
# Updating a directory
from Algorithmia.acl import ReadAcl, AclType
print robots.get_permissions().read_acl == AclType.my_algos #  True
# Supports: ReadAcl.public, ReadAcl.private, ReadAcl.my_algos
robots.update_permissions(ReadAcl.private)  # True if update succeeded
# Deleting a directory
robots = client.dir("data://.my/robots")
if robots.exists():
    robots.delete()

# Check if a file exists
if client.file("data://.my/robots/T-800.png").exists():
    print("HAL 9000 exists")
# Download file and get the file handle
t800File = client.file("data://.my/robots/T-800.png").getFile()
# Get file's contents as a string
t800Text = client.file("data://.my/robots/T-800.txt").getString()
# Get file's contents as JSON
t800Json =  client.file("data://.my/robots/T-800.txt").getJson()
# Get file's contents as a byte array
t800Bytes = client.file("data://.my/robots/T-800.png").getBytes()
# Upload local file
client.file("data://.my/robots/Optimus_Prime.png").putFile("/path/to/Optimus_Prime.png")
# Write a text file
client.file("data://.my/robots/Optimus_Prime.txt").put("Leader of the Autobots")
# Write a dict to a JSON file
client.file("data://.my/robots/Optimus_Prime.json").putJson({"faction": "Autobots"})
# Delete a file
client.file("data://.my/robots/C-3PO.txt").delete()'''