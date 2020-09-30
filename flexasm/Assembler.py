import collections
import copy
import re
import parsy

from InstructionSet import InstructionSet
from Expression import parse_expression
from ParserBuilder import ParserBuilder

R_COMMENT = re.compile(r'\s*[#;].*', re.IGNORECASE)
R_LABEL = re.compile(r'(?:(?:[^\d\W]\w*)?\.)?[^\d\W]\w*:\s*', re.IGNORECASE)
R_SPACE = re.compile(r'\s+', re.IGNORECASE)
R_COMMA_SPACE = re.compile(r'\s*,\s*', re.IGNORECASE)
R_INTEGER = re.compile(r'[+-]?\d+', re.IGNORECASE)

class Assembler:
	def __init__(self, instruction_set):
		self._iset = instruction_set
		self._parsers = []
		for ins in instruction_set._instructions:
			syntax_parts = ins['syntax']
			for part in syntax_parts:
				if part[0] == '{' and part[-1] == '}' and part[1:-1] not in instruction_set._elements:
					raise ValueError('Element ' + part[1:-1] + ' is not defined!')
			@parsy.generate
			def parser(ins=ins, syntax_parts=syntax_parts):
				keys = None
				for part in syntax_parts:
					if part.isspace():
						yield parsy.regex(R_SPACE)
					elif part == ',':
						yield parsy.regex(R_COMMA_SPACE)
					elif part[0] == '{':
						new_keys = yield instruction_set._elements[part[1:-1]]
						if keys is None:
							keys = copy.copy(ins)
							del keys['syntax']
						keys.update(new_keys)
					else:
						yield parsy.regex(re.compile(re.escape(part), re.IGNORECASE))
				return keys
			self._parsers.append(parser.optional())

		@parsy.generate
		def parse_instruction():
			comment = yield parsy.regex(R_COMMENT).desc('comment').optional()
			if comment:
				return None
			i = None
			for p in self._parsers:
				i = yield p
				if i:
					break
			comment = yield parsy.regex(R_COMMENT).desc('comment').optional()
			return i
		self.parse_instruction = parse_instruction.desc('instruction')

	def parse_file(self, filename):
		instructions = []
		labels = {}
		last_label = ''
		line_number = 0
		errors = False
		with open(filename, encoding='utf-8') as file:
			for line in file:
				line_number += 1
				line = line.strip()
				if line != '':
					line_labels, line = parse_labels.parse_partial(line)
					for label in line_labels:
						if '.' in label:
							if label.startswith('.'):
								label = last_label + label
							labels[label] = len(instructions)
							last_label = label[0:label.find('.')]
						else:
							labels[label] = len(instructions)
							last_label = label
					try:
						instruction = self.parse_instruction.parse(line)
						if instruction:
							instruction['line_number'] = line_number
							instructions.append(instruction)
					except parsy.ParseError as e:
						errors = True
						partial = self.parse_instruction.parse_partial(line)
						prefix = 'Line ' + str(line_number) + ': '
						if e.index == 0:
							print(prefix + 'unknown instruction: ' + line)
						else:
							print(prefix + 'unexpected character: ' + line + '\n' + (' ' * (22 + e.index + len(prefix))) + '^')
		return (labels, instructions, errors)

	def process_file(self, filename):
		labels, instructions, parse_errors = self.parse_file(filename)

		#TODO: Encode instructions / determine instruction sizes
		#TODO: Write output

def options(func):
	pb = ParserBuilder()
	func(pb)
	return pb.build()

@parsy.generate
def parse_labels():
	labels = yield parsy.regex(R_LABEL).desc('label').many()
	return [label.rstrip().rstrip(':') for label in labels]

def expression(output_key):
	@parsy.generate
	def result(output_key=output_key):
		ex = yield parse_expression
		return {output_key: ex}
	return result

def integer(output_key):
	@parsy.generate
	def result(output_key=output_key):
		number = yield parsy.regex(R_INTEGER)
		return {output_key: int(number)}
	return result
