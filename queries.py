from flashcard import Set, Card
# from models import Set_SQL, Side_SQL, Card_SQL, Cell_SQL
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy import insert
# import os
#
# from sqlalchemy import create_engine
# engine = create_engine('mysql://root:' + os.environ.get('password') + '@localhost/flashcards?auth_plugin=mysql_native_password')
# # Session = sessionmaker(bind=engine)
# # session = Session()
# conn = engine.connect()
from models import db, Set_SQL, Card_SQL, Side_SQL, Cell_SQL, User

### READ
def query_cells(card_id):  # returns a dictionary of cells {side_id: [info, card_id]} in the f for a given card_id
    records = db.session.query(Cell_SQL).filter_by(card_id=card_id).all()
    cells = {}
    for record in records:
        cells[record.side_id] = [record.info, record.card_id]
    return cells

def query_cards(id):  # returns an array of Card objects for a given set_id
    records = db.session.query(Card_SQL).filter_by(set_id=id).all()
    print("querying cards")
    print(records)
    cards = []
    for record in records:
        card = Card(record.card_ID, record.card_order, query_cells(record.card_ID), record.set_id)
        cards.append(card)
    return cards

# print(query_cards(25))

def query_sides(set_id):  # returns a dictionary of {id_name: [order, name, set_id]} for a given set_id
    records = db.session.query(Side_SQL).filter_by(set_id=set_id).all()
    sides = {}
    for record in records:
        sides[record.side_id] = [record.side_order, record.name, record.set_id]
    return sides

def query_sets(records):  # returns an array of all sets in [set_id, name, description, user_id, public]
    # records = db.session.query(Set_SQL).all()
    sets = []
    for record in records:
        # user = db.session.query(User).filter_by(id=record.user_id).one()
        set = [record.set_id, record.name, record.description, record.user_id, record.public]
        sets.append(set)
    return sets

def query_sets_public(user):
    records = db.session.query(Set_SQL).filter_by(public=True).all()
    all_records = query_sets(records)
    return all_records

def query_sets_private(user):
    records = db.session.query(Set_SQL).filter_by(user_id=user.id).all()
    return query_sets(records)

def build_sets(records):  # builds an array of Set objects for all sets in db using query methods
    # records = query_sets()
    sets = []
    for record in records:
        set = Set(record[0], record[1], record[2], query_sides(record[0]), query_cards(record[0]), record[3], record[4])
        sets.append(set)
    return sets

def build_sets_public(user):
    return build_sets(query_sets_public(user))

def build_sets_private(user):
    return build_sets(query_sets_private(user))

def get_set(set_id):  # builds a Set object for a given set_id
    record = db.session.query(Set_SQL).filter_by(set_id=set_id).one()
    user = db.session.query(User).filter_by(id=record.user_id).one()
    set = Set(record.set_id, record.name, record.description, query_sides(record.set_id), query_cards(record.set_id), record.user_id, record.public)
    return set


### WRITE
def process_form(form, user):
    # create set
    public = True if form.getlist('public') else False
    ins = Set_SQL(name=form['name'], description=form['description'], user=user, public=public)
    db.session.add(ins)
    db.session.commit()
    set_id = ins.set_id
    # ins = insert(Set_SQL).values(name=form['name'], description=form['description'])
    # set_result = conn.execute(ins)
    # set_id = set_result.inserted_primary_key[0]
    print(set_id)

    # create sides
    sides = []
    side_fields = dict(filter(lambda elem: 'cell[0]' in elem[0], form.items()))
    for field in side_fields:
        if field == 'cell[0][0]':
            ins_side = Side_SQL(set_id=set_id, name=form[field])
            db.session.add(ins_side)
            db.session.commit()
            side_id = ins_side.side_id
            # ins_side = insert(Side_SQL).values(set_id=set_id, name=form[field])
            # side_result = conn.execute(ins_side)
            # side_id = side_result.inserted_primary_key[0]
            print(side_id)
        else:
            side = {'set_id': set_id, 'name': form[field]}
            sides.append(side)
    if sides:
        side_result = db.engine.execute(Side_SQL.__table__.insert(), sides)

    # create cards
    cards = []
    card_fields = dict(filter(lambda elem: 'cell' in elem[0] and '][0]' in elem[0] and 'cell[0]' not in elem[0], form.items()))
    for field in card_fields:
        if field == 'cell[1][0]':
            ins_card = Card_SQL(set_id=set_id)
            db.session.add(ins_card)
            db.session.commit()
            card_id = ins_card.card_ID
            # ins_card = insert(Card_SQL).values(set_id=set_id)
            # card_result = conn.execute(ins_card)
            # card_id = card_result.inserted_primary_key[0]
            print(card_id)
        else:
            card = {'set_id': set_id}
            cards.append(card)
    if cards:
        card_result = db.engine.execute(Card_SQL.__table__.insert(), cards)

    # create cells
    cells = []
    cell_fields = dict(filter(lambda elem: 'cell' in elem[0] and 'cell[0]' not in elem[0], form.items()))
    # records = session.query(Card_SQL.card_ID).filter_by(set_id=id).all()
    # print(records)
    for field in cell_fields:
        card_index = int(field[5:6])-1
        side_index = int(field[-2:-1])
        print(card_index)
        print(side_index)
        cell = {'card_id': card_index+card_id, 'side_id': side_id+side_index, 'info': form[field]}
        cells.append(cell)
    cells_result = db.engine.execute(Cell_SQL.__table__.insert(), cells)

