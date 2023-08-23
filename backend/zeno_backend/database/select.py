"""Functions to select data from the database."""
import json
import re
from operator import itemgetter

from psycopg import DatabaseError, sql

from zeno_backend.classes.base import ZenoColumn
from zeno_backend.classes.chart import Chart
from zeno_backend.classes.filter import FilterPredicateGroup, Join
from zeno_backend.classes.folder import Folder
from zeno_backend.classes.metadata import StringFilterRequest
from zeno_backend.classes.metric import Metric
from zeno_backend.classes.project import Project, ProjectStats
from zeno_backend.classes.slice import Slice
from zeno_backend.classes.slice_finder import SQLTable
from zeno_backend.classes.tag import Tag
from zeno_backend.classes.user import Organization, User
from zeno_backend.database.database import Database


def models(project: str) -> list[str]:
    """Get all models for a specified project.

    Args:
        project (str): the project the user is currently working with.

    Returns:
        list[str]: a list of model names included in the project.
    """
    db = Database()
    model_results = db.connect_execute_return(
        sql.SQL("SELECT DISTINCT model FROM {} WHERE model IS NOT NULL;").format(
            sql.Identifier(f"{project}_column_map")
        ),
        return_all=True,
    )
    return list(map(itemgetter(0), model_results)) if model_results is not None else []


def projects(user: User) -> list[Project]:
    """Get all projects available to the user.

    Args:
        user (User): the user for which to fetch the available projects.

    Returns:
        list[Project]: the projects that the user can interact with.
    """
    db = Database()
    try:
        db.connect()
        own_projects_result = db.execute_return(
            "SELECT uuid, name, view, data_url, calculate_histogram_metrics, "
            "samples_per_page, public FROM projects WHERE owner_id = %s;",
            [user.id],
            return_all=True,
        )
        own_projects = (
            list(
                map(
                    lambda project: Project(
                        uuid=project[0],
                        name=project[1],
                        owner_name=user.name,
                        view=project[2],
                        data_url=project[3],
                        calculate_histogram_metrics=bool(project[4]),
                        samples_per_page=project[5],
                        editor=True,
                        public=project[6],
                    ),
                    own_projects_result,
                )
            )
            if own_projects_result is not None
            else []
        )

        user_projects_result = db.execute_return(
            "SELECT p.uuid, p.name, p.owner_id, p.view, p.data_url, "
            "p.calculate_histogram_metrics, p.samples_per_page, up.editor, p.public "
            "FROM projects AS p JOIN user_project AS up ON p.uuid = up.project_uuid "
            "WHERE up.user_id = %s;",
            [user.id],
            return_all=True,
        )
        user_projects = []
        if user_projects_result is not None:
            for res in user_projects_result:
                owner_name = db.execute_return(
                    "SELECT name FROM users WHERE id = %s", [res[2]]
                )
                if owner_name is not None:
                    owner_name = owner_name[0]
                    user_projects.append(
                        Project(
                            uuid=res[0],
                            name=res[1],
                            owner_name=str(owner_name),
                            view=res[3],
                            data_url=res[4],
                            calculate_histogram_metrics=bool(res[5]),
                            samples_per_page=res[6],
                            editor=res[7],
                            public=res[8],
                        )
                    )

        project_org_result = db.execute_return(
            "SELECT p.uuid, p.name, p.owner_id, p.view, p.calculate_histogram_metrics,"
            " p.data_url, p.samples_per_page, op.editor, p.public FROM projects AS p "
            "JOIN (SELECT op.project_uuid, uo.organization_id, editor "
            "FROM user_organization as uo JOIN organization_project as op"
            " ON uo.organization_id = op.organization_id "
            "WHERE user_id = %s) AS op ON p.uuid = op.project_uuid;",
            [user.id],
            return_all=True,
        )
        org_projects = []
        if project_org_result is not None:
            for res in project_org_result:
                owner_name = db.execute_return(
                    "SELECT name FROM users WHERE id = %s", [res[2]]
                )
                if owner_name is not None:
                    owner_name = owner_name[0]
                    org_projects.append(
                        Project(
                            uuid=res[0],
                            name=res[1],
                            owner_name=str(owner_name),
                            view=res[3],
                            calculate_histogram_metrics=bool(res[4]),
                            data_url=res[5],
                            samples_per_page=res[6],
                            editor=res[7],
                            public=res[8],
                        )
                    )
        org_projects = list(
            filter(
                lambda project: not any(p.uuid == project.uuid for p in user_projects)
                and not any(p.uuid == project.uuid for p in own_projects),
                org_projects,
            )
        )
        return own_projects + user_projects + org_projects
    except (Exception, DatabaseError) as error:
        raise Exception(error) from error
    finally:
        db.disconnect()


