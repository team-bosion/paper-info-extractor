import sys
import os

import pdfExtractor
from pdfExtractor import PaperPageInfo

def main(argv):
	path = pdfExtractor.testpath()
	pages_xml = pdfExtractor.extractPagesXml(path)
	pages_xml_objs = pdfExtractor.getXmlObjects(pages_xml)
	page_obj = pdfExtractor.getPages(pages_xml_objs[0])[0]

	pageObject = PaperPageInfo(page_obj)

	sys.exit(1)

if __name__ == '__main__': sys.exit(main(sys.argv))
