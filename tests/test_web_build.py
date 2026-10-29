"""The public build accepts a gateway origin, never credentials or script URLs."""

import pytest

from scripts.build_web import build


def test_separate_gateway_build_sets_connection_policy(tmp_path):
    build(tmp_path, "https://search.example.com/")
    assert (tmp_path / "config.js").read_text() == 'export const gatewayUrl = "https://search.example.com";\n'
    assert "connect-src 'self' https://search.example.com;" in (tmp_path / "index.html").read_text()
    assert (tmp_path / "worker.js").is_file() and (tmp_path / ".nojekyll").is_file()


def test_amex_converter_is_bundled_without_provider_access(tmp_path):
    build(tmp_path)
    html = (tmp_path / "index.html").read_text()
    assert 'id="amex-form"' in html
    assert 'src="./amex-ui.js"' in html
    assert (tmp_path / "amex.js").is_file()
    assert (tmp_path / "amex-ui.js").is_file()


@pytest.mark.parametrize("value", ["javascript:alert(1)", "https://user:secret@example.com", "https://example.com/?token=secret",
    "https://*.example.com", "http://public.example.com", "https://example.com;script-src *"])
def test_gateway_configuration_cannot_inject_credentials_or_policy(tmp_path, value):
    output = tmp_path / "site"
    with pytest.raises(ValueError):
        build(output, value)
    assert not output.exists()
