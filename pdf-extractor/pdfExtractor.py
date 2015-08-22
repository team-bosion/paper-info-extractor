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
import re

import functools


'''
	Box:
		which has the properties 'width' and 'height'.
'''
class Box(object):

	def __init__(self, xml_obj):
		self.xmlObj = xml_obj
		self.width = -1
		self.height = -1
		self.objId = -1
		self.center = np.array([-1, -1])

		boxSize = self.calBoxSize(xml_obj)
		boxCenter = self.calBoxCenter(xml_obj)
		if boxSize is not None:
			objId = -1
			if xml_obj.attributes:
				if 'id' in xml_obj.attributes.keys(): objId = xml_obj.attributes['id'].value

			self.width = boxSize[0]
			self.height = boxSize[1]
			self.objId = objId
			self.center = boxCenter

	def getWidth(self): return self.width

	def getHeight(self): return self.height

	def getBoxCenter(self): return self.center

	def getId(self): return self.objId

	def getBoxSize(self): return np.array([self.getWidth(), self.getHeight()])

	def getXMLObject(self): return self.xmlObj

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


class Text(Box):

	def __init__(self, text_xml_obj):
		super(Text, self).__init__(text_xml_obj)
		self.textFont = ''
		self.textSize = -1
		if text_xml_obj.attributes:
			if 'font' in text_xml_obj.attributes.keys(): self.textFont = text_xml_obj.attributes['font'].value
		if text_xml_obj.attributes:
			if 'size' in text_xml_obj.attributes.keys():
				try: self.textSize = text_xml_obj.attributes['size'].value
				except: self.textSize = -1


	def getTextFont(self): return self.textFont

	def getTextSize(self): return self.textSize

	def getInnerXml(self):
		if self.xmlObj.firstChild is not None:
			return str(self.xmlObj.firstChild.nodeValue)
		else:
			return ''

class TextLine(Box):

	def __init__(self, textLine_xml_obj):
		super(TextLine, self).__init__(textLine_xml_obj)
		texts = textLine_xml_obj.getElementsByTagName('text')
		self.texts = map(Text, texts)

	def getTexts(self): return self.texts
    
	def getAvgFontSize(self):
		if len(self.texts) > 0:
			fontsizes = map(lambda text: float(text.getTextSize()), self.texts)
			fontsizes = filter(lambda x: x > 0, fontsizes)
			return float(int( sum(fontsizes) / len(fontsizes) * 1000 )) / 1000
		else:
			return -1

	def getLineText(self):
		strings = map(lambda text: text.getInnerXml(), self.texts)
		return reduce(lambda x,y: x+y, strings)


class TextBox(Box):

	def __init__(self, textBox_xml_obj):
		super(TextBox, self).__init__(textBox_xml_obj)
		textLines = textBox_xml_obj.getElementsByTagName('textline')
		self.textLines = map(TextLine, textLines)

	def getTextLines(self): return self.textLines
    
	def getAvgFontSize(self):
		if len(self.textLines) > 0:
			fontsizes = map(lambda textline: float(textline.getAvgFontSize()), self.textLines)
			fontsizes = filter(lambda x: x > 0, fontsizes)
			return float(int( sum(fontsizes) / len(fontsizes) * 1000 )) / 1000
		else:
			return -1
        
	def merge_box(self, box):
		map(lambda x: self.textLines.append(x), box.getTextLines())

	def toString(self): return reduce( lambda x,y: x+y , map(lambda x: x.getLineText(), self.textLines) );


'''
	Page:
		which contains the contents within a single page.
'''
class Page(Box):

	def __init__(self, page_xml_obj):
		super(Page, self).__init__(page_xml_obj)
		textBoxes = page_xml_obj.getElementsByTagName('textbox')
		textBoxes = textBoxes[:-(len(textBoxes)/2)]
		self.textBoxes = map(TextBox, textBoxes)

	def getTextBoxes(self): return self.textBoxes