def edit_form(form, set_id):
    # update set info
    record = db.session.query(Set_SQL).filter_by(set_id=set_id).one()
    public = True if form.getlist('public') else False
    record.name = form['name']
    record.description = form['description']
    record.public = public
    db.session.commit()
    set_id = record.set_id
    # print(set_id)

    # update sides
    sides = db.session.query(Side_SQL).filter_by(set_id=set_id).all()
    side_fields = dict(filter(lambda elem: 'cell[0]' in elem[0], form.items()))
    for i in range(len(sides)): # update existing sides
        side = sides[i]
        side.name = form['cell[0][' + str(i) + ']']
    db.session.commit()

    new_sides = []
    if len(side_fields) > len(sides): # new sides
        for i in range(len(sides), len(side_fields)):
            side = {'set_id': set_id, 'name': form['cell[0][' + str(i) + ']']}
            new_sides.append(side)
        db.engine.execute(Side_SQL.__table__.insert(), new_sides)

    old_sides = len(sides)

    # update cards
    cards = db.session.query(Card_SQL).filter_by(set_id=set_id).all()
    card_fields = dict(filter(lambda elem: 'cell' in elem[0] and '][0]' in elem[0] and 'cell[0]' not in elem[0], form.items()))
    # existing cards don't need to be updated

    new_cards = []
    if len(card_fields) > len(cards): # new cards
        for i in range(len(cards), len(card_fields)):
            card = {'set_id': set_id}
            new_cards.append(card)
        print(new_cards)
        db.engine.execute(Card_SQL.__table__.insert(), new_cards)
    old_cards = len(cards)

    # update cells
    cards = db.session.query(Card_SQL).filter_by(set_id=set_id).all()
    sides = db.session.query(Side_SQL).filter_by(set_id=set_id).all()
    card_index = cards[0].card_ID
    side_index = sides[0].side_id
    cells = []
    for i in range(len(cards)):
        for j in range(len(sides)):
            if i < old_cards and j < old_sides: # update existing cell
                cell = db.session.query(Cell_SQL).filter_by(card_id=cards[i].card_ID, side_id=sides[j].side_id).one()
                cell.info = form['cell[' + str(i+1) + '][' + str(j) + ']']
                db.session.commit()
            else:
                cell = {'card_id': cards[i].card_ID, 'side_id': sides[j].side_id, 'info': form['cell[' + str(i+1) + '][' + str(j) + ']']}
                cells.append(cell)
    if cells:
        db.engine.execute(Cell_SQL.__table__.insert(), cells)

### DELETE
def delete_set(set_id):
    sides = query_sides(set_id)
    for side in sides:
        db.session.query(Cell_SQL).filter_by(side_id=side).delete()
    db.session.query(Side_SQL).filter_by(set_id=set_id).delete()
    db.session.query(Card_SQL).filter_by(set_id=set_id).delete()
    db.session.query(Set_SQL).filter_by(set_id=set_id).delete()
    db.session.commit()


