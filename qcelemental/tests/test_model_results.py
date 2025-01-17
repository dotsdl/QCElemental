import copy

import numpy as np
import pytest

import qcelemental as qcel
from qcelemental.models import basis

center_data = {
    "bs_sto3g_h": {
        "electron_shells": [{
            "harmonic_type": "spherical",
            "angular_momentum": [0],
            "exponents": [3.42525091, 0.62391373, 0.16885540],
            "coefficients": [[0.15432897, 0.53532814, 0.44463454]]
        }]
    },
    "bs_sto3g_o": {
        "electron_shells": [{
            "harmonic_type": "spherical",
            "angular_momentum": [0],
            "exponents": [130.70939, 23.808861, 6.4436089],
            "coefficients": [[0.15432899, 0.53532814, 0.44463454]]
        }, {
            "harmonic_type":
            "cartesian",
            "angular_momentum": [0, 1],
            "exponents": [5.0331513, 1.1695961, 0.3803890],
            "coefficients": [[-0.09996723, 0.39951283, 0.70011547], [0.15591629, 0.60768379, 0.39195739]]
        }, {
            "harmonic_type":
            "cartesian",
            "angular_momentum": [0],
            "exponents": [5.0331513, 1.1695961, 0.3803890],
            "coefficients": [[-5.09996723, 0.39951283, 0.70011547], [0.15591629, 0.60768379, 0.39195739]]
        }]
    },
    "bs_def2tzvp_zr": {
        "electron_shells": [{
            "harmonic_type": "spherical",
            "angular_momentum": [0],
            "exponents": [11.000000000, 9.5000000000, 3.6383667759, 0.76822026698],
            "coefficients": [[-0.19075595259, 0.33895588754, 0.0000000, 0.0000000],
                             [0.0000000, 0.0000000, 1.0000000000, 0.0000000]]
        }, {
            "harmonic_type": "spherical",
            "angular_momentum": [2],
            "exponents": [4.5567957795, 1.2904939799, 0.51646987229],
            "coefficients": [[-0.96190569023E-09, 0.20569990155, 0.41831381851], [0.0000000, 0.0000000, 0.0000000],
                             [0.0000000, 0.0000000, 0.0000000]]
        }, {
            "harmonic_type": "spherical",
            "angular_momentum": [3],
            "exponents": [0.3926100],
            "coefficients": [[1.0000000]]
        }],
        "ecp_electrons": 28,
        "ecp_potentials": [{
            "ecp_type": "scalar",
            "angular_momentum": [0],
            "r_exponents": [2, 2, 2, 2],
            "gaussian_exponents": [7.4880494, 3.7440249, 6.5842120, 3.2921060],
            "coefficients": [[135.15384419, 15.55244130, 19.12219811, 2.43637549]]
        }, {
            "ecp_type": "spinorbit",
            "angular_momentum": [1],
            "r_exponents": [2, 2, 2, 2],
            "gaussian_exponents": [6.4453779, 3.2226886, 6.5842120, 3.2921060],
            "coefficients": [[87.78499169, 11.56406599, 19.12219811, 2.43637549]]
        }]
    }
} # yapf: disable

@pytest.fixture(scope="function")
def result_data_fixture():
    mol = qcel.models.Molecule.from_data("""
        O 0 0 0
        H 0 0 2
        H 0 2 0
    """)

    return {
        "molecule": mol,
        "driver": "energy",
        "model": {
            "method": "UFF"
        },
        "return_result": 5,
        "success": True,
        "properties": {},
        "provenance": {
            "creator": "qcel"
        }
    }


@pytest.fixture(scope="function")
def wavefunction_data_fixture(result_data_fixture):
    bas = basis.BasisSet(name="custom_basis",
                         center_data=center_data,
                         atom_map=["bs_sto3g_o", "bs_sto3g_h", "bs_sto3g_h"])
    c_matrix = np.random.rand(bas.nbf, bas.nbf)
    result_data_fixture["protocols"] = {"wavefunction": "all"}
    result_data_fixture["wavefunction"] = {
        "basis": bas,
        "restricted": True,
        "scf_orbitals_a": c_matrix,
        "orbitals_a": "scf_orbitals_a"
    }

    return result_data_fixture


@pytest.fixture(scope="function")
def optimization_data_fixture(result_data_fixture):

    trajectory = []
    energies = []
    for x in range(5):
        result = result_data_fixture.copy()
        result["return_result"] = x
        trajectory.append(result)
        energies.append(x)

    ret = {
        "initial_molecule": result_data_fixture["molecule"],
        "final_molecule": result_data_fixture["molecule"],
        "trajectory": trajectory,
        "energies": energies,
        "success": True,
        "provenance": {
            "creator": "qcel"
        },
        "input_specification": {
            "model": {
                "method": "UFF"
            }
        }
    }

    return ret


@pytest.mark.parametrize("center_name", center_data.keys())
def test_basis_shell_centers(center_name):
    assert basis.BasisCenter(**center_data[center_name])


def test_basis_set_build():
    bas = basis.BasisSet(name="custom_basis",
                         center_data=center_data,
                         atom_map=["bs_sto3g_o", "bs_sto3g_h", "bs_sto3g_h", "bs_def2tzvp_zr"])

    assert len(bas.center_data) == 3
    assert len(bas.atom_map) == 4
    assert bas.nbf == 21

    es = bas.center_data["bs_sto3g_o"].electron_shells
    assert es[0].is_contracted() is False
    assert es[1].is_contracted() is False
    assert es[2].is_contracted()


