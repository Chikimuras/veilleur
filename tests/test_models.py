from veilleur.models import Item, Connection


def test_item_defaults():
    it = Item(title="T", url="https://x", source="HN")
    assert it.hot is False
    assert it.score is None
    assert it.tags == []
    assert it.connections == []
    assert it.enrich_failed is False


def test_connection_holds_title_and_reason():
    c = Connection(note_title="Ma note", reason="parce que")
    assert c.note_title == "Ma note"
    assert c.reason == "parce que"


def test_items_have_independent_lists():
    a = Item(title="a", url="u", source="s")
    b = Item(title="b", url="u", source="s")
    a.tags.append("x")
    assert b.tags == []