def project_uuid(owner_name: str, project_name: str) -> str | None:
    """Get the project uuid given an owner and project name.

    Args:
        owner_name (str): The name of the owner of the project.
        project_name (str): The name of the project.

    Returns:
        str | None: The uuid of the requested project.
    """
    db = Database()
    try:
        db.connect()
        owner_id = db.execute_return(
            "SELECT id FROM users WHERE name = %s;", [owner_name]
        )
        if owner_id is None:
            raise Exception("Owner does not exist.")
        else:
            owner_id = owner_id[0]

        project_uuid = db.execute_return(
            "SELECT uuid FROM projects WHERE name = %s AND owner_id = %s;",
            [project_name, owner_id],
        )
        return str(project_uuid[0]) if project_uuid is not None else None
    except (Exception, DatabaseError) as error:
        raise Exception(error) from error
    finally:
        db.disconnect()


def project(owner_name: str, project_name: str, user: User) -> Project | None:
    """Get the project data given an owner and project name.

    Args:
        owner_name (str): The name of the project owner.
        project_name (str): The name of the project.
        user (User): The user making the request.

    Returns:
        Project | None: the data for the requested project.
    """
    db = Database()
    try:
        db.connect()

        owner_id = db.execute_return(
            "SELECT id FROM users WHERE name = %s;", [owner_name]
        )
        if owner_id is None:
            raise Exception("Owner does not exist.")
        else:
            owner_id = owner_id[0]

        project_result = db.execute_return(
            "SELECT uuid, name, owner_id, view, data_url, calculate_histogram_metrics, "
            "samples_per_page, public FROM projects WHERE name = %s AND owner_id = %s;",
            [project_name, owner_id],
        )
        if project_result is None:
            raise Exception("Project does not exist.")
        project_uuid = project_result[0][0]

        if owner_name == user.name:
            # Owners can always edit projects
            editor = True
        else:
            # Check whether the user or an org of the user have project edit rights
            user_editor = db.execute_return(
                "SELECT editor FROM user_project WHERE user_id = %s "
                "AND project_uuid = %s",
                [user.id, project_uuid],
            )
            org_editor = db.execute_return(
                "SELECT editor FROM organization_project AS p JOIN user_organization "
                "AS o ON p.organization_id = o.organization_id "
                "WHERE p.project_uuid = %s AND o.user_id = %s",
                [project_uuid, user.id],
            )
            editor = (bool(org_editor[0]) if org_editor is not None else False) or (
                bool(user_editor) if user_editor is not None else False
            )

        return (
            Project(
                uuid=str(project_result[0]),
                name=str(project_result[1]),
                owner_name=owner_name,
                view=str(project_result[3]),
                data_url=str(project_result[4]),
                calculate_histogram_metrics=bool(project_result[5]),
                samples_per_page=project_result[6]
                if isinstance(project_result[6], int)
                else 10,
                editor=editor,
                public=bool(project_result[7]),
            )
            if project_result is not None
            else None
        )
    except (Exception, DatabaseError) as error:
        raise Exception(error) from error
    finally:
        db.disconnect()


