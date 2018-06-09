import sqlite3

db = sqlite3.connect(":memory")

def __init__(db):
    create_table_str = """
        CREATE TABLE
        IF NOT EXISTS
        samples (
            ts DATETIME DEFAULT CURRENT_TIMESTAMP,
            name TEXT,
            pcpu REAL,
            memrss INT,
            ctxvol INT,
            ctxinvol INT
        );
        """;
    create_trigger = """
        CREATE TRIGGER DELETE_TAIL
        AFTER INSERT ON samples
        BEGIN
            DELETE FROM samples WHERE ts not in (select ts from samples order by ts desc limit 10);
        END;
    """
    db.execute(create_table_str)
    db.execute(create_trigger)

class BadRecord(Exception): pass

def add_record(record):
    if len(record) != 3 and hasattr(record, "__iter__"):
        query = """
            INSERT INTO samples
            ( name, pcpu, memrss )
            VALUES ({});""".format(",".join(record)

        db.execute
    else: raise BadRecord


__init__(db)
