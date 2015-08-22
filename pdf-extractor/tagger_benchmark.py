import os
import json
import glob
import re
import sys

from difflib import SequenceMatcher

from pdfExtractor import getTitleCandidates, getTitleStringCandidates

counter = 0
THRESHOLD = 0.8

def dummy_get_candidates(path):
	global counter
	counter += 1
	sys.stdout.write('\rrunning ' + str(counter) + ': ' + path)
	sys.stdout.flush()

	title_candidates = ['^']

	try:
		title_candidates = getTitleStringCandidates(path)
	except:
		title_candidates = ['^']
		print '\nerror >.^'
	return title_candidates

class BenchmarkRunner:
	def __init__(self, categories):
		self.categories = categories
		pass

	def _compare(self, pair):
		result, target = pair
		try:
			ratio = SequenceMatcher(None, result, target['title']).ratio()
		except:
			raise
		return ratio

	def _compare_candidates(self, pair):
		results, target = pair
		return max(map(self._compare, zip(results, [target] * len(results))))

	def _load_json(self, path):
		return json.load(open(path, 'r'))

	def _run_category(self, category, max_number = 100):
		pdf_list = sorted(glob.glob(category + '/*.pdf'))[:max_number]
		json_list = sorted(glob.glob(category + '/*.json'))[:max_number]
		if len(pdf_list) != len(json_list):
			raise Error('pdf file count != json file count')
		pattern = '.*/(.*).pdf'
		matcher = re.compile(pattern)
		filenames = map(lambda x: x.group(1), map(matcher.match, pdf_list))
		candidates = map(dummy_get_candidates, pdf_list)
		targets = map(self._load_json, json_list)
		results = map(lambda x: x[0], candidates)
		scores = map(self._compare, zip(results, targets))
		failed = map(lambda x: x[1], filter(lambda x: x[0] < THRESHOLD, zip(scores, zip(filenames, results))))
		candidates_scores = map(self._compare_candidates, zip(candidates, targets))

		print('\n[%s] candidate score: %f / %d' % (category, sum(candidates_scores), min(max_number, len(pdf_list))))
		print('[%s] actual score: %f / %d' % (category, sum(scores), min(max_number, len(pdf_list))))

		print('[%s] failed pdfs: (written in files)' % (category))
		failed_file = open(category + '.txt', 'w')
		for pdf in failed:
			failed_file.write(pdf[0] + '.pdf\t' + str([pdf[1]]) + '\n')

	def run(self):
		map(self._run_category, self.categories)

def main():

	categories = [
		'exoplanet',
		'dark matter',
		'neural network',
		'theory of relativity',
		'boson',
		'STM',
		'dynamic programming',
		'binary tree',
		'directed graph',
		'active learning'
	]
	runner = BenchmarkRunner(categories)
	results = runner.run()


if __name__ == '__main__':
	main()