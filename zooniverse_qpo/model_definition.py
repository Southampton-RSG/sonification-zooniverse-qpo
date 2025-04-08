from abc import ABC, abstractmethod
from copy import copy
from typing import Any, Dict, List

from dataclasses import dataclass
from logging import getLogger

import numpy as np
from astropy import units as u
from astropy.modeling import Model
from astropy.time import TimeDelta
from astropy.units import Quantity, UnitBase


logger = getLogger(__name__)



@dataclass
class ModelDefinitionBase(ABC):
    """
    The abstract base class for a single model component or a collection of many.
    """
    @abstractmethod
    def get_model_for_mean_rate(self, rate_mean: Quantity[u.s**-1]) -> Model:
        """
        For a mean lightcurve count rate, generate a model that can be passed to MindTheGaps.

        :param rate_mean: Mean light curve count.
        :return: An Astropy model.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_title(self, time_units: UnitBase = u.day) -> str:
        """
        Generates a title for a plot of this model.

        :param time_units: The time unit to use, if different from default.
        :return: A string designed for use on a plot.
        """
        raise NotImplementedError()

    @abstractmethod
    def to_metadata(self, time_units: UnitBase = u.day,idx: int = 0) -> dict:
        """
        Converts the model parameters into a dictionary, for saving to metadata.

        :param idx: For multi-component models, which index is this?
        :param time_units: The time units to display using.
        :return: A dictionary containing the model parameters.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_period(self) -> TimeDelta:
        """

        :return:
        """
        raise NotImplementedError()

@dataclass
class ModelDefinition(ModelDefinitionBase):
    """
    Component of a lightcurve model
    """
    model: Model
    coherence: float
    variance_fraction: float
    period: TimeDelta

    def get_model_for_mean_rate(self, rate_mean: Quantity[u.s**-1]) -> Model:
        """
         For a mean lightcurve count rate, generate a model that can be passed to MindTheGaps.

         :param rate_mean: Mean light curve count.
         :return: An Astropy model.
         """
        return self.model(
            omega0=2 * np.pi / self.period.to(u.s).value,
            Q=self.coherence,
            S0=self.variance_fraction ** 2 * rate_mean.to(u.s ** -1).value ** 2,
        )

    def get_title(self, time_units: UnitBase = u.day) -> str:
        """
        Generates a title for a plot of this model.

        :param time_units: The time unit to use, if different from default.
        :return: A string designed for use on a plot.
        """
        return f"{self.model.name}, period {self.period.to(time_units)}, variance fraction of mean {self.variance_fraction}"

    def to_metadata(self, time_units: UnitBase = u.day, idx: int = 0) -> dict:
        """
        Converts the model parameters into a dictionary, for saving to metadata.

        :param idx: For multi-component models, which index is this?
        :param time_units: The time unit to use, if different from default.
        :return: A dict containing the period, coherence, variance fraction and model name.
        """
        return {
            f"component_{idx}_period": f"{self.period.to(time_units)}",
            f"component_{idx}_coherence": self.coherence,
            f"component_{idx}_variance_fraction": self.variance_fraction,
            f"component_{idx}_model": f"{self.model.name}",
        }

    def get_period(self) -> TimeDelta:
        """

        :return:
        """
        return self.period


@dataclass
class ModelComposite(ModelDefinitionBase):
    """
    A composite model consisting of many components.
    """
    model_components: List[ModelDefinition]

    def get_model_for_mean_rate(self, rate_mean: Quantity[u.s**-1]) -> Model:
        """
         For a mean lightcurve count rate, generate a model that can be passed to MindTheGaps.

         :param rate_mean: Mean light curve count.
         :return: An Astropy model.
         """
        model_total: Model = self.model_components[0].get_model_for_mean_rate(rate_mean)
        for model_component in self.model_components[1:]:
            model_total += model_component.get_model_for_mean_rate(rate_mean)

        return model_total

    def get_title(self, time_units: UnitBase = u.day) -> str:
        """
        Generates a title for a plot of this model.

        :param time_units: The time unit to use, if different from default.
        :return: A string designed for use on a plot.
        """
        return ' & '.join(
            model_component.get_title(time_units) for model_component in self.model_components
        )

    def to_metadata(self, time_units: UnitBase = u.day) -> dict:
        """
        Collects the metadata for all model components together into a single dictionary.
        Can't be nested as it's for the Zooniverse, so it's flat with the model index on it.

        :param time_units: The time unit to use, if different from default.
        :return: A dict containing the period, coherence, variance fraction and model name for each component.
        """
        metadata: Dict[str, Any] = {}
        for idx, model_component in enumerate(self.model_components):
            metadata.update(model_component.to_metadata(time_units=time_units, idx=idx))

        return metadata

    def get_period(self) -> TimeDelta:
        """

        :return:
        """
        return self.model_components[0].period