"""
syntax_highlighter.py — resaltado de sintaxis para el editor de documentos.

Soporta: Python, JavaScript/TypeScript, HTML/XML, CSS, JSON, SQL,
         C/C++/C#, Java, Shell (bash/sh), Go, Rust, PHP, Ruby.
"""

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import (
    QSyntaxHighlighter, QTextCharFormat, QColor, QFont,
)


def _fmt(color: str, bold: bool = False, italic: bool = False) -> QTextCharFormat:
    f = QTextCharFormat()
    f.setForeground(QColor(color))
    if bold:
        f.setFontWeight(QFont.Weight.Bold)
    if italic:
        f.setFontItalic(True)
    return f


# ── Common colour palette ──────────────────────────────────────────────────
_C_KEYWORD   = _fmt("#c792ea", bold=True)
_C_BUILTIN   = _fmt("#82aaff")
_C_STRING    = _fmt("#c3e88d")
_C_NUMBER    = _fmt("#f78c6c")
_C_COMMENT   = _fmt("#546e7a", italic=True)
_C_OPERATOR  = _fmt("#89ddff")
_C_DECORATOR = _fmt("#ffcb6b")
_C_CLASS     = _fmt("#ffcb6b", bold=True)
_C_FUNCTION  = _fmt("#82aaff", bold=True)
_C_TAG       = _fmt("#f07178", bold=True)
_C_ATTR      = _fmt("#ffcb6b")
_C_PROPERTY  = _fmt("#89ddff")
_C_AT_RULE   = _fmt("#c792ea", bold=True)
_C_SELECTOR  = _fmt("#c792ea")
_C_SYMBOL    = _fmt("#89ddff")


class _Rule:
    """Pairs a compiled QRegularExpression with a QTextCharFormat."""

    def __init__(self, pattern: str, fmt: QTextCharFormat, flags=None):
        if flags is None:
            expr = QRegularExpression(pattern)
        else:
            expr = QRegularExpression(pattern, flags)
        expr.optimize()
        self.expr = expr
        self.fmt = fmt


# ── Python ─────────────────────────────────────────────────────────────────
_PY_KEYWORDS = (
    "False None True and as assert async await break class continue def del "
    "elif else except finally for from global if import in is lambda nonlocal "
    "not or pass raise return try while with yield"
).split()

_PY_BUILTINS = (
    "abs all any ascii bin bool breakpoint bytearray bytes callable chr "
    "classmethod compile complex delattr dict dir divmod enumerate eval exec "
    "filter float format frozenset getattr globals hasattr hash help hex id "
    "input int isinstance issubclass iter len list locals map max memoryview "
    "min next object oct open ord pow print property range repr reversed round "
    "set setattr slice sorted staticmethod str sum super tuple type vars zip"
).split()

_PY_RULES = [
    _Rule(r'#[^\n]*', _C_COMMENT),
    _Rule(r'"""[\s\S]*?"""', _C_STRING),
    _Rule(r"'''[\s\S]*?'''", _C_STRING),
    _Rule(r'"[^"\\]*(?:\\.[^"\\]*)*"', _C_STRING),
    _Rule(r"'[^'\\]*(?:\\.[^'\\]*)*'", _C_STRING),
    _Rule(r'@\w+', _C_DECORATOR),
    _Rule(r'\bdef\s+(\w+)', _C_FUNCTION),
    _Rule(r'\bclass\s+(\w+)', _C_CLASS),
    _Rule(r'\b(' + '|'.join(_PY_KEYWORDS) + r')\b', _C_KEYWORD),
    _Rule(r'\b(' + '|'.join(_PY_BUILTINS) + r')\b', _C_BUILTIN),
    _Rule(r'\b\d+\.?\d*([eE][+-]?\d+)?\b', _C_NUMBER),
    _Rule(r'[=+\-*/<>!&|^~%]+', _C_OPERATOR),
]

