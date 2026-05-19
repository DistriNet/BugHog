from bughog.subject.js_engine.v8.executable import V8Executable


class V8SandboxTestingExecutable(V8Executable):
    def _get_cli_command(self) -> list[str]:
        if self.state.commit_nb < 93153:
            runtime_flags = [
                "--sandbox-fuzzing" if flag == "--sandbox-testing" else flag
                for flag in self._runtime_flags
            ]
        elif self.state.commit_nb < 97151:
            runtime_flags = [
                "--sandbox-testing" if flag == "--sandbox-fuzzing" else flag
                for flag in self._runtime_flags
            ]
        else:
            runtime_flags = list(self._runtime_flags)
        return [self.executable_path] + runtime_flags
