import psycopg2
from code.config import get_db_config

def get_db_connection():
    db_config = get_db_config()
    return psycopg2.connect(
        dbname=db_config['dbname'],
        user=db_config['user'],
        password=db_config['password'],
        host=db_config['host']
    )

def rebuild_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DO $$ '
                'DECLARE _tableName TEXT; BEGIN '
                'FOR _tableName IN SELECT tablename FROM pg_tables WHERE tablename LIKE \'group_%\' '
                'LOOP EXECUTE \'DROP TABLE IF EXISTS \' || quote_ident(_tableName) || \' CASCADE\'; END LOOP; '
                'END; $$;'
                'CREATE TABLE groups_students_ptk'
                '(group_course SMALLINT NOT NULL, group_id VARCHAR(6) NOT NULL);'
                'CREATE TABLE groups_students_pedcol' 
                '(group_course SMALLINT NOT NULL, group_id VARCHAR(6) NOT NULL);'
                'CREATE TABLE groups_students_medcol' 
                '(group_course SMALLINT NOT NULL, group_id VARCHAR(6) NOT NULL);'
                'CREATE TABLE groups_students_spour'
                '(group_course SMALLINT NOT NULL, group_id VARCHAR(6) NOT NULL);'
                'CREATE TABLE groups_students_spoinpo'
                '(group_course SMALLINT NOT NULL, group_id VARCHAR(6) NOT NULL);')
    conn.commit()
    conn.close()