# ── JavaScript / TypeScript ────────────────────────────────────────────────
_JS_KEYWORDS = (
    "break case catch class const continue debugger default delete do else "
    "export extends finally for from function if import in instanceof let new "
    "of return static super switch this throw try typeof var void while with "
    "yield async await"
).split()

_JS_RULES = [
    _Rule(r'//[^\n]*', _C_COMMENT),
    _Rule(r'/\*[\s\S]*?\*/', _C_COMMENT),
    _Rule(r'`[\s\S]*?`', _C_STRING),
    _Rule(r'"[^"\\]*(?:\\.[^"\\]*)*"', _C_STRING),
    _Rule(r"'[^'\\]*(?:\\.[^'\\]*)*'", _C_STRING),
    _Rule(r'\b(' + '|'.join(_JS_KEYWORDS) + r')\b', _C_KEYWORD),
    _Rule(r'\b(true|false|null|undefined|NaN|Infinity)\b', _C_BUILTIN),
    _Rule(r'\b\d+\.?\d*([eE][+-]?\d+)?\b', _C_NUMBER),
    _Rule(r'[=+\-*/<>!&|^~%]+', _C_OPERATOR),
    _Rule(r'\bfunction\s+(\w+)', _C_FUNCTION),
    _Rule(r'\bclass\s+(\w+)', _C_CLASS),
]

# ── HTML / XML ────────────────────────────────────────────────────────────
_HTML_RULES = [
    _Rule(r'<!--[\s\S]*?-->', _C_COMMENT),
    _Rule(r'<[/!]?\w[\w.-]*', _C_TAG),
    _Rule(r'>', _C_TAG),
    _Rule(r'\w[\w-]*\s*=', _C_ATTR),
    _Rule(r'"[^"]*"', _C_STRING),
    _Rule(r"'[^']*'", _C_STRING),
    _Rule(r'&\w+;', _C_OPERATOR),
]

# ── CSS ────────────────────────────────────────────────────────────────────
_CSS_RULES = [
    _Rule(r'/\*[\s\S]*?\*/', _C_COMMENT),
    _Rule(r'@[\w-]+', _C_AT_RULE),
    _Rule(r'#[\w-]+|\.[\w-]+|:[\w-]+(\([^)]*\))?', _C_SELECTOR),
    _Rule(r'[\w-]+\s*:', _C_PROPERTY),
    _Rule(r'"[^"]*"', _C_STRING),
    _Rule(r"'[^']*'", _C_STRING),
    _Rule(r'\b\d+\.?\d*(px|em|rem|%|vh|vw|pt|cm|mm|s|ms)?\b', _C_NUMBER),
    _Rule(r'#[0-9a-fA-F]{3,8}\b', _C_NUMBER),
    _Rule(r'[{};:,]', _C_OPERATOR),
]

# ── JSON ──────────────────────────────────────────────────────────────────
_JSON_RULES = [
    _Rule(r'"[^"\\]*(?:\\.[^"\\]*)*"\s*:', _fmt("#89ddff")),  # key
    _Rule(r'"[^"\\]*(?:\\.[^"\\]*)*"', _C_STRING),             # value string
    _Rule(r'\b(true|false|null)\b', _C_KEYWORD),
    _Rule(r'-?\b\d+\.?\d*([eE][+-]?\d+)?\b', _C_NUMBER),
    _Rule(r'[{}\[\]:,]', _C_OPERATOR),
]

# ── SQL ──────────────────────────────────────────────────────────────────
_SQL_KEYWORDS = (
    "SELECT FROM WHERE AND OR NOT IN LIKE BETWEEN IS NULL AS JOIN LEFT RIGHT "
    "INNER OUTER FULL CROSS ON GROUP BY ORDER HAVING LIMIT OFFSET INSERT INTO "
    "VALUES UPDATE SET DELETE CREATE TABLE ALTER DROP INDEX VIEW UNIQUE "
    "PRIMARY KEY FOREIGN REFERENCES CONSTRAINT DEFAULT CHECK DISTINCT COUNT "
    "SUM AVG MIN MAX CASE WHEN THEN ELSE END WITH UNION EXCEPT INTERSECT "
    "BEGIN COMMIT ROLLBACK TRANSACTION GRANT REVOKE"
).split()

