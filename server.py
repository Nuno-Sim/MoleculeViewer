import sys
from io import BytesIO, TextIOWrapper
from http.server import HTTPServer, BaseHTTPRequestHandler
from MolDisplay import Molecule

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)  # OK
            self.send_header("Content-type", "text/html")
            self.send_header("Content-length", len(home_page))
            self.end_headers()

            self.wfile.write(bytes(home_page, "utf-8"))

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(bytes("404: not found", "utf-8"))

    def do_POST(self):
      if self.path == "/molecule":
        
        fileLength = int(self.headers.get("Content-length"))

        fileContents = self.rfile.read(fileLength)

        fileWrapper = TextIOWrapper(BytesIO(fileContents))

        mol = Molecule()

        # Parse Molecule    
        mol.parse(fileWrapper)

        # Sort Molecule
        mol.sort()

        # Create SVG
        svg = mol.svg()

        # Send SVG
        self.send_response(200)
        self.send_header("Content-type", "image/svg+xml")
        self.end_headers()
        self.wfile.write(bytes(svg, "utf-8"))

      else:
        self.send_response(404)
        self.end_headers()
        self.wfile.write(bytes("404: not found", "utf-8"))

home_page = """ 
<html>
<head>
<title> File Upload </title>
</head>
<body>
<h1> File Upload </h1>
<form action="molecule" enctype="multipart/form-data" method="post">
<p>
<input type="file" id="sdf_file" name="filename"/>
</p>
<p>
<input type="submit" value="Upload"/>
</p>
</form>
</body>
</html>
""";

print('-+-+-+-+-+-+-+-+-+-+-+-+')
print('Starting server...')
print('-+-+-+-+-+-+-+-+-+-+-+-+')

httpd = HTTPServer(('localhost', int(sys.argv[1])), MyHandler)
httpd.serve_forever()