def project_from_uuid(project_uuid: str) -> Project | None:
    """Get the project data given a UUID.

    Args:
        project_uuid (str): the uuid of the project to be fetched.

    Returns:
        Project | None: data for the requested project.
    """
    db = Database()
    try:
        db.connect()
        project_result = db.execute_return(
            "SELECT uuid, name, owner_id, view, "
            "data_url, calculate_histogram_metrics, samples_per_page, public "
            "FROM projects WHERE uuid = %s;",
            [project_uuid],
        )
        if project_result is None:
            raise Exception("Project does not exist.")
        owner_result = db.execute_return(
            "SELECT name from users WHERE id = %s;", [project_result[2]]
        )
        if owner_result is not None:
            return Project(
                uuid=str(project_result[0]),
                name=str(project_result[1]),
                owner_name=str(owner_result[0]),
                view=str(project_result[3]),
                data_url=str(project_result[4]),
                editor=False,
                calculate_histogram_metrics=bool(project_result[5]),
                samples_per_page=project_result[6]
                if isinstance(project_result[6], int)
                else 10,
                public=bool(project_result[7]),
            )
    except (Exception, DatabaseError) as error:
        raise Exception(error) from error
    finally:
        db.disconnect()


def project_stats(project: str) -> ProjectStats | None:
    """Get statistics for a specified project.

    Args:
        project (str): uuid of the project to get statistics for.

    Returns:
        ProjectStats | None: statistics of the specified project.
    """
    db = Database()
    try:
        db.connect()
        num_instances = db.execute_return(
            sql.SQL("SELECT COUNT(*) FROM {};").format(sql.Identifier(project))
        )
        num_charts = db.execute_return(
            "SELECT COUNT(*) FROM charts " "WHERE project_uuid = %s;", [project]
        )
        num_models = db.execute_return(
            sql.SQL("SELECT COUNT(DISTINCT model) " "FROM {};").format(
                sql.Identifier(f"{project}_column_map")
            )
        )
        return (
            ProjectStats(
                num_instances=num_instances[0]
                if isinstance(num_instances[0], int)
                else 0,
                num_charts=num_charts[0] if isinstance(num_charts[0], int) else 0,
                num_models=num_models[0] if isinstance(num_models[0], int) else 0,
            )
            if num_charts is not None
            and num_instances is not None
            and num_models is not None
            else None
        )
    except (Exception, DatabaseError) as error:
        raise Exception(error) from error
    finally:
        db.disconnect()


def metrics(project: str) -> list[Metric]:
    """Get a list of all metrics that are used in the project.

    Args:
        project (str): the project the user is currently working with.

    Returns:
        list[Metric]: list of metrics used with the project.
    """
    db = Database()
    metric_results = db.connect_execute_return(
        "SELECT metrics.id, metrics.name FROM metrics INNER JOIN project_metrics ON "
        "metrics.id = project_metrics.metric_id "
        "WHERE project_metrics.project_uuid = %s;",
        [
            project,
        ],
        return_all=True,
    )
    return (
        list(map(lambda metric: Metric(id=metric[0], name=metric[1]), metric_results))
        if metric_results is not None
        else []
    )


def folders(project: str) -> list[Folder]:
    """Get a list of all folders in a project.

    Args:
        project (str): the project the user is currently working with.

    Returns:
        list[Folder]: list of folders created in the project.
    """
    db = Database()
    folder_results = db.connect_execute_return(
        "SELECT id, name, project_uuid FROM folders WHERE project_uuid = %s;",
        [
            project,
        ],
        return_all=True,
    )
    return (
        list(
            map(
                lambda folder: Folder(id=folder[0], name=folder[1]),
                folder_results,
            )
        )
        if folder_results is not None
        else []
    )