_SQL_RULES = [
    _Rule(r'--[^\n]*', _C_COMMENT),
    _Rule(r'/\*[\s\S]*?\*/', _C_COMMENT),
    _Rule(r"'[^']*'", _C_STRING),
    _Rule(r'\b(' + '|'.join(_SQL_KEYWORDS) + r')\b',
          _C_KEYWORD, QRegularExpression.CaseInsensitiveOption),
    _Rule(r'\b\d+\.?\d*\b', _C_NUMBER),
    _Rule(r'[=<>!+\-*/,;()]', _C_OPERATOR),
]

# ── C / C++ / C# ─────────────────────────────────────────────────────────
_C_KEYWORDS = (
    "auto break case char const continue default do double else enum extern "
    "float for goto if int long register return short signed sizeof static "
    "struct switch typedef union unsigned void volatile while inline restrict "
    "bool true false nullptr class namespace template typename virtual "
    "override final new delete public private protected throw try catch "
    "using namespace"
).split()

_C_RULES = [
    _Rule(r'//[^\n]*', _C_COMMENT),
    _Rule(r'/\*[\s\S]*?\*/', _C_COMMENT),
    _Rule(r'#\s*\w+[^\n]*', _C_DECORATOR),   # preprocessor
    _Rule(r'"[^"\\]*(?:\\.[^"\\]*)*"', _C_STRING),
    _Rule(r"'[^'\\]*(?:\\.[^'\\]*)*'", _C_STRING),
    _Rule(r'\b(' + '|'.join(_C_KEYWORDS) + r')\b', _C_KEYWORD),
    _Rule(r'\b\d+\.?\d*([eE][+-]?\d+)?[uUlLfF]*\b', _C_NUMBER),
    _Rule(r'0x[0-9a-fA-F]+\b', _C_NUMBER),
    _Rule(r'[=+\-*/<>!&|^~%]+', _C_OPERATOR),
]

# ── Shell (bash/sh/zsh) ────────────────────────────────────────────────────
_SH_KEYWORDS = (
    "if then else elif fi for while until do done case esac in function "
    "return export local readonly declare echo printf read source . alias "
    "unset exit break continue shift trap"
).split()

_SH_RULES = [
    _Rule(r'#[^\n]*', _C_COMMENT),
    _Rule(r'"[^"\\]*(?:\\.[^"\\]*)*"', _C_STRING),
    _Rule(r"'[^']*'", _C_STRING),
    _Rule(r'\$\{[^}]*\}|\$\w+|\$[#@*?$!0-9]', _C_DECORATOR),  # variables
    _Rule(r'\b(' + '|'.join(_SH_KEYWORDS) + r')\b', _C_KEYWORD),
    _Rule(r'\b\d+\b', _C_NUMBER),
    _Rule(r'[=+\-*/<>!&|;]+', _C_OPERATOR),
]

# ── Go ────────────────────────────────────────────────────────────────────
_GO_KEYWORDS = (
    "break case chan const continue default defer else fallthrough for func "
    "go goto if import interface map package range return select struct switch "
    "type var"
).split()

_GO_RULES = [
    _Rule(r'//[^\n]*', _C_COMMENT),
    _Rule(r'/\*[\s\S]*?\*/', _C_COMMENT),
    _Rule(r'`[\s\S]*?`', _C_STRING),
    _Rule(r'"[^"\\]*(?:\\.[^"\\]*)*"', _C_STRING),
    _Rule(r"'[^'\\]*(?:\\.[^'\\]*)*'", _C_STRING),
    _Rule(r'\b(' + '|'.join(_GO_KEYWORDS) + r')\b', _C_KEYWORD),
    _Rule(r'\b(true|false|nil|iota)\b', _C_BUILTIN),
    _Rule(r'\b\d+\.?\d*([eE][+-]?\d+)?\b', _C_NUMBER),
    _Rule(r'[=+\-*/<>!&|^~%:]+', _C_OPERATOR),
]

