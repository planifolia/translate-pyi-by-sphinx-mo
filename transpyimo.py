import argparse
import ast
import gettext
import re
from pathlib import Path
from typing import List, Tuple

import astor
from babel import Locale
from babel.messages import pofile
from babel.messages import mofile
from sphinx.writers.text import my_wrap as sphinx_wrap


SECTION_DECORATOR = '=-`:.\'\"~^_*+#'
LIST_DECORATORS = ['-', '*', '#.', '|']
ORDERED_LIST_PATTERN = re.compile(r'^\d+\.')


class TranslationBuffer():
    def __init__(self, translation: gettext.NullTranslations, line_width: int, base_indent: str):
        self.translation = translation
        self.line_width = line_width
        self.base_indent = base_indent
        self.start_at = -1
        self.indent = ''
        self.lines = []
        self.original_lines = []

    def _reset(self):
        self.start_at = -1
        self.indent = ''
        self.lines = []
        self.original_lines = []

    def flush_original(self) -> List[str]:
        original_lines = self.original_lines
        self._reset()
        return original_lines

    def flush_translated(self) -> List[str]:
        if not self.lines:
            return []
        original_text = ' '.join(self.lines)
        translated = self.translation.gettext(original_text)
        if self.line_width <= 0:
            translated_lines = [self.indent + translated]
        else:
            indent_size = max(len(self.indent), len(self.base_indent))
            if self.start_at == 0:
                first_size = max(
                    len(self.indent),
                    len(self.base_indent) + len('"""')
                )
            else:
                first_size = indent_size
            translated_lines = sphinx_wrap(
                translated, self.line_width - first_size)
            translated_lines[0] = self.indent + translated_lines[0]
            for i in range(1, len(translated_lines)):
                translated_lines[i] = (' ' * indent_size) + translated_lines[i]
        self._reset()
        return translated_lines

    def put(self, line_no: int, indent: str, text: str, original: str):
        if not self.lines:
            self.start_at = line_no
            self.indent = indent
        self.lines.append(text)
        self.original_lines.append(original)


def _split_indent(line: str) -> Tuple[str, str]:
    text = line.strip()
    if not text:
        return line, ''
    indent = line[:line.find(text)]
    return indent, text


def _is_section_decoration(text: str) -> bool:
    c = text[0]
    if not c in SECTION_DECORATOR:
        return False
    for other in text[1:]:
        if other != c:
            return False
    return True


def _split_header(text: str, header) -> Tuple[str, str]:
    body = text[len(header):].strip()
    header = text[:text.find(body)]
    return header, body


def _try_split_list_header(text: str) -> Tuple[bool, str, str]:
    for decorator in LIST_DECORATORS:
        if text.startswith(decorator + ' '):
            header, text = _split_header(text, decorator)
            return True, header, text
    ordered_list_match = ORDERED_LIST_PATTERN.match(text)
    if ordered_list_match:
        header, text = _split_header(text, ordered_list_match[0])
        return True, header, text
    return False, '', text


def translate_docstring(original: str, translation: gettext.NullTranslations, line_width: int) -> str:

    original_lines = original.splitlines()
    base_indent, _ = _split_indent(original_lines[-1])
    buffer = TranslationBuffer(translation, line_width, base_indent)
    translated = []

    for line_no, line in enumerate(original_lines):
        indent, text = _split_indent(line)

        # blank line
        if not line.strip():
            translated.extend(buffer.flush_translated())
            translated.append(line)
            continue

        # section
        if _is_section_decoration(text):
            translated.extend(buffer.flush_original())
            translated.append(line)
            continue

        # list
        text_is_list, header, body = _try_split_list_header(text)
        if text_is_list:
            translated.extend(buffer.flush_translated())
            buffer.put(line_no, indent + header, body, line)
            continue

        # indent
        if len(indent) > (len(base_indent) if line_no == 1 else len(buffer.indent)):
            translated.extend(buffer.flush_translated())
            buffer.put(line_no, indent, text, line)
            continue

        # unindent
        if len(indent) < len(buffer.indent):
            translated.extend(buffer.flush_translated())
            buffer.put(line_no, indent, text, line)
            continue

        # paragraph
        buffer.put(line_no, indent, text, line)

    translated.extend(buffer.flush_translated())

    return '\n'.join(translated)


class DocStringTranslator(ast.NodeTransformer):

    def __init__(self, translation: gettext.NullTranslations, line_width: int):
        self.translation = translation
        self.line_width = line_width

    def visit_Str(self, node: ast.Module):
        node.s = translate_docstring(node.s, self.translation, self.line_width)
        return node


def compile_mo(domain: str, locale_dir: str, language: str):
    locale = Locale(language)
    file_path_base = Path(locale_dir) / language / 'LC_MESSAGES' / domain
    with open(file_path_base.with_suffix('.po'), mode='r', encoding='utf-8') as po_file:
        catalog = pofile.read_po(po_file, locale)
    with open(file_path_base.with_suffix('.mo'), mode='wb') as mo_file:
        mofile.write_mo(mo_file, catalog)


def translate_pyi_source(source_code: str, translation: gettext.NullTranslations, line_width: int = 72) -> str:

    node = ast.parse(source_code)
    DocStringTranslator(translation, line_width).visit(node)
    return astor.to_source(node)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='.pyi file translater with Sphinx .mo file')
    parser.add_argument(
        'pyi', type=str, help='.pyi file path for translation')
    parser.add_argument(
        'domain', type=str, help='Translation domain')
    parser.add_argument(
        'locale_dir', type=str, help='Locale path output by sphinx-intl')
    parser.add_argument(
        'language', type=str, help='Language which translation into')
    parser.add_argument(
        '--output', '-o', type=str, default=None,
        help='Output .pyi file path or output to stdout')
    parser.add_argument(
        '--line-width', '-l', type=int, default=72,
        help='Line width limitation of source code. if 0 is specified, line width is not limited. default is 72')
    parser.add_argument(
        '--compile-mo', '-c',  default=False, action='store_true',
        help='Compile .po file to .mo file before translation')
    return parser.parse_args()


if __name__ == '__main__':

    args = _parse_args()

    if args.compile_mo:
        compile_mo(args.domain, args.locale_dir, args.language)

    with open(args.pyi, mode='r', encoding='utf-8') as f:
        original_code = f.read()

    translation = gettext.translation(
        args.domain, args.locale_dir, [args.language])
    translated_code = translate_pyi_source(
        original_code, translation, args.line_width)

    if args.output is None:
        print(translated_code)
    else:
        with open(args.output, mode='w', encoding='utf-8') as f:
            f.write(translated_code)