def folder(id: int) -> Folder | None:
    """Get a single folder by its ID.

    Args:
        id (int): id of the folder to be fetched.

    Returns:
        Folder | None: Folder as requested by the user.
    """
    db = Database()
    folder_result = db.connect_execute_return(
        "SELECT id, name, project_uuid FROM folders WHERE id = %s;",
        [
            id,
        ],
    )
    return (
        Folder(
            id=folder_result[0] if isinstance(folder_result[0], int) else 0,
            name=str(folder_result[1]),
        )
        if folder_result is not None
        else None
    )


def slices(project: str, ids: list[int] | None = None) -> list[Slice]:
    """Get a list of all slices of a project with certain IDs.

    Args:
        project (str): the project the user is currently working with.
        ids (list[int] | None, optional): Limited list of slice IDs to fetch from,
        using all slices of the project if None. Defaults to None.

    Returns:
        list[Slice]: list of requested slices.
    """
    if ids is not None and len(ids) == 0:
        return []
    db = Database()
    if ids is None:
        slice_results = db.connect_execute_return(
            "SELECT id, name, folder_id, filter FROM slices WHERE project_uuid = %s;",
            [
                project,
            ],
            return_all=True,
        )
    else:
        slice_results = db.connect_execute_return(
            "SELECT id, name, folder_id, filter FROM slices "
            "WHERE project_uuid = %s AND id = ANY(%s);",
            [
                project,
                ids,
            ],
            return_all=True,
        )
    return (
        list(
            map(
                lambda slice: Slice(
                    id=slice[0],
                    slice_name=slice[1],
                    folder_id=slice[2],
                    filter_predicates=FilterPredicateGroup(
                        predicates=json.loads(slice[3])["predicates"],
                        join=Join.OMITTED,
                    ),
                ),
                slice_results,
            )
        )
        if slice_results is not None
        else []
    )


def charts(project: str) -> list[Chart]:
    """Get a list of all charts created in the project.

    Args:
        project (str): the project the user is currently working with.

    Returns:
        list[Chart]: list of all the charts in the project.
    """
    db = Database()
    chart_results = db.connect_execute_return(
        "SELECT id, name, type, parameters FROM charts WHERE project_uuid = %s;",
        [
            project,
        ],
        return_all=True,
    )
    return (
        list(
            map(
                lambda chart: Chart(
                    id=chart[0],
                    name=chart[1],
                    type=chart[2],
                    parameters=json.loads(chart[3]),
                ),
                chart_results,
            )
        )
        if chart_results is not None
        else []
    )


def columns(project: str) -> list[ZenoColumn]:
    """Get a list of all columns in the project's data table.

    Args:
        project (str): the project the user is currently working with.

    Returns:
        list[ZenoColumn]: list of all the project's data columns.
    """
    db = Database()
    column_results = db.connect_execute_return(
        sql.SQL("SELECT column_id, name, type, model, data_type FROM {};").format(
            sql.Identifier(f"{project}_column_map")
        ),
        return_all=True,
    )
    return (
        (
            list(
                map(
                    lambda column: ZenoColumn(
                        id=column[0],
                        name=column[1],
                        column_type=column[2],
                        model=column[3],
                        data_type=column[4],
                    ),
                    column_results,
                )
            )
        )
        if column_results is not None
        else []
    )


