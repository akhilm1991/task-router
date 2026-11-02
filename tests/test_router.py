"""Tests for the parts that must not depend on a model. No model is called."""
import importlib.machinery
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROUTER = pathlib.Path(__file__).resolve().parent.parent / "bin" / "router"
loader = importlib.machinery.SourceFileLoader("router", str(ROUTER))
spec = importlib.util.spec_from_loader("router", loader)
router = importlib.util.module_from_spec(spec)
loader.exec_module(router)


class Sandbox(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self.tmp.name)
        self.brief = self.dir / "brief.txt"
        self.brief.write_text("do the thing")
        self.env = dict(os.environ, TASK_ROUTER_STATE=str(self.dir / "state"))

    def tearDown(self):
        self.tmp.cleanup()


class Launch(Sandbox):
    def launch(self, model="gpt-6.1-sol", *extra):
        return subprocess.run(
            [sys.executable, str(ROUTER), "launch", "--title", "t", "--model", model, "--reason", "r",
             "--brief", str(self.brief), "--cwd", str(self.dir), "--dry-run"] + list(extra),
            capture_output=True, text=True, env=self.env)

    def command(self, *args):
        result = self.launch(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)["command"]

    def test_codex_is_always_sandboxed(self):
        command = self.command()
        self.assertEqual(command[command.index("-s") + 1], "workspace-write")
        self.assertEqual(command[command.index("-a") + 1], "on-request")

    def test_unknown_model_refused(self):
        self.assertNotEqual(self.launch("no-such-model").returncode, 0)

    def test_secret_refused(self):
        self.brief.write_text("key sk-abcdefghijklmnopqrstuvwxyz123456")
        self.assertIn("secret", self.launch().stderr)

    def test_oversized_brief_refused(self):
        self.brief.write_text("x" * (router.MAX_BRIEF_BYTES + 1))
        self.assertNotEqual(self.launch().returncode, 0)

    def test_project_can_block_a_provider(self):
        (self.dir / ".router.json").write_text('{"blocked_providers": ["openai"]}')
        self.assertIn("blocks", self.launch().stderr)
        self.assertEqual(self.launch("claude-sonnet-5-5").returncode, 0)

    def test_worktree_only_in_git(self):
        self.assertNotIn("--worktree", self.command("claude-sonnet-5-5"))
        subprocess.run(["git", "init", "-q", str(self.dir)], check=True)
        self.assertIn("--worktree", self.command("claude-sonnet-5-5"))
        self.assertNotIn("--worktree", self.command("claude-sonnet-5-5", "--no-worktree"))

    def test_other_tools_rules_are_named(self):
        (self.dir / "CLAUDE.md").write_text("rules")
        self.assertIn("CLAUDE.md", self.command("gpt-6.1-sol")[-1])
        self.assertNotIn("CLAUDE.md", self.command("claude-sonnet-5-5")[-1])


class Record(Sandbox):
    """`record` checks what `launch` checks, logs the route, and starts nothing."""

    def record(self, model="claude-sonnet-5-5", *extra):
        return subprocess.run(
            [sys.executable, str(ROUTER), "record", "--title", "t", "--model", model, "--reason", "r",
             "--brief", str(self.brief), "--cwd", str(self.dir)] + list(extra),
            capture_output=True, text=True, env=self.env)

    def logged(self):
        return [json.loads(line) for line in (self.dir / "state" / "routes.jsonl").read_text().splitlines()]

    def test_logs_one_app_route_and_prints_its_id(self):
        result = self.record()
        self.assertEqual(result.returncode, 0, result.stderr)
        (route,) = self.logged()
        self.assertEqual((route["via"], route["model"], route["isolated"]), ("app", "claude-sonnet-5-5", False))
        self.assertIn("Route " + route["id"], result.stdout)

    def test_same_refusals_as_launch(self):
        self.assertNotEqual(self.record("no-such-model").returncode, 0)
        self.brief.write_text("key sk-abcdefghijklmnopqrstuvwxyz123456")
        self.assertIn("secret", self.record().stderr)
        self.brief.write_text("x" * (router.MAX_BRIEF_BYTES + 1))
        self.assertNotEqual(self.record().returncode, 0)
        self.brief.write_text("ok")
        (self.dir / ".router.json").write_text('{"blocked_providers": ["anthropic"]}')
        self.assertIn("blocks", self.record().stderr)
        self.assertFalse((self.dir / "state" / "routes.jsonl").exists())

    def test_codex_cannot_be_an_app_session(self):
        result = self.record("gpt-6.1-sol")
        self.assertIn("router launch", result.stderr)
        self.assertFalse((self.dir / "state" / "routes.jsonl").exists())

    def test_worktree_is_reported_for_git_only(self):
        self.assertIn("use_worktree=false", self.record().stdout)
        subprocess.run(["git", "init", "-q", str(self.dir)], check=True)
        self.assertIn("use_worktree=true", self.record().stdout)
        self.assertIn("use_worktree=false", self.record("claude-sonnet-5-5", "--no-worktree").stdout)



