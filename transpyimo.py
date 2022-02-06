import argparse
import ast
import gettext
import re
from pathlib import Path
from typing import List, Tuple

import astor

SECTION_DECORATOR = '=-`:.\'\"~^_*+#'
LIST_DECORATORS = ['-', '*', '#.', '|']
ORDERED_LIST_PATTERN = re.compile(r'^\d+\.')
LIST_TABLE_DECORATORS = ['.. list-table::', '* -']

SCRIPT_DIR = Path(__file__).absolute().parent


class TranslationBuffer():
    def __init__(self, translator: gettext.NullTranslations):
        self.translator = translator
        self.indent = ''
        self.lines = []
        self.original_lines = []

    def _reset(self):
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
        translated = self.indent + self.translator.gettext(original_text)
        self._reset()
        return [translated]

    def put(self, indent: str, text: str, original: str):
        if not self.lines:
            self.indent = indent
        self.lines.append(text)
        self.original_lines.append(original)


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


def _try_split_list_table_header(text: str) -> Tuple[bool, str, str]:
    for decorator in LIST_TABLE_DECORATORS:
        if text.startswith(decorator + ' '):
            header, text = _split_header(text, decorator)
            return True, header, text
    return False, '', text


def translate_docstring(original: str, translator: gettext.NullTranslations) -> str:
    buffer = TranslationBuffer(translator)
    translated = []

    original_lines = original.splitlines()
    base_indent = original_lines[-1]

    for line_no, line in enumerate(original_lines):
        text = line.strip()

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

        indent = line[:line.find(text)]

        # list
        text_is_list, header, body = _try_split_list_header(text)
        if text_is_list:
            translated.extend(buffer.flush_translated())
            buffer.put(indent + header, body, line)
            continue

        # list table
        text_is_list_table, header, body = _try_split_list_table_header(text)
        if text_is_list_table:
            translated.extend(buffer.flush_translated())
            buffer.put(indent + header, body, line)
            continue

        # indent
        if len(indent) > (len(base_indent) if line_no == 1 else len(buffer.indent)):
            translated.extend(buffer.flush_translated())
            buffer.put(indent, text, line)
            continue

        # unindent
        if len(indent) < len(buffer.indent):
            translated.extend(buffer.flush_translated())
            buffer.put(indent, text, line)
            continue

        # paragraph
        buffer.put(indent, text, line)

    translated.extend(buffer.flush_translated())

    return '\n'.join(translated)


class DocStringTranslator(ast.NodeTransformer):

    def __init__(self, translator: gettext.NullTranslations):
        self.translator = translator

    def visit_Str(self, node):
        node.s = translate_docstring(node.s, self.translator)
        return node


def translate_pyi(source_code: str, translator: gettext.NullTranslations) -> str:

    node = ast.parse(source_code)
    DocStringTranslator(translator).visit(node)
    return astor.to_source(node)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='.pyi file translater with Sphinx .mo file')
    parser.add_argument(
        'pyi', type=str, help='.pyi file path for translation')
    parser.add_argument(
        'domain', type=str, help='translation domain')
    parser.add_argument(
        'locale_dir', type=str, help='locale path output by sphinx-intl')
    parser.add_argument(
        'language', type=str, help='language which translation into')
    parser.add_argument(
        '--output', '-o', type=str, default=None, help='output .pyi file path or output to stdout')
    return parser.parse_args()


if __name__ == '__main__':

    args = parse_args()
    with open(args.pyi, encoding='utf-8') as f:
        original_code = f.read()

    translator = gettext.translation(
        args.domain, args.locale_dir, [args.language])
    translated_code = translate_pyi(original_code, translator)

    if args.output is None:
        print(translated_code)
    else:
        with open(args.output, mode='w', encoding='utf-8') as f:
            f.write(original_code)

