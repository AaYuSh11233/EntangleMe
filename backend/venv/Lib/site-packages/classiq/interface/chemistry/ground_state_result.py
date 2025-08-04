from pydantic import BaseModel


class MoleculeResult(BaseModel):
    energy: float
    nuclear_repulsion_energy: float
    total_energy: float
    hartree_fock_energy: float
