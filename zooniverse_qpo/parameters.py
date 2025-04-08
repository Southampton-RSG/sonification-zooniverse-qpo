from itertools import product
from typing import Dict, Generator, Any


def generate_parameter_grid(
        parameter_grid: Dict,
) -> Generator[Dict, Dict, None]:
    """

    :param parameter_grid:
    :url: https://stackoverflow.com/questions/65392737/python-how-to-create-a-parameter-grid-with-dynamic-number-of-parameters
    :return:
    """
    fixed_parameters: Dict[str, Any] = {
        key: value for key, value in parameter_grid.items() if not isinstance(value, list)
    }
    varying_parameters: Dict[str, Any] = {
        key: value for key, value in parameter_grid.items() if isinstance(value, list)
    }

    for value_combinations in product(*varying_parameters.values()):
        yield fixed_parameters | dict(zip(varying_parameters.keys(), value_combinations))
