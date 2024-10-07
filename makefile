CC = clang
CFLAGS = -Wall -std=c99 -pedantic
PYTHON_HEADER = /usr/include/python3.7m
LIBS = -L/usr/lib/python3.7/config-3.7m-x86_64-linux-gnu -lpython3.7m

all: libmol.so _molecule.so mol.o molecule_wrap.o

libmol.so: mol.o
	$(CC) mol.o -shared -o libmol.so -lm

mol.o: mol.c mol.h
	$(CC) $(CFLAGS) -c mol.c -fpic -o mol.o

molecule_wrap.c: molecule.i mol.h
	swig3.0 -python molecule.i

molecule_wrap.o: molecule_wrap.c
	$(CC) $(CFLAGS) -I$(PYTHON_HEADER) -c molecule_wrap.c -fpic

_molecule.so: molecule_wrap.o libmol.so
	$(CC) molecule_wrap.o -shared -o _molecule.so -L. -lmol $(LIBS)
clean:
	rm -f *.o *.so

# // REMOVE THESE AFTER
#  export LD_LIBRARY_PATH=.
# python3 server.py 55582