def test_basis_electron_center_raises():
    data = center_data["bs_sto3g_h"]["electron_shells"][0].copy()

    # Check bad coefficient length
    bad_coef = data.copy()
    bad_coef["coefficients"] = [[5, 3]]
    with pytest.raises(ValueError) as e:
        basis.ElectronShell(**bad_coef)

    assert "does not match the" in str(e.value)

    # Check bad fused shell
    bad_fused = data.copy()
    bad_fused["angular_momentum"] = [0, 1]
    with pytest.raises(ValueError) as e:
        basis.ElectronShell(**bad_fused)

    assert "fused shell" in str(e.value)


def test_basis_ecp_center_raises():
    # Check coefficients
    data = center_data["bs_def2tzvp_zr"]["ecp_potentials"][0].copy()
    data["coefficients"] = [[5, 3]]

    with pytest.raises(ValueError):
        basis.ECPPotential(**data)

    # Check gaussian_exponents
    data = center_data["bs_def2tzvp_zr"]["ecp_potentials"][0].copy()
    data["gaussian_exponents"] = [5, 3]

    with pytest.raises(ValueError):
        basis.ECPPotential(**data)


def test_basis_map_raises():

    with pytest.raises(ValueError) as e:
        assert basis.BasisSet(name="custom_basis", center_data=center_data, atom_map=["something_odd"])


def test_result_build(result_data_fixture):
    ret = qcel.models.Result(**result_data_fixture)
    assert ret.wavefunction is None


def test_result_build_wavefunction_delete(wavefunction_data_fixture):
    del wavefunction_data_fixture["protocols"]
    ret = qcel.models.Result(**wavefunction_data_fixture)
    assert ret.wavefunction is None


def test_wavefunction_build(wavefunction_data_fixture):
    assert qcel.models.Result(**wavefunction_data_fixture)


def test_wavefunction_matrix_size_error(wavefunction_data_fixture):

    wavefunction_data_fixture["wavefunction"]["scf_orbitals_a"] = np.random.rand(2, 2)
    with pytest.raises(ValueError) as e:
        qcel.models.Result(**wavefunction_data_fixture)

    assert "castable to shape" in str(e.value)


def test_wavefunction_return_result_pointer(wavefunction_data_fixture):

    del wavefunction_data_fixture["wavefunction"]["scf_orbitals_a"]
    with pytest.raises(ValueError) as e:
        qcel.models.Result(**wavefunction_data_fixture)

    assert "does not exist" in str(e.value)


@pytest.mark.parametrize("protocol, restricted, provided, expected", [
    ('none', True, ['orbitals_a', 'orbitals_b'], []),
    (None, True, ['orbitals_a', 'orbitals_b'], []),
    ('all', False, ['orbitals_a', 'orbitals_b'], ['orbitals_a', 'orbitals_b']),
    ('all', True, ['orbitals_a', 'orbitals_b'], ['orbitals_a']),
    ('orbitals_and_eigenvalues', False, ['orbitals_a', 'orbitals_b', 'fock_a', 'fock_b'], ['orbitals_a', 'orbitals_b'
                                                                                           ]),
    ('orbitals_and_eigenvalues', True, ['orbitals_a', 'orbitals_b', 'eigenvalues_a', 'fock_a', 'fock_b'
                                        ], ['orbitals_a', 'eigenvalues_a']),
    ('return_results', True, ['orbitals_a', 'fock_a', 'fock_b'], ['orbitals_a', 'fock_a']),
])
def test_wavefunction_protocols(protocol, restricted, provided, expected, wavefunction_data_fixture):

    wfn_data = wavefunction_data_fixture["wavefunction"]

    if protocol is None:
        wavefunction_data_fixture.pop("protocols")
    else:
        wavefunction_data_fixture["protocols"]["wavefunction"] = protocol

    wfn_data["restricted"] = restricted
    bas = wfn_data["basis"]

    for name in provided:
        scf_name = "scf_" + name
        wfn_data[name] = scf_name
        if "eigen" in name:
            wfn_data[scf_name] = np.random.rand(bas.nbf)
        else:
            wfn_data[scf_name] = np.random.rand(bas.nbf, bas.nbf)

    wfn = qcel.models.Result(**wavefunction_data_fixture)

    if len(expected) == 0:
        assert wfn.wavefunction is None
    else:
        expected_keys = (set(expected) | {"scf_" + x for x in expected} | {"basis", "restricted"})
        assert wfn.wavefunction.dict().keys() == expected_keys


@pytest.mark.parametrize("keep, indices", [
    (None, [0, 1, 2, 3, 4]),
    ('all', [0, 1, 2, 3, 4]),
    ('initial_and_final', [0, 4]),
    ('final', [4]),
    ('none', []),
])
def test_optimization_trajectory_protocol(keep, indices, optimization_data_fixture):

    if keep is not None:
        optimization_data_fixture["protocols"] = {"trajectory": keep}
    opt = qcel.models.Optimization(**optimization_data_fixture)

    assert len(opt.trajectory) == len(indices)
    for result, index in zip(opt.trajectory, indices):
        assert result.return_result == index