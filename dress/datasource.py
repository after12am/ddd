# encoding: utf-8
import os, sys, re, subprocess, defs
from config import get_config
from abc import ABCMeta, abstractmethod
from misc import dict2obj

class DataSource(object):
    
    __metaclass__ = ABCMeta
    
    def __init__(self):
        self.conn = None
        self.cursor = None
    
    def __del__(self):
        self.close()
    
    @abstractmethod
    def connect(self):
        pass
    
    @abstractmethod
    def close(self):
        pass
    
    @abstractmethod
    def get_tables(self):
        pass
    
    @abstractmethod
    def get_columns(self, table):
        pass
    
    @abstractmethod
    def get_table_comment(self, table):
        pass
    
    @abstractmethod
    def get_create_statements(self):
        pass


class MySQL(DataSource):
    
    def __init__(self, host, user, password, charset, database):
        super(MySQL, self).__init__()
        self.host = host
        self.user = user
        self.password = password if password is not None else ''
        self.database = database
        self.charset = charset
    
    def connect(self):
        import MySQLdb
        self.conn = MySQLdb.connect(host=self.host, user=self.user, \
            passwd=self.password, charset=self.charset, db=self.database)
        self.cursor = self.conn.cursor()
    
    def close(self):
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
    
    def get_tables(self):
        self.cursor.execute("show tables;")
        return sorted([item[0] for item in self.cursor.fetchall()])
    
    def get_columns(self, table):
        self.cursor.execute("show full columns from %s;" % table)
        return self.cursor.fetchall()
    
    def get_table_comment(self, table):
        self.cursor.execute("show table status where name = '%s';" % table)
        ret = self.cursor.fetchall()
        return ret[0][-1]
    
    # this is not compatible with other datasources
    def get_create_statement(self, table):
        self.cursor.execute("show create table %s;" % table)
        ret = self.cursor.fetchall()
        return ret[0][1]
    
    def get_create_statements(self):
        res = ""
        for table in self.get_tables():
            res += self.get_create_statement(table) + ";\n\n"
        return res


class SQLite3(DataSource):
    
    def __init__(self, database):
        super(SQLite3, self).__init__()
        self.database = database
        self.timeout = 5000
    
    def connect(self):
        import sqlite3
        self.conn = sqlite3.connect(self.database, timeout = self.timeout)
        self.cursor = self.conn.cursor()
    
    def close(self):
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
    
    def get_tables(self):
        self.cursor.execute("select name from sqlite_master where type = 'table'")
        return sorted([item[0] for item in self.cursor.fetchall()])
    
    def get_columns(self, table):
        self.cursor.execute("pragma table_info('%s')" % table)
        return self.cursor.fetchall()
    
    def get_table_comment(self, table):
        # SQLite3 does not support comment
        return ''
    
    # this is not compatible with other datasources
    def get_create_statement(self, table):
        self.cursor.execute("select sql from sqlite_master where type = 'table' and name = '%s'" % table)
        ret = self.cursor.fetchall()
        return ret[0][0]
    
    def get_create_statements(self):
        res = ""
        for table in self.get_tables():
            res += self.get_create_statement(table) + ";\n\n"
        return res


