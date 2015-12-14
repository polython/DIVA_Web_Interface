from datetime import datetime, date
from diva.views import db


class Tape(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    barcode = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=date.today())

    @staticmethod
    def find_tape(barcode, *args):
        if not barcode:
            return "No barcode found"
        elif len(barcode) > 8:
            return "Invalid barcode"
        elif not args[0]:
            return Tape.query(Tape.barcode).all()
        else:
            if args & int(*args):
                for _ in args:
                    return Tape.query(Tape.barcode)

    def __repr__(self):
        return "Tape with barcode {} was restored on {}".format(self.barcode, self.date)


class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reqnum = db.Column(db.Integer, nullable=False)
    barcode = db.Column(db.Text, db.ForeignKey('Tape.barcode'), nullable=False)
    date = db.Column(db.DateTime, default=date.today())

    def __repr__(self):
        return "Tape with barcode {} has been imported, with Diva request number {}".format(self.barcode, self.reqnum)
