import sys
import os
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.layout import LAParams
from cStringIO import StringIO

import nltk
from nltk import word_tokenize
from nltk.stem.lancaster import LancasterStemmer

from xml.dom import minidom

import numpy as np
import math

import string


'''
	Box:
		which has the properties 'width' and 'height'.
'''
class Box(object):

	def __init__(self, width, height, center=np.array([0, 0]), objId=-1):
		self.id = objId
		self.width = width
		self.height = height
		self.center = center

	def getWidth(self): return self.width

	def getHeight(self): return self.height

	def getBoxCenter(self): return self.center

	def getId(self): return self.id

	def getBoxSize(self): return np.array([self.getWidth(), self.getHeight()])

	@staticmethod
	def calBoxSize(xml_obj):
		if 'bbox' in xml_obj.attributes.keys():
			pointsValues = xml_obj.attributes['bbox'].value.split(',')
			return np.array([ float(pointsValues[2]), float(pointsValues[3]) ]) - np.array([ float(pointsValues[0]), float(pointsValues[1]) ])
		return np.array([0, 0])

	@staticmethod
	def calBoxCenter(xml_obj):
		if 'bbox' in xml_obj.attributes.keys():
			pointsValues = xml_obj.attributes['bbox'].value.split(',')
			return ( np.array([ float(pointsValues[2]), float(pointsValues[3]) ]) + np.array([ float(pointsValues[0]), float(pointsValues[1]) ]) )/2
		return np.array([0, 0])


'''
	PaperPageInfo:
		which contains the contents within a single page.
'''
class PaperPageInfo(Box):

	def __init__(self, page_xml_obj):
		self.xmlObj = page_xml_obj
		boxSize = Box.calBoxSize(page_xml_obj)
		boxCenter = Box.calBoxCenter(page_xml_obj)
		if boxSize is not None:
			if 'id' in page_xml_obj.attributes.keys(): objId = page_xml_obj.attributes['id'].value
			else: objId = -1
			super(PaperPageInfo, self).__init__(width=boxSize[0], height=boxSize[1], objId=objId, center=boxCenter)

			textBoxes = page_xml_obj.getElementsByTagName('textbox')
			textBoxes = textBoxes[:-(len(textBoxes)/2)]
			self.textBoxes = []
			for textBox in textBoxes:
				self.textBoxes.append(TextBox(textBox))

		return

	def getXMLObject(self): return self.xmlObj

	def getTextBoxes(self): return self.textBoxes




class TextBox(Box):

	def __init__(self, textBox_xml_obj):
		self.xmlObj = textBox_xml_obj
		boxSize = Box.calBoxSize(textBox_xml_obj)
		boxCenter = Box.calBoxCenter(textBox_xml_obj)
		if boxSize is not None:
			if 'id' in textBox_xml_obj.attributes.keys(): objId = textBox_xml_obj.attributes['id'].value
			else: objId = -1
			super(TextBox, self).__init__(width=boxSize[0], height=boxSize[1], objId=objId, center=boxCenter)

			textLines = textBox_xml_obj.getElementsByTagName('textline')
			self.textLines = []
			for textLine in textLines:
				self.textLines.append(TextLine(textLine))

		return

	def getXMLObject(self): return self.xmlObj

	def getTextLines(self): return self.textLines


class TextLine(Box):

	def __init__(self, textLine_xml_obj):
		self.xmlObj = textLine_xml_obj
		boxSize = Box.calBoxSize(textLine_xml_obj)
		boxCenter = Box.calBoxCenter(textLine_xml_obj)
		if boxSize is not None:
			if 'id' in textLine_xml_obj.attributes.keys(): objId = textLine_xml_obj.attributes['id'].value
			else: objId = -1
			super(TextLine, self).__init__(width=boxSize[0], height=boxSize[1], objId=objId, center=boxCenter)

			texts = textLine_xml_obj.getElementsByTagName('text')
			self.texts = []
			for text in texts:
				self.texts.append(Text(text))

		return

	def getXMLObject(self): return self.xmlObj

	def getTexts(self): return self.texts

	def getLineText(self):
		string = ''
		for text in self.texts:
			string += getInnerXml(text.getXMLObject())
		return string


class Text(Box):

	def __init__(self, text_xml_obj):
		self.xmlObj = text_xml_obj
		boxSize = Box.calBoxSize(text_xml_obj)
		boxCenter = Box.calBoxCenter(text_xml_obj)
		if boxSize is not None:
			if 'id' in text_xml_obj.attributes.keys(): objId = text_xml_obj.attributes['id'].value
			else: objId = -1
			super(Text, self).__init__(width=boxSize[0], height=boxSize[1], objId=objId, center=boxCenter)

		if 'font' in text_xml_obj.attributes.keys(): self.textFont = text_xml_obj.attributes['font'].value
		else: self.textFont = ''
		
		if 'size' in text_xml_obj.attributes.keys(): self.textSize = text_xml_obj.attributes['size'].value
		else: self.textSize = ''

		return

	def getXMLObject(self): return self.xmlObj

	def getTextFont(self): return self.textFont

	def getTextSize(self): return self.textSize