class PostgreSQL(DataSource):
    
    _get_columns_query = """
        select
            column_name,
            udt_name,
            character_maximum_length,
            collation_name,
            is_nullable,
            column_default
        from
            information_schema.columns
        where
            table_catalog = '%s'
        and table_name = '%s'
        order by ordinal_position;
    """
    
    _get_comment_query = """
        select
            pd.description
        from
            pg_stat_all_tables as psat
        inner join
            pg_description as pd on psat.relid = pd.objoid
        inner join
            pg_attribute as pa on pd.objoid = pa.attrelid and pd.objsubid = pa.attnum
        where
            psat.schemaname = (select schemaname from pg_stat_user_tables where relname = '%s')
        and psat.relname = '%s'
        and pa.attname = '%s'
        and pd.objsubid <> 0
        order by pd.objsubid;
    """
    
    _get_key_query = """
        select
            tc.constraint_name,
            tc.constraint_type
        from
            information_schema.table_constraints as tc
        inner join
            information_schema.constraint_column_usage as ccu on 
                    tc.table_catalog = ccu.table_catalog 
                and tc.table_schema = ccu.table_schema 
                and tc.table_name = ccu.table_name 
                and tc.constraint_name = ccu.constraint_name
        where
            tc.table_catalog = '%s'
        and tc.table_name = '%s'
        and ccu.column_name = '%s'
    """
    
    _get_table_comment_query = """
        select
            pd.description
        from
            pg_stat_user_tables as psut
        inner join
            pg_description as pd on psut.relid = pd.objoid
        where
            psut.relname = '%s'
        and pd.objsubid = 0;
    """
    
    def __init__(self, host, user, password, database, port):
        super(PostgreSQL, self).__init__()
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
    
    def connect(self):
        import pgdb
        server = "%s:%s" % (str(self.host), str(self.port),)
        self.conn = pgdb.connect(host=server, user=self.user, \
            password=self.password, database=self.database)
        self.cursor = self.conn.cursor()
    
    def close(self):
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
    
    def get_tables(self):
        self.cursor.execute("select relname from pg_stat_user_tables;")
        return sorted([item[0] for item in self.cursor.fetchall()])
    
    def get_columns(self, table):
        self.cursor.execute(self._get_columns_query % (self.database, table))
        status = self.cursor.fetchall()
        # convert to signage of MySQL
        for i, x in enumerate(status):
            status[i].append('')
            if x[-2] is None:
                continue
            if re.match(r"^nextval", x[-2]):
                status[i][-2] = None
                # add additional info as Extra
                status[i][-1] = 'auto_increment'
                continue
            m = re.match(r"^'(.*)'::", x[-2])
            if m:
                status[i][-2] = m.group(1)
                continue
            m = re.match(r"^(.*)::", x[-2])
            if m:
                status[i][-2] = m.group(1)
                continue
        # add additional data, comment and key, to basic column data
        for i, item in enumerate(status):
            column = item[0]
            # merge column comment
            self.cursor.execute(self._get_comment_query % (table, table, column))
            ret = self.cursor.fetchone()
            status[i] += ret if ret is not None else ['']
            # merge key information
            self.cursor.execute(self._get_key_query % (self.database, table, column))
            ret = self.cursor.fetchone()
            status[i] += ret if ret is not None else [None, '']
        # if multiple unique index, change key name to multiple
        for i, item in enumerate(status):
            for j in range(i + 1, len(status)):
                if status[i][-2] == status[j][-2] and status[i][-1] and status[i][-1].lower() == 'unique':
                    status[i][-1] = status[j][-1] = 'MULTIPLE'
        # shorten key name in 3 characters
        return [x[:8] + [x[-1][:3]] for x in status]
    
    def get_table_comment(self, table):
        self.cursor.execute(self._get_table_comment_query % table)
        ret = self.cursor.fetchall()
        return ret[0][-1]
    
    def get_create_statements(self):
        # https://github.com/raspi/pypgbackup/blob/master/src/pgbackup.py
        os.putenv('PGPASSWORD', self.password)
        cmd = "pg_dump -U %s --no-password -h %s --schema-only %s -p %s"
        cmd = cmd % (self.user, self.host, self.database, self.port)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        p.wait()
        res = p.stdout.readlines().strip()
        if len(res) > 0:
            return "\n".join(res)
        sys.exit("\n".join(p.stderr.readlines()))


class DB(object):
    
    @classmethod
    def getinstance(cls):
        if hasattr(cls, 'instance') and cls.instance:
            return cls.instance
        
        options =dict2obj(get_config(defs.config_name).database)
        
        if options.datasource == 'Database/MySQL':
            cls.instance = MySQL(host=options.host, user=options.user, \
                password=options.password, charset=options.charset, database=options.database)
            cls.instance.connect()
            return cls.instance
        
        if options.datasource == 'Database/PostgreSQL':
            cls.instance = PostgreSQL(host=options.host, user=options.user, \
                password=options.password, database=options.database, port=options.port)
            cls.instance.connect()
            return cls.instance
        
        if options.datasource == 'Database/SQLite3':
            cls.instance = SQLite3(options.database)
            cls.instance.connect()
            return cls.instance
        
        raise ValueError("Invalid datasource: {0}".format(options.datasource))
    
    @classmethod
    def close(cls):
        if hasattr(cls, 'instance') and cls.instance:
            cls.instance.close()
