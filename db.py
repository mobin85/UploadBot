from peewee import (SqliteDatabase, CharField,
                    Model, FloatField,
                    DateTimeField, IntegerField)


class UserConfig:
    NORMAL = "عادی"
    VIP = "ویژه"  # WILL CHANGE


db = SqliteDatabase("database.sqlite3")


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    user_id = CharField()
    traffic = FloatField(default=1000.0)  # (MEGABYTE) 1000MG = 1G
    coin = IntegerField(default=0)
    members = IntegerField(default=0)
    account_type = CharField(default=UserConfig.NORMAL)
    download_files = IntegerField(default=0)
    generated_links = IntegerField(default=0)
    file_limit_size = IntegerField(default=512)  # 512MG


db.connect()

if __name__ == '__main__':
    db.create_tables([User, ])
