import Bio.PDB
from .data import Data
import numpy as np


class PDB(Data):

    def __init__(self, filepath, chain=None, datatype="pdb", offset=None, fasta=None):
        self.datatype = datatype
        get_offset = offset is None
        get_seq = fasta is None
        self.sequence = ""
        if chain is None:
            self.chain = " "
        else:
            self.chain = chain
        if get_offset or get_seq:
            self.get_sequence_offset(filepath, get_seq, get_offset)
        if not get_offset:
            self.offset = offset
        if not get_seq:
            super().__init__(filepath=fasta)
        self.read_pdb(filepath)
        self.path = filepath
        self.distance_matrix = {}

    def get_sequence_offset(self, pdb, get_seq=True, get_offset=True):
        with open(pdb) as file:
            for line in file.readlines():
                line = [field.strip() for field in line.split()]
                if line[0] == "DBREF" and line[2] == self.chain and get_offset:
                    self.offset = int(line[3])-1
                if line[0] == "SEQRES" and line[2] == self.chain and get_seq:
                    for nt in line[4:]:
                        valid = nt[0].upper() in 'GUACT'
                        if valid and (len(nt) == 3) and nt.endswith("TP"):
                            self.sequence += nt[0]
                        elif valid and (len(nt) == 1):
                            self.sequence += nt[0]
                        else:
                            raise ValueError('invalid nt in SEQRES: ' + nt)

    def read_pdb(self, pdb):
        if pdb.split('.')[-1] == "pdb":
            parser = Bio.PDB.PDBParser(QUIET=True)
        elif pdb.split('.')[-1] == 'cif':
            parser = Bio.PDB.MMCIFParser(QUIET=True)
        self.pdb = parser.get_structure('RNA', pdb)
        self.pdb_idx = []
        self.pdb_seq = []
        for res in self.pdb[0][self.chain].get_residues():
            res_id = res.get_id()
            res_seq = res.get_resname()
            if res_id[0] == " ":
                self.pdb_idx.append(res_id[1])
                self.pdb_seq.append(res_seq.strip())
        self.pdb_idx = np.array(self.pdb_idx)
        self.set_indices()

    def set_indices(self):
        for i in range(len(self.sequence)):
            correct_offset = True
            for pdb_nt, pdb_idx in zip(self.pdb_seq, self.pdb_idx):
                if self.sequence[pdb_idx-i-1] != pdb_nt:
                    correct_offset = False
                    break
            if correct_offset:
                self.offset = i
                break
        if not correct_offset:
            print('PDB entries could not be matched to sequence.')

    def get_pdb_idx(self, seq_idx):
        return seq_idx + self.offset

    def get_seq_idx(self, pdb_idx):
        return pdb_idx - self.offset

    def is_valid_idx(self, pdb_idx=None, seq_idx=None):
        if pdb_idx is not None and pdb_idx in self.pdb_idx:
            return True
        elif seq_idx is not None and (seq_idx in (self.pdb_idx - self.offset)):
            return True
        else:
            return False

    def get_xyz_coord(self, nt, atom):
        pdb_idx = self.get_pdb_idx(nt)
        if atom == "DMS":
            if self.sequence.upper()[nt-1] in "AG":
                atom = "N1"
            elif self.sequence.upper()[nt-1] in "UC":
                atom = "N3"
        xyz = [float(c) for c in self.pdb[0][self.chain]
               [int(pdb_idx)][atom].get_coord()]
        return xyz

    def get_distance(self, i, j, atom="O2'"):
        if atom in self.distance_matrix.keys():
            return self.distance_matrix[atom][i-1, j-1]
        if self.is_valid_idx(seq_idx=i) and self.is_valid_idx(seq_idx=j):
            xi, yi, zi = self.get_xyz_coord(i, atom)
            xj, yj, zj = self.get_xyz_coord(j, atom)
            distance = ((xi-xj)**2 + (yi-yj)**2 + (zi-zj)**2)**0.5
        else:
            distance = 1000
        return distance

    def get_distance_matrix(self, atom="O2'"):
        if atom in self.distance_matrix.keys():
            return self.distance_matrix[atom]
        x = np.full(self.length, np.nan)
        y = np.full(self.length, np.nan)
        z = np.full(self.length, np.nan)
        for i in (self.pdb_idx - self.offset):
            x[i-1], y[i-1], z[i-1] = self.get_xyz_coord(i, atom)
        a = x - x[:, np.newaxis]
        b = y - y[:, np.newaxis]
        c = z - z[:, np.newaxis]
        matrix = np.sqrt(a*a + b*b + c*c)
        self.distance_matrix[atom] = np.nan_to_num(matrix, nan=1000)
        return matrix
