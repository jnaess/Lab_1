from cs50 import SQL

db = SQL("postgres://tdordoxeldwmqu:8f5dd3c7322b6a83fa9279eb76cdc139979adcc7b3c03ace597bac1661d1e696@ec2-34-239-196-254.compute-1.amazonaws.com:5432/dal40v64r9dbnv")

#;



db.execute("DROP TABLE registrants")

db.execute("CREATE TABLE registrants (id SERIAL, name TEXT NOT NULL, email TEXT NOT NULL, sport TEXT NOT NULL, PRIMARY KEY(id))")