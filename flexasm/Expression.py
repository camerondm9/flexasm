import ast
import re
import parsy

R_REFERENCE = re.compile(r'(?:(?:[^\d\W]\w*)?\.)?[^\d\W]\w*\s*', re.IGNORECASE)
R_SPACE = re.compile(r'\s+', re.IGNORECASE)
R_STRING = re.compile(r"('[^'\\]*(?:\\.[^'\\]*)*'|\"[^\"\\]*(?:\\.[^\"\\]*)*\")\s*", re.IGNORECASE)
R_OPERATOR_UNARY = re.compile(r'[+\-!~]\s*', re.IGNORECASE)
R_OPERATOR_BINARY = re.compile(r'(\*\*|\<{1,2}|\<=|\>{1,2}|\>=|\.\.|==|!=|\<\>|\/{1,2}|[-+*%&|^])\s*', re.IGNORECASE)
R_INTEGER = re.compile(r'(0[xh][0-9a-f]+(?:_[0-9a-f]+)*|0[oq][0-7]+(?:_[0-7]+)*|0[by][01]+(?:_[01]+)*|(?:0[dt])?[0-9]+(?:_[0-9]+)*)\s*', re.IGNORECASE)
R_PAREN_OPEN = re.compile(r'\(\s*', re.IGNORECASE)
R_PAREN_CLOSE = re.compile(r'\)\s*', re.IGNORECASE)
R_END_ALL = re.compile(r'(?:;|,|\)|\])\s*|$', re.IGNORECASE)

@parsy.generate
def parse_integer():
	num = yield parsy.regex(R_INTEGER).desc('integer').optional()
	if num:
		num = num.strip().replace('_', '').lower()
		if num.startswith('0x') or num.startswith('0h'):
			return int(num[2:], 16)
		elif num.startswith('0o') or num.startswith('0q'):
			return int(num[2:], 8)
		elif num.startswith('0b') or num.startswith('0y'):
			return int(num[2:], 2)
		elif num.startswith('0d') or num.startswith('0t'):
			return int(num[2:], 10)
		else:
			return int(num, 10)
	return None

@parsy.generate
def parse_expression():
	yield parsy.regex(R_SPACE).optional()
	result = []
	while True:
		c = yield parsy.regex(R_OPERATOR_UNARY).desc('unary operator').optional()
		if c:
			c = c.strip()
			result.append(UnaryExpression(c))
			continue
		c = yield parse_integer
		if c is not None:
			result.append(ConstantExpression(c))
		else:
			c = yield parsy.regex(R_REFERENCE).desc('reference').optional()
			if c:
				c = c.strip()
				result.append(ReferenceExpression(c))
			else:
				c = yield parsy.regex(R_STRING).desc('string').optional()
				if c:
					c = ast.literal_eval(c)
					result.append(ConstantExpression(c))
				else:
					c = yield parsy.regex(R_PAREN_OPEN).desc('expression')
					if c:
						c = yield parse_expression
						result.append(c)
						yield parsy.regex(R_PAREN_CLOSE).desc('closing )')
		c = yield parsy.regex(R_OPERATOR_BINARY).desc('binary operator').optional()
		if c:
			c = c.strip()
			bin = BinaryExpression(c)
			if c != '**':
				reduce_expression(result, bin.level())
			bin.A = result.pop()
			result.append(bin)
		else:
			c = yield parsy.peek(parsy.regex(R_END_ALL).desc('expression'))
			break
	reduce_expression(result)
	return validate_expression(result.pop())

def reduce_expression(ops, level=0):
	while len(ops) > 1:
		e = ops.pop()
		t = ops[-1]
		if t.level() >= level:
			if isinstance(t, BinaryExpression):
				t.B = e
			else:
				if isinstance(t, UnaryExpression):
					t.A = e
				else:
					raise RuntimeError('Cannot reduce expression stack!')
		else:
			ops.append(e)
			break

def validate_expression(e):
	if e is None:
		raise RuntimeError('Expected expression!')
	if isinstance(e, BinaryExpression):
		validate_expression(e.A)
		validate_expression(e.B)
	elif isinstance(e, UnaryExpression):
		validate_expression(e.A)
	return e

class BinaryExpression:
	operations = {
		'**': (55, lambda a, b: a ** b),
		'*': (43, lambda a, b: a * b),
		'/': (43, lambda a, b: a / b),
		'//': (43, lambda a, b: a // b),
		'%': (43, lambda a, b: a % b),
		'+': (42, lambda a, b: a + b),
		'-': (42, lambda a, b: a - b),
		'<<': (35, lambda a, b: a << b),
		'>>': (35, lambda a, b: a >> b),
		'==': (20, lambda a, b: a == b and 1 or 0),
		'!=': (20, lambda a, b: a != b and 1 or 0),
		'<>': (20, lambda a, b: a != b and 1 or 0),
		'&': (12, lambda a, b: a & b),
		'^': (11, lambda a, b: a ^ b),
		'|': (10, lambda a, b: a | b),
	}
	def __init__(self, text):
		self.text = text
		self.A = None
		self.B = None
	def __repr__(self):
		return '(' + repr(self.A) + str(self.text) + repr(self.B) + ')'
	def level(self):
		return BinaryExpression.operations[self.text][0]
	def execute(self, options, labels):
		a = self.A.execute(options, labels)
		b = self.B.execute(options, labels)
		return BinaryExpression.operations[self.text][1](a, b)
	def reduce(self, options, labels):
		result = self
		a = self.A.reduce(options, labels)
		b = self.B.reduce(options, labels)
		if a is not self.A or b is not self.B:
			result = BinaryExpression(self.text)
			result.A = a
			result.B = b
		if isinstance(a, ConstantExpression) and isinstance(b, ConstantExpression):
			result = ConstantExpression(result.execute(options, labels))
		return result

class UnaryExpression:
	operations = {
		'+': (50, lambda a: a),
		'-': (50, lambda a: -a),
		'!': (50, lambda a: 1 - (a and 1 or 0)),
		'~': (50, lambda a: ~a),
	}
	def __init__(self, text):
		self.text = text
		self.A = None
	def __repr__(self):
		return str(self.text) + repr(self.A)
	def level(self):
		return UnaryExpression.operations[self.text][0]
	def execute(self, options, labels):
		a = self.A.execute(options, labels)
		return UnaryExpression.operations[self.text][1](a)
	def reduce(self, options, labels):
		result = self
		a = self.A.reduce(options, labels)
		if a is not self.A:
			result = UnaryExpression(self.text)
			result.A = a
		if isinstance(a, ConstantExpression):
			result = ConstantExpression(result.execute(options, labels))
		return result

class ConstantExpression:
	def __init__(self, text):
		self.text = text
	def __repr__(self):
		return 'constant(' + repr(self.text) + ')'
	def level(self):
		return 65
	def execute(self, options, labels):
		#TODO: How to encode strings?
		return int(self.text)
	def reduce(self, options, labels):
		return self

class ReferenceExpression:
	def __init__(self, text):
		self.text = text
	def __repr__(self):
		return 'reference(' + repr(self.text) + ')'
	def level(self):
		return 65
	def execute(self, options, labels):
		return labels[self.text]
	def reduce(self, options, labels):
		return self
