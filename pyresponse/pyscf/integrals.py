from pyresponse.integrals import JK, IntegralLabel, Integrals, IntegralSymmetry

ANGMOM_COMMON_GAUGE = IntegralLabel("cint1e_cg_irxp_sph", 3)
ANGMOM_GIAO = IntegralLabel("cint1e_giao_irjxp_sph", 3)
DIPOLE = IntegralLabel("cint1e_r_sph", 3)
DIPVEL = IntegralLabel("cint1e_ipovlp_sph", 3)
KINETIC = IntegralLabel("int1e_kin")
A11PART_GIAO = IntegralLabel("int1e_giao_a11part", 9)
A11PART_CG = IntegralLabel("int1e_cg_a11part", 9)
A01 = IntegralLabel("int1e_a01gp", 9)
NUCLEAR = IntegralLabel("int1e_nuc")
SO_1e = IntegralLabel("int1e_prinvxp", 3, IntegralSymmetry.ANTISYMMETRIC)
NSO_1e = IntegralLabel("int1e_pnucxp", 3, IntegralSymmetry.ANTISYMMETRIC)
SO_SPHER_1e = IntegralLabel("cint1e_prinvxp_sph", 3)


class IntegralsPyscf(Integrals):
    def __init__(self, pyscfmol, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.mol = pyscfmol

    def _compute(self, label):
        if label.symmetry == IntegralSymmetry.ANTISYMMETRIC:
            return self.mol.intor_asymmetric(label.label, comp=label.comp)
        return self.mol.intor(label.label, comp=label.comp)


class JKPyscf(JK):
    def __init__(self, pyscfmol, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.mol = pyscfmol

    def compute_from_density(self, D):
        raise NotImplementedError

    def compute_from_mocoeffs(self, C_left, C_right=None):
        raise NotImplementedError
