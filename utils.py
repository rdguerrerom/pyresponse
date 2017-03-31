import numpy as np

from itertools import accumulate


def form_results(vecs_property, vecs_response):
    assert vecs_property.shape[1:] == vecs_response.shape[1:]
    assert len(vecs_property.shape) == 3
    assert vecs_property.shape[2] == 1
    results = np.dot(vecs_property[:, :, 0], vecs_response[:, :, 0].T)
    return results


def np_load(filename):
    arr = np.load(filename)
    if isinstance(arr, np.lib.npyio.NpzFile):
        # Make the assumption that there's only a single array
        # present, even though *.npz files can hold multiple arrays.
        arr = arr.items()[0][1]
    return arr


def parse_int_file_2(filename, dim):
    mat = np.zeros(shape=(dim, dim))
    with open(filename) as fh:
        contents = fh.readlines()
    for line in contents:
        mu, nu, intval = [float(x) for x in line.split()]
        mu, nu = int(mu - 1), int(nu - 1)
        mat[mu, nu] = mat[nu, mu] = intval
    return mat


def repack_matrix_to_vector(mat):
    return np.reshape(mat, -1, order='F')


def clean_dalton_label(original_label):
    cleaned_label = original_label.lower().replace(' ', '_')
    return cleaned_label


def dalton_label_to_operator(label):

    label = clean_dalton_label(label)

    from cphf import Operator

    coord1_to_slice = {
        'x': 0, 'y': 1, 'z': 2,
    }
    coord2_to_slice = {
        'xx': 0, 'xy': 1, 'xz': 2, 'yy': 3, 'yz': 4, 'zz': 5,
        'yx': 1, 'zx': 2, 'zy': 4,
    }
    slice_to_coord1 = {v:k for (k, v) in coord1_to_slice.items()}

    # dipole length
    if 'diplen' in label:
        operator_label = 'dipole'
        _coord = label[0]
        slice_idx = coord1_to_slice[_coord]
        is_imaginary = False
        is_spin_dependent = False
    # dipole velocity
    elif 'dipvel' in label:
        operator_label = 'dipvel'
        _coord = label[0]
        slice_idx = coord1_to_slice[_coord]
        is_imaginary = True
        is_spin_dependent = False
    # angular momentum
    elif 'angmom' in label:
        operator_label = 'angmom'
        _coord = label[0]
        slice_idx = coord1_to_slice[_coord]
        is_imaginary = True
        is_spin_dependent = False
    # spin-orbit
    elif 'spnorb' in label:
        operator_label = 'spinorb'
        _coord = label[0]
        slice_idx = coord1_to_slice[_coord]
        is_imaginary = True
        is_spin_dependent = True
        _nelec = label[1]
        if _nelec in ('1', '2'):
            operator_label += _nelec
        # combined one- and two-electron
        elif _nelec in (' ', '_'):
            operator_label += 'c'
        else:
            pass
    # Fermi contact
    elif 'fc' in label:
        operator_label = 'fermi'
        _atomid = label[6:6+2]
        slice_idx = int(_atomid) - 1
        is_imaginary = False
        is_spin_dependent = True
    # spin-dipole
    elif 'sd' in label:
        operator_label = 'sd'
        _coord_atom = label[3:3+3]
        _coord = label[7]
        _atomid = (int(_coord_atom) - 1) // 3
        _coord_1 = (int(_coord_atom) - 1) % 3
        _coord_2 = slice_to_coord1[_coord_1] + _coord
        slice_idx = (6 * _atomid) + coord2_to_slice[_coord_2]
        is_imaginary = False
        is_spin_dependent = True
    # TODO SD+FC?
    # nucleus-orbit
    elif 'pso' in label:
        operator_label = 'pso'
        # TODO coord manipulation
        is_imaginary = True
        # TODO is this correct?
        is_spin_dependent = False
        # FIXME
        slice_idx=None
    else:
        operator_label = ''
        is_imaginary = None
        is_spin_dependent = None
        slice_idx = None

    operator = Operator(
        label=operator_label,
        is_imaginary=is_imaginary,
        is_spin_dependent=is_spin_dependent,
        slice_idx=slice_idx,
    )

    return operator


