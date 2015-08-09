import sys
import os

import pdfExtractor
from pdfExtractor import PaperPageInfo, TextBox, TextLine, Text

def main(argv):
	path = pdfExtractor.testpath()
	pages_xml = pdfExtractor.extractPagesXml(path)

	pxml = pdfExtractor.getXmlObject(pages_xml[0])
	print pages_xml[0]
	

	sys.exit(1)
	pages_xml_objs = pdfExtractor.getXmlObjects(pages_xml)
	page_obj = pdfExtractor.getPages(pages_xml_objs[0])[0]

	pageObject = PaperPageInfo(page_obj)

	print pageObject.getBoxSize()
	print pageObject.getBoxCenter()
	print pageObject.getId()
	print len(pageObject.getTextBoxes()[0].getTextLines()[0].getTexts())

	for text in pageObject.getTextBoxes():
		print('id: ' + str(text.getId()) + ', size: ' + str(text.getBoxCenter()))

	sys.exit(1)

if __name__ == '__main__': sys.exit(main(sys.argv))
