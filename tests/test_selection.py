import pytest

from hwcomponents import (
    ComponentModel,
    action,
    ActionCost,
    get_action_cost,
    get_model,
)
from hwcomponents._model_wrapper import ComponentModelWrapper, ModelQuery
from hwcomponents.select_models import (
    _selection_key,
    _count_arg_matches,
)


def _wrap(cls):
    return ComponentModelWrapper(cls, cls.__name__)


def _key(cls, query):
    return _selection_key(_wrap(cls), query)


ACTION_Q = ModelQuery("c", {}, "op", {"x": 1, "y": 2})
INIT_Q = ModelQuery("c", {"a": 1, "b": 2}, None, None)
EMPTY_Q = ModelQuery("c", {}, None, None)


# --- Models used to exercise each tie-break criterion ------------------------


class NoPriority(ComponentModel):
    component_name = "c"

    def __init__(self):
        super().__init__(area=1.0, leak_power=1.0)


class PHigh(ComponentModel):
    component_name = "c"
    priority = 0.9

    def __init__(self):
        super().__init__(area=1.0, leak_power=1.0)

    @action
    def op(self):
        return ActionCost(energy=9.0, throughput=1.0, latency=1.0)


class PLow(ComponentModel):
    component_name = "c"
    priority = 0.1

    def __init__(self):
        super().__init__(area=1.0, leak_power=1.0)

    @action
    def op(self):
        return ActionCost(energy=1.0, throughput=1.0, latency=1.0)


class Broken(ComponentModel):
    component_name = "c"
    priority = 0.9

    def __init__(self):
        raise ValueError("boom")

    @action
    def op(self):
        return ActionCost(energy=9.0, throughput=1.0, latency=1.0)


class Works(ComponentModel):
    component_name = "c"
    priority = 0.1

    def __init__(self):
        super().__init__(area=1.0, leak_power=1.0)

    @action
    def op(self):
        return ActionCost(energy=1.0, throughput=1.0, latency=1.0)


class ArgModel(ComponentModel):
    component_name = "c"

    def __init__(self, a, b=2):
        super().__init__(area=1.0, leak_power=1.0)


# Criterion 2: more provided arguments accepted by the action wins.
class C2More(ComponentModel):
    component_name = "c"

    def __init__(self):
        super().__init__(area=1.0, leak_power=1.0)

    @action
    def op(self, x=1, y=2):
        return ActionCost(energy=1.0, throughput=1.0, latency=1.0)


class C2Less(ComponentModel):
    component_name = "c"

    def __init__(self):
        super().__init__(area=1.0, leak_power=1.0)

    @action
    def op(self, x=1):
        return ActionCost(energy=1.0, throughput=1.0, latency=1.0)


# Criterion 3: more provided attributes accepted by the init function wins.
class C3More(ComponentModel):
    component_name = "c"

    def __init__(self, a=1, b=2):
        super().__init__(area=1.0, leak_power=1.0)


class C3Less(ComponentModel):
    component_name = "c"

    def __init__(self, a=1):
        super().__init__(area=1.0, leak_power=1.0)


# Criterion 4: fewer unfilled defaulted action arguments wins.
class C4Few(ComponentModel):
    component_name = "c"

    def __init__(self):
        super().__init__(area=1.0, leak_power=1.0)

    @action
    def op(self, x=1):
        return ActionCost(energy=1.0, throughput=1.0, latency=1.0)


class C4Many(ComponentModel):
    component_name = "c"

    def __init__(self):
        super().__init__(area=1.0, leak_power=1.0)

    @action
    def op(self, x=1, y=2):
        return ActionCost(energy=1.0, throughput=1.0, latency=1.0)


# Criterion 5: fewer unfilled defaulted init arguments wins.
class C5Few(ComponentModel):
    component_name = "c"

    def __init__(self):
        super().__init__(area=1.0, leak_power=1.0)


class C5Many(ComponentModel):
    component_name = "c"

    def __init__(self, z=1):
        super().__init__(area=1.0, leak_power=1.0)


# Criterion 6: alphabetically earlier class name wins.
class C6Aaa(ComponentModel):
    component_name = "c"

    def __init__(self):
        super().__init__(area=1.0, leak_power=1.0)


class C6Zzz(ComponentModel):
    component_name = "c"

    def __init__(self):
        super().__init__(area=1.0, leak_power=1.0)


# --- Default priority --------------------------------------------------------


def test_default_priority_is_0_5():
    assert NoPriority.priority == 0.5
    assert _wrap(NoPriority).priority == 0.5


# --- _count_arg_matches ------------------------------------------------------


def test_count_arg_matches():
    func = _wrap(ArgModel).init_function
    assert _count_arg_matches(func, {"a": 1}) == (1, 1)
    assert _count_arg_matches(func, {"a": 1, "b": 5}) == (2, 0)
    assert _count_arg_matches(func, {"a": 1, "c": 9}) == (1, 1)


# --- Tie-break ordering (criteria 1-7) ---------------------------------------


def test_criterion_1_priority():
    assert _key(PHigh, ACTION_Q) < _key(PLow, ACTION_Q)


def test_criterion_2_more_action_args_provided():
    assert _key(C2More, ACTION_Q) < _key(C2Less, ACTION_Q)


def test_criterion_3_more_init_args_provided():
    assert _key(C3More, INIT_Q) < _key(C3Less, INIT_Q)


def test_criterion_4_fewer_unfilled_action_defaults():
    query = ModelQuery("c", {}, "op", {"x": 1})
    assert _key(C4Few, query) < _key(C4Many, query)


def test_criterion_5_fewer_unfilled_init_defaults():
    assert _key(C5Few, EMPTY_Q) < _key(C5Many, EMPTY_Q)


def test_criterion_6_class_name():
    assert _key(C6Aaa, EMPTY_Q) < _key(C6Zzz, EMPTY_Q)


def test_criterion_7_is_fully_qualified_name():
    fqn = f"{C6Aaa.__module__}.{C6Aaa.__qualname__}"
    assert _key(C6Aaa, EMPTY_Q)[-1] == fqn


# --- End-to-end selection ----------------------------------------------------


@pytest.mark.parametrize("order", [[PLow, PHigh], [PHigh, PLow]])
def test_priority_decides_regardless_of_input_order(order):
    cost = get_action_cost("c", {}, "op", {}, models=order)
    assert cost.energy == 9.0


def test_lower_priority_used_when_higher_errors():
    cost = get_action_cost("c", {}, "op", {}, models=[Broken, Works])
    assert cost.energy == 1.0


def test_non_action_path_uses_tie_break():
    model = get_model("c", {}, models=[C5Many, C5Few])
    assert type(model).__name__ == "C5Few"