# ── Rust ──────────────────────────────────────────────────────────────────
_RS_KEYWORDS = (
    "as async await break const continue crate dyn else enum extern false fn "
    "for if impl in let loop match mod move mut pub ref return self Self "
    "static struct super trait true type union unsafe use where while"
).split()

_RS_RULES = [
    _Rule(r'//[^\n]*', _C_COMMENT),
    _Rule(r'/\*[\s\S]*?\*/', _C_COMMENT),
    _Rule(r'"[^"\\]*(?:\\.[^"\\]*)*"', _C_STRING),
    _Rule(r"'[^'\\]+'", _C_STRING),
    _Rule(r'#\[[\s\S]*?\]', _C_DECORATOR),   # attributes
    _Rule(r'\b(' + '|'.join(_RS_KEYWORDS) + r')\b', _C_KEYWORD),
    _Rule(r'\b\d+\.?\d*([eE][+-]?\d+)?(_[a-z0-9]+)?\b', _C_NUMBER),
    _Rule(r'[=+\-*/<>!&|^~%:]+', _C_OPERATOR),
]

# ── PHP ───────────────────────────────────────────────────────────────────
_PHP_KEYWORDS = (
    "abstract and array as break callable case catch class clone const "
    "continue declare default do echo else elseif empty enddeclare endfor "
    "endforeach endif endswitch endwhile eval exit extends final finally fn "
    "for foreach function global goto if implements include include_once "
    "instanceof insteadof interface isset list match namespace new null print "
    "private protected public require require_once return static switch throw "
    "trait try unset use var while yield"
).split()

_PHP_RULES = [
    _Rule(r'//[^\n]*|#[^\n]*', _C_COMMENT),
    _Rule(r'/\*[\s\S]*?\*/', _C_COMMENT),
    _Rule(r'"[^"\\]*(?:\\.[^"\\]*)*"', _C_STRING),
    _Rule(r"'[^'\\]*(?:\\.[^'\\]*)*'", _C_STRING),
    _Rule(r'\$\w+', _C_DECORATOR),
    _Rule(r'\b(' + '|'.join(_PHP_KEYWORDS) + r')\b', _C_KEYWORD),
    _Rule(r'\b(true|false|null|TRUE|FALSE|NULL)\b', _C_BUILTIN),
    _Rule(r'\b\d+\.?\d*([eE][+-]?\d+)?\b', _C_NUMBER),
    _Rule(r'[=+\-*/<>!&|^~%]+', _C_OPERATOR),
]

# ── Ruby ──────────────────────────────────────────────────────────────────
_RB_KEYWORDS = (
    "BEGIN END alias and begin break case class def defined? do else elsif end "
    "ensure false for if in module next nil not or redo rescue retry return "
    "self super then true undef unless until when while yield __FILE__ "
    "__LINE__ __ENCODING__"
).split()

_RB_RULES = [
    _Rule(r'#[^\n]*', _C_COMMENT),
    _Rule(r'=begin[\s\S]*?=end', _C_COMMENT),
    _Rule(r'"[^"\\]*(?:\\.[^"\\]*)*"', _C_STRING),
    _Rule(r"'[^'\\]*(?:\\.[^'\\]*)*'", _C_STRING),
    _Rule(r':[a-zA-Z_]\w*', _C_SYMBOL),   # symbols
    _Rule(r'\b(' + '|'.join(_RB_KEYWORDS) + r')\b', _C_KEYWORD),
    _Rule(r'\b\d+\.?\d*([eE][+-]?\d+)?\b', _C_NUMBER),
    _Rule(r'[=+\-*/<>!&|^~%]+', _C_OPERATOR),
]

# ── Java ──────────────────────────────────────────────────────────────────
_JAVA_KEYWORDS = (
    "abstract assert boolean break byte case catch char class const continue "
    "default do double else enum extends final finally float for goto if "
    "implements import instanceof int interface long native new null package "
    "private protected public return short static strictfp super switch "
    "synchronized this throw throws transient try var void volatile while "
    "true false"
).split()

