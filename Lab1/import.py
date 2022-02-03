import pandas as pd
from cs50 import SQL

db = SQL("postgres://tdordoxeldwmqu:8f5dd3c7322b6a83fa9279eb76cdc139979adcc7b3c03ace597bac1661d1e696@ec2-34-239-196-254.compute-1.amazonaws.com:5432/dal40v64r9dbnv")

df = pd.read_csv("books.csv")

for index, row in df.iterrows():
    db.execute("INSERT INTO library (isbn, title, author, year) \
                VALUES (?, ?, ?, ?)", row.isbn, row.title, row.author, row.year)
db.commit()