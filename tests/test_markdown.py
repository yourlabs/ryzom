from ryzom.components import Markdown


def test_markdown():
    assert Markdown('''
    ```
    foo
    ```
    ''').to_html() == '<p><code>foo</code></p>'


def test_kwargs():
    assert Markdown('''
    ```html
    foo
    ```
    ''', extensions=['fenced_code']).to_html() == '''
<pre><code class="language-html">foo
</code></pre>
    '''.strip()
