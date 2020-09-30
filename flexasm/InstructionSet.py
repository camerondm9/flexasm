import copy
import re
import parsy

R_COMMA_SPACE = re.compile(r'\s*,\s*', re.IGNORECASE)
R_SPLIT = re.compile(r'(\s+|{[^\s\}]*}|[^\d\W]\w*|[^\w\s{}]+|\d+)', re.IGNORECASE)

class InstructionSet:
	def __init__(self, name):
		self._locked = False
		self._registers = {}
		self._formats = {}
		self._elements = {}
		self._instructions = []

	def _lock(self):
		self._locked = True

	def clone(self):
		result = copy.deepcopy(self)
		result._locked = False
		return result

	def register(self, names, **keys):
		if self._locked:
			raise RuntimeError('Instruction set is readonly after use!')
		if isinstance(names, str):
			names = [names]
		keys['name'] = names[0]
		for n in names:
			n = n.lower()
			if n in self._registers:
				raise RuntimeError('Register names must be unique!')
			self._registers[n] = keys

	def instruction_format(self, name, *words):
		if self._locked:
			raise RuntimeError('Instruction set is readonly after use!')
		pass

	def instruction_element(self, names, element):
		if self._locked:
			raise RuntimeError('Instruction set is readonly after use!')
		if isinstance(names, str):
			names = [names]
		for n in names:
			n = n.lower()
			if n in self._elements:
				raise RuntimeError('Element names must be unique!')
			self._elements[n] = element

	def instruction(self, syntax, **keys):
		if self._locked:
			raise RuntimeError('Instruction set is readonly after use!')
		syntax = R_COMMA_SPACE.sub(',', syntax).strip()
		parts = list(filter(None, R_SPLIT.split(syntax)))
		if not parts[0][0].isalpha() and parts[0][0] != '_':
			raise ValueError('Instruction must start with a name!')
		keys['name'] = parts[0]
		keys['syntax'] = parts
		self._instructions.append(keys)

	def registers(self):
		r = re.compile('(' + str.join('|', [re.escape(r) for r in self._registers.keys()]) + ')', re.IGNORECASE)
		@parsy.generate
		def result():
			result = yield parsy.regex(r)
			return result
		return result


	# def address_space(self, name, addr_bits = 32, data_bits = 8):

	# 	return AddressSpace()
