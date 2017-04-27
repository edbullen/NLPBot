
import utils  # General utils including config params and database connection

conf = utils.get_config()
DBHOST = conf["MySQL"]["server"] 
DBUSER = conf["MySQL"]["dbuser"]
DBNAME = conf["MySQL"]["dbname"]
DBCHARSET = conf["MySQL"]["dbcharset"]

if __name__ == '__main__':
    
    connection = utils.db_connection(DBHOST, DBUSER, DBNAME, DBCHARSET)

    tests = { 'create_test_tab': ('create table bot_test_tab (col1 varchar(10), col2 integer)', None)
             ,'insert_test_tab': ('insert into bot_test_tab values (%s, %s)', ('a',1))
             , 'select_test_tab': ('select col1 from bot_test_tab where col2 = (%s)', (1))
             , 'drop_test_tab': ('drop table if exists bot_test_tab', None )
             }
  
    test_sequence = ('drop_test_tab', 'create_test_tab', 'insert_test_tab', 'select_test_tab', 'drop_test_tab')
    
    for key in test_sequence:
        print("execute",key, "Args:", tests[key][1], end=" " )
        sql = tests[key][0]
        args = tests[key][1]
        c = connection.cursor()
        ret = c.execute(sql, args)
        print("Response", ret)

    """
    sql = 'select col2 from test1 where col1 = %s'
    c = connection.cursor()
    c.execute(sql,('a'))
    result = c.fetchone()
    print(result)
    """    
        