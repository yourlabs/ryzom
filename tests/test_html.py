from ryzom.components import CAttrs


def test_doublequote_escape():
    assert CAttrs(a='"b"').to_html() == 'a="&quot;b&quot;"'
