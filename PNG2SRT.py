#This script is written for Python 3 and requires the following packages: Requests, Pillow, Gooey

import xml.etree.ElementTree as ET
import requests
import base64
import json
import os
import sys
import argparse
from io import BytesIO
from PIL import Image, ImageOps
from gooey import Gooey, GooeyParser

AUTH_KEY = "Please put your Google API Key into API_KEY.txt"
VISION_ENDPOINT = "https://vision.googleapis.com/v1/images:annotate"
REQUEST_CHUNK_SIZE = 15 # There is a limit to the size of the request, so chunk it down to as much data as we can send without being rejected
						# If you run into errors with it crashing during the OCR step, try reducing this value
ADD_BACKGROUND = True # Can result in better OCR
SHRINK_IMAGE = True # Can result in better OCR
SCALE_FACTOR = 0.50 # Scale down to 50%
INVERT_COLORS = False
PRIMARY_LANGUAGE = "ja"
NETFLIX = True # when true look for netflix xml, when false look for dvd/bluray xml

def read_master_xml(filename):

	tree = ET.parse(filename)
	root = tree.getroot()
	
	entries = []
	if NETFLIX:
		print("starting netflix")
		for child in root:
			if "body" in child.tag:
				for child in child:
					start = child.attrib['begin'].replace(".",",")
					end = child.attrib['end'].replace(".",",")
					if "," not in start:
						start += ","
					if "," not in end:
						end += ","	
					start = start.ljust(12,"0")
					end = end.ljust(12,"0")
					filename = child[0].attrib['src']
					entries.append({"start": start, "end": end, "filename": filename})
	else:
		print("starting bluray")
		for child in root:
			if "Events" in child.tag:
				for child in child:
					if "Event" in child.tag:
						pre_start = child.attrib['InTC'] + '0'
						k = pre_start.rfind(":")
						start = pre_start[:k] + "," + pre_start[k+1:]
						pre_end = child.attrib['OutTC'] + '0'
						k = pre_start.rfind(":")
						end = pre_end[:k] + "," + pre_end[k+1:]
						for child in child:
							if "Graphic" in child.tag:
								filename = child.text
								entries.append({"start": start, "end": end, "filename": filename})	
	return entries
	
def ocr_text(filenames):
	output = {}
	
	# Break filenames array down into chunks so that the API can handle it
	chunked_filenames = [filenames[i:i+REQUEST_CHUNK_SIZE] for i in range(0, len(filenames), REQUEST_CHUNK_SIZE)]		 

	for i in range(len(chunked_filenames)):
		filenames = chunked_filenames[i]
		print("Generating request (%d/%d)..." % (i + 1, len(chunked_filenames)))
		sys.stdout.flush()
		data = { "requests": [] }  
		requested_filenames = []
		for filename in filenames:
			if not os.path.exists(filename):
				continue
			
			requested_filenames.append(filename)
		
			im = Image.open(filename)
			if ADD_BACKGROUND:
				# Put the subtitles on a background for better results
				bg = Image.new("RGB", im.size, (0,0,0))
				bg.paste(im,im)
				im = bg					   
			else:
				im = Image.open(filename)
				
			if INVERT_COLORS:
				im = ImageOps.invert(im)
				
			if SHRINK_IMAGE:
				im = im.resize((int(im.size[0] * SCALE_FACTOR), int(im.size[1] * SCALE_FACTOR)), Image.ANTIALIAS)
			
			# Save the compressed image to a memory IO buffer instead of a real file
			raw_image = BytesIO()
			im.save(raw_image, format="png")
			raw_image.seek(0)  # rewind to the start
			
			# Add request list
			data['requests'].append({ "image": { "content": base64.b64encode(raw_image.read()).decode() },
					"imageContext": { "languageHints": [ PRIMARY_LANGUAGE, "en" ] },
					"features": [ { "type": "TEXT_DETECTION", "maxResults": 1 } ],
				})
				
		if len(data['requests']) == 0:
			continue
				
		print("Requesting OCR text...")
		sys.stdout.flush()
		data = json.dumps(data)
		resp = requests.post(VISION_ENDPOINT, data=data, params={"key": AUTH_KEY}, headers={'Content-Type': 'application/json'})
		#open("output.json","wb").write(resp.text.encode('utf-8'))
		
		for idx, r in enumerate(resp.json()['responses']):
			#open("output_%d.json" % idx,"wb").write(json.dumps(r, indent=4, ensure_ascii=False, encoding="utf-8").encode('utf-8'))
			
			if 'textAnnotations' in r:
				output[requested_filenames[idx]] = r['textAnnotations'][0]['description']#.encode('utf8') # First entry is always the "final" output
		
	return output
	
