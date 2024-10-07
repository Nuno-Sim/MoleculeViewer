import sqlite3
import os

from MolDisplay import Molecule, Atom, Bond
import MolDisplay

class Database:
    def __init__(self, reset=False):
        if reset:
            # Deletes database file if one exists
            if os.path.exists("molecules.db"):
                os.remove("molecules.db")
    
        try:
            self.conn = sqlite3.connect('molecules.db')
        except Exception as e:
            print(f"Error creating/connecting to database file: {e}")

    def create_tables(self):
        try:
            self.conn.execute("""CREATE TABLE Elements 
                 ( ELEMENT_NO     INTEGER NOT NULL,
                   ELEMENT_CODE   VARCHAR(3) NOT NULL,
                   ELEMENT_NAME   VARCHAR(32) NOT NULL,
                   COLOUR1        CHAR(6) NOT NULL,
                   COLOUR2        CHAR(6) NOT NULL,
                   COLOUR3        CHAR(6) NOT NULL,
                   RADIUS         DECIMAL(3) NOT NULL,
                   PRIMARY KEY (ELEMENT_NAME) );""")

            self.conn.execute("""CREATE TABLE Atoms
                 ( ATOM_ID        INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL ,
                   ELEMENT_CODE   VARCHAR(3) NOT NULL,
                   X              DECIMAL(7,4) NOT NULL,
                   Y              DECIMAL(7,4) NOT NULL,
                   Z              DECIMAL(7,4) NOT NULL,
                   FOREIGN KEY (ELEMENT_CODE) REFERENCES Elements);""")

            self.conn.execute("""CREATE TABLE Bonds (
                  BOND_ID     INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                   A1          INTEGER NOT NULL,
                   A2          INTEGER NOT NULL,
                   EPAIRS      INTEGER NOT NULL);""")

            self.conn.execute("""CREATE TABLE Molecules 
                 ( MOLECULE_ID     INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                   NAME            TEXT UNIQUE NOT NULL);""")

            self.conn.execute("""CREATE TABLE MoleculeAtom
                 ( MOLECULE_ID     INTEGER NOT NULL,
                   ATOM_ID         INTEGER NOT NULL,
                   PRIMARY KEY (MOLECULE_ID,ATOM_ID),
                   FOREIGN KEY (MOLECULE_ID) REFERENCES Molecules,
                   FOREIGN KEY (ATOM_ID) REFERENCES Atoms);""")

            self.conn.execute("""CREATE TABLE MoleculeBond
                 ( MOLECULE_ID     INTEGER NOT NULL,
                   BOND_ID         INTEGER NOT NULL,
                   PRIMARY KEY (MOLECULE_ID,BOND_ID),
                   FOREIGN KEY (MOLECULE_ID) REFERENCES Molecules,
                   FOREIGN KEY (BOND_ID) REFERENCES Bonds);""")
            self.conn.commit() 
            
        except Exception as e:
            print(f"Error Creating table: {e}")

    def __setitem__(self, table, values):
        try:
             # Create a string of question marks for the number of values to be inserted
            questionMarks = ','.join(['?'] * len(values)) 
            query = f"INSERT INTO {table} VALUES ({questionMarks})"
            # Execute the query and commit to database
            self.conn.execute(query, values)
            self.conn.commit() 
        except Exception as e:
            print(f"Error setting table: {e}")

    def add_atom (self, molname, atom):
        # Atom object
        atom = Atom(atom)
        # Add attributes to Atoms table
        self.conn.execute("INSERT INTO Atoms (ELEMENT_CODE, X, Y, Z) VALUES (?, ?, ?, ?)", 
                  (atom.c_atom.element, atom.c_atom.x, atom.c_atom.y, atom.c_atom.z))
        
        # Gets atom_id
        atom_id_cursor = self.conn.execute("SELECT last_insert_rowid()")
        atom_id = (atom_id_cursor.fetchone()[0])

        # Gets molecule_id
        molecule_id_cursor = self.conn.execute("SELECT MOLECULE_ID FROM Molecules WHERE NAME = ?", [molname])
        molecule_id = (molecule_id_cursor.fetchone()[0])

        # Add to MoleculeAtom table
        self.conn.execute("INSERT INTO MoleculeAtom VALUES (?,?)", (molecule_id,atom_id))

    def add_bond (self, molname, bond):
        # Bond object
        bond = Bond(bond)
        # Add attributes to Bonds table
        self.conn.execute("INSERT INTO Bonds (A1, A2, EPAIRS) VALUES (?, ?, ?)", 
                  (bond.c_bond.a1,bond.c_bond.a2, bond.c_bond.epairs))
        
        # Gets bond_id
        bond_id_cursor = self.conn.execute("SELECT last_insert_rowid()")
        bond_id = (bond_id_cursor.fetchone()[0])

        # Gets molecule_id
        molecule_id_cursor = self.conn.execute("SELECT MOLECULE_ID FROM Molecules WHERE NAME = ?", [molname])
        molecule_id = (molecule_id_cursor.fetchone()[0])

        # Add to MoleculeBond table
        self.conn.execute("INSERT INTO MoleculeBond VALUES (?,?)", (molecule_id,bond_id))

    def add_molecule(self, name, atom):
        # Create Mol.Display.Molecule object
        mol = Molecule()

        # Call its parse method
        mol.parse(fp)

        # Add entry to Molecules table
        self.conn.execute("INSERT INTO Molecules (NAME) VALUES (?)", [name])

        # Call add_atom & add_bond
        for i in range (mol.atom_no):
            atom = mol.get_atom(i)
            self.add_atom(name,atom)

        for i in range (mol.bond_no):
            bond = mol.get_bond(i)
            self.add_bond(name,bond)
        self.conn.commit() 

    def load_mol(self, name):
        # Create MolDisplay.Molecule object
        mol = Molecule()

        # Retrieve all atoms associated with the named molecule
        atoms_query = """
        SELECT Atoms.ATOM_ID, Elements.ELEMENT_CODE, Atoms.X, Atoms.Y, Atoms.Z
        FROM Atoms 
        INNER JOIN Elements ON Atoms.ELEMENT_CODE = Elements.ELEMENT_CODE
        INNER JOIN MoleculeAtom ON Atoms.ATOM_ID = MoleculeAtom.ATOM_ID
        INNER JOIN Molecules ON MoleculeAtom.MOLECULE_ID = Molecules.MOLECULE_ID
        WHERE Molecules.NAME = ? 
        ORDER BY Atoms.ATOM_ID ASC
        """

        # Retrieve all atoms associated with the named molecule
        bonds_query = """
        SELECT Bonds.BOND_ID, Bonds.A1, Bonds.A2, Bonds.EPAIRS
        FROM Bonds INNER JOIN MoleculeBond ON Bonds.BOND_ID = MoleculeBond.BOND_ID
        INNER JOIN Molecules ON MoleculeBond.MOLECULE_ID = Molecules.MOLECULE_ID
        WHERE Molecules.NAME = ? 
        ORDER BY Bonds.BOND_ID ASC
        """

        atomsCursor = self.conn.cursor().execute(atoms_query, (name,))
        atoms = atomsCursor.fetchall()
        
        bondsCursor = self.conn.cursor().execute(bonds_query, (name,))
        bonds = bondsCursor.fetchall()

        # Loops through each bond and calls append_bond
        for atom in atoms:
            atom_id, element, x, y, z = atom
            mol.append_atom(element, x, y, z)

        # Loops through each bond and calls append_bond
        for bond in bonds:
            bond_id, a1, a2, epairs = bond
            mol.append_bond(a1, a2, epairs)

        return mol

    def radius (self):
        result_set = self.conn.execute("SELECT ELEMENT_CODE, RADIUS FROM Elements")
        rows = result_set.fetchall()

        # Creates a dictionary
        radius_dict ={}
        for row in rows:
            key = row[0]
            value = row[1]
            radius_dict[key] = value

        return radius_dict

    def element_name (self):
        result_set = self.conn.execute("SELECT ELEMENT_CODE, ELEMENT_NAME FROM Elements")

        rows = result_set.fetchall()

        # Creates a dictionary 
        elementName_dict ={}
        for row in rows:
            key = row[0]
            value = row[1]
            elementName_dict[key] = value

        return elementName_dict

    def radial_gradients (self):
        result_set = self.conn.execute("SELECT ELEMENT_NAME, COLOUR1, COLOUR2, COLOUR3 FROM Elements")
        rows = result_set.fetchall()

        radial_gradients_str = ""
        for row in rows:
            radial_gradient = """
            <radialGradient id="%s" cx="-50%%" cy="-50%%" r="220%%" fx="20%%" fy="20%%">
                <stop offset="0%%" stop-color="#%s"/>
                <stop offset="50%%" stop-color="#%s"/>
                <stop offset="100%%" stop-color="#%s"/>
            </radialGradient>
            """ % (row[0], row[1], row[2], row[3])
            radial_gradients_str += radial_gradient

        return radial_gradients_str

