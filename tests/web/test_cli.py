
from ttobak import cli


def test_web_subcommand_dispatches_to_serve(monkeypatch):
    called = {}
    monkeypatch.setattr(cli, "_serve", lambda host, port, provider_name, share: called.update(
        host=host, port=port, provider_name=provider_name, share=share))
    rc = cli.main(["web", "--host", "127.0.0.1", "--port", "7861", "--provider", "fake"])
    assert rc == 0
    assert called == {"host": "127.0.0.1", "port": 7861, "provider_name": "fake", "share": False}


def test_web_defaults(monkeypatch):
    captured = {}
    monkeypatch.setattr(cli, "_serve", lambda host, port, provider_name, share: captured.update(
        host=host, port=port, share=share))
    rc = cli.main(["web"])
    assert rc == 0
    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == 7860
    assert captured["share"] is False


def test_no_subcommand_returns_nonzero():
    assert cli.main([]) != 0
