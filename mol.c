#include "mol.h"

#define PI 3.1415926535897932384

void atomset(atom *atom, char element[3], double *x, double *y, double *z)
{
    strcpy(atom->element, element);
    atom->x = *x;
    atom->y = *y;
    atom->z = *z;
}

void atomget(atom *atom, char element[3], double *x, double *y, double *z)
{
    strcpy(element, atom->element);
    *x = atom->x;
    *y = atom->y;
    *z = atom->z;
}

void bondset(bond *bond, unsigned short *a1, unsigned short *a2, atom **atoms, unsigned char *epairs)
{
    bond->epairs = *epairs;
    bond->a1 = *a1;
    bond->a2 = *a2;
    bond->atoms = *atoms;
    compute_coords(bond);
}

void bondget(bond *bond, unsigned short *a1, unsigned short *a2, atom **atoms, unsigned char *epairs)
{
    *epairs = bond->epairs;
    *a1 = bond->a1;
    *a2 = bond->a2;
    *atoms = bond->atoms;
}

molecule *molmalloc(unsigned short atom_max, unsigned short bond_max)
{
    molecule *mol = malloc(sizeof(molecule));
    if (mol == NULL)
    {
        printf("Error allocating memory\n");
        return NULL;
    }
    // Initialize atom values
    mol->atom_max = atom_max;
    mol->atom_no = 0;

    mol->atoms = malloc(sizeof(atom) * atom_max);
    if (mol->atoms == NULL)
    {
        free(mol);
        return NULL;
    }

    mol->atom_ptrs = malloc(sizeof(atom) * atom_max);
    if (mol->atom_ptrs == NULL)
    {
        free(mol->atoms);
        free(mol);
        return NULL;
    }

    // Initialize bond values
    mol->bond_max = bond_max;
    mol->bond_no = 0;

    mol->bonds = malloc(sizeof(bond) * bond_max);
    if (mol->bonds == NULL)
    {
        free(mol->atom_ptrs);
        free(mol->atoms);
        free(mol);
        return NULL;
    }
    mol->bond_ptrs = malloc(sizeof(bond) * bond_max);
    if (mol->bond_ptrs == NULL)
    {
        free(mol->bonds);
        free(mol->atom_ptrs);
        free(mol->atoms);
        free(mol);
        return NULL;
    }
    return mol;
}

molecule *molcopy(molecule *src)
{
    molecule *copy = molmalloc(src->atom_max, src->bond_max);

    if (copy == NULL)
    {
        printf("Error allocating memory\n");
        return NULL;
    }

    for (int i = 0; i < src->atom_no; i++)
    {
        molappend_atom(copy, &src->atoms[i]);
    }
    for (int i = 0; i < src->bond_no; i++)
    {
        molappend_bond(copy, &src->bonds[i]);
    }

    return copy;
}

void molfree(molecule *ptr)
{
    free(ptr->atoms);
    free(ptr->atom_ptrs);
    free(ptr->bonds);
    free(ptr->bond_ptrs);
    free(ptr);
}

void molappend_atom(molecule *molecule, atom *atom)
{
    if (molecule->atom_max == 0)
    {
        // atoms
        molecule->atoms = (struct atom *)realloc(molecule->atoms, sizeof(struct atom));
        if (molecule->atoms == NULL)
        {
            printf("Error allocating memory\n");
            exit(-1);
        }
        // atom_ptrs
        molecule->atom_ptrs = (struct atom **)realloc(molecule->atom_ptrs, sizeof(struct atom *));
        if (molecule->atom_ptrs == NULL)
        {
            printf("Error allocating memory\n");
            exit(-1);
        }

        molecule->atom_max = 1;
        molecule->atoms[molecule->atom_no] = *atom;
        molecule->atom_ptrs[molecule->atom_no] = &molecule->atoms[molecule->atom_no];
    }

    if (molecule->atom_no == molecule->atom_max)
    {
        molecule->atom_max *= 2;
        // atoms
        molecule->atoms = (struct atom *)realloc(molecule->atoms, molecule->atom_max * sizeof(struct atom));
        if (molecule->atoms == NULL)
        {
            printf("Error allocating memory\n");
            exit(-1);
        }
        // atom_ptrs
        molecule->atom_ptrs = (struct atom **)realloc(molecule->atom_ptrs, molecule->atom_max * sizeof(struct atom *));
        if (molecule->atoms == NULL)
        {
            printf("Error allocating memory\n");
            exit(-1);
        }

        molecule->atoms[molecule->atom_no] = *atom;

        for (int i = 0; i < molecule->atom_no; i++)
        {
            molecule->atom_ptrs[i] = &molecule->atoms[i];
        }
        molecule->atom_ptrs[molecule->atom_no] = &molecule->atoms[molecule->atom_no];
    }
    else
    {
        molecule->atoms[molecule->atom_no] = *atom;
        molecule->atom_ptrs[molecule->atom_no] = &molecule->atoms[molecule->atom_no];
    }
    molecule->atom_no += 1;
}

