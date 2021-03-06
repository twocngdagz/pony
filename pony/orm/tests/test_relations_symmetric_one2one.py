import unittest
from pony.orm.core import *
from testutils import raises_exception

db = Database('sqlite', ':memory:')

class Person(db.Entity):
    name = Required(unicode)
    spouse = Optional('Person', reverse='spouse')

db.generate_mapping(create_tables=True)

class TestSymmetric(unittest.TestCase):
    def setUp(self):
        rollback()
        db.execute('delete from Person')
        db.insert('Person', id=1, name='A', spouse=2)
        db.insert('Person', id=2, name='B', spouse=1)
        db.insert('Person', id=3, name='C', spouse=4)
        db.insert('Person', id=4, name='D', spouse=3)
        db.insert('Person', id=5, name='E', spouse=None)
        commit()
        rollback()
    def test1(self):
        p1 = Person[1]
        p2 = Person[2]
        p5 = Person[5]
        p1.spouse = p5
        commit()
        self.assertEquals(p1._vals_.get('spouse'), p5)
        self.assertEquals(p5._vals_.get('spouse'), p1)
        self.assertEquals(p2._vals_.get('spouse'), None)
        data = db.select('spouse from Person order by id')
        self.assertEquals([5, None, 4, 3, 1], data)
    def test2(self):
        p1 = Person[1]
        p2 = Person[2]
        p1.spouse = None
        commit()
        self.assertEquals(p1._vals_.get('spouse'), None)
        self.assertEquals(p2._vals_.get('spouse'), None)
        data = db.select('spouse from Person order by id')
        self.assertEquals([None, None, 4, 3, None], data)
    def test3(self):
        p1 = Person[1]
        p2 = Person[2]
        p3 = Person[3]
        p4 = Person[4]
        p1.spouse = p3
        commit()
        self.assertEquals(p1._vals_.get('spouse'), p3)
        self.assertEquals(p2._vals_.get('spouse'), None)
        self.assertEquals(p3._vals_.get('spouse'), p1)
        self.assertEquals(p4._vals_.get('spouse'), None)
        data = db.select('spouse from Person order by id')
        self.assertEquals([3, None, 1, None, None], data)
    def test4(self):
        persons = set(select(p for p in Person if p.spouse.name in ('B', 'D')))
        self.assertEquals(persons, set([Person[1], Person[3]]))
    @raises_exception(UnrepeatableReadError, 'Value of Person.spouse for Person(1) was updated outside of current transaction')
    def test5(self):
        db.execute('update Person set spouse = 3 where id = 2')
        p1 = Person[1]
        p1.spouse
        p2 = Person[2]
        p2.name
    def test6(self):
        db.execute('update Person set spouse = 3 where id = 2')
        p1 = Person[1]
        p2 = Person[2]
        p2.name
        p1.spouse
        self.assertEquals(p2._vals_.get('spouse'), p1)

if __name__ == '__main__':
    unittest.main()