def getInfo(path):
	info = {}
	info['title'] = ''
	info['authors'] = []
	info['publisher'] = ''

	title_candidates = getTitleStringCandidates(path)
	if len(title_candidates) > 0:
		info['title'] = title_candidates[0]

	return info

def getTitleStringCandidates(path):
	title_candidates = getTitleCandidates(path)
	title_aggred = []
	str_to_assert = ''

	for x in range(len(title_candidates)):
		needassert = True
		cur_cand = title_candidates[x]

		if len(cur_cand.getTextLines()) > 0 and len(cur_cand.getTextLines()[0].getTexts()) > 0:
			cur_text_size = cur_cand.getTextLines()[0].getTexts()[0].getTextSize()
			cur_text_font = cur_cand.getTextLines()[0].getTexts()[0].getTextFont()
		else:
			cur_text_size = ''
			cur_text_font = ''

		if str_to_assert == '':
			for titleline in cur_cand.getTextLines(): str_to_assert += titleline.getLineText()

		if x < len(title_candidates)-1:
			nxt_cand = title_candidates[x+1]
			if len(nxt_cand.getTextLines()) > 0 and len(nxt_cand.getTextLines()[0].getTexts()) > 0:
				first_text = nxt_cand.getTextLines()[0].getTexts()[0]
				if first_text.getTextSize() == cur_text_size and first_text.getTextFont() == cur_text_font:
					for titleline in nxt_cand.getTextLines(): str_to_assert += titleline.getLineText()
					needassert = False

		if needassert:
			title_aggred.append(str_to_assert)
			str_to_assert = ''

	return title_aggred

def getTitleCandidates(path):
	first_page_xml = extractPagesXml(path)[0]
	page_obj = getXmlObject(first_page_xml)
	page = PaperPageInfo(getPages(page_obj)[0])
	textboxes = page.getTextBoxes()

	titlecandidates = []
	tol = 50
	pagecenterX = page.getBoxCenter()[0]
	
	for textbox in textboxes:
		if len(textbox.getTextLines()) > 3:
			continue
		needsort = False
		if abs(textbox.getBoxCenter()[0] - pagecenterX) < tol or len(titlecandidates) == 0:
			titlecandidates.append(textbox)
			needsort = True
		else:
			if abs(textbox.getBoxCenter()[0] - pagecenterX) < abs(titlecandidates[0].getBoxCenter()[0] - pagecenterX):
				titlecandidates[0] = textbox
				needsort = True
        
		if len(titlecandidates) > 1 and needsort:
			firstcandidate = titlecandidates[0]
			for x in range(len(titlecandidates)):
				if x == 0:
					continue
				if abs(titlecandidates[x].getBoxCenter()[0] - pagecenterX) > abs(firstcandidate.getBoxCenter()[0] - pagecenterX):
					titlecandidates[0] = titlecandidates[x]
					titlecandidates[x] = firstcandidate
					firstcandidate = titlecandidates[0]

	for x in range(len(titlecandidates)-1):
		for y in range(len(titlecandidates)-x-1):
			xcand = titlecandidates[x]
			ycand = titlecandidates[y+x+1]

			xfontsizes = []
			yfontsizes = []
			for textline in xcand.getTextLines():
				size = textline.getTexts()[0].getTextSize()
				if float(size) > 0: xfontsizes.append(float(size))
			for textline in ycand.getTextLines():
				size = textline.getTexts()[0].getTextSize()
				if float(size) > 0: yfontsizes.append(float(size))
			if len(xfontsizes) > 0: xfontsize = sum(xfontsizes) / float(len(xfontsizes))
			else: xfontsize = 0
			if len(yfontsizes) > 0: yfontsize = sum(yfontsizes) / float(len(yfontsizes))
			else: yfontsize = 0

			if xfontsize < yfontsize or (xfontsize == yfontsize and xcand.getBoxCenter()[1] < ycand.getBoxCenter()[1]):
				titlecandidates[x] = ycand
				titlecandidates[y+x+1] = xcand

	return titlecandidates



def getInnerXml(xml_obj):
	if xml_obj.firstChild is not None:
		return str(xml_obj.firstChild.nodeValue)
	else:
		return ''

def getXmlObjects(stringArray):
	cnt = 0
	xmlObjArray = []
	for string in stringArray:
		xmlObjArray.append(getXmlObject(string))
	return xmlObjArray

def getXmlObject(string):
	return minidom.parseString(string)

def getPages(source):
	page = source.getElementsByTagName('page')
	return page