if __name__ == "__main__":
    db = Database(reset=False); # or use default
    MolDisplay.radius = db.radius();
    MolDisplay.element_name = db.element_name();
    MolDisplay.header += db.radial_gradients();
    for molecule in [ 'Water', 'Caffeine', 'Isopentanol' ]:    
        mol = db.load_mol( molecule );
        mol.sort();
        fp = open( molecule + ".svg", "w" );
        fp.write( mol.svg() );
        fp.close();


        
# if __name__ == "__main__":
#     db = Database(reset=True)
#     db.create_tables()
#     db['Elements'] = (1, 'H', 'Hydrogen', 'FFFFFF', '050505', '020202', 25)
#     db['Elements'] = (6, 'C', 'Carbon', '808080', '010101', '000000', 40)
#     db['Elements'] = (7, 'N', 'Nitrogen', '0000FF', '000005', '000002', 40)
#     db['Elements'] = (8, 'O', 'Oxygen', 'FF0000', '050000', '020000', 40)
#     fp = open('water-3D-structure-CT1000292221.sdf')
#     db.add_molecule('Water', fp)
#     fp = open('caffeine-3D-structure-CT1001987571.sdf')
#     db.add_molecule('Caffeine', fp)
#     fp = open('CID_31260.sdf')
#     db.add_molecule('Isopentanol', fp)
#    # display tables
#     print(db.conn.execute("SELECT * FROM Elements;").fetchall())
#     print(db.conn.execute("SELECT * FROM Molecules;").fetchall())
#     print(db.conn.execute("SELECT * FROM Atoms;").fetchall())
#     print(db.conn.execute("SELECT * FROM Bonds;").fetchall())
#     print(db.conn.execute("SELECT * FROM MoleculeAtom;").fetchall())
#     print(db.conn.execute("SELECT * FROM MoleculeBond;").fetchall())
