import re
from docutils.parsers.rst import Directive, directives
from docutils import nodes
from sphinx import addnodes


class HighlightedText(nodes.General, nodes.TextElement):
    def __init__(self, *args, **kwargs):
        nodes.TextElement.__init__(self, *args, **kwargs)


def visit_highlighted_text_node(self, node):
    text_node = node.children[0]
    language = node['language']

    if language == 'none':
        self.body.append(text_node)
    else:
        options = {}
        options['stripnl'] = False
        options['ensurenl'] = False

        text = text_node

        # pygments always ensures a newline at the end and there is no way to tell
        # if the newline is originating from source or was it inserted by pygments
        # as a workaround, duplicate trailing newline and then strip it

        if text.endswith('\n'):
            text = text + '\n'

        highlighted = self.highlighter.highlight_block(text, language, options)

        match = re.search('<pre>(.*)\n</pre>', highlighted, re.DOTALL)
        if not match:
            self.body.append(text_node)
        else:
            self.body.append(match.group(1))

    raise nodes.SkipNode


class RefCodeBlock(Directive):
    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = False

    option_spec = {
        'linenos': directives.flag,
        'dedent': int,
        'lineno-start': int,
        'emphasize-lines': directives.unchanged_required,
        'caption': directives.unchanged_required,
        'class': directives.class_option,
        'name': directives.unchanged,
    }

    def __init__(self, *args, **kwargs):
        Directive.__init__(self, *args, **kwargs)
        self.re_prog = re.compile(':ref:`(.+?)\s*<([^<>]*)>`')

    def run(self):
        code = u'\n'.join(self.content)
        pos = 0
        node = nodes.literal_block('.', '') # we need non-empty raw_text
        node['classes'] += ['highlight']    # we are stripping pyments-generated <div>
        node['classes'] += self.options.get('class', [])

        while True:
            match = self.re_prog.search(code, pos)
            if match is None:
                plain_text = code[pos:]
                if plain_text != "":
                    node += HighlightedText(plain_text, plain_text, language=self.arguments[0])
                break

            plain_text = code[pos:match.start()]
            if plain_text != "":
                node += HighlightedText(plain_text, plain_text, language=self.arguments[0])

            node += create_xref_node(match.group(0), match.group(1), match.group(2))
            pos = match.end()

        self.add_name(node)

        return [node]


def create_xref_node(raw_text, text, target):
    node = addnodes.pending_xref(raw_text)
    node['reftype'] = 'ref'
    node['refdomain'] = 'std'
    node['reftarget'] = target
    node['refwarn'] = True
    node['refexplicit'] = True

    node += nodes.Text(text, text)

    return node


def setup(app):
    app.add_node(
        HighlightedText,
        html=(visit_highlighted_text_node, None),
        latex=(visit_highlighted_text_node, None)
        )

    directives.register_directive('ref-code-block', RefCodeBlock)
