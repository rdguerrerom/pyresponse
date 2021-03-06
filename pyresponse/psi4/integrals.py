from enum import Enum, auto, unique

import numpy as np

import psi4

from pyresponse.integrals import JK, IntegralLabel, Integrals

DIPOLE = object()
DIPVEL = object()
ANGMOM_COMMON_GAUGE = object()


class IntegralsPsi4(Integrals):
    def __init__(self, wfn_or_mol, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if isinstance(wfn_or_mol, psi4.core.Molecule):
            wfn = psi4.core.Wavefunction.build(
                wfn_or_mol, psi4.core.get_global_option("BASIS")
            )
        elif isinstance(wfn_or_mol, psi4.core.Wavefunction):
            wfn = wfn_or_mol
        else:
            raise RuntimeError
        self._mints = psi4.core.MintsHelper(wfn)

    def _compute(self, label):
        if label == DIPOLE:
            return np.stack([np.asarray(Mc) for Mc in self._mints.ao_dipole()])
        elif label == DIPVEL:
            return np.stack([np.asarray(Mc) for Mc in self._mints.ao_nabla()])
        elif label == ANGMOM_COMMON_GAUGE:
            return np.stack([np.asarray(Lc) for Lc in self._mints.ao_angular_momentum()])
        else:
            raise RuntimeError


class JKPsi4(JK):
    def __init__(self, wfn, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._jk = psi4.core.JK.build(wfn.basisset())
        self._jk.initialize()

    def compute_from_density(self, D):
        raise NotImplementedError

    def compute_from_mocoeffs(self, C_left, C_right=None):
        self._jk.C_clear()
        self._jk.C_left_add(psi4.core.Matrix.from_array(C_left))
        if C_right is not None:
            if len(C_left) != len(C_right):
                raise ValueError(
                    "JK: length of left and right MO coefficient matrices is not equal"
                )
            self._jk.C_right_add(psi4.core.Matrix.from_array(C_right))
        self._jk.compute()
        return self._jk.J()[0].np, self._jk.K()[0].np