_JAVA_RULES = [
    _Rule(r'//[^\n]*', _C_COMMENT),
    _Rule(r'/\*[\s\S]*?\*/', _C_COMMENT),
    _Rule(r'"[^"\\]*(?:\\.[^"\\]*)*"', _C_STRING),
    _Rule(r"'[^'\\]*(?:\\.[^'\\]*)*'", _C_STRING),
    _Rule(r'@\w+', _C_DECORATOR),
    _Rule(r'\b(' + '|'.join(_JAVA_KEYWORDS) + r')\b', _C_KEYWORD),
    _Rule(r'\b\d+\.?\d*([eE][+-]?\d+)?[lLfFdD]?\b', _C_NUMBER),
    _Rule(r'0x[0-9a-fA-F]+[lL]?\b', _C_NUMBER),
    _Rule(r'[=+\-*/<>!&|^~%]+', _C_OPERATOR),
]

# ── Markdown ──────────────────────────────────────────────────────────────
_MD_RULES = [
    _Rule(r'^#{1,6}\s.*$', _fmt("#c792ea", bold=True),
          QRegularExpression.MultilineOption),
    _Rule(r'\*\*[^*]+\*\*|__[^_]+__', _fmt("#ffcb6b", bold=True)),
    _Rule(r'\*[^*]+\*|_[^_]+_', _fmt("#c3e88d", italic=True)),
    _Rule(r'`[^`]+`', _fmt("#f07178")),
    _Rule(r'```[\s\S]*?```', _fmt("#f07178")),
    _Rule(r'^\s*[-*+]\s', _fmt("#82aaff"),
          QRegularExpression.MultilineOption),
    _Rule(r'^\s*\d+\.\s', _fmt("#82aaff"),
          QRegularExpression.MultilineOption),
    _Rule(r'\[([^\]]+)\]\([^)]+\)', _fmt("#89ddff")),
    _Rule(r'^>\s.*$', _C_COMMENT, QRegularExpression.MultilineOption),
    _Rule(r'---+|===+', _fmt("#546e7a")),
]

# ── INI / CONF ────────────────────────────────────────────────────────────
_INI_RULES = [
    _Rule(r';[^\n]*|#[^\n]*', _C_COMMENT),
    _Rule(r'^\[.*\]$', _fmt("#c792ea", bold=True),
          QRegularExpression.MultilineOption),
    _Rule(r'^[\w.-]+\s*[=:]', _fmt("#89ddff"),
          QRegularExpression.MultilineOption),
    _Rule(r'"[^"]*"', _C_STRING),
    _Rule(r"'[^']*'", _C_STRING),
    _Rule(r'\b(true|false|yes|no|on|off)\b',
          _C_KEYWORD, QRegularExpression.CaseInsensitiveOption),
    _Rule(r'\b\d+\.?\d*\b', _C_NUMBER),
]

# ── TOML ──────────────────────────────────────────────────────────────────
_TOML_RULES = [
    _Rule(r'#[^\n]*', _C_COMMENT),
    _Rule(r'^\[[\w."-]+\]$', _fmt("#c792ea", bold=True),
          QRegularExpression.MultilineOption),
    _Rule(r'^\[\[[\w."-]+\]\]$', _fmt("#c792ea", bold=True),
          QRegularExpression.MultilineOption),
    _Rule(r'"""[\s\S]*?"""', _C_STRING),
    _Rule(r"'''[\s\S]*?'''", _C_STRING),
    _Rule(r'"[^"\\]*(?:\\.[^"\\]*)*"', _C_STRING),
    _Rule(r"'[^']*'", _C_STRING),
    _Rule(r'\b(true|false)\b', _C_KEYWORD),
    _Rule(r'\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2})?', _C_NUMBER),
    _Rule(r'\b\d+\.?\d*([eE][+-]?\d+)?\b', _C_NUMBER),
    _Rule(r'[\w-]+\s*=', _fmt("#89ddff")),
]

