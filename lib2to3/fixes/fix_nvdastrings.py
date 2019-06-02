r"""Fixer for unicode.

* Changes unicode to str and unichr to chr.

* If "...\u..." is not unicode literal change it into "...\\u...".

* Change u"..." into "...".

"""

from ..pgen2 import token
from .. import fixer_base
from ..patcomp import PatternCompiler

printHelp = False

STR_MARKER = "p3_Str"
RAW_MARKER = "p3_Raw"


def _encase_raw(str):
	marker = RAW_MARKER
	return f"{marker}_ {str} _{marker}"


def _encase_str(str):
	marker = STR_MARKER
	return f"{marker}_ {str} _{marker}"


excludedStrings = [
# used in com interfaces
		"out",
		"in",
		"propget",
		"retVal",
		"retval",
		"gainFocus",
		"IAccessible::role",
		"next",
		" ",
		"element",
		"cacheRequest",
		"exception: %s",
		"kb:upArrow",
		"kb:downArrow",
		"kb:leftArrow",
		"kb:rightArrow",
		"kb:enter",
	]

def _excluded(val):
	stripped = val.strip(r"\"'")
	return stripped in excludedStrings

class FixNvdastrings(fixer_base.BaseFix):
	BM_compatible = True
	explicit = True # dont run with -f all
	PATTERN = "STRING"

	DONT_MATCH = """
	power< 
		[ '_' 
		| 'ValueError' 
		| 'LookupError' 
		| 'getattr' 
		| any trailer<
				'.' 
				[ 'setEndPoint' 
				| 'compareEndPoints'
				| 'move'
				]
			>
		]
		trailer<
			lpar='('
			any*
			rpar=')'
		>
		after=any*
	>
	| power< [any trailer< '.' 'conf'> | 'conf'] 
		trailer<
			lpar='['
			any
			rpar=']'
		>
		after=any*
	> |
	power< any trailer< '.' 'get'>
		trailer<
			lpar='('
			any
			rpar=')'
		>
		after=any*
	> |
	power< 'pgettext'
		trailer<
			lpar='('
			any+
			rpar=')'
		>
		after=any*
	> | 
	power< 're' trailer< '.' 'compile'>
		trailer<
			lpar='('
			any
			rpar=')'
		>
		after=any*
	> | 
	power< 'log' trailer< '.' any>
		trailer<
			lpar='('
			any
			rpar=')'
		>
		after=any*
	> |
	power< [
		'os' trailer<'.' 'path'> 
		| 'path' 
		| "''" 
		| '""' 
		| "' '" 
		| '" "'
		] 
		trailer< '.' 'join'>
		trailer<
			lpar='('
			any*
			rpar=')'
		>
	> 
	"""


	def compile_pattern(self):
		super(FixNvdastrings, self).compile_pattern()
		PC = PatternCompiler()
		self.dont_match = PC.compile_pattern(self.DONT_MATCH, with_tree=False)

	def match(self, node):
		if printHelp: print(f"match node: {repr(node)}")
		#return not self.dont_match.match(node) and super(FixNvdastrings, self).match(node)
		return super(FixNvdastrings, self).match(node)

	def transform(self, node, results):

		if printHelp: print(f"node: {repr(node)}")
		if printHelp: print(f"results: {results}")

		pNode = node.parent
		while pNode:
			if printHelp: print(f"parent: {repr(pNode)}")
			if self.dont_match.match(pNode):
				return node
			pNode = pNode.parent

		if node.type == token.STRING:
			val = node.value
			couldBeDocString = len(val) >= 3 and (val[:3] in ['"""', "'''"])
			noPrefix = val[0] not in 'rRuUbB'
			isEmptyString = len(val) == 2
			if val[0] in 'rR':
				val = _encase_raw(val)
			elif noPrefix and not (couldBeDocString or isEmptyString or _excluded(val)):
				val = _encase_str(val)
			else:
				return node
			new = node.clone()
			new.value = val
			return new
