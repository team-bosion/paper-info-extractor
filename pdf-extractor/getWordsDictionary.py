# To get the number of occurrence of each word in a pdf file
import sys
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
	words = nltk.Text(tokens)
	return tokens

def main(argv):
	# Assign the PDF path
	path = argv[1];

	# Extract text of the PDF file
	pages_text = extractPagesString(path)

	# Initiate stem tools
	st = LancasterStemmer()
	
	# Convert to string
	pdfStr = toString(pages_text)
	pdfStr = str.lower(pdfStr)

	# Split words
	words = extractWord(pdfStr)
	for word in words:
		word = st.stem(word)
		print(word)

	sys.exit(1)

if __name__ == '__main__': sys.exit(main(sys.argv))
