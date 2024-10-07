import sys
import os
from io import BytesIO, TextIOWrapper
from http.server import HTTPServer, BaseHTTPRequestHandler
import MolDisplay
from MolDisplay import Molecule
from molsql import Database
import cgi
import sqlite3
import json
import urllib


FILE_DIR = os.path.dirname(os.path.abspath(__file__))

publicFiles = ["/index.html","/add-removeElements.html","/sdf-molecules.html"]

class MyHandler(BaseHTTPRequestHandler):
    conn = sqlite3.connect('molecules.db')
    def do_GET(self):
        if self.path in publicFiles:      
            self.send_response(200)  # OK
            self.send_header("Content-type", "text/html")
            fp = open (self.path[1:]) # removes the /
            page = fp.read()
            fp.close()
            self.send_header("Content-length", len(page))
            self.end_headers()
            self.wfile.write(bytes(page, "utf-8"))

        elif self.path == "/get-molecules":
            cursor = db.conn.cursor()
            cursor.execute("""
               SELECT Molecules.NAME, COUNT(DISTINCT MoleculeAtom.ATOM_ID), COUNT(DISTINCT MoleculeBond.BOND_ID)
               FROM Molecules
               LEFT JOIN MoleculeAtom ON MoleculeAtom.MOLECULE_ID = Molecules.MOLECULE_ID
               LEFT JOIN Atoms ON Atoms.ATOM_ID = MoleculeAtom.ATOM_ID
               LEFT JOIN MoleculeBond ON MoleculeBond.MOLECULE_ID = Molecules.MOLECULE_ID
               LEFT JOIN Bonds ON Bonds.BOND_ID = MoleculeBond.BOND_ID
               GROUP BY Molecules.NAME
            """)
            rows = cursor.fetchall()
            molecules = []
            for row in rows:
               molecules.append({"name": row[0], "num_atoms": row[1], "num_bonds": row[2]})
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(bytes(json.dumps(molecules), "utf-8"))
           
        elif self.path.endswith (".svg"):
      
          svgPath = os.path.join(FILE_DIR, self.path[1:])
          with open(svgPath, 'rb') as f:
                svg_data = f.read()
                self.send_response(200)
                self.send_header("Content-type", "image/svg+xml")
                self.end_headers()
                self.wfile.write(svg_data)
           
        elif self.path == "/get-elements":
           cursor = db.conn.cursor()
           cursor.execute("""
             SELECT ELEMENT_NO, ELEMENT_CODE, ELEMENT_NAME, COLOUR1, COLOUR2, COLOUR3, RADIUS
             FROM Elements
           """)
           rows = cursor.fetchall()
           elements = []
           for row in rows:
              elements.append({
              "ELEMENT_NO": row[0],
              "ELEMENT_CODE": row[1],
              "ELEMENT_NAME": row[2],
              "COLOUR1": row[3],
              "COLOUR2": row[4],
              "COLOUR3": row[5],
              "RADIUS": row[6]
            })
           # Send the response
           self.send_response(200)
           self.send_header('Content-type', 'application/json')
           self.end_headers()
           self.wfile.write(json.dumps(elements).encode())
           

        elif self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            fp = open ("index.html")
            page = fp.read()
            fp.close()
            self.send_header("Content-length", len(page))
            self.end_headers()
            self.wfile.write(bytes(page, "utf-8"))


        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(bytes("404: not found", "utf-8"))

    def do_POST(self):    

      if self.path == "/sdf-molecules":
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST'})
        uploadedFile = form['sdf-file']
        fileData = uploadedFile.file.read()
        fileWrapper = TextIOWrapper(BytesIO(fileData))
        mol = Molecule()

        moleculeName = form.getvalue('molecule-name')


        

        # Call add_molecule
        db.add_molecule(moleculeName,fileWrapper)

        MolDisplay.radius = db.radius();
        MolDisplay.element_name = db.element_name();
        MolDisplay.header += db.radial_gradients();


       # Create SVG for uploaded molecule
        mol = db.load_mol(moleculeName)
        mol.sort()
        with open(moleculeName + ".svg", "w") as fp:
           fp.write(mol.svg())
        fp.close();

        # Create SVG
        svg = mol.svg()


        # Send SVG
        self.send_response(200)
        self.send_header("Content-type", "image/svg+xml")
        self.end_headers()
        self.wfile.write(bytes(svg, "utf-8"))

      elif self.path == "/add-element":
         content_length = int(self.headers['Content-Length'])
         post_data = self.rfile.read(content_length)
         post_data = post_data.decode("utf-8")
         # Parse the POST data
         data = {}
         for item in post_data.split("&"):
            key, value = item.split("=")
            data[key] = urllib.parse.unquote(value)

         cursor = db.conn.cursor()
         cursor.execute("SELECT * FROM Elements WHERE element_name = ? OR element_code = ?", 
                                    (data["element-name"], data["element-code"]))
         
         existing_elements = cursor.fetchall()
         if existing_elements:
           self.send_response(400) 
           self.end_headers()
           self.wfile.write(b"Element with same name or code already exists")
           return
          
         db['Elements'] = ((data["element-number"], data["element-code"], data["element-name"], data["color-1"], data["color-2"], data["color-3"], data["radius"]))
         db.conn.commit()

         self.send_response(200)
         self.end_headers()

      else:
        self.send_response(404)
        self.end_headers()
        self.wfile.write(bytes("404: not found", "utf-8"))

    def do_DELETE(self):
      if self.path == "/remove-molecule":
        # Extract the molecule name from the URL
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        molecule_name = data['name']

        # Delete the molecule from the database
        cursor = db.conn.cursor()
        cursor.execute("DELETE FROM Molecules WHERE NAME = ?", (molecule_name,))
        db.conn.commit()

        # Delete SVG file
        svgPath = "./"+molecule_name+".svg"
        if os.path.exists(svgPath):
          os.remove(svgPath)

        # Send a response indicating that the molecule was deleted
        response = {'status': 'success'}
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')

        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

      elif self.path.startswith("/delete-element"):
          # Extract the element name from the URL
          element_name = self.path.split('/')[-1]
          # print(element_name)

          # Delete the element from the database
          cursor = db.conn.cursor()
          cursor.execute("DELETE FROM Elements WHERE ELEMENT_NAME = ?", (element_name,))
          db.conn.commit()

          MolDisplay.radius = db.radius();
          MolDisplay.element_name = db.element_name();
          MolDisplay.header += db.radial_gradients();

          # Send a response indicating that the element was deleted
          response = {'status': 'success', 'message': 'Element deleted successfully'}
          self.send_response(200)
          self.send_header("Content-type", "text/plain")
          self.end_headers()
          self.wfile.write(json.dumps(response).encode('utf-8'))

      else:
         self.send_response(400)
         self.send_header("Content-type", "text/plain")
         self.end_headers()
         self.wfile.write(bytes("Invalid request data", "utf-8"))


db = Database(reset=False)
# if db == None:
db.create_tables()


# Database('./molecules.db')
# db.create_tables()

print('-+-+-+-+-+-+-+-+-+-+-+-+')
print('Starting server...')
print('-+-+-+-+-+-+-+-+-+-+-+-+')

httpd = HTTPServer(('localhost', int(sys.argv[1])), MyHandler)
httpd.serve_forever()