void molappend_bond(molecule *molecule, bond *bond)
{

    if (molecule->bond_max == 0)
    {
        // bonds
        molecule->bonds = (struct bond *)realloc(molecule->bonds, sizeof(struct bond));
        if (molecule->bonds == NULL)
        {
            printf("Error allocating memory\n");
            exit(-1);
        }
        // bond_ptrs
        molecule->bond_ptrs = (struct bond **)realloc(molecule->bond_ptrs, sizeof(struct bond *));
        if (molecule->bond_ptrs == NULL)
        {
            printf("Error allocating memory\n");
            exit(-1);
        }
        molecule->bond_max = 1;
        molecule->bonds[molecule->bond_no] = *bond;
        molecule->bond_ptrs[molecule->bond_no] = &molecule->bonds[molecule->bond_no];
    }

    if (molecule->bond_no == molecule->bond_max)
    {
        molecule->bond_max *= 2;
        // bonds
        molecule->bonds = (struct bond *)realloc(molecule->bonds, molecule->bond_max * sizeof(struct bond));
        if (molecule->bonds == NULL)
        {
            printf("Error allocating memory\n");
            exit(-1);
        }
        // bond ptrs
        molecule->bond_ptrs = (struct bond **)realloc(molecule->bond_ptrs, molecule->bond_max * sizeof(struct bond *));
        if (molecule->bond_ptrs == NULL)
        {
            printf("Error allocating memory\n");
            exit(-1);
        }

        molecule->bonds[molecule->bond_no] = *bond;

        for (int i = 0; i < molecule->bond_no; i++)
        {
            molecule->bond_ptrs[i] = &molecule->bonds[i];
        }
        molecule->bond_ptrs[molecule->bond_no] = &molecule->bonds[molecule->bond_no];
    }
    else
    {
        molecule->bonds[molecule->bond_no] = *bond;
        molecule->bond_ptrs[molecule->bond_no] = &molecule->bonds[molecule->bond_no];
    }
    molecule->bond_no += 1;
}

int atomCompare(const void *atom1, const void *atom2)
{
    const atom **a1 = (const atom **)atom1;
    const atom **a2 = (const atom **)atom2;

    if ((*a1)->z < (*a2)->z)
    {
        return -1;
    }
    if ((*a1)->z > (*a2)->z)
    {
        return 1;
    }
    return 0;
}

int bondCompare(const void *bond1, const void *bond2)
{
    const bond **b1 = (const bond **)bond1;
    const bond **b2 = (const bond **)bond2;

    double z1 = ((*b1)->atoms[(*b1)->a1].z + (*b1)->atoms[(*b1)->a2].z) / 2;
    double z2 = ((*b2)->atoms[(*b2)->a1].z + (*b2)->atoms[(*b2)->a2].z) / 2;

    if (z1 < z2)
    {
        return -1;
    }
    if (z1 > z2)
    {
        return 1;
    }
    return 0;
}

