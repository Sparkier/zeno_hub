CREATE TABLE users (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL UNIQUE
    api_key text NOT NULL UNIQUE,
);

CREATE TABLE projects (
    uuid text PRIMARY KEY,
    name text NOT NULL,
    owner_id integer NOT NULL REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    view text NOT NULL,
    data_url text,
    calculate_histogram_metrics boolean NOT NULL DEFAULT false,
    samples_per_page integer NOT NULL DEFAULT 10,
    public boolean NOT NULL DEFAULT false
);

CREATE TABLE organizations (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL
);

CREATE TABLE metrics (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL
);

CREATE TABLE folders (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL,
    project_uuid text NOT NULL REFERENCES projects(uuid) ON DELETE CASCADE
);

CREATE TABLE charts (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_uuid text NOT NULL REFERENCES projects(uuid) ON DELETE CASCADE ON UPDATE CASCADE,
    name text NOT NULL,
    type text NOT NULL,
    parameters text NOT NULL
);

CREATE TABLE slices (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL,
    folder_id integer REFERENCES folders(id) ON DELETE SET NULL ON UPDATE CASCADE,
    filter text,
    project_uuid text NOT NULL REFERENCES projects(uuid) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE tags (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL,
    folder_id integer REFERENCES folders(id) ON DELETE CASCADE ON UPDATE CASCADE,
    project_uuid text NOT NULL REFERENCES projects(uuid) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE user_project (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id integer NOT NULL REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    project_uuid text NOT NULL REFERENCES projects(uuid) ON DELETE CASCADE ON UPDATE CASCADE,
    editor boolean NOT NULL DEFAULT false
);

CREATE TABLE user_organization (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id integer NOT NULL REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    organization_id integer NOT NULL REFERENCES organizations(id) ON DELETE CASCADE ON UPDATE CASCADE,
    admin boolean NOT NULL DEFAULT false
);

CREATE TABLE project_metrics (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_uuid text NOT NULL REFERENCES projects(uuid) ON DELETE CASCADE,
    metric_id integer NOT NULL REFERENCES metrics(id)
);

CREATE TABLE organization_project (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    organization_id integer NOT NULL REFERENCES organizations(id) ON DELETE CASCADE ON UPDATE CASCADE,
    project_uuid text NOT NULL REFERENCES projects(uuid) ON DELETE CASCADE ON UPDATE CASCADE,
    editor boolean NOT NULL DEFAULT false
);
