import logging

import sqlalchemy as sqla
from sqlalchemy.ext.declarative import declarative_base

import psycopg2
import psycopg2.extensions

Base = declarative_base()

logger = logging.getLogger(__name__)


def create_db(database, user, password, host, port=5432):
    connection = psycopg2.connect(user=user, password=password, host=host, port=port)
    connection.autocommit = True

    try:
        connection.cursor().execute("CREATE DATABASE %s;",
                                    [psycopg2.extensions.AsIs(database)])
    except Exception as error:
        if not hasattr(error, "pgerror") or "already exists" not in error.pgerror:
            raise error
        logger.warning("Database '%s' already exists.", database)

    connection.close()
    logger.debug("""It is possible that you want to install some extensions. 
    Check utils.EXTENSIONS and use create_db_with_extensions if desired.""")


class GatewayConnection(Base):
    __tablename__ = "gateway_connection_config"

    gw_identifier = sqla.Column(sqla.String, nullable=False, index=True, primary_key=True)
    gw_eui = sqla.Column(sqla.String, nullable=True)
    gw_ip = sqla.Column(sqla.String, nullable=True)
    gw_up_port = sqla.Column(sqla.Integer, nullable=True)
    gw_down_port = sqla.Column(sqla.Integer, nullable=True)

    def __init__(self, gw_identifier, gw_eui=None, gw_ip=None, gw_up_port=None, gw_down_port=None):
        self.gw_identifier = gw_identifier
        self.gw_eui = gw_eui
        self.gw_ip = gw_ip
        self.gw_up_port = gw_up_port
        self.gw_down_port = gw_down_port


class GatewayManager(object):
    def __init__(self, db_config):
        database_uri = "postgresql://{}:{}@{}:{}/{}".format(db_config["user"],
                                                            db_config["password"],
                                                            db_config["host"],
                                                            db_config["port"],
                                                            db_config["database"])
        create_db(**db_config)
        engine = sqla.create_engine(database_uri)
        engine.connect()
        Session = sqla.orm.sessionmaker(bind=engine)
        self.session = Session()
        Base.metadata.create_all(engine)
        try:
            self.session.execute(sqla.text("""CREATE TABLE alembic_version (
                        version_num character varying(32) NOT NULL,
                        PRIMARY KEY (version_num)
                        );
                """))
            self.session.execute(
                sqla.text("""INSERT INTO alembic_version VALUES ('c4821ceae1a2')"""))
            self.session.commit()
        except:
            logger.warning("Table alembic_version already exist")
            self.session.rollback()

    def query_gw_ip(self, gw_ip):
        return self.session.query(GatewayConnection).filter(
            GatewayConnection.gw_ip == gw_ip).first()

    def query_gw_identifier(self, gw_identifier):
        return self.session.query(GatewayConnection).filter(
            GatewayConnection.gw_identifier == gw_identifier).first()

    def store_gw_connection(self, gw_identifier, gw_eui=None, gw_ip=None, gw_up_port=None,
                            gw_down_port=None):
        try:
            gw_connection = self.query_gw_identifier(gw_identifier=gw_identifier)
            if gw_connection is None:
                gw_connection = GatewayConnection(gw_identifier=gw_identifier,
                                                  gw_eui=gw_eui,
                                                  gw_ip=gw_ip,
                                                  gw_up_port=gw_up_port,
                                                  gw_down_port=gw_down_port)
                logger.info(
                    f"Storing first connection for: {gw_identifier} ()")
                self.session.add(gw_connection)
            else:
                if gw_eui is not None:
                    gw_connection.gw_eui = gw_eui
                if gw_ip is not None:
                    gw_connection.gw_ip = gw_ip
                if gw_up_port is not None:
                    gw_connection.gw_up_port = gw_up_port
                if gw_down_port is not None:
                    gw_connection.gw_down_port = gw_down_port

        except Exception as e:
            logger.error(f"Error storing connection for {gw_identifier}.")
        else:
            self.session.commit()

    def get_up_addr_tuple(self, gw_identifier):
        gw_connection = self.query_gw_identifier(gw_identifier=gw_identifier)
        if gw_connection is not None:
            ip = gw_connection.gw_ip
            up_port = gw_connection.gw_up_port
            if ip is not None and up_port is not None:
                return ip, up_port

    def get_down_addr_tuple(self, gw_identifier):
        gw_connection = self.query_gw_identifier(gw_identifier=gw_identifier)
        if gw_connection is not None:
            ip = gw_connection.gw_ip
            down_port = gw_connection.gw_down_port
            if ip is not None and down_port is not None:
                return ip, down_port
