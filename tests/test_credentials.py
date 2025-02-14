import pytest
from prefect import flow
from sqlalchemy.engine import URL, Engine
from sqlalchemy.ext.asyncio.engine import AsyncEngine

from prefect_sqlalchemy.credentials import AsyncDriver, DatabaseCredentials, SyncDriver


@pytest.mark.parametrize(
    "url_param", ["driver", "username", "password", "database", "host", "port", "query"]
)
def test_sqlalchemy_credentials_post_init_url_param_conflict(url_param):
    @flow
    def test_flow():
        url_params = {url_param: url_param}
        if url_param == "query":
            url_params["query"] = {"query": "query"}
        with pytest.raises(
            ValueError, match="The `url` should not be provided alongside"
        ):
            DatabaseCredentials(url="url", **url_params)

    test_flow()


@pytest.mark.parametrize("url_param", ["driver", "database"])
def test_sqlalchemy_credentials_post_init_url_param_missing(url_param):
    @flow
    def test_flow():
        url_params = {
            "driver": "driver",
            "database": "database",
        }
        url_params.pop(url_param)
        with pytest.raises(ValueError, match="If the `url` is not provided"):
            DatabaseCredentials(**url_params)

    test_flow()


@pytest.mark.parametrize(
    "driver", [AsyncDriver.POSTGRESQL_ASYNCPG, "postgresql+asyncpg"]
)
def test_sqlalchemy_credentials_get_engine_async(driver):
    @flow
    def test_flow():
        sqlalchemy_credentials = DatabaseCredentials(
            driver=driver,
            username="user",
            password="password",
            database="database",
            host="localhost",
            port=5432,
        )
        assert sqlalchemy_credentials._async_supported is True
        assert sqlalchemy_credentials.url is None

        expected_rendered_url = "postgresql+asyncpg://user:***@localhost:5432/database"
        assert repr(sqlalchemy_credentials.rendered_url) == expected_rendered_url
        assert isinstance(sqlalchemy_credentials.rendered_url, URL)

        engine = sqlalchemy_credentials.get_engine()
        assert engine.url.render_as_string() == expected_rendered_url
        assert isinstance(engine, AsyncEngine)

    test_flow()


@pytest.mark.parametrize(
    "driver", [SyncDriver.POSTGRESQL_PSYCOPG2, "postgresql+psycopg2"]
)
def test_sqlalchemy_credentials_get_engine_sync(driver):
    @flow
    def test_flow():
        sqlalchemy_credentials = DatabaseCredentials(
            driver=driver,
            username="user",
            password="password",
            database="database",
            host="localhost",
            port=5432,
        )
        assert sqlalchemy_credentials._async_supported is False
        assert sqlalchemy_credentials.url is None

        expected_rendered_url = "postgresql+psycopg2://user:***@localhost:5432/database"
        assert repr(sqlalchemy_credentials.rendered_url) == expected_rendered_url
        assert isinstance(sqlalchemy_credentials.rendered_url, URL)

        engine = sqlalchemy_credentials.get_engine()
        assert engine.url.render_as_string() == expected_rendered_url
        assert isinstance(engine, Engine)

    test_flow()


@pytest.mark.parametrize("url_type", ["string", "URL"])
def test_sqlalchemy_credentials_get_engine_url(url_type):
    @flow
    def test_flow():
        if url_type == "string":
            url = "postgresql://username:password@account/database"
        else:
            url = URL.create(
                "postgresql",
                "username",
                "password",
                host="account",
                database="database",
            )
        sqlalchemy_credentials = DatabaseCredentials(url=url)
        assert sqlalchemy_credentials._async_supported is False
        assert sqlalchemy_credentials.url == url

        expected_rendered_url = "postgresql://username:***@account/database"
        assert repr(sqlalchemy_credentials.rendered_url) == expected_rendered_url
        assert isinstance(sqlalchemy_credentials.rendered_url, URL)

        engine = sqlalchemy_credentials.get_engine()
        assert engine.url.render_as_string() == expected_rendered_url
        assert isinstance(engine, Engine)

    test_flow()


def test_sqlalchemy_credentials_sqlite(tmp_path):
    @flow
    def test_flow():
        driver = SyncDriver.SQLITE_PYSQLITE
        database = str(tmp_path / "prefect.db")
        sqlalchemy_credentials = DatabaseCredentials(driver=driver, database=database)
        assert sqlalchemy_credentials._async_supported is False

        expected_rendered_url = f"sqlite+pysqlite:///{database}"
        assert repr(sqlalchemy_credentials.rendered_url) == expected_rendered_url
        assert isinstance(sqlalchemy_credentials.rendered_url, URL)

        engine = sqlalchemy_credentials.get_engine()
        assert engine.url.render_as_string() == expected_rendered_url
        assert isinstance(engine, Engine)

    test_flow()
