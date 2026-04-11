from spite.ingest import IngestionManager


def test_is_allowed_file():
    manager = IngestionManager()

    # Allowed
    assert manager._is_allowed_file("README.md")
    assert manager._is_allowed_file("docs/api.rst")
    assert manager._is_allowed_file("src/types.pyi")
    assert manager._is_allowed_file("lib/index.d.ts")
    assert manager._is_allowed_file("index.html")
    assert manager._is_allowed_file("requirements.txt")

    # Not allowed
    assert not manager._is_allowed_file("main.py")
    assert not manager._is_allowed_file("index.js")
    assert not manager._is_allowed_file("src/app.go")
    assert not manager._is_allowed_file("image.png")
