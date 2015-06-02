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
                     sa.Column('id', sa.UnicodeText, primary_key=True),
                     sa.Column('short_url', sa.UnicodeText, nullable=False),
                     sa.Column('domain', sa.UnicodeText, nullable=False),
                     sa.Column('appId', sa.UnicodeText, nullable=False),
                     sa.Column('userId', sa.UnicodeText, nullable=False),
                     sa.Column('url_android', sa.UnicodeText, nullable=False),
                     sa.Column('url_apple', sa.UnicodeText, nullable=False)
                     )

if __name__ == '__main__':
    connection_query = 'postgresql+psycopg2://{}:{}@{}/{}'.format(LOGIN, PASSW, HOST, DBNAME)
    engine = sa.create_engine(connection_query)
    test.drop(engine, checkfirst=True)
    metadata.create_all(engine)