def table_data_paginated(
    project: str, filter_sql: sql.Composed | None, offset: int, limit: int
) -> SQLTable:
    """Get a slice of the data saved in the project table.

    Args:
        project (str): the project the user is currently working with.
        filter_sql (sql.Composed | None): filter to apply before fetching a slice of
        the data.
        offset (int): where in the remaining data to start extracting the slice.
        limit (int): maximum slice length to be extracted.

    Raises:
        Exception: something failed while reading the data from the database.

    Returns:
        SQLTable: the resulting slice of the data as requested by the user.
    """
    db = Database()
    try:
        filter_results = None
        columns = []
        db.connect()
        if filter_sql is None:
            if db.cur is not None:
                db.cur.execute(
                    sql.SQL(
                        "SELECT * FROM {} ORDER BY data_id LIMIT %s OFFSET %s;"
                    ).format(sql.Identifier(f"{project}")),
                    [
                        limit,
                        offset,
                    ],
                )
                if db.cur.description is not None:
                    columns = [desc[0] for desc in db.cur.description]
                filter_results = db.cur.fetchall()
        else:
            if db.cur is not None:
                db.cur.execute(
                    sql.SQL("SELECT * FROM {} WHERE ").format(sql.Identifier(project))
                    + filter_sql
                    + sql.SQL("ORDER BY data_id LIMIT {} OFFSET {};").format(
                        sql.Literal(limit), sql.Literal(offset)
                    )
                )
                if db.cur.description is not None:
                    columns = [desc[0] for desc in db.cur.description]
                filter_results = db.cur.fetchall()
        return (
            SQLTable(table=filter_results, columns=columns)
            if filter_results is not None
            else SQLTable(table=[], columns=[])
        )
    except (Exception, DatabaseError) as error:
        raise Exception(error) from error
    finally:
        db.disconnect()


def table_data(project: str, filter_sql: sql.Composed | None) -> SQLTable:
    """Get the filtered data table for the current project.

    Args:
        project (str): the project the user is currently working with.
        filter_sql (sql.Composed | None): filters to apply to the fetched data.

    Raises:
        Exception: something failed while reading the data from the database.

    Returns:
        SQLTable: the filtered data table for the project.
    """
    db = Database()
    try:
        filter_results = None
        columns = []
        db.connect()
        if filter_sql is None:
            if db.cur is not None:
                db.cur.execute(
                    sql.SQL("SELECT * FROM {};").format(sql.Identifier(f"{project}")),
                )
                if db.cur.description is not None:
                    columns = [desc[0] for desc in db.cur.description]
                filter_results = db.cur.fetchall()
        else:
            if db.cur is not None:
                db.cur.execute(
                    sql.SQL("SELECT * FROM {} WHERE ").format(sql.Identifier(project))
                    + filter_sql
                )
                if db.cur.description is not None:
                    columns = [desc[0] for desc in db.cur.description]
                filter_results = db.cur.fetchall()
        return (
            SQLTable(table=filter_results, columns=columns)
            if filter_results is not None
            else SQLTable(table=[], columns=[])
        )
    except (Exception, DatabaseError) as error:
        raise Exception(error) from error
    finally:
        db.disconnect()


def column_id_from_name_and_model(project: str, column_name: str, model: str) -> str:
    """Get a column's id given its name and model.

    Args:
        project (str): the project the user is currently working with.
        column_name (str): the name of the column to be fetched.
        model (str): the model of the column to be fetched.

    Returns:
        str: _description_
    """
    db = Database()
    column_result = db.connect_execute_return(
        sql.SQL(
            "SELECT column_id FROM {} "
            "WHERE name = %s AND (model = %s OR model IS NULL);"
        ).format(sql.Identifier(f"{project}_column_map")),
        [column_name, model],
    )
    return str(column_result[0]) if column_result is not None else ""


def column(
    project: str, column: ZenoColumn, filter_sql: sql.Composed | None = None
) -> list[str | int | float | bool]:
    """Get the data for one column of the project's data table.

    Args:
        project (str): the project the user is currently working with.
        column (ZenoColumn): the column for which to fetch the data.
        filter_sql (sql.Composed | None, optional): Any filters to apply before
        fetching the column data. Defaults to None.

    Returns:
        list[str | int | float | bool]: the data that is stored in the requested
        column.
    """
    db = Database()
    if filter_sql is None:
        column_result = db.connect_execute_return(
            sql.SQL("SELECT {} FROM {}").format(
                sql.Identifier(column.id), sql.Identifier(project)
            ),
            return_all=True,
        )
    else:
        column_result = db.connect_execute_return(
            sql.SQL("SELECT {} FROM {} WHERE ").format(
                sql.Identifier(column.id), sql.Identifier(project)
            )
            + filter_sql,
            return_all=True,
        )
    return (
        list(map(lambda column: column[0], column_result))
        if column_result is not None
        else []
    )