'''
	PaperInfo
'''
class PaperInfo(object):

	def __init__(self, pdf_path=None):
		self.titles = []
		self.authors = []
		self.publisher = ''

		if pdf_path:
			fp = file(pdf_path, 'rb')
			rsrcmgr = PDFResourceManager()
			retstr = StringIO()
			codec = 'utf-8'
			laparams = LAParams()
			device = XMLConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
			interpreter = PDFPageInterpreter(rsrcmgr, device)
			pages_iterator = PDFPage.get_pages(fp)

			first_page = None
			for page in pages_iterator:
				read_position = retstr.tell()
				interpreter.process_page(page)
				retstr.seek(read_position, 0)
				first_page = retstr.read()
				first_page = filter(string.printable.__contains__, first_page)
				break

			if not first_page: pass

			first_page_xml = minidom.parseString(first_page).getElementsByTagName('page')[0]
			title_page = Page(first_page_xml)

			centerX = title_page.getBoxCenter()[0]
			textboxes = title_page.getTextBoxes()
			might_be_title = map(functools.partial(self._might_be_title, page_centerX=centerX), textboxes)
			title_cands = filter(lambda x: x[0], zip(might_be_title, textboxes))
			title_cands = map(lambda x: x[1], title_cands)

			title_cands = self._aggregate(title_cands)
			title_cands = self._post_filter(title_cands)

			title_cands = self._sorted(title_cands)

			if len(title_cands) > 0:
				self.titles = map(lambda title_cand: title_cand.toString(), title_cands)


	def _is_aligned_center_or_edge(self, box_obj=None, tol=0, page_centerX=0):
		if box_obj:
			if abs(box_obj.getBoxCenter()[0] - page_centerX) < tol: return True
			if abs(box_obj.getBoxCenter()[0] - box_obj.getBoxSize()[0]/2) < tol: return True
			if abs(box_obj.getBoxCenter()[0] + box_obj.getBoxSize()[0]/2 - page_centerX*2) < tol: return True

		return False

	def _might_be_title(self, textbox, page_centerX):
		if not textbox: return False
		if len(textbox.getTextLines()) > 3: return False
		if not self._is_aligned_center_or_edge(box_obj=textbox, tol=20, page_centerX=page_centerX): return False

		return True

	def _have_same_fontsize_n_fonttype(self, a, b):
		afont = a.getTextLines()[0].getTexts()[0].getTextFont()
		bfont = b.getTextLines()[0].getTexts()[0].getTextFont()
		if afont != bfont: return False
		if a.getAvgFontSize() != b.getAvgFontSize(): return False
 
		return True

	def _sorted(self, title_cands):
		# return sorted(title_cands, key=lambda x: x.getAvgFontSize(), reverse=True)

		for x in range(len(title_cands)-1):
			for y in range(len(title_cands)-x-1):
				xcand = title_cands[x]
				ycand = title_cands[x+y+1]

				if xcand.getAvgFontSize() <= xcand.getAvgFontSize():
					if xcand.getAvgFontSize() < xcand.getAvgFontSize() or xcand.getBoxCenter()[1] < ycand.getBoxCenter()[1]:
						title_cands[x] = xcand
						title_cands[x+y+1] = ycand

		return title_cands

	def _aggregate(self, title_cands):
		if len(title_cands) == 0:
			return title_cands

		title_cands_aggred = []
		cnt = 0
		title_cands_aggred.append(title_cands[cnt])
		curfontsize = title_cands_aggred[cnt].getAvgFontSize()
		curfontstyle = title_cands_aggred[cnt].getTextLines()[0].getTexts()[0].getTextFont()

		for x in range(len(title_cands)):
			if x == 0: continue

			dummyfontsize = title_cands[x].getAvgFontSize()
			dummyfontstyle = title_cands[x].getTextLines()[0].getTexts()[0].getTextFont()

			if curfontstyle == dummyfontstyle and curfontsize == dummyfontsize:
				title_cands_aggred[cnt].merge_box(title_cands[x])
			else:
				title_cands_aggred.append(title_cands[x])
				cnt += 1
				curfontsize = title_cands_aggred[cnt].getAvgFontSize()
				curfontstyle = title_cands_aggred[cnt].getTextLines()[0].getTexts()[0].getTextFont()

		return title_cands_aggred

	def _post_filter(self, title_cands):
		condition1 = lambda x: len(re.sub('[^a-zA-Z]+', '', x)) > 30
		condition2 = lambda x: len(re.sub('[^\.\?\=\+\-]+', '', x)) < 5

		title_cands_filtered = title_cands
		title_cands_filtered = filter(lambda x: condition1(x.toString()), title_cands_filtered)
		title_cands_filtered = filter(lambda x: condition2(x.toString()), title_cands_filtered)

		return title_cands_filtered

	def getTitles(self): return self.titles

	def getTitle(self): return self.titles[0]

	def getAuthors(self): return self.authors

	def getPublisher(self): return self.publisher



def testpath(idx=0):
	paths = [
		'./test-samples/OpticalMusicRecognition/Overview_of_Algorithms_and_Techniques_for_Optical_Music_Recognition.pdf',
		'./test-samples/OpticalMusicRecognition/HUMAN-DIRECTED OPTICAL MUSIC RECOGNITION.pdf',
		'./test-samples/OpticalMusicRecognition/2012ARebeloIJMIR.pdf',
		'./test-samples/AudioSignalProcessing/Oppenheim-1970_for_March_5.pdf',
		'./test-samples/AudioSignalProcessing/Oppenheim-Monasco-PhysRevLett-2013_for_March_12.pdf',
		'./test-samples/AudioSignalProcessing/BoorstynRife-IEEE-TransInfoTheory_for_March_19.pdf',
		'./test-samples/AudioSignalProcessing/11[jstsp]Signal Processing for Music Analysis_April_11.pdf',
		'./test-samples/AudioSignalProcessing/AllenBerkley79_for_Feb_26.pdf',
		'./test-samples/Articles/1302.4862v1 copy.pdf',
		'./test-samples/Articles/Beyond molecules self assembly of mesoscopic and macroscopic components copy.pdf',
		'./test-samples/Articles/A synthetic nanomaterial for virus recognition produced by surface imprinting copy.pdf',
		'./test-samples/Articles/1302.4102v1 copy.pdf'
	]

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

	info = PaperInfo(testpath())

	print('title: ' + info.getTitle())
	print('authors: ')
	print(info.getAuthors())
	print('publisher: ' + info.getPublisher())

	sys.exit(1)

if __name__ == '__main__': sys.exit(main(sys.argv))