# ── YAML ──────────────────────────────────────────────────────────────────
_YAML_RULES = [
    _Rule(r'#[^\n]*', _C_COMMENT),
    _Rule(r'^---$|^\.\.\.$', _fmt("#c792ea", bold=True),
          QRegularExpression.MultilineOption),
    _Rule(r'"[^"\\]*(?:\\.[^"\\]*)*"', _C_STRING),
    _Rule(r"'[^']*'", _C_STRING),
    _Rule(r'^\s*[\w-]+\s*:', _fmt("#89ddff"),
          QRegularExpression.MultilineOption),
    _Rule(r'\b(true|false|null|yes|no|on|off|True|False|None)\b', _C_KEYWORD),
    _Rule(r'\b\d+\.?\d*([eE][+-]?\d+)?\b', _C_NUMBER),
    _Rule(r'!!\w+', _C_DECORATOR),
    _Rule(r'&\w+|\*\w+', _C_SYMBOL),
]

# ── Mapping: file extension → rule list ──────────────────────────────────
_EXT_RULES: dict[str, list[_Rule]] = {
    ".py": _PY_RULES,
    ".pyw": _PY_RULES,
    ".js": _JS_RULES,
    ".jsx": _JS_RULES,
    ".ts": _JS_RULES,
    ".tsx": _JS_RULES,
    ".mjs": _JS_RULES,
    ".html": _HTML_RULES,
    ".htm": _HTML_RULES,
    ".xhtml": _HTML_RULES,
    ".xml": _HTML_RULES,
    ".svg": _HTML_RULES,
    ".css": _CSS_RULES,
    ".scss": _CSS_RULES,
    ".sass": _CSS_RULES,
    ".less": _CSS_RULES,
    ".json": _JSON_RULES,
    ".jsonc": _JSON_RULES,
    ".sql": _SQL_RULES,
    ".psql": _SQL_RULES,
    ".c": _C_RULES,
    ".h": _C_RULES,
    ".cpp": _C_RULES,
    ".hpp": _C_RULES,
    ".cc": _C_RULES,
    ".cxx": _C_RULES,
    ".cs": _C_RULES,
    ".sh": _SH_RULES,
    ".bash": _SH_RULES,
    ".zsh": _SH_RULES,
    ".fish": _SH_RULES,
    ".cmd": _SH_RULES,
    ".bat": _SH_RULES,
    ".go": _GO_RULES,
    ".rs": _RS_RULES,
    ".php": _PHP_RULES,
    ".rb": _RB_RULES,
    ".java": _JAVA_RULES,
    ".kt": _JAVA_RULES,
    ".kts": _JAVA_RULES,
    ".scala": _JAVA_RULES,
    ".md": _MD_RULES,
    ".markdown": _MD_RULES,
    ".rst": _MD_RULES,
    ".ini": _INI_RULES,
    ".cfg": _INI_RULES,
    ".conf": _INI_RULES,
    ".config": _INI_RULES,
    ".properties": _INI_RULES,
    ".env": _INI_RULES,
    ".toml": _TOML_RULES,
    ".lock": _TOML_RULES,
    ".yaml": _YAML_RULES,
    ".yml": _YAML_RULES,
}


class CodeSyntaxHighlighter(QSyntaxHighlighter):
    """Generic rule-based syntax highlighter."""

    def __init__(self, document, rules: list[_Rule]):
        super().__init__(document)
        self._rules = rules

    def highlightBlock(self, text: str) -> None:
        for rule in self._rules:
            it = rule.expr.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), rule.fmt)


def get_highlighter_for_ext(ext: str, document) -> "CodeSyntaxHighlighter | None":
    """Return a CodeSyntaxHighlighter for the given extension, or None."""
    rules = _EXT_RULES.get(ext.lower())
    if rules is None:
        return None
    return CodeSyntaxHighlighter(document, rules)
