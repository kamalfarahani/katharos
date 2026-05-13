from dataclasses import dataclass

from katharos.types.side_effect.function_with_side_effect import FunctionWithSideEffect


@dataclass
class Command:
    name: str


class FakeSideEffectFunction:
    def __init__(
        self,
        cmd: Command,
        command_list: list[Command],
    ):
        self.called_count = 0
        self.cmd = cmd
        self.command_list = command_list

    def __call__(self):
        self.called_count += 1
        self.command_list.append(self.cmd)


def test_seq():
    command_list = []
    fake_func_1 = FakeSideEffectFunction(
        cmd=Command("cmd_1"), command_list=command_list
    )
    fake_func_2 = FakeSideEffectFunction(
        cmd=Command("cmd_2"), command_list=command_list
    )

    f_1 = FunctionWithSideEffect(f=fake_func_1, description="f_1")
    f_2 = FunctionWithSideEffect(f=fake_func_2, description="f_2")
    f_3 = f_1 >> f_2
    f_3()

    assert fake_func_1.called_count == 1
    assert fake_func_2.called_count == 1
    assert command_list == [Command("cmd_1"), Command("cmd_2")]
