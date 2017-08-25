from news2mbox import read_config
import os
import pytest
import shutil
import tempfile


def assert_parsed_output(cfgtxt, result):
    cfgdir = tempfile.mkdtemp()
    cfgfile = os.path.join(cfgdir, "config")

    with open(cfgfile, "w") as f:
        f.write(cfgtxt)

    try:
        assert read_config(cfgfile) == result
    finally:
        shutil.rmtree(cfgdir)


def test_minimal():
    assert_parsed_output("""
        { "server" : "news.server.com", "groups" : ["comp.lang.python"] }""",
        [ dict(server="news.server.com",
               groups=[ "comp.lang.python" ]) ])


def test_userpass():
    assert_parsed_output("""
        { "server"   : "news.server.com",
          "user"     : "user@site.com", 
          "password" : "secret",
          "groups"   : [ "comp.lang.python", "comp.lang.c" ] }""",
        [ dict(server="news.server.com",
               user="user@site.com",
               password="secret",
               groups=[ "comp.lang.python", "comp.lang.c" ]) ])


def test_multiple_servers():
    assert_parsed_output("""
    [
        { "server"   : "news.server.com",
          "user"     : "user@site.com",
          "password" : "secret",
          "groups"   : [ "comp.lang.python"] },

        { "server"   : "news2.server.com",
          "user"     : "user2@site.com",
          "password" : "secret2",
          "groups"   : [ "comp.lang.c"] },

        { "server"   : "news3.server.com",
          "user"     : "user3@site.com",
          "password" : "secret3",
          "groups"   : [ "comp.lang.scheme"] }
    ]""",
        [ dict(server="news.server.com",
               user="user@site.com",
               password="secret",
               groups=[ "comp.lang.python" ]),
          dict(server="news2.server.com",
               user="user2@site.com",
               password="secret2",
               groups=[ "comp.lang.c" ]),
          dict(server="news3.server.com",
               user="user3@site.com",
               password="secret3",
               groups=[ "comp.lang.scheme" ]) ])


def test_maximal():
    assert_parsed_output("""
        { "server"   : "news.server.com",
          "user"     : "user@site.com",
          "password" : "secret",
          "outdir"   : "/home/user/news",
          "ssl"      : false,
          "groups"   : ["comp.lang.python"] }""",
        [ dict(server="news.server.com",
               user="user@site.com",
               password="secret",
               outdir="/home/user/news",
               ssl=False,
               groups=[ "comp.lang.python" ]) ])


def test_invalid_no_groups():
    with pytest.raises(SyntaxError):
        assert_parsed_output("""
            { "server"   : "news.server.com", 
              "user"     : "user@list.com",
              "password" : "secret" }""",
            [])


def test_invalid_no_server():
    with pytest.raises(SyntaxError):
        assert_parsed_output('{ "groups" : ["comp.lang.python"] }', [])


def test_invalid_wrong_key():
    with pytest.raises(SyntaxError):
        assert_parsed_output("""
            { "server" : "news.server.com",
              "groups" : ["comp.lang.c"],
              "unknown" : "invalid" }""",
            [])


def test_invalid_no_group_list():
    with pytest.raises(SyntaxError):
        assert_parsed_output("""
            { "server" : "news.server.com",
              "groups" : "comp.lang.c" }""",
            [])


def test_invalid_server_type():
    with pytest.raises(SyntaxError):
        assert_parsed_output("""
            { "server" : 14,
              "groups" : ["comp.lang.c"] }""",
            [])


def test_invalid_json_syntax():
    with pytest.raises(SyntaxError):
        assert_parsed_output("""
            { "server" : news.server.com",
              "groups" : ["comp.lang.c"] }""",
            [])
