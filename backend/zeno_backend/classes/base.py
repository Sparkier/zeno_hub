"""Base types used in Zeno's backend."""
from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict


def to_camel(string: str) -> str:
    """Converter for variables from snake_case to camelCase.

    Args:
        string (str): the variable to convert to camelCase.

    Returns:
        str: camelCase representation of the variable.
    """
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class CamelModel(BaseModel):
    """Converting snake_case pydantic models to camelCase models."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ZenoColumnType(str, Enum):
    """Enumeration of possible column types in Zeno.

    Attributes:
        DATA: Input data instance. Either raw data or filename.
        LABEL: Ground truth label.
        OUTPUT: Model output.
        FEATURE: Metadata feature for an input data instance.
        EMBEDDING: Vector embedding representing a data instance or output.
    """

    DATA = "DATA"
    LABEL = "LABEL"
    OUTPUT = "OUTPUT"
    FEATURE = "FEATURE"
    EMBEDDING = "EMBEDDING"


class MetadataType(str, Enum):
    """Enumeration of possible metadata types in Zeno.

    Attributes:
        NOMINAL: Nominal metadata type, e.g. string or small cardinality number.
        CONTINUOUS: Continuous metadata type, e.g. large cardinality number.
        BOOLEAN: Boolean metadata type, e.g. True or False.
        DATETIME: Datetime metadata type, e.g. 2021-01-01 00:00:00.
        OTHER: Any other metadata type, e.g. strings.
    """

    NOMINAL = "NOMINAL"
    CONTINUOUS = "CONTINUOUS"
    BOOLEAN = "BOOLEAN"
    DATETIME = "DATETIME"
    OTHER = "OTHER"

    def __str__(self) -> str:
        """Get a SQL representation for a metadata type.

        Returns:
            str: the sql data type corresponding to the metadata type.
        """
        if self == MetadataType.BOOLEAN:
            return "BOOLEAN"
        if self == MetadataType.CONTINUOUS:
            return "NUMERIC"
        if self == MetadataType.DATETIME:
            return "DATETIME"
        return "TEXT"


class Project(CamelModel):
    """Projects with datasets & models.

    Attributes:
        uuid (str): UUID of the task.
        name (str): name of the task.
        view (str): name of the view to use for the task.
        calculate_histogram_metrics (bool): whether to calculate histogram metrics.
        samples_per_page (int): number of items to show per page.
        public (bool): whether the task is public.
        editor (bool): whether the current user is an editor of the project.
    """

    uuid: str
    name: str
    view: str
    calculate_histogram_metrics: bool = True
    samples_per_page: int = 10
    editor: bool
    public: bool


class ProjectStats(CamelModel):
    """Statistical numbers of a Zeno project.

    Attributes:
        num_instances (int): number of data instances in the project.
        num_charts (int): number of charts that have been created for the project.
        num_models (int): number of models associated with the project
    """

    num_instances: int
    num_charts: int
    num_models: int


class ZenoColumn(CamelModel):
    """Representation of a column in Zeno's project data."""

    id: str
    name: str
    column_type: ZenoColumnType
    data_type: MetadataType
    model: Optional[str] = None


class LabelSpec(CamelModel):
    """Specification for a label in Zeno's project data."""

    item: str
    label: str


class OutputSpec(CamelModel):
    """Specification for a model output in Zeno's project data."""

    item: str
    output: str
    model: str


class FeatureSpec(CamelModel):
    """Specification for metadata in Zeno."""

    col_name: str
    value: Any = None
    item: str
    type: MetadataType
    model: Optional[str] = None


class GroupMetric(CamelModel):
    """Specification for a metric on a group of items."""

    metric: Union[float, None] = None
    size: int
