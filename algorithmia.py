import os
import uuid
import mimetypes
import urllib
import requests
from PIL import Image
from io import BytesIO
import Algorithmia

def colorit(local_file=None, algorithmia_file=None, image_url=None, image_path=None, user_id=None):
	if local_file:
		image = local_file
		input = bytearray(open(local_file, "rb").read())
	if algorithmia_file:
		input = {"image": algorithmia_file}
	if image_url:
		# Try this: https://scontent.xx.fbcdn.net/v/t1.15752-9/52297953_405991800162283_7056520676215095296_n.jpg?_nc_cat=111&_nc_ad=z-m&_nc_cid=0&_nc_zor=9&_nc_ht=scontent.xx&oh=4a1c6de3a6614aa21f5fe8e20e84f43b&oe=5CE4CA2D
		response = requests.get(image_url)
		image = BytesIO(response.content)
		input = bytearray(image)
	if not algorithmia_file:
		im = Image.open(image).convert('RGB')
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
		return "It's not a black & white image. Provide a black & white one."
	if image_path:
		if not os.path.exists("static/colored_images"):
			os.mkdir("static/colored_images")
			print('Directory Created')
		else:
			print("Directory Exists")
		#image_type = mimetypes.guess_type(urllib.parse.urlparse(result['output']).path)[0].split("/")[1]
		image_type = 'png'
		file_name = "static/colored_images/" + uuid.uuid4().hex + '.%s' %image_type
		while os.path.isfile(file_name):
			print("File (%s) already exists" %file_name)
			file_name = "static/colored_images/" + uuid.uuid4().hex + '.%s' %image_type
		__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
		image_path = os.path.join(__location__, file_name)
		print(image_path)
	client = Algorithmia.client(os.environ['ALGORITHMIA_KEY'])
	algo = client.algo('deeplearning/ColorfulImageColorization/1.1.5')
	try:
		if user_id:
			utilities.send_message(user_id, {"text": "It is coming!"})
			time.sleep(5)
			utilities.send_message(user_id, {"text": "I beg you few more seconds."})
		result = algo.pipe(input).result  # Outputs the image url
		print(result)
		t800Bytes = client.file(result["output"]).getBytes()
		if image_path:
			Image.open(BytesIO(t800Bytes)).save(image_path)
			return file_name
	except Exception as e:
		print(str(e))
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