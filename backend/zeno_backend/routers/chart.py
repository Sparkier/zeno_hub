"""FastAPI server endpoints for data-table-related queries."""

from amplitude import BaseEvent
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)

import zeno_backend.database.delete as delete
import zeno_backend.database.insert as insert
import zeno_backend.database.select as select
import zeno_backend.database.update as update
import zeno_backend.util as util
from zeno_backend.classes.amplitude import AmplitudeHandler
from zeno_backend.classes.chart import Chart, ChartConfig
from zeno_backend.processing.chart import calculate_chart_data

router = APIRouter(tags=["zeno"])


@router.get(
    "/charts/{project_uuid}",
    response_model=list[Chart],
    tags=["zeno"],
)
async def get_charts(project_uuid: str, request: Request):
    """Get all charts of a project.

    Args:
        project_uuid (str): UUID of the project to get all charts for.
        request (Request): http request to get user information from.

    Returns:
        list[Chart]: list of all of a project's charts.
    """
    await util.project_access_valid(project_uuid, request)
    return await select.charts(project_uuid)


@router.get(
    "/chart/{project}/{chart_id}",
    response_model=Chart,
    tags=["zeno"],
)
async def get_chart(project_uuid: str, chart_id: int, request: Request):
    """Get a chart by its id.

    Args:
        project_uuid (str): UUID of the project to get a chart from.
        chart_id (int): id of the chart to be fetched.
        request (Request): http request to get user information from.

    Raises:
        HTTPException: error if the chart could not be fetched.

    Returns:
        ChartResponse: chart spec.
    """
    await util.project_access_valid(project_uuid, request)
    return await select.chart(chart_id)


@router.get("/chart-data/{project_uuid}/{chart_id}", response_model=str, tags=["Zeno"])
async def get_chart_data(project_uuid, chart_id: int, request: Request):
    """Get a chart's data.

    Args:
        project_uuid (str): UUID of the project to get a chart from.
        chart_id (int): id of the chart to be fetched.
        request (Request): http request to get user information from.

    Raises:
        HTTPException: error if the chart could not be fetched.

    Returns:
        str: chart data.
    """
    await util.project_access_valid(project_uuid, request)
    data = await select.chart_data(chart_id)
    if data is None:
        chart = await select.chart(chart_id)
        data = await calculate_chart_data(chart, project_uuid)
        await update.chart_data(chart_id, data)
    return data


@router.post("/chart-config/{project_uuid}", response_model=ChartConfig, tags=["zeno"])
async def get_chart_config(
    project_uuid: str, request: Request, chart_id: int | None = None
):
    """Get a project's chart configuration.

    Args:
        project_uuid (str): uuid of the project for which to get the configuration.
        chart_id (int | None): the id of the chart this is linked to. Defaults to None.
        request (Request): http request to get user information from.

    Returns:
        ChartConfig: the configuration of all charts in the project.
    """
    await util.project_access_valid(project_uuid, request)
    config = await select.chart_config(project_uuid)
    config = ChartConfig(project_uuid=project_uuid) if config is None else config
    if chart_id is not None:
        chart_config = await select.chart_config(project_uuid, chart_id)
        config = config if chart_config is None else {**config, **chart_config}  # type: ignore
    return config


@router.post(
    "/charts-for-projects/",
    response_model=list[Chart],
    tags=["zeno"],
)
async def get_charts_for_projects(project_uuids: list[str], request: Request):
    """Get all charts for a list of projects.

    Args:
        project_uuids (list[str]): list of UUIDs of projects to fetch all charts for.
        request (Request): http request to get user information from.

    Returns:
        list[Chart]: all charts for the list of projects
    """
    if len(project_uuids) == 0:
        return []

    for project_uuid in project_uuids:
        await util.project_access_valid(project_uuid, request)
    charts = await select.charts_for_projects(project_uuids)
    return charts


@router.post(
    "/chart/{project_uuid}",
    response_model=int,
    tags=["zeno"],
)
async def add_chart(
    project_uuid: str,
    chart: Chart,
    request: Request,
    current_user=Depends(util.auth.claim()),
):
    """Add a new chart to a project.

    Args:
        project_uuid (str): UUID of the project to add a chart to.
        chart (Chart): chart to be added to the project.
        request (Request): http request to get user information from.
        current_user (Any, optional): user making the addition of the chart.
            Defaults to Depends(util.auth.claim()).

    Raises:
        HTTPException: error if the chart could not be added.

    Returns:
        int: id of the newly added chart.
    """
    await util.project_editor(project_uuid, request)
    id = await insert.chart(project_uuid, chart)
    if id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to insert chart",
        )
    AmplitudeHandler().track(
        BaseEvent(
            event_type="Chart Created",
            user_id=current_user["sub"],
            event_properties={"project_uuid": project_uuid},
        )
    )
    return id


@router.patch(
    "/chart/{project_uuid}",
    tags=["zeno"],
    dependencies=[Depends(util.auth)],
)
async def update_chart(project_uuid: str, chart: Chart, request: Request):
    """Update a chart.

    Args:
        chart (Chart): new chart data.
        project_uuid (str): UUID of the project that holds the chart.
        request (Request): http request to get user information from.
    """
    await util.project_editor(project_uuid, request)
    selected_chart = await select.chart(chart.id)
    if selected_chart.project_uuid == project_uuid:
        await update.chart(chart, project_uuid)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Project UUID does not match chart's project UUID.",
        )


@router.patch("/chart-config", tags=["zeno"], dependencies=[Depends(util.auth)])
async def update_chart_config(
    chart_config: ChartConfig, request: Request, chart_id: int | None = None
):
    """Update or add a chart configuration for a project.

    Args:
        chart_config (ChartConfig): chart configuration to be written.
        request (Request): http request to get user information from.
        chart_id (int | None): the id of the chart this is linked to. Defaults to None.
    """
    await util.project_editor(chart_config.project_uuid, request)
    if await select.chart_config(chart_config.project_uuid, chart_id) is not None:
        await update.chart_config(chart_config, chart_id)
    else:
        await insert.chart_config(chart_config, chart_id)


@router.delete(
    "/chart/{project_uuid}/{chart_id}", tags=["zeno"], dependencies=[Depends(util.auth)]
)
async def delete_chart(project_uuid: str, chart_id: int, request: Request):
    """Delete a chart from the database.

    Args:
        project_uuid (str): project to which the chart belongs.
        chart_id (int): id of the chart to be deleted.
        request (Request): http request to get user information from.
    """
    await util.project_editor(project_uuid, request)
    chart = await select.chart(chart_id)
    if chart.project_uuid == project_uuid:
        await delete.chart(chart_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Project UUID does not match chart's project UUID.",
        )


@router.delete(
    "/chart-config/{project_uuid}", tags=["zeno"], dependencies=[Depends(util.auth)]
)
async def delete_chart_config(
    project_uuid: str, request: Request, chart_id: int | None = None
):
    """Delete the chart config for a project.

    Args:
        project_uuid (str): uuid of the project to delete the chart config for.
        request (Request): http request to get the user information from.
        chart_id (int | None): the id of the chart this is linked to. Defaults to None.
    """
    await util.project_editor(project_uuid, request)
    await delete.chart_config(project_uuid, chart_id)