def PNG2SRT(input_folder):
	global NETFLIX
	if os.path.isfile(os.path.join(input_folder, "manifest_ttml2.xml")):
		NETFLIX = True
		xml_filename = os.path.join(input_folder, "manifest_ttml2.xml")
	elif os.path.isfile(os.path.join(input_folder, "BDN_Index.xml")):
		NETFLIX = False
		xml_filename = os.path.join(input_folder, "BDN_Index.xml")
	else:
		print("ERROR: No XML file detected")
	srt_filename = os.path.join(input_folder, os.path.basename(input_folder)+".srt")

	entries = read_master_xml(xml_filename)
	print("Found input file "+xml_filename)
	
	filenames = [os.path.join(input_folder, c['filename']) for c in entries]
	results = ocr_text(filenames)
	
	print("Generating SRT file...")
	sys.stdout.flush()
	with open(srt_filename, "w", encoding='utf-8') as output:
		for i in range(len(entries)):
			entry = entries[i]
			
			text = "<TEXT HERE>"
			f = os.path.join(input_folder, entry['filename'])
			if f in results:
				text = results[f]
			
			output.write("%d\n" % (i + 1))
			output.write("%s --> %s\n" % (entry['start'], entry['end']))
			output.write("%s\n" % text)
			output.write("\n")
			output.write("\n")

	print("Finished!")
	sys.stdout.flush()

@Gooey(program_name = 'PNG2SRT')
def main():
	global REQUEST_CHUNK_SIZE
	global PRIMARY_LANGUAGE
	global AUTH_KEY
	
	#__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
	if getattr(sys, 'frozen', False):
		application_path = sys._MEIPASS
	else:
		application_path = os.path.dirname(os.path.abspath(__file__))
	with open(os.path.join(application_path, 'API_KEY.txt')) as myfile:
		AUTH_KEY=myfile.readline()
	
	parser = GooeyParser(description="Authkey: "+AUTH_KEY)
	parser.add_argument('InputFolder', widget="DirChooser")
	parser.add_argument('-c', '--chunk-size', default=REQUEST_CHUNK_SIZE, type=int, help="If you get errors, reduce to 10 or 5.", dest='chunk')
	parser.add_argument('-l', '--language', choices=['af', 'ar', 'as', 'az', 'be', 'bn', 'bg', 'ca', 'zh', 'hr', 'cs', 'da', 'nl', 'en', 'et', 'fil', 'fi', 'fr', 'de', 'el', 'he', 'hi', 'hu', 'is', 'id', 'it', 'iw', 'ja', 'kk', 'ko', 'ky', 'lv', 'lt', 'mk', 'mr', 'mn', 'ne', 'no', 'ps', 'fa', 'pl', 'pt', 'ro', 'ru', 'sa', 'sr', 'sk', 'sl', 'es', 'sv', 'ta', 'th', 'tl', 'tr', 'uk', 'ur', 'uz', 'vi'], default=PRIMARY_LANGUAGE, help="Select the primary language of the subtitles: \nhttps://cloud.google.com/vision/docs/languages", dest='lang')
	

	args = parser.parse_args()

	input_folder = args.InputFolder
	REQUEST_CHUNK_SIZE = args.chunk
	PRIMARY_LANGUAGE = args.lang
	
	PNG2SRT(input_folder)

if __name__ == '__main__':
	main()
