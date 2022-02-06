# transpyimo

This tool translate .pyi docstring by Sphinx .mo translation data.

## Translation Flow

```
  source_code.py
       |
+------+----------------------------------------+
|      |                                        |
|      v                                        v
| [sphinx-build gettext]                   [stubdoc]
|      |                                        |
|      v                                        v
| source_code.pot                          source_code.pyi
|      |                                        |
|      v                                        |
| [sphinx-intl]                                 |
|      |                                        |
|      v                                        |
| source_code.po                                |
|      |                                        |
|      v                                        |
| <translation>                                 |
|      |                                        |
|      v                                        |
| source_code.po (translated)                   |
|      |                                        |
+----+ | +--------------------+                 |
     | | |                    |                 |
     v v v                    |                 v
  [sphinx-build html] -> source_code.mo -> [transpyimo]
       |                                        |
       v                                        v
  source_code.html (translated)            source_code.pyi (translated)
```

# Dependencies

This tool and translation flow depends on the following awesome tools and libraries:

* [astor](https://github.com/berkerpeksag/astor)
* [sphinx](https://github.com/sphinx-doc/sphinx)
* [sphinx-intl](https://github.com/sphinx-doc/sphinx-intl)
* [stubdoc](https://github.com/simon-ritchie/stubdoc)

# How to use

``` sh
# python3 transpyimo.py path/to/source_code.py mo_file_domain_name path/to/locale language -l line_width(default: 72)
# e.g.
python3 transpyimo.py src/source_code.py source_code doc/locale ja
```

or

``` python
import gettext
import transpyimo

...
translation = gettext.translation(domain, locale_dir, [language])
translated_code = translate_pyi_source(original_code, translation)
...
```

# Limitations

* This tool supports only numpy style simple docstring.
* The line breaks in a paragraph is not kept. And one paragraph is converted to one line.
