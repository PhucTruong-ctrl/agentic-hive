#!/usr/bin/env python3
"""Focused dashboard control tests; no live sessions or Room are touched."""
import importlib.machinery
import importlib.util
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
source = Path(__file__).resolve().parents[1] / "bin/hive-web"
loader = importlib.machinery.SourceFileLoader("hive_web_test", str(source))
spec = importlib.util.spec_from_loader(loader.name, loader)
web = importlib.util.module_from_spec(spec)
loader.exec_module(web)


class DashboardControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for member in ("alice", "bob", "beekeeper"):
            (self.root / "members" / member).mkdir(parents=True)
        self.root_patch = patch.object(web, "HIVE_ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def request(self, path, payload, origin="http://hive.local"):
        handler = object.__new__(web.Handler)
        body = json.dumps(payload).encode()
        handler.path = path
        handler.headers = {"Content-Length": str(len(body)), "Origin": origin, "Host": "hive.local"}
        handler.rfile = io.BytesIO(body)
        responses = []
        handler._send = lambda status, data, _: responses.append((status, json.loads(data)))
        handler.do_POST()
        return responses[0]

    def get_json(self, path):
        handler = object.__new__(web.Handler)
        handler.path = path
        handler._send = lambda status, data, _: responses.append((status, json.loads(data)))
        responses = []
        handler.do_GET()
        return responses[0]

    def test_room_all_posts_once_and_sends_to_every_agent(self):
        calls = []
        with patch.object(web, "run_hive", side_effect=lambda *args, **kwargs: calls.append((args, kwargs)) or "ok"):
            status, data = self.request("/api/room", {"message": "@all please check status"})
        self.assertEqual(status, 200)
        self.assertEqual(data["sent"], ["alice", "bob"])
        self.assertEqual(len([args for args, _ in calls if args[:2] == ("hive", "say")]), 1)
        sends = sorted(args[2] for args, _ in calls if args[:2] == ("hive-member", "send"))
        self.assertEqual(sends, ["alice", "bob"])

    def test_plain_room_post_uses_hive_cli(self):
        with patch.object(web, "run_hive", wraps=web.run_hive):
            web.run_hive("hive", "init")
            status, data = self.request("/api/room", {"message": "A note for the Room"})
        self.assertEqual(status, 200)
        self.assertEqual(data["sent"], [])
        room = (self.root / "ROOM.md").read_text()
        self.assertIn("member=beekeeper", room)
        self.assertIn("A note for the Room", room)

    def test_unknown_mention_never_posts(self):
        with patch.object(web, "run_hive") as run:
            status, data = self.request("/api/room", {"message": "@missing do work"})
        self.assertEqual(status, 400)
        self.assertIn("unknown member", data["error"])
        run.assert_not_called()

    def test_lifecycle_buttons_execute_session_commands(self):
        with patch.object(web, "run_hive", return_value="ok") as run:
            status, _ = self.request("/api/member", {"member": "alice", "action": "restart"})
        self.assertEqual(status, 200)
        run.assert_called_once_with("hive-member", "restart", "alice", "--force", "--no-attach")
        with patch.object(web, "run_hive", return_value="ok") as run:
            status, _ = self.request("/api/member", {"member": "alice", "action": "delete"})
        self.assertEqual(status, 200)
        run.assert_called_once_with("hive-member", "delete", "alice", "--force")

    def test_live_pane_overrides_stale_telemetry_pid(self):
        values = {"/proc/100/comm": "bash", "/proc/100/task/100/children": "101",
                  "/proc/101/comm": ".codex-wrapped", "/proc/101/task/101/children": ""}
        with patch.object(web, "read", side_effect=lambda path, default="": values.get(str(path), default)):
            self.assertEqual(web.pane_harness_pid(100, "codex"), 101)
        telemetry = self.root / "telemetry/members/alice.json"
        telemetry.parent.mkdir(parents=True)
        telemetry.write_text(json.dumps({"harness": "codex", "pid": 99999, "status": "idle"}))
        with patch.object(web, "member_panes", return_value={"alice": 100}), \
             patch.object(web, "pane_harness_pid", return_value=101):
            alice = next(m for m in web.members(0, 0, []) if m["member"] == "alice")
        self.assertEqual((alice["state"], alice["pid"]), ("idle", 101))

    def test_cross_origin_command_is_rejected(self):
        with patch.object(web, "run_hive") as run:
            status, _ = self.request("/api/member", {"member": "alice", "action": "kill"}, "http://other.site")
        self.assertEqual(status, 403)
        run.assert_not_called()

    def test_member_card_uses_latest_room_message(self):
        posts = [{"member": "alice", "body": "first", "ts": "2026-10-01T10:00:00-04:00"},
                 {"member": "alice", "body": "latest", "ts": "2026-10-01T10:01:00-04:00"}]
        members = web.members(2, 0, posts)
        self.assertEqual(len(members), 2)
        self.assertEqual(next(m for m in members if m["member"] == "alice")["last_room"]["body"], "latest")

    def test_steer_uses_member_send(self):
        with patch.object(web, "run_hive", return_value="ok") as run:
            status, _ = self.request("/api/steer", {"member": "alice", "prompt": "do work"})
        self.assertEqual(status, 200)
        run.assert_called_once_with("hive-member", "send", "alice", "do work")

    def test_git_projects_include_projects_without_live_members(self):
        repo = self.root / "projects" / "sample"
        repo.mkdir(parents=True)
        subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
        (repo / "README.md").write_text("first\n")
        subprocess.run(["git", "-C", str(repo), "add", "README.md"], check=True)
        subprocess.run(["git", "-C", str(repo), "-c", "user.name=Test", "-c", "user.email=test@example.com",
                        "commit", "-qm", "Initial"], check=True)
        (repo / "README.md").write_text("changed\n")
        (repo / "new.txt").write_text("new\n")
        projects = web.git_projects([])
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["name"], "sample")
        self.assertEqual((projects[0]["modified"], projects[0]["untracked"]), (1, 1))
        self.assertEqual(projects[0]["commit"]["subject"], "Initial")

    def test_hive_files_list_and_preview_with_path_boundaries(self):
        note = self.root / "members" / "alice" / "notes" / "plan.md"
        note.parent.mkdir()
        note.write_text("Only relevant notes are read.\n")
        status, listing = self.get_json("/api/files?path=members/alice/notes")
        self.assertEqual(status, 200)
        self.assertEqual(listing["entries"][0]["name"], "plan.md")
        status, preview = self.get_json("/api/file?path=members/alice/notes/plan.md")
        self.assertEqual(status, 200)
        self.assertEqual(preview["text"], note.read_text())
        handler = object.__new__(web.Handler)
        handler.path = "/api/file?path=members/alice/notes/plan.md&download=1"
        handler.command = "GET"
        handler.wfile = io.BytesIO()
        headers = {}
        handler.send_response = lambda code: headers.update(status=code)
        handler.send_header = lambda name, value: headers.update({name: value})
        handler.end_headers = lambda: None
        handler.do_GET()
        self.assertEqual(headers["status"], 200)
        self.assertEqual(handler.wfile.getvalue(), note.read_bytes())
        with self.assertRaises(ValueError):
            web.browser_path("members/alice/notes/../../bob/state/launch.json")
        (note.parent / "outside").symlink_to(Path(self.temp.name).parent)
        with self.assertRaises(ValueError):
            web.browser_path("members/alice/notes/outside")

    def test_fragmented_websocket_input(self):
        class OneByteSocket:
            def __init__(self, data):
                self.data = bytearray(data)

            def recv(self, _):
                if not self.data:
                    return b""
                return bytes([self.data.pop(0)])

        payload = b"hello"
        mask = os.urandom(4)
        frame = bytes([0x81, 0x80 | len(payload)]) + mask + bytes(c ^ mask[i % 4] for i, c in enumerate(payload))
        self.assertEqual(web.read_ws_frame(OneByteSocket(frame)), (1, payload))

    def test_terminal_upgrade_uses_http_1_1(self):
        # Firefox rejects an HTTP/1.0 upgrade even when its other headers are valid.
        # Exercise the actual response on the wire without starting a shell.
        with patch.object(web, "TerminalBridge") as bridge_class:
            bridge_class.return_value.running = False
            server = ThreadingHTTPServer(("127.0.0.1", 0), web.Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                host = f"127.0.0.1:{server.server_port}"
                with socket.create_connection(server.server_address, timeout=2) as connection:
                    connection.sendall((
                        "GET /ws/shell HTTP/1.1\r\n"
                        f"Host: {host}\r\nOrigin: http://{host}\r\n"
                        "Connection: Upgrade\r\nUpgrade: websocket\r\n"
                        "Sec-WebSocket-Version: 13\r\n"
                        "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n\r\n"
                    ).encode())
                    response = b""
                    while b"\r\n\r\n" not in response:
                        chunk = connection.recv(4096)
                        self.assertTrue(chunk, "connection closed before upgrade headers")
                        response += chunk
                self.assertEqual(response.split(b"\r\n", 1)[0], b"HTTP/1.1 101 Switching Protocols")
                self.assertIn(b"Upgrade: websocket\r\n", response)
                self.assertIn(b"Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=\r\n", response)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

    def test_terminal_foreground_process_receives_resize(self):
        server_socket, client_socket = socket.socketpair()
        client_socket.settimeout(2)
        script = """
import os
import signal

def resized(*_):
    print('size=' + str(os.get_terminal_size(0).columns), flush=True)

signal.signal(signal.SIGWINCH, resized)
try:
    foreground = os.tcgetpgrp(0) == os.getpgrp()
except OSError:
    foreground = False
print('foreground=' + str(foreground), flush=True)
print('ready', flush=True)
while True:
    signal.pause()
"""
        bridge = web.TerminalBridge([sys.executable, "-u", "-c", script], "steer", server_socket,
                                    cwd=str(self.root))

        def receive_until(marker):
            data = b""
            while marker not in data:
                chunk = client_socket.recv(4096)
                self.assertTrue(chunk, "terminal closed before expected output")
                data += chunk
            return data

        try:
            bridge.start()
            self.assertIn(b"foreground=True", receive_until(b"ready"))
            web.set_winsize(bridge.master_fd, 25, 132)
            self.assertIn(b"size=132", receive_until(b"size=132"))
        finally:
            bridge.stop()
            server_socket.shutdown(socket.SHUT_RDWR)
            server_socket.close()
            client_socket.close()
            if bridge.proc:
                bridge.proc.wait(timeout=2)


if __name__ == "__main__":
    unittest.main()
