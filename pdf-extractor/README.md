# pdfExtractor API

## Requirements
- Python 2
- pdfminer
- xml.dom
- numpy

## Features
- extracting strings which might be the title of the pdf

## Classes
### Box
- An object contains its position/size information.
- methods
	- `box.getWidth()`
	- `box.getHeight()`
	- `box.getBoxCenter()`
	- `box.getId()`
	- `box.getBoxSize()`

### TextBox extends Box
- An object contains several `TextLine` objects.
- methods
	- `textbox.getTextLines()`: return `TextLine` array

### TextLine extends Box
- An object contains several `Text` objects.
- methods
	- `textline.getTexts()`: return `Text` array
	- `textline.getLineText()`: return the string of the line

### Text extends Box
- An object contains a character, its font style and size.
- methods
	- `text.getTextFont()`: return font style
	- `text.getTextSize()`: return font size

## APIs
### `pdfExtractor.getTitleCandidates(path={PATH})`
- return `TextBox` array.

### `pdfExtractor.getTitleStringCandidates(path={PATH})`
- return string array.