class CheckModels(unittest.TestCase):
    def run_check(self, models, claude, codex):
        with tempfile.TemporaryDirectory() as tmp:
            router.CATALOG = pathlib.Path(tmp) / "catalog.json"
            router.CATALOG.write_text(json.dumps({"models": models}))
            router.fetch_claude_ids = lambda: claude
            router.fetch_codex_ids = lambda: codex
            args = type("Args", (), {"write": True})()
            with self.assertRaises(SystemExit) as stop, open(os.devnull, "w") as quiet:
                saved, sys.stdout = sys.stdout, quiet
                try:
                    router.cmd_check_models(args)
                finally:
                    sys.stdout = saved
            data = json.loads(router.CATALOG.read_text())
        return stop.exception.code, {m["id"]: m["status"] for m in data["models"]}

    def test_new_model_is_only_a_trial(self):
        code, status = self.run_check(
            [{"id": "a", "provider": "anthropic", "status": "active"}], ({"a", "b"}, {"a", "b"}), (set(), set()))
        self.assertEqual((code, status), (10, {"a": "active", "b": "trial"}))

    def test_older_model_still_named_stays_usable(self):
        code, status = self.run_check(
            [{"id": "a", "provider": "anthropic", "status": "active"}], ({"b"}, {"a", "b"}), (set(), set()))
        self.assertEqual(status["a"], "active")

    def test_gone_model_is_retired(self):
        _, status = self.run_check(
            [{"id": "a", "provider": "openai", "status": "active"}], (set(), set()), ({"b"}, {"b"}))
        self.assertEqual(status["a"], "retired")

    def test_source_down_changes_nothing(self):
        def down():
            raise RuntimeError("down")
        models = [{"id": "a", "provider": "openai", "status": "active"}]
        with tempfile.TemporaryDirectory() as tmp:
            router.CATALOG = pathlib.Path(tmp) / "catalog.json"
            router.CATALOG.write_text(json.dumps({"models": models}))
            router.fetch_claude_ids = down
            router.fetch_codex_ids = down
            args = type("Args", (), {"write": True})()
            with self.assertRaises(SystemExit) as stop, open(os.devnull, "w") as quiet:
                saved, sys.stdout = sys.stdout, quiet
                try:
                    router.cmd_check_models(args)
                finally:
                    sys.stdout = saved
            self.assertEqual(stop.exception.code, 1)
            self.assertEqual(json.loads(router.CATALOG.read_text())["models"], models)


class CleanEnv(unittest.TestCase):
    def test_only_inside_a_claude_session(self):
        keep = dict(os.environ)
        config = router.CONFIG
        router.CONFIG = pathlib.Path(tempfile.gettempdir()) / "no-such-router-config"
        try:
            os.environ.pop("CLAUDECODE", None)
            os.environ["ANTHROPIC_API_KEY"] = "user-key"
            self.assertEqual(router.clean_env()["ANTHROPIC_API_KEY"], "user-key")
            os.environ["CLAUDECODE"] = "1"
            self.assertNotIn("ANTHROPIC_API_KEY", router.clean_env())
        finally:
            router.CONFIG = config
            os.environ.clear()
            os.environ.update(keep)

    def test_direct_login_ignores_shell_settings(self):
        keep = dict(os.environ)
        config = router.CONFIG
        with tempfile.TemporaryDirectory() as tmp:
            router.CONFIG = pathlib.Path(tmp)
            (router.CONFIG / "config.json").write_text('{"direct_login": true}')
            try:
                os.environ.pop("CLAUDECODE", None)
                os.environ["ANTHROPIC_BASE_URL"] = "http://localhost:1"
                self.assertNotIn("ANTHROPIC_BASE_URL", router.clean_env())
            finally:
                router.CONFIG = config
                os.environ.clear()
                os.environ.update(keep)


class Skill(unittest.TestCase):
    def test_prompt_stays_short(self):
        self.assertLess(len(router.SKILL.read_text().split()), 350)

    def test_removing_an_instruction_removes_only_that_line(self):
        full = router.skill_without(None)
        lines, _ = router.instructions(router.SKILL.read_text())
        self.assertNotIn(lines[0], router.skill_without(1))
        self.assertIn(lines[1], router.skill_without(1))
        self.assertIn(lines[0], full)


if __name__ == "__main__":
    unittest.main()