def tags(project: str) -> list[Tag]:
    """Get a list of all tags created for a project.

    Args:
        project (str): the project the user is currently working with.

    Raises:
        Exception: something went wrong while extracting the tags from the database.

    Returns:
        list[Tag]: the list of tags associated with a project.
    """
    db = Database()
    try:
        db.connect()
        tags_result = db.execute_return(
            "SELECT id, name, folder_id FROM tags WHERE project_uuid = %s",
            [
                project,
            ],
            return_all=True,
        )
        if tags_result is None:
            return []
        tags: list[Tag] = []
        for tag_result in tags_result:
            data_results = db.execute_return(
                sql.SQL("SELECT data_id FROM {} WHERE tag_id = %s").format(
                    sql.Identifier(f"{project}_tags_datapoints")
                ),
                [
                    tag_result[0],
                ],
                return_all=True,
            )
            tags.append(
                Tag(
                    id=tag_result[0],
                    tag_name=tag_result[1],
                    folder_id=tag_result[2],
                    data_ids=[]
                    if data_results is None
                    else list(map(lambda d: d[0], data_results)),
                )
            )
        return tags
    except (Exception, DatabaseError) as error:
        raise Exception(error) from error
    finally:
        db.disconnect()


def user(name: str) -> User | None:
    """Get the user with a specific name.

    Args:
        name (str): the name of the user for which to fetch the user.

    Returns:
        User | None: the requested user.
    """
    db = Database()
    user = db.connect_execute_return(
        "SELECT id, name FROM users WHERE name = %s", [name]
    )
    if user is None:
        return None
    return User(
        id=user[0] if isinstance(user[0], int) else -1,
        name=str(user[1]),
        admin=None,
    )


def users() -> list[User]:
    """Get a list of all registered users.

    Returns:
        list[User]: all registered users.
    """
    db = Database()
    users = db.connect_execute_return("SELECT id, name FROM users;", return_all=True)
    return (
        list(
            map(
                lambda user: User(id=user[0], name=user[1], admin=None),
                users,
            )
        )
        if users is not None
        else []
    )


def organization_names() -> list[Organization]:
    """Get a list of all organizations.

    Returns:
        list[Organization]: all organizations in the database.
    """
    db = Database()
    organizations = db.connect_execute_return(
        "SELECT id, name FROM organizations;", return_all=True
    )
    return (
        list(
            map(
                lambda organization: Organization(
                    id=organization[0], name=organization[1], admin=False, members=[]
                ),
                organizations,
            )
        )
        if organizations is not None
        else []
    )


def organizations(user: User) -> list[Organization]:
    """Get the organizations that a user is a member of.

    Args:
        user (User): the user for which to fetch available organizations.

    Returns:
        list[Organization]: all organizations the user is a member of.
    """
    organizations: list[Organization] = []
    db = Database()
    try:
        db.connect()
        organizations_result = db.execute_return(
            "SELECT o.id, o.name, uo.admin FROM organizations AS o "
            "JOIN user_organization AS uo ON o.id = uo.organization_id "
            "WHERE uo.user_id = %s;",
            [user.id],
            return_all=True,
        )
        if organizations_result is None:
            return organizations
        for org in organizations_result:
            members = db.execute_return(
                "SELECT u.id, u.name, uo.admin FROM users as u "
                "JOIN user_organization as uo ON u.id = uo.user_id "
                "WHERE uo.organization_id = %s;",
                [org[0]],
                return_all=True,
            )
            organizations.append(
                Organization(
                    id=org[0],
                    name=org[1],
                    admin=org[2],
                    members=[]
                    if members is None
                    else list(
                        map(
                            lambda member: User(
                                id=member[0],
                                name=member[1],
                                admin=member[2],
                            ),
                            members,
                        )
                    ),
                )
            )
        return organizations
    except (Exception, DatabaseError) as error:
        raise Exception(error) from error
    finally:
        db.disconnect()


