"""Functions for extracting chart data from SQL."""
import json
from typing import Any

from zeno_backend.classes.chart import (
    BeeswarmParameters,
    Chart,
    ChartType,
    HeatmapParameters,
    RadarParameters,
    SlicesMetricsOrModels,
    SlicesOrModels,
    TableParameters,
    XCParameters,
)
from zeno_backend.classes.filter import FilterPredicateGroup, Join
from zeno_backend.classes.metric import Metric
from zeno_backend.classes.slice import Slice
from zeno_backend.database.select import metrics, slices
from zeno_backend.processing.metrics.map import metric_map


def xyc_data(chart: Chart, project: str) -> str:
    """Generate data for a chart that is based on x, y, and color values.

    Args:
        chart (Chart): the chart for which to generate data.
        project (str): the project the user is currently working with

    Returns:
        str: the chart data in JSON representation.
    """
    elements: list[dict[str, Any]] = []
    if not (isinstance(chart.parameters, XCParameters)):
        return json.dumps({"table": elements})

    all_metrics = metrics(project)
    selected_metric = next(
        (x for x in all_metrics if x.id == chart.parameters.metric),
        Metric(id=-1, name="count", type="count", columns=[]),
    )

    selected_slices = slices(project, chart.parameters.slices)
    if -1 in chart.parameters.slices:
        selected_slices = selected_slices + [
            Slice(
                id=-1,
                slice_name="All instances",
                filter_predicates=FilterPredicateGroup(
                    predicates=[], join=Join.OMITTED
                ),
            )
        ]

    selected_models = chart.parameters.models
    for current_slice in selected_slices:
        for model in selected_models:
            metric = metric_map(
                project, selected_metric, model, current_slice.filter_predicates
            )
            elements.append(
                {
                    "x_value": current_slice.slice_name
                    if chart.parameters.x_channel == SlicesOrModels.SLICES
                    else model,
                    "color_value": model
                    if chart.parameters.color_channel == SlicesOrModels.MODELS
                    else current_slice.slice_name,
                    "y_value": metric.metric,
                    "size": metric.size,
                }
            )

    return json.dumps({"table": elements})


def table_data(chart: Chart, project: str) -> str:
    """Generate data for a tabular visualization.

    Args:
        chart (Chart): the chart for which to generate data.
        project (str): the project the user is currently working with

    Returns:
        str: the chart data in JSON representation.
    """
    elements: list[dict[str, Any]] = []
    params = chart.parameters
    if not isinstance(params, TableParameters):
        return json.dumps({"table": elements})
    selected_metrics = list(
        filter(
            lambda metric: metric.id in params.metrics,
            metrics(project) + [Metric(id=-1, name="count", type="count", columns=[])],
        )
    )
    selected_slices = slices(project, params.slices)
    if -1 in params.slices:
        selected_slices = selected_slices + [
            Slice(
                id=-1,
                slice_name="All instances",
                filter_predicates=FilterPredicateGroup(
                    predicates=[], join=Join.OMITTED
                ),
            )
        ]
    selected_models = params.models

    for current_metric in selected_metrics:
        for current_slice in selected_slices:
            for model in selected_models:
                metric = metric_map(
                    project, current_metric, model, current_slice.filter_predicates
                )
                elements.append(
                    {
                        "x_value": current_slice.id
                        if params.x_channel == SlicesMetricsOrModels.SLICES
                        else model
                        if params.x_channel == SlicesMetricsOrModels.MODELS
                        else current_metric.id,
                        "fixed_value": metric.metric,
                        "y_value": current_slice.id
                        if params.y_channel == SlicesOrModels.SLICES
                        else model,
                        "size": metric.size,
                    }
                )
    return json.dumps({"table": elements})


def beeswarm_data(chart: Chart, project: str) -> str:
    """Generate data for a beeswarm visualization.

    Args:
        chart (Chart): the chart for which to generate data.
        project (str): the project the user is currently working with

    Returns:
        str: the chart data in JSON representation.
    """
    elements: list[dict[str, Any]] = []
    params = chart.parameters
    if not (isinstance(params, BeeswarmParameters)):
        return json.dumps({"table": elements})
    selected_metrics = list(
        filter(
            lambda metric: metric.id in params.metrics,
            metrics(project) + [Metric(id=-1, name="count", type="count", columns=[])],
        )
    )
    selected_slices = slices(project, params.slices)
    if -1 in params.slices:
        selected_slices = selected_slices + [
            Slice(
                id=-1,
                slice_name="All instances",
                filter_predicates=FilterPredicateGroup(
                    predicates=[], join=Join.OMITTED
                ),
            )
        ]
    selected_models = params.models

    for current_metric in selected_metrics:
        for current_slice in selected_slices:
            for model in selected_models:
                metric = metric_map(
                    project, current_metric, model, current_slice.filter_predicates
                )
                elements.append(
                    {
                        "color_value": current_slice.slice_name
                        if params.color_channel == SlicesOrModels.SLICES
                        else model,
                        "x_value": metric.metric,
                        "y_value": current_slice.slice_name
                        if params.y_channel == SlicesOrModels.SLICES
                        else model,
                        "size": metric.size,
                        "metric": current_metric.name,
                    }
                )
    return json.dumps({"table": elements})


