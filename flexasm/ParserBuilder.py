import re
import parsy

class ParserBuilder:
	def __init__(self):
		self.keys = {}
		self.options = {}

	def __call__(self, value, **keys):
		return self.option(value, **keys)

	def option(self, value, **keys):
		if value in self.options:
			raise ValueError('Duplicate options are not allowed!')
		self.options[value] = keys
		return self

	def always(self, **keys):
		self.keys.update(keys)
		return self

	def build(self):
		r = re.compile(str.join('|', [re.escape(o) for o in self.options.keys()]), re.IGNORECASE)
		@parsy.generate
		def result(self=self, r=r):
			o = yield parsy.regex(r)
			return {**self.keys, **self.options[o]}
		return result
