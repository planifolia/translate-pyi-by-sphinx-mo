# transpyimo

transpyimo translate .pyi docstring by Sphinx .mo translation data.

## Flow

```
  source_code.py
       |
+------+----------------------------------------+
|      |                                        |
|      v                                        v
| [sphinx-build gettext]                   [pygenstub]
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
