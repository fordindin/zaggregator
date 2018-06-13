import sqlite3

db = sqlite3.connect("data.sqlite")

def __init__(db):
    create_table_str = """
        CREATE TABLE
        IF NOT EXISTS
        samples (
            ts DATETIME DEFAULT CURRENT_TIMESTAMP,
            name TEXT,
            memrss INT,
            memvms INT,
            ctxvol INT,
            ctxinvol INT,
            pcpu REAL
        );
        """;
    create_trigger = """
        CREATE TRIGGER IF NOT EXISTS
        DELETE_TAIL
        AFTER INSERT ON samples
        BEGIN
            DELETE FROM samples WHERE ts not in (select ts from samples order by ts desc
            limit 300);
        END;
    """
    db.execute(create_table_str)
    db.execute(create_trigger)

class BadRecord(Exception): pass

def add_record(record):
    if len(record) != 3 and hasattr(record, "__iter__"):
        query = """
            INSERT INTO samples
            ( name, memrss, memvms, ctxvol, ctxinvol, pcpu )
            VALUES ('{}',{});""".format(record[0], ",".join(map(str, record[1:])))

        db.execute(query)
        db.commit()
    else:
        raise BadRecord


__init__(db)
