import argparse
from hwcomponents.estimator_wrapper import EnergyAreaEstimatorWrapper
from hwcomponents.find_estimators import get_estimators


def list_components(printfunc=print):
    printfunc("\n")
    printfunc("Supported Components:")

    class Entry:
        def __init__(
            self,
            name: str,
            class_name: str,
            init_function: str,
            actions: list[str],
        ):
            self.name = name
            self.class_name = class_name
            self.init_function = init_function
            self.actions = actions

        def __str__(self):
            return (
                f"{self.class_name}{self.init_function} from class {self.name} \n"
                + "\n".join(f"\t{a}" for a in self.actions)
            )

    entries = []
    for estimator in get_estimators():

        def add_entry(name, class_names, init_func, actions):
            class_names = [class_names] if isinstance(class_names, str) else class_names
            entries.append(
                (class_names[0], Entry(name, class_names[0], str(init_func), actions))
            )
            for c in class_names[1:]:
                entries.append(
                    (c, f"{c}: alias for {name} from class {class_names[0]}")
                )

        add_entry(
            estimator.get_name(),
            estimator.get_component_names(),
            str(estimator.init_function),
            estimator.actions,
        )

    entries = sorted(entries, key=lambda x: x[0].lower())
    for entry in entries:
        printfunc(entry[1])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--list", action="store_true", help="List all available components"
    )
    args = parser.parse_args()

    if args.list:
        list_components()


if __name__ == "__main__":
    main()