def testpath(idx=0):
	paths = []
	paths.append('./test-samples/OpticalMusicRecognition/Overview_of_Algorithms_and_Techniques_for_Optical_Music_Recognition.pdf')
	paths.append('./test-samples/OpticalMusicRecognition/HUMAN-DIRECTED OPTICAL MUSIC RECOGNITION.pdf')
	paths.append('./test-samples/OpticalMusicRecognition/2012ARebeloIJMIR.pdf')
	paths.append('./test-samples/AudioSignalProcessing/Oppenheim-1970_for_March_5.pdf')
	paths.append('./test-samples/AudioSignalProcessing/Oppenheim-Monasco-PhysRevLett-2013_for_March_12.pdf')
	paths.append('./test-samples/AudioSignalProcessing/BoorstynRife-IEEE-TransInfoTheory_for_March_19.pdf')
	paths.append('./test-samples/AudioSignalProcessing/11[jstsp]Signal Processing for Music Analysis_April_11.pdf')
	paths.append('./test-samples/AudioSignalProcessing/AllenBerkley79_for_Feb_26.pdf')
	paths.append('./test-samples/Articles/1302.4862v1 copy.pdf')
	paths.append('./test-samples/Articles/Beyond molecules self assembly of mesoscopic and macroscopic components copy.pdf')
	paths.append('./test-samples/Articles/A synthetic nanomaterial for virus recognition produced by surface imprinting copy.pdf')
	paths.append('./test-samples/Articles/1302.4102v1 copy.pdf')

	if idx not in range(len(paths)): idx = len(paths)-1

	return paths[idx]

def extractPages(pdfPath, format='txt'):
	fp = file(pdfPath, 'rb')
	rsrcmgr = PDFResourceManager()
	retstr = StringIO()
	codec = 'utf-8'
	laparams = LAParams()
	if format == 'xml':
		device = XMLConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
	elif format == 'txt':
		device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
	else:
		return []
	# Create a PDF interpreter object
	interpreter = PDFPageInterpreter(rsrcmgr, device)

	# Process each page contained in the document
	pages_text = []

	for page in PDFPage.get_pages(fp):
		# Get (and store) the "cursor" position of stream before reading from PDF
		# On the first page, this will be zero
		read_position = retstr.tell()
		# Read PDF page, write text into stream
		interpreter.process_page(page)
		# Move the "cursor" to the position stored
		retstr.seek(read_position, 0)
		# Read the text (from the "cursor" to the end)
		page_text = retstr.read()
		# Add this page's text to a convenient list
		page_text = filter(string.printable.__contains__, page_text)
		pages_text.append(page_text)

	return pages_text

def extractPagesXml(pdfPath):
	return extractPages(pdfPath, format='xml')

def extractPagesString(pdfPath):
	return extractPages(pdfPath, format='txt')

def toString(pages_text):
	string = ''
	for page_text in pages_text:
		string += page_text
	return string

def extractWord(string):
	raw = string.decode('utf-8')
	tokens = word_tokenize(raw)
	words = []
	for x in range(len(tokens)):
		if (tokens[x].endswith('-')): words.append(tokens[x][:-1] + tokens[x+1])
		else: words.append(tokens[x])
	return words

def stem(words):
	stemmedWords = []
	# Initiate stem tools
	st = LancasterStemmer()
	for word in words:
		stemmedWords.append(st.stem(word))
	return stemmedWords

def getUniqueCount(symbols):
	D = {}
	for symbol in symbols:
		if (symbol in D.keys()): D[symbol] += 1
		else: D[symbol] = 1
	return D

def mergeDictionaries(dic1_org, dic2_org, mode='union'):
	dic1 = dic1_org.copy()
	dic2 = dic2_org.copy()
	if str.lower(mode) == 'intersection':
		for key in dic1.keys():
			if not (key in dic2.keys()): del dic1[key]
		for key in dic2.keys():
			if not (key in dic1.keys()): del dic2[key]
	else:
		for key in dic1.keys():
			if not (key in dic2.keys()): dic2[key] = 0
		for key in dic2.keys():
			if not (key in dic1.keys()): dic1[key] = 0


	dic = {}
	for key in dic2.keys():
		dic[key] = dic1[key] + dic2[key]
	return dic

def main(argv):
	sys.exit(1)
	if len(argv) > 2:
		dictionary = {}
		for x in range(len(argv)-1):
			files = []
			if argv[x+1].endswith('.pdf'): files.append(argv[x+1])
			else:
				files = [f for f in os.listdir(argv[x+1]) if f.endswith('.pdf')]
				for i in range(len(files)):
					files[i] = argv[x+1] + files[i]

			for path in files:
				# Print log
				print('Processing ' + path + '...')

				# Extract text of the PDF file
				pages_text = extractPagesString(path)
	
				# Convert to string
				pdfStr = toString(pages_text)
				pdfStr = str.lower(pdfStr)

				# Split words
				# if len(dictionary.keys()) == 0: mode = 'union'
				# else: mode = 'intersection'
				mode = 'union'
				dictionary = mergeDictionaries( getUniqueCount( stem( extractWord(pdfStr) ) ), dictionary, mode=mode )

		for key in dictionary.keys():
			print(key + ": " + str(dictionary[key]))
		
	else:
		path = argv[1]
		pages_text = extractPagesXml(path)

		# for page in pages_text:
		print(pages_text[0])

	sys.exit(1)

if __name__ == '__main__': sys.exit(main(sys.argv))