def radar_data(chart: Chart, project: str) -> str:
    """Generate data for a radar chart.

    Args:
        chart (Chart): the chart for which to generate data.
        project (str): the project the user is currently working with

    Returns:
        str: the chart data in JSON representation.
    """
    elements: list[dict[str, Any]] = []
    params = chart.parameters
    if not (isinstance(params, RadarParameters)):
        return json.dumps({"table": elements})
    selected_metrics = list(
        filter(
            lambda metric: metric.id in params.metrics,
            metrics(project) + [Metric(id=-1, name="count", type="count", columns=[])],
        )
    )
    selected_slices = slices(project, params.slices)
    if -1 in params.slices:
        selected_slices = selected_slices + [
            Slice(
                id=-1,
                slice_name="All instances",
                filter_predicates=FilterPredicateGroup(
                    predicates=[], join=Join.OMITTED
                ),
            )
        ]
    selected_models = params.models

    for current_metric in selected_metrics:
        for current_slice in selected_slices:
            for model in selected_models:
                metric = metric_map(
                    project, current_metric, model, current_slice.filter_predicates
                )
                elements.append(
                    {
                        "axis_value": current_slice.slice_name
                        if params.axis_channel == SlicesMetricsOrModels.SLICES
                        else model
                        if params.axis_channel == SlicesMetricsOrModels.MODELS
                        else current_metric.name,
                        "fixed_value": metric.metric,
                        "layer_value": current_slice.slice_name
                        if params.layer_channel == SlicesOrModels.SLICES
                        else model,
                        "size": metric.size,
                    }
                )
    return json.dumps({"table": elements})


def heatmap_data(chart: Chart, project: str) -> str:
    """Generate data for a heatmap visualization.

    Args:
        chart (Chart): the chart for which to generate data.
        project (str): the project the user is currently working with

    Returns:
        str: the chart data in JSON representation.
    """
    elements: list[dict[str, Any]] = []
    params = chart.parameters
    if not (isinstance(params, HeatmapParameters)):
        return json.dumps({"table": elements})
    selected_metric = next(
        (x for x in metrics(project) if x.id == params.metric),
        Metric(id=-1, name="count", type="count", columns=[]),
    )
    x_slice = params.x_channel == SlicesOrModels.SLICES
    y_slice = params.y_channel == SlicesOrModels.SLICES
    selected_x = (
        slices(project, params.x_values) if x_slice else params.x_values  # type: ignore
    )
    if x_slice and -1 in params.x_values:
        selected_x = selected_x + [
            Slice(
                id=-1,
                slice_name="All instances",
                filter_predicates=FilterPredicateGroup(
                    predicates=[], join=Join.OMITTED
                ),
            )
        ]

    selected_y = (
        slices(project, params.y_values) if y_slice else params.y_values  # type: ignore
    )
    if y_slice and -1 in params.y_values:
        selected_y = selected_y + [
            Slice(
                id=-1,
                slice_name="All instances",
                filter_predicates=FilterPredicateGroup(
                    predicates=[], join=Join.OMITTED
                ),
            )
        ]

    for current_x in selected_x:
        for current_y in selected_y:
            metric = {"metric": None, "size": 0}
            if x_slice and y_slice:
                current_y.filter_predicates.join = Join.AND  # type: ignore
                metric = metric_map(
                    project,
                    selected_metric,
                    params.model,
                )
            else:
                metric = metric_map(
                    project,
                    selected_metric,
                    params.model,
                    FilterPredicateGroup(
                        predicates=[
                            current_x.filter_predicates,  # type: ignore
                            current_y.filter_predicates,  # type: ignore
                        ],
                        join=Join.OMITTED,
                    ),
                )
            elements.append(
                {
                    "x_value": current_x.slice_name  # type: ignore
                    if x_slice
                    else current_x,
                    "fixed_value": metric.metric,
                    "y_value": current_y.slice_name  # type: ignore
                    if y_slice
                    else current_y,
                    "size": metric.size,
                }
            )
    return json.dumps({"table": elements})


def chart_data(chart: Chart, project: str) -> str:
    """Extract the chart data for a specific chart that the user created.

    Args:
        chart (Chart): the chart for which to extract the data.
        project (str): the project the user is currently working with

    Returns:
        str: JSON representation of the chart data the user requested.
    """
    if chart.type == ChartType.BAR or chart.type == ChartType.LINE:
        return xyc_data(chart, project)
    elif chart.type == ChartType.TABLE:
        return table_data(chart, project)
    elif chart.type == ChartType.BEESWARM:
        return beeswarm_data(chart, project)
    elif chart.type == ChartType.RADAR:
        return radar_data(chart, project)
    elif chart.type == ChartType.HEATMAP:
        return heatmap_data(chart, project)
    else:
        return json.dumps({"table": []})