def get_reference_value_from_file(filename, hamiltonian, spin, frequency, label_1, label_2):
    # TODO need to pass the frequency as a string identical to the one
    # found in the file, can't pass a float due to fp error; how to
    # get around this?
    found = False
    with open(filename) as fh:
        for line in fh:
            tokens = line.split()
            # no comments allowed for now
            assert len(tokens) == 6
            l_hamiltonian, l_spin, l_frequency, l_label_1, l_label_2, l_val = tokens
            if (l_hamiltonian == hamiltonian) and \
               (l_spin == spin) and \
               (l_frequency == frequency) and \
               (l_label_1 == label_1) and \
               (l_label_2 == label_2):
                ref = float(l_val)
                found = True

    if not found:
        # TODO blow up, "Could not find reference value"
        pass

    return ref


def read_file_occupations(filename):
    with open(filename) as fh:
        contents = fh.read().strip()
    tokens = contents.split()
    assert len(tokens) == 4
    nocc_alph, nvirt_alph, nocc_beta, nvirt_beta = [int(x) for x in tokens]    
    return [nocc_alph, nvirt_alph, nocc_beta, nvirt_beta]


def read_file_1(filename):
    elements = []
    with open(filename) as fh:
        n_elem = int(next(fh))
        for line in fh:
            elements.append(float(line))
    assert len(elements) == n_elem
    return np.array(elements, dtype=float)


def read_file_2(filename):
    elements = []
    with open(filename) as fh:
        n_rows, n_cols = [int(x) for x in next(fh).split()]
        for line in fh:
            elements.append(float(line))
    assert len(elements) == (n_rows * n_cols)
    # The last index is the fast index (cols).
    return np.reshape(np.array(elements, dtype=float), (n_rows, n_cols))


def read_file_3(filename):
    elements = []
    with open(filename) as fh:
        n_slices, n_rows, n_cols = [int(x) for x in next(fh).split()]
        for line in fh:
            elements.append(float(line))
    assert len(elements) == (n_rows * n_cols * n_slices)
    return np.reshape(np.array(elements, dtype=float), (n_slices, n_rows, n_cols))


def read_file_4(filename):
    elements = []
    with open(filename) as fh:
        n_d1, n_d2, n_d3, n_d4 = [int(x) for x in next(fh).split()]
        for line in fh:
            elements.append(float(line))
    assert len(elements) == (n_d1 * n_d2 * n_d3 * n_d4)
    return np.reshape(np.array(elements, dtype=float), (n_d1, n_d2, n_d3, n_d4))


def occupations_from_pyscf_mol(mol, C):
    norb = C.shape[-1]
    nocc_a, nocc_b = mol.nelec
    nvirt_a, nvirt_b = norb - nocc_a, norb - nocc_b
    occupations = (nocc_a, nvirt_a, nocc_b, nvirt_b)
    return occupations


def occupations_from_sirifc(ifc):
    nocc_a, nocc_b = ifc.nisht + ifc.nasht, ifc.nisht
    norb = ifc.norbt
    nvirt_a, nvirt_b = norb - nocc_a, norb - nocc_b
    occupations = (nocc_a, nvirt_a, nocc_b, nvirt_b)
    return occupations


class Splitter:
    def __init__(self, widths):
        self.start_indices = [0] + list(accumulate(widths))[:-1]
        self.end_indices = list(accumulate(widths))

    def split(self, line):
        elements = [line[start:end].strip()
                    for (start, end) in zip(self.start_indices, self.end_indices)]
        for i in range(1, len(elements)):
            if elements[-1] == '':
                elements.pop()
            else:
                break
        return elements


def fix_mocoeffs_shape(mocoeffs):
    shape = mocoeffs.shape
    assert len(shape) in (2, 3)
    if len(shape) == 2:
        mocoeffs_new = mocoeffs[np.newaxis, ...]
    else:
        mocoeffs_new = mocoeffs
    return mocoeffs_new


def fix_moenergies_shape(moenergies):
    shape = moenergies.shape
    return moenergies_new


def read_dalton_propfile(tmpdir):
    proplist = []
    with open(os.path.join(tmpdir, 'DALTON.PROP')) as propfile:
        proplines = propfile.readlines()
    splitter = Splitter([5, 3, 4, 11, 23, 9, 9, 9, 9, 23, 23, 23, 4, 4, 4])
    for line in proplines:
        sline = splitter.split(line)
        # print(sline)
        proplist.append(sline)
    return proplist