def project_users(project: str) -> list[User]:
    """Get all the users that have access to a project.

    Args:
        project (str): the project for which to get user access.

    Returns:
        list[User]: the list of users who can access the project.
    """
    db = Database()
    project_users = db.connect_execute_return(
        "SELECT u.id, u.name, up.editor FROM users as u "
        "JOIN user_project AS up ON u.id = up.user_id WHERE up.project_uuid = %s",
        [project],
        return_all=True,
    )
    return (
        list(
            map(
                lambda user: User(id=user[0], name=user[1], admin=user[2]),
                project_users,
            )
        )
        if project_users is not None
        else []
    )


def project_orgs(project: str) -> list[Organization]:
    """Get all the organizations that have access to a project.

    Args:
        project (str): the project for which to get organization access.

    Returns:
        list[User]: the list of organizations who can access the project.
    """
    db = Database()
    project_organizations = db.connect_execute_return(
        "SELECT o.id, o.name, op.editor FROM organizations as o "
        "JOIN organization_project AS op ON o.id = op.organization_id "
        "WHERE op.project_uuid = %s",
        [project],
        return_all=True,
    )
    return (
        list(
            map(
                lambda org: Organization(
                    id=org[0], name=org[1], members=[], admin=org[2]
                ),
                project_organizations,
            )
        )
        if project_organizations is not None
        else []
    )


def filered_short_string_column_values(
    project: str, req: StringFilterRequest
) -> list[str]:
    """Select distinct string values of a column and return their short representation.

    Args:
        project (str): the project for which to filter the column
        req (StringFilterRequest): the specification of the filter operation.


    Returns:
        list[str]: the filtered string column data.
    """
    db = Database()
    short_ret: list[str] = []
    if not req.is_regex:
        if not req.whole_word_match:
            req.filter_string = f"%{req.filter_string}%"
        if not req.case_match:
            req.filter_string = req.filter_string.lower()
            returned_strings = db.connect_execute_return(
                sql.SQL("SELECT {} from {} WHERE UPPER({}) LIKE %s;").format(
                    sql.Identifier(req.column.id),
                    sql.Identifier(project),
                    sql.Identifier(req.column.id),
                ),
                [
                    req.filter_string,
                ],
                return_all=True,
            )
        else:
            returned_strings = db.connect_execute_return(
                sql.SQL("SELECT {} from {} WHERE {} LIKE %s").format(
                    sql.Identifier(req.column.id),
                    sql.Identifier(project),
                    sql.Identifier(req.column.id),
                ),
                [
                    req.filter_string,
                ],
                return_all=True,
            )

        if returned_strings is None:
            return short_ret
        for result in returned_strings[0:5]:
            idx = result[0].find(req.filter_string)
            loc_str = result[0][0 if idx < 20 else idx - 20 : idx + 20]
            if len(result[0]) > 40 + len(req.filter_string):
                if idx - 20 > 0:
                    loc_str = "..." + loc_str
                if idx + 20 < len(result[0]):
                    loc_str = loc_str + "..."
            short_ret.append(loc_str)

    else:
        returned_strings = db.connect_execute_return(
            sql.SQL("SELECT {} from {} WHERE {} LIKE %s").format(
                sql.Identifier(req.column.id),
                sql.Identifier(project),
                sql.Identifier(req.column.id),
            ),
            [
                req.filter_string,
            ],
            return_all=True,
        )

        if returned_strings is None:
            return short_ret
        for result in returned_strings:
            idx = re.search(req.filter_string, result[0])
            if idx is not None:
                idx = idx.start()
                loc_str = result[0][0 if idx < 20 else idx - 20 : idx + 20]
                short_ret.append(loc_str)

    return short_ret
