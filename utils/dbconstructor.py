from aiopg.sa import create_engine
import sqlalchemy as sa

# CREATE DATABASE test;
# CREATE USER test WITH PASSWORD 'testpasswd';
# GRANT ALL ON DATABASE test TO test;

LOGIN = 'test'
PASSW = 'testpasswd'
DBNAME = 'test'
HOST = 'localhost'

metadata = sa.MetaData()

test = sa.Table('test', metadata,
                     sa.Column('id', sa.BigInteger, primary_key=True),
                     sa.Column('short_url', sa.UnicodeText, nullable=False),
                     sa.Column('domain', sa.UnicodeText, nullable=False),
                     sa.Column('appId', sa.UnicodeText, nullable=False),
                     sa.Column('userId', sa.UnicodeText, nullable=False),
                     sa.Column('url_android', sa.UnicodeText, nullable=False),
                     sa.Column('url_apple', sa.UnicodeText, nullable=False)
                     )

connection_query = 'postgresql+psycopg2://{}:{}@{}/{}'.format(LOGIN, PASSW, HOST, DBNAME)
engine = sa.create_engine(connection_query)
metadata.create_all(engine)
