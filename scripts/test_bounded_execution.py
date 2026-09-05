#!/usr/bin/env python3
"""Bounded execution regression contract, including bypass and false-positive cases."""
import unittest
import guidecheck_verify as gv


class BoundedExecutionTests(unittest.TestCase):
    def test_shapes(self):
        cases = {
            'bound-script': ['bash scripts/setup.sh', './scripts/setup.sh', 'python setup',
                             '.venv/bin/python prompter_kit.py', 'python script.py -c ignored',
                             'bash ./setup.sh -c ignored', 'awk -f script.awk',
                             '"./script with spaces.sh"', 'sudo bash setup.sh',
                             "python -c 'print(1)' && ./setup.sh", 'perl script.pl', 'python -E setup.py', 'python -W ignore setup.py'],
            'inline': ["python -c 'print(1)'", "bash -lc 'echo hello'", "bash -f -c 'echo hello'", "python -W ignore -c 'print(1)'", "awk '{print $1}' data.txt",
                       "perl -e 'print 1'", "python -c 'print(\"./setup.sh; bash x.sh\")'"],
            'exempt-installer': ['npm ci', 'npm install --global tool@2', 'pip install -r requirements.txt',
                                 'pip install requests', 'bundle install', './gradlew build'],
            'ambiguous': ['python -m pkg', 'make test', 'npm run build', 'pip install .',
                          'pip install -e .', 'cargo build', 'go build', 'docker build .', 'bash -s arg', 'python - arg'],
            'none': ['docker ps', 'sed -n 1p file', 'jq . file', '.venv/bin/python --version', 'git clone repo'],
        }
        for expected, commands in cases.items():
            for command in commands:
                with self.subTest(command=command):
                    self.assertEqual(gv.classify_exec_target(command), expected)

    def findings(self, command, fields=''):
        text = f'[action]\nid: test\nclass: code-executing\napproval: required\ncommand: {command}\ncwd: .\nrunner: argv\n{fields}[/action]\n'
        findings = []
        actions = gv.parse_actions(text, findings)
        gv.check_actions(actions, findings)
        return {(f.id, f.severity) for f in findings}

    def test_pin_does_not_claim_verification(self):
        got = self.findings('bash setup.sh', 'exec-sha256: ' + 'a' * 64 + '\n')
        self.assertIn(('exec-sha256.unverified', 'info'), got)
        self.assertNotIn(('action.exec-unbounded', 'error'), got)

    def test_invalid_pins_do_not_bypass(self):
        for pin in ['', 'A' * 64, 'a' * 63, 'g' * 64]:
            got = self.findings('./setup.sh', f'exec-sha256: {pin}\n')
            self.assertIn(('action-block.malformed', 'error'), got)
            self.assertIn(('action.exec-unbounded', 'error'), got)

    def test_opaque_cannot_override_pin_on_script(self):
        got = self.findings('./setup.sh', 'exec-opaque: acknowledged\nnotes: Reviewed\nexec-sha256: ' + 'a' * 64 + '\n')
        self.assertIn(('action.exec-unbounded', 'error'), got)

    def test_opaque_installer_and_malformed_fields(self):
        self.assertIn(('action.exec-opaque', 'warning'), self.findings('npm ci', 'exec-opaque: acknowledged\nnotes: Dependency code\n'))
        for fields in ['exec-opaque: acknowledged\n', 'exec-opaque: yes\nnotes: reason\n']:
            self.assertIn(('action-block.malformed', 'error'), self.findings('npm ci', fields))

    def test_detected_script_blocks_even_if_underdeclared(self):
        findings = []
        gv.check_actions([{'id': 'test', 'command': './setup.sh', 'class': 'normal', 'approval': 'not-required'}], findings)
        self.assertIn('action.exec-unbounded', {f.id for f in findings if f.severity == 'error'})


if __name__ == '__main__':
    unittest.main()
