from peewee import (SqliteDatabase, CharField,
                    Model, BooleanField,
                    DateTimeField, IntegerField, FloatField)
import os

db_name = "db.sqlite3"
if __name__ == "__main__":
    os.system(f"rm -f {db_name}")

db = SqliteDatabase(db_name)


# class UserConfig:
#     NORMAL = "عادی"
#     VIP = "ویژه"  # WILL CHANGE


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    user_id = CharField()
    phone = CharField()
    traffic = FloatField(default=1000.0)  # (MEGABYTE) 1000MG = 1G
    pay = IntegerField(default=0)
    members = IntegerField(default=0)
    download_files = IntegerField(default=0)
    generated_links = IntegerField(default=0)
    first_pay = BooleanField(default=False)
    download_limit = BooleanField(default=False)
    is_admin = BooleanField(default=False)


class Links(BaseModel):
    user_id = CharField()
    deleted = BooleanField(default=False)
    filename = CharField()
    filesize = FloatField()
    file_link = CharField()
    link_lifetime = DateTimeField()
    file_id = CharField()
    short_file_id = CharField()
    file_type = CharField()


class AdminPassword(BaseModel):
    password = CharField()


class Payments(BaseModel):
    user = IntegerField()
    amount = IntegerField()
    traffic = IntegerField()


db.connect()

if __name__ == '__main__':
    db.create_tables([User, Links, Payments, AdminPassword])
