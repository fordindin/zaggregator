import sqlite3

DBPATH="/var/run/zaggregator/zaggregator.sqlite"
db = None

def __init__() -> None:
    """ Initalize sqlite dataabase """
    global db
    db = sqlite3.connect(DBPATH)
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

def add_record(record) -> None:
    """
        Add record into sqlite database
    """
    if len(record) != 3 and hasattr(record, "__iter__"):
        query = """
            INSERT INTO samples
            ( name, memrss, memvms, ctxvol, ctxinvol, pcpu )
            VALUES ('{}',{});""".format(record[0], ",".join(map(str, record[1:])))

        db.execute(query)
        db.commit()
    else:
        raise BadRecord

def get_bundle_names() -> [str]:
    """
        Get list of bundle names from sqlite database
    """
    query = """
        SELECT DISTINCT(name) FROM samples;
        """
    return [ row[0] for row in db.execute(query) ]

def get(bname:str, check:str):
    """
        Get value of `check' variable for bundle with name `bname'
    """
    query = """
        SELECT {} FROM samples
        WHERE name='{}' AND
            ( (julianday('now') - julianday(ts))*24*60*60 < 30 )
        ORDER BY ts DESC
        LIMIT 1;
        """.format(check, bname)
    result = list(db.execute(query))
    if len(result) > 0:
        return result[0][0]

__init__()
