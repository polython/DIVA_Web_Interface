from diva.views import app, db
from flask.ext.script import Manager, prompt_bool

manager = Manager(app)


@manager.command
def initdb():
    db.create_all()
    print("Initialized the database")


@manager.command
def dropdb():
    if prompt_bool("Delete the database?  Are you sure?"):
        db.drop_all()
        print("Dropped the database")


if __name__ == '__main__':
    manager.run()
