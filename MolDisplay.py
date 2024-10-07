import molecule

# radius = {
#     'H': 25,
#     'C': 40,
#     'O': 40,
#     'N': 40,
# }

# element_name = {
#     'H': 'grey',
#     'C': 'black',
#     'O': 'red',
#     'N': 'blue',
# }

header = """<svg version="1.1" width="1000" height="1000"
xmlns="http://www.w3.org/2000/svg">"""

footer = """</svg>"""

offsetx = 500
offsety = 500


class Atom:
    def __init__(self, c_atom):
        self.c_atom = c_atom
        self.z = c_atom.z

    def __str__(self):
        return f"Element: [{self.c_atom.element}] x: {self.c_atom.x}, y: {self.c_atom.y}, z: {self.z}"

    def svg(self):
        return ' <circle cx="%.2f" cy="%.2f" r="%d" fill="url(#%s)"/>\n' % (
            self.c_atom.x * 100.0 + offsetx,  # x coord of the centre of the circle
            self.c_atom.y * 100.0 + offsety,  # y coord of the centre of the circle
            radius[self.c_atom.element],  # radius of the circle
            element_name[self.c_atom.element]  # colour of the circle
        )


class Bond:
    def __init__(self, c_bond):
        self.c_bond = c_bond
        self.z = c_bond.z

    def __str__(self):
        return f"Did not use"

    def svg(self):

        start_x = self.c_bond.x1 * 100 + 500
        start_y = self.c_bond.y1 * 100 + 500
        end_x = self.c_bond.x2 * 100 + 500
        end_y = self.c_bond.y2 * 100 + 500

        delta_x = end_x - start_x
        delta_y = end_y - start_y
        length = (delta_x ** 2 + delta_y ** 2) ** 0.5
        unit_x = delta_x / length
        unit_y = delta_y / length
        point1_x = start_x + unit_y * 10
        point1_y = start_y - unit_x * 10
        point2_x = end_x + unit_y * 10
        point2_y = end_y - unit_x * 10
        point3_x = end_x - unit_y * 10
        point3_y = end_y + unit_x * 10
        point4_x = start_x - unit_y * 10
        point4_y = start_y + unit_x * 10

        # return f' <polygon points="{point1_x:.2f},{point1_y:.2f} {point2_x:.2f},{point2_y:.2f} {point3_x:.2f},{point3_y:.2f} {point4_x:.2f},{point4_y:.2f}" fill="green"/>\n'
        return f' <polygon points="{point4_x:.2f},{point4_y:.2f} {point1_x:.2f},{point1_y:.2f} {point2_x:.2f},{point2_y:.2f} {point3_x:.2f},{point3_y:.2f}" fill="green"/>\n'



class Molecule(molecule.molecule):

    def __str__(self):
        return f"Did not use"

    def parse(self, file):
        data = file.read().split('\n')[4:]

        for line in data:
            if "END" in line:
                break

            line = line.split()

            # Reads Atoms
            if len(line) > 7:
                self.append_atom(line[3], float(line[0]),
                                 float(line[1]), float(line[2]))

            # Reads Bonds
            elif len(line) == 7:
                self.append_bond(int(line[0])-1, int(line[1])-1, int(line[2]))

    def svg(self):
        atomCount, bondCount = 0, 0
        numAtoms = self.atom_no
        numBonds = self.bond_no
        svgString = ""

        # MergeSort
        while atomCount < numAtoms and bondCount < numBonds:
            # If atom z val is < bond z val
            if self.get_atom(atomCount).z < self.get_bond(bondCount).z:
                svgString += Atom(self.get_atom(atomCount)).svg()
                atomCount += 1

            #  If bond z val is < atom z val
            else:
                svgString += Bond(self.get_bond(bondCount)).svg()
                bondCount += 1

        while atomCount < numAtoms:
            svgString += Atom(self.get_atom(atomCount)).svg()
            atomCount += 1

        while bondCount < numBonds:
            svgString += Bond(self.get_bond(bondCount)).svg()
            atomCount += 1

        # SVG String with header and footer
        svgString = header + svgString + footer

        return svgString