int bond_comp(const void *a, const void *b)
{
    const bond **b1 = (const bond **)a;
    const bond **b2 = (const bond **)b;

    double z1 = ((*b1)->atoms[(*b1)->a1].z + (*b1)->atoms[(*b1)->a2].z) / 2;
    double z2 = ((*b2)->atoms[(*b2)->a1].z + (*b2)->atoms[(*b2)->a2].z) / 2;

    if (z1 < z2)
    {
        return -1;
    }
    if (z1 > z2)
    {
        return 1;
    }
    return 0;
}

void molsort(molecule *molecule)
{
    qsort(molecule->atom_ptrs, molecule->atom_no, sizeof(atom *), atomCompare);
    qsort(molecule->bond_ptrs, molecule->bond_no, sizeof(bond *), bondCompare);
}

void xrotation(xform_matrix xform_matrix, unsigned short deg)
{
    double rad = deg * (PI / 180);
    xform_matrix[0][0] = 1;
    xform_matrix[0][1] = 0;
    xform_matrix[0][2] = 0;

    xform_matrix[1][0] = 0;
    xform_matrix[1][1] = cos(rad);
    xform_matrix[1][2] = -sin(rad);

    xform_matrix[2][0] = 0;
    xform_matrix[2][1] = sin(rad);
    xform_matrix[2][2] = cos(rad);
}

void yrotation(xform_matrix xform_matrix, unsigned short deg)
{
    double rad = deg * (PI / 180);

    xform_matrix[0][0] = cos(rad);
    xform_matrix[0][1] = 0;
    xform_matrix[0][2] = sin(rad);

    xform_matrix[1][0] = 0;
    xform_matrix[1][1] = 1;
    xform_matrix[1][2] = 0;

    xform_matrix[2][0] = -sin(rad);
    xform_matrix[2][1] = 0;
    xform_matrix[2][2] = cos(rad);
}

void zrotation(xform_matrix xform_matrix, unsigned short deg)
{
    double rad = deg * (PI / 180);

    xform_matrix[0][0] = cos(rad);
    xform_matrix[0][1] = -sin(rad);
    xform_matrix[0][2] = 0;

    xform_matrix[1][0] = sin(rad);
    xform_matrix[1][1] = cos(rad);
    xform_matrix[1][2] = 0;

    xform_matrix[2][0] = 0;
    xform_matrix[2][1] = 0;
    xform_matrix[2][2] = 1;
}

void compute_coords(bond *bond)
{
    // Get pointers to the atoms in the bond using the indices a1 and a2
    atom *atom1 = &bond->atoms[bond->a1];
    atom *atom2 = &bond->atoms[bond->a2];

    // Compute bond coordinates and length
    bond->x1 = atom1->x;
    bond->y1 = atom1->y;
    bond->x2 = atom2->x;
    bond->y2 = atom2->y;
    bond->z = (atom1->z + atom2->z) / 2.0;
    bond->len = sqrt(pow(bond->x2 - bond->x1, 2) + pow(bond->y2 - bond->y1, 2));

    // Compute bond vector components
    bond->dx = (bond->x2 - bond->x1) / bond->len;
    bond->dy = (bond->y2 - bond->y1) / bond->len;
}

void mol_xform(molecule *molecule, xform_matrix matrix)
{
    double x, y, z;
    double *temp = malloc(3 * sizeof(double));

    if (temp == NULL)
    {
        printf("Error allocating memory\n");
        exit(-1);
    }

    for (int i = 0; i < molecule->atom_no; i++)
    {
        x = molecule->atoms[i].x;
        y = molecule->atoms[i].y;
        z = molecule->atoms[i].z;

        temp[0] = matrix[0][0] * x + matrix[0][1] * y + matrix[0][2] * z;
        temp[1] = matrix[1][0] * x + matrix[1][1] * y + matrix[1][2] * z;
        temp[2] = matrix[2][0] * x + matrix[2][1] * y + matrix[2][2] * z;

        molecule->atoms[i].x = temp[0];
        molecule->atoms[i].y = temp[1];
        molecule->atoms[i].z = temp[2];
    }

    for (int i = 0; i < molecule->bond_no; i++)
    {
        bond *b = &molecule->bonds[i];
        compute_coords(b);
    }
    free(temp);
}
// export LD_LIBRARY_PATH=.
