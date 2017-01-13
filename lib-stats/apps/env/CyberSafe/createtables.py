import MySQLdb
db = MySQLdb.connect('localhost','root',*MYSQL_PASSWORD_HERE*,*DATABASE_NAME_HERE*)
cursor = db.cursor()
cursor.execute('CREATE TABLE EDISONTEMP (READING INT(50) auto_increment primary key, VALUE INT)')
cursor.execute('CREATE TABLE EDISONLIGHT (READING INT(50) auto_increment primary key, VALUE INT)')
db.commit()
db.close()
