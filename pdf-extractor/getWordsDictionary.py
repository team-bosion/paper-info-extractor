# To get the number of occurrence of each word in a pdf file
import sys
import os
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from cStringIO import StringIO

import nltk
from nltk import word_tokenize
from nltk.stem.lancaster import LancasterStemmer

def extractPagesString(pdfPath):
	fp = file(pdfPath, 'rb')
	rsrcmgr = PDFResourceManager()
	retstr = StringIO()
	codec = 'utf-8'
	laparams = LAParams()
	device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
	# Create a PDF interpreter object.
	interpreter = PDFPageInterpreter(rsrcmgr, device)

	# Process each page contained in the document.
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
		pages_text.append(page_text)

	return pages_text

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

	# Testing Code
	# d1 = {'apple': 2, 'bird': 3, 'cat': 4, 'dog': 5}
	# d2 = {'cat': 2, 'dog': 3, 'egg': 4, 'fish': 5}
	# d3_union = mergeDictionaries(d1, d2, mode='union')
	# d3_intsec = mergeDictionaries(d1, d2, mode='intersection')
	# print('Union results:')
	# for key in d3_union.keys():
	# 	print(key + ": " + str(d3_union[key]))
	# print('Intersection results:')
	# for key in d3_intsec.keys():
	# 	print(key + ": " + str(d3_intsec[key]))
	# sys.exit(0)

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
		
	sys.exit(1)

if __name__ == '__main__': sys.exit(main(sys.argv))
