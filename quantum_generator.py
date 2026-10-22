from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

def generate_dynamic_circuit(n_qubits: int):
    qc = QuantumCircuit(n_qubits)
    for n in range(n_qubits):
        qc.h(n)
    return qc

def get_results(qc: QuantumCircuit, n_shots: int):
    sampler = StatevectorSampler()
    result = sampler.run([qc], shots=n_shots).result()
    return result

def generate_and_measure(n_qubits: int, n_shots: int):
    dqc = generate_dynamic_circuit(n_qubits)
    dqc.measure_all()
    results = get_results(dqc, n_shots)
    return results

results = generate_and_measure(1, 1000)
print(results[0].data.meas.get_counts())
bitstrings = results[0].data.meas.get_bitstrings()
bitstrings = [int(b, 2) for b in bitstrings]
print(bitstrings)